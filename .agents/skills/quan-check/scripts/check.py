"""Repeatable TV3 verification command; no Git mutations."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[4]
PROOF = ROOT / 'docs' / 'proof' / 'phase-2'


def main():
    PROOF.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               PYTHONPATH=os.pathsep.join((str(ROOT / 'tests'), str(ROOT))))
    for name, args in (
        ('tests', ['-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        ('team', ['tools/check_team.py']),
    ):
        result = subprocess.run([sys.executable, *args], cwd=ROOT, env=env,
                                capture_output=True, encoding='utf-8')
        (PROOF / f'quan-{name}.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            print(f'FAIL: {name}; see {PROOF}')
            return result.returncode
    with tempfile.TemporaryDirectory() as temp:
        p = Path(temp)
        dish = 'ca_keo_nuong'
        fixture = {'quan': {'stock': {'ca_keo': 2, 'keo_neo': 1}, 'random_customers': False,
                           'player': {'pos': [5, 8]}, 'time_left_ticks': 600,
                           'customers': [{'id': 'C1', 'table_id': 'T4', 'dish_id': dish}]}}
        (p / 'fixture.json').write_text(json.dumps(fixture), encoding='utf-8')
        (p / 'inputs.json').write_text(json.dumps({'frames': [
            {'tick': 0, 'interact': True}, {'tick': 1, 'interact': False},
            {'tick': 360, 'interact': True}]}), encoding='utf-8')
        for name in ('first', 'repeat'):
            subprocess.run([sys.executable, '-m', 'chonoi.headless', '--mode', 'quan',
                            '--seed', '1', '--ticks', '600', '--scenario', str(p / 'fixture.json'),
                            '--inputs', str(p / 'inputs.json'), '--out', str(p / f'{name}.jsonl')],
                           cwd=ROOT, env=env, check=True)
        first = (p / 'first.jsonl').read_bytes()
        if first != (p / 'repeat.jsonl').read_bytes():
            raise RuntimeError('JSONL differs for identical input')
        rows = [json.loads(line) for line in first.splitlines()]
        events = [r for r in rows if r['type'] == 'event']
        expected = ['cook_started', 'dish_ready', 'dish_picked', 'customer_left', 'quan_end']
        if [e['name'] for e in events] != expected or events[0]['data']['stove_id'] != 'B2':
            raise RuntimeError('Incorrect B2 lifecycle')
        if rows[-1]['reason'] != 'time':
            raise RuntimeError('Shift failed to close')
        (PROOF / 'quan-headless.jsonl').write_bytes(first)
        # Real CLI inventory input must accept both new kinds.
        (p / 'inventory.json').write_text(json.dumps({'items': {'ca_keo': 2, 'keo_neo': 1}}), encoding='utf-8')
        subprocess.run([sys.executable, '-m', 'chonoi.headless', '--mode', 'quan', '--seed', '1',
                        '--ticks', '0', '--inventory', str(p / 'inventory.json'), '--out', str(p / 'inv.jsonl')],
                       cwd=ROOT, env=env, check=True)
        # Service on the final tick must be paid before quan_end.
        block = fixture['quan']
        block.pop('stock')
        block.update(time_left_ticks=1, player={'pos': [13, 6]},
                     hand={'order_id': 'C1', 'dish_id': dish, 'base_price': 70})
        block['customers'][0].update(order_status='assigned', patience_ticks_left=1)
        (p / 'fixture.json').write_text(json.dumps(fixture), encoding='utf-8')
        subprocess.run([sys.executable, '-m', 'chonoi.headless', '--mode', 'quan', '--seed', '1',
                        '--ticks', '1', '--scenario', str(p / 'fixture.json'), '--inputs', str(p / 'inputs.json'),
                        '--out', str(p / 'closing.jsonl')], cwd=ROOT, env=env, check=True)
        closing = [json.loads(line) for line in (p / 'closing.jsonl').read_text(encoding='utf-8').splitlines()]
        if [r['name'] for r in closing if r['type'] == 'event'] != ['served', 'paid', 'quan_end']:
            raise RuntimeError('Closing service order failed')
        if closing[-1]['money'] != 70:
            raise RuntimeError('Closing payment failed')
    (PROOF / 'quan-smoke.txt').write_text(
        'PASS: identical headless JSONL bytes; B2 cook/ready/pick; T4 closing service/payment; '
        'CLI inventory accepts ca_keo and keo_neo.\n', encoding='utf-8')
    print(f'PASS: tests, team, headless determinism and closing; logs: {PROOF}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
