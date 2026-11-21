import { spawn, spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';

const [, , python, seed, duration, output] = process.argv;
const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function browserPath() {
  if (process.env.CHONOI_BROWSER) return process.env.CHONOI_BROWSER;
  const candidates = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    ...[process.env.ProgramFiles, process.env['ProgramFiles(x86)'], process.env.LOCALAPPDATA]
      .filter(Boolean).flatMap(base => [
        join(base, 'Google', 'Chrome', 'Application', 'chrome.exe'),
        join(base, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
      ]),
  ];
  const installed = candidates.find(existsSync);
  if (installed) return installed;
  for (const command of ['chromium', 'chromium-browser', 'google-chrome', 'microsoft-edge']) {
    if (spawnSync(command, ['--version'], { stdio: 'ignore' }).status === 0) return command;
  }
  throw new Error('Cần Chrome, Chromium hoặc Edge. Có thể chỉ đường dẫn bằng CHONOI_BROWSER.');
}

function waitForAddress(child, stream, pattern) {
  return new Promise((resolveAddress, rejectAddress) => {
    let transcript = '';
    const stop = (reason, address) => {
      clearTimeout(timer);
      stream.off('data', onData);
      child.off('exit', onExit);
      child.off('error', onError);
      if (reason) rejectAddress(reason);
      else resolveAddress(address);
    };
    const onData = chunk => {
      transcript += chunk;
      const address = transcript.match(pattern)?.[0];
      if (address) stop(null, address);
    };
    const onExit = code => stop(new Error(`Tiến trình thoát mã ${code}: ${transcript}`));
    const onError = error => stop(error);
    const timer = setTimeout(() => stop(new Error(`Không nhận địa chỉ sau 12 giây: ${transcript}`)), 12000);
    stream.on('data', onData);
    child.once('exit', onExit);
    child.once('error', onError);
  });
}

async function connect(address) {
  const ws = new WebSocket(address);
  await new Promise((ok, fail) => {
    ws.addEventListener('open', ok, { once: true });
    ws.addEventListener('error', fail, { once: true });
  });
  let nextId = 0;
  const pending = new Map();
  ws.addEventListener('message', ({ data }) => {
    const reply = JSON.parse(data);
    const match = pending.get(reply.id);
    if (!match) return;
    pending.delete(reply.id);
    clearTimeout(match.timer);
    if (reply.error) match.reject(new Error(reply.error.message));
    else match.resolve(reply.result);
  });
  return {
    close: () => ws.close(),
    call: (method, params = {}, sessionId) => new Promise((resolveCall, reject) => {
      const id = ++nextId;
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error(`Hết giờ chờ Chromium ${method}`));
      }, 8000);
      pending.set(id, { resolve: resolveCall, reject, timer });
      ws.send(JSON.stringify({ id, method, params, sessionId }));
    }),
  };
}

function measureFrames(started, seconds) {
  let warmup, previous, loadMs;
  const intervals = [];
  let totalMs = 0;
  window.__chonoiRendered = t => {
    if (warmup === undefined) {
      loadMs = Date.now() - started;
      warmup = t + 3000;
    }
    if (t < warmup || window.__chonoiBench) return;
    if (previous !== undefined) {
      totalMs += t - previous;
      intervals.push(t - previous);
    }
    previous = t;
    if (totalMs < seconds * 1000) return;
    const frames = intervals.length;
    const measured_s = totalMs / 1000;
    const slow = intervals.sort((a, b) => b - a).slice(0, Math.max(1, Math.ceil(frames * 0.01)));
    window.__chonoiBench = {
      avg_fps: frames / measured_s,
      p1_low_fps: 1000 * slow.length / slow.reduce((sum, item) => sum + item, 0),
      frames, measured_s, load_ms: loadMs,
    };
  };
}

async function measure() {
  const binary = browserPath();
  const started = Date.now();
  const temporaryRoot = resolve(tmpdir());
  const profile = await mkdtemp(join(temporaryRoot, 'chonoi-bench-'));
  const server = spawn(python, ['-X', 'utf8', '-m', 'chonoi.live', '--mode', 'gather', '--seed', seed, '--port', '0'],
    { cwd: root, stdio: ['ignore', 'pipe', 'inherit'] });
  let chromium, devtools;
  try {
    const url = await waitForAddress(server, server.stdout, /http:\/\/127\.0\.0\.1:\d+\//);
    chromium = spawn(binary, ['--headless=new', '--remote-debugging-port=0', '--no-first-run',
      '--disable-background-networking', '--disable-background-timer-throttling', '--window-size=1280,720',
      `--user-data-dir=${profile}`, ...(process.getuid?.() === 0 ? ['--no-sandbox'] : []), 'about:blank'],
    { stdio: ['ignore', 'ignore', 'pipe'] });
    const address = await waitForAddress(chromium, chromium.stderr, /ws:\/\/127\.0\.0\.1:\d+\/devtools\/browser\/[^\s]+/);
    chromium.stderr.resume();
    devtools = await connect(address);
    const { targetId } = await devtools.call('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await devtools.call('Target.attachToTarget', { targetId, flatten: true });
    const call = (method, params) => devtools.call(method, params, sessionId);
    await call('Page.enable');
    await call('Emulation.setDeviceMetricsOverride', { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
    await call('Page.addScriptToEvaluateOnNewDocument',
      { source: `(${measureFrames})(${started}, ${Number(duration)});` });
    await call('Page.navigate', { url });
    const deadline = Date.now() + (Number(duration) + 15) * 1000;
    while (Date.now() < deadline) {
      const result = await call('Runtime.evaluate', { expression: 'window.__chonoiBench || null', returnByValue: true });
      if (result.result?.value) {
        await writeFile(output, JSON.stringify(result.result.value) + '\n');
        return;
      }
      await delay(250);
    }
    throw new Error('Không nhận đủ khung hình từ cảnh Lặn & Hái.');
  } finally {
    if (devtools) {
      await devtools.call('Browser.close').catch(() => {});
      devtools.close();
    }
    chromium?.kill();
    server.kill();
    if (dirname(resolve(profile)) === temporaryRoot) {
      await rm(profile, { recursive: true, force: true, maxRetries: 5, retryDelay: 200 });
    }
  }
}

await measure().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
