"""QA (TV5) — test hộp đen Phase 4 (TICKET-04, Test Contract v1.3): bench, soak, hồ sơ phát hành.

TỰ KÍCH HOẠT: chỉ chạy khi `contract_version == "1.3"` hoặc QA_P4=1 (QA_P4_FULL=1 để chạy soak 10 Ngày đủ).
Lý do: trước v1.3 chưa có bench_cmd/soak_cmd, chạy sẽ làm CI của `main` đỏ vô nghĩa. Kỳ vọng lấy từ TICKET-04.
Test đỏ = lệch ticket: báo chủ lát, không sửa test cho xanh.
"""

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, "tools")
import check_team  # noqa: E402  (đọc bảng TEAM.md bằng đúng code của lab)

with open("game.contract.json", encoding="utf-8") as _f:
    CONTRACT = json.load(_f)
ACTIVE = CONTRACT.get("contract_version") == "1.3" or bool(os.environ.get("QA_P4"))
FULL = bool(os.environ.get("QA_P4_FULL"))
needs_v13 = unittest.skipUnless(ACTIVE, "contract chưa lên 1.3 (đặt QA_P4=1 để chạy thử)")


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def need_cmd(tc, key):
    tc.assertIn(key, CONTRACT, f"game.contract.json chưa khai {key}")
    return shlex.split(CONTRACT[key])


def run_cmd(args, timeout):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def soak(tc, seed, days):
    cmd = need_cmd(tc, "soak_cmd")
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "soak.json")
        p = run_cmd(cmd + ["--seed", str(seed), "--days", str(days), "--out", out], timeout=600)
        tc.assertEqual(p.returncode, 0, f"soak_cmd thoát {p.returncode}: {p.stderr[-200:]}")
        tc.assertTrue(os.path.exists(out), "soak_cmd không tạo soak.json")
        with open(out, encoding="utf-8") as f:
            return json.load(f)


@needs_v13
class P4_Hop_dong(unittest.TestCase):
    def test_ac_p4_01_contract_va_lenh(self):
        self.assertEqual(CONTRACT["contract_version"], "1.3", "AC-P4-01")
        for k in ("bench_cmd", "soak_cmd"):
            self.assertTrue(isinstance(CONTRACT.get(k), str) and CONTRACT[k].strip(), f"AC-P4-01: thiếu {k} ở gốc manifest")


@needs_v13
class P4_Bench(unittest.TestCase):
    def test_ac_p4_02_03_bench_json(self):
        cmd = need_cmd(self, "bench_cmd")
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "bench.json")
            p = run_cmd(cmd + ["--seed", "42", "--duration", "2", "--out", out], timeout=180)
            self.assertEqual(p.returncode, 0, f"AC-P4-02: bench_cmd thoát {p.returncode}: {p.stderr[-200:]}")
            self.assertTrue(os.path.exists(out), "AC-P4-02: không tạo bench.json")
            with open(out, encoding="utf-8") as f:
                b = json.load(f)
        for k in ("avg_fps", "p1_low_fps", "frames", "measured_s", "load_ms"):
            self.assertIn(k, b, f"AC-P4-03: thiếu {k}")
            self.assertTrue(isinstance(b[k], (int, float)) and not isinstance(b[k], bool), f"AC-P4-03: {k} phải là số")
        self.assertGreater(b["frames"], 0)
        self.assertGreater(b["measured_s"], 0)
        self.assertAlmostEqual(b["avg_fps"], b["frames"] / b["measured_s"], delta=max(1.0, 0.02 * b["avg_fps"]),
                               msg="AC-P4-03: avg_fps = frames / measured_s")
        self.assertLessEqual(b["p1_low_fps"], b["avg_fps"] + 1e-6, "AC-P4-03: 1% low không thể cao hơn trung bình")
        self.assertGreaterEqual(b["load_ms"], 0)


@needs_v13
class P4_Soak(unittest.TestCase):
    def test_ac_p4_15_cau_truc_soak(self):
        s = soak(self, 7, 2)
        for k in ("days", "days_completed", "crashes", "results", "duration_s"):
            self.assertIn(k, s, f"AC-P4-15: thiếu {k}")
        self.assertEqual((s["days"], s["days_completed"], s["crashes"]), (2, 2, 0), "AC-P4-15/16")
        self.assertEqual(len(s["results"]), 2)
        for i, r in enumerate(s["results"], 1):
            for k in ("day", "earned", "reputation", "score"):
                self.assertIn(k, r, f"AC-P4-15: results[{i}] thiếu {k}")
            self.assertEqual(r["day"], i)

    def test_ac_p4_17_soak_tat_dinh(self):
        a, b = soak(self, 7, 2), soak(self, 7, 2)
        for x in (a, b):
            x.pop("duration_s", None)
        self.assertEqual(a, b, "AC-P4-17: cùng seed phải cho các trường gameplay giống nhau (bỏ số đo thời gian)")

    def test_ac_p4_18_xuyen_ngay(self):
        s = soak(self, 7, 2)
        earned = [r["earned"] for r in s["results"]]
        self.assertEqual(earned, sorted(earned), "AC-P4-18: earned là tổng thu, không giảm qua các Ngày")
        for r in s["results"]:
            self.assertTrue(0 <= r["reputation"] <= 5, "AC-P4-18: uy tín trong [0,5]")
            self.assertEqual(r["score"], r["earned"] + 100 * int(r["reputation"] // 1), "AC-P4-18: score = earned + 100 × floor(uy tín)")

    @unittest.skipUnless(FULL, "đặt QA_P4_FULL=1 để chạy 10 Ngày")
    def test_ac_p4_16_soak_10_ngay(self):
        s = soak(self, 7, 10)
        self.assertEqual((s["days_completed"], s["crashes"]), (10, 0), "AC-P4-16")
        self.assertEqual(len(s["results"]), 10)


@needs_v13
class P4_Ho_so(unittest.TestCase):
    def test_ac_p4_11_readme(self):
        t = read("README.md") or ""
        for name, pat in (("benchmark", r"bench"), ("headless", r"headless"), ("lệnh test", r"unittest|pytest|test"),
                          ("điều khiển", r"WASD|điều khiển"), ("môi trường", r"Python|macOS|Linux")):
            self.assertRegex(t, re.compile(pat, re.I), f"AC-P4-11: README thiếu {name}")
        self.assertRegex(t, r"(?m)^#+ .*Sáng tạo của nhóm", "AC-P4-11: README thiếu mục riêng 'Sáng tạo của nhóm'")

    def test_ac_p4_13_changelog(self):
        t = (read("CHANGELOG.md") or "").lower()
        for p in range(1, 5):
            self.assertRegex(t, rf"phase[ -]?{p}", f"AC-P4-13: CHANGELOG thiếu Phase {p}")
        self.assertRegex(t, r"breaking|kho cá thể|v1\.2", "AC-P4-13: CHANGELOG chưa ghi breaking change v1.2")

    def test_ac_p4_14_license_va_credits(self):
        self.assertTrue((read("LICENSE") or "").strip(), "AC-P4-14: chưa có LICENSE")
        credits = read("CREDITS.md") or ""
        self.assertRegex(credits, r"CC0|CC-BY|MIT|tự tạo|vẽ", "AC-P4-14: CREDITS.md chưa nêu nguồn/giấy phép tài sản")

    def test_ac_p4_21_nhat_ky(self):
        rows = [l for l in (read("docs/ai-usage-log.md") or "").splitlines() if re.match(r"\|\s*[0-9P]", l)]
        self.assertTrue(rows, "AC-P4-21: ai-usage-log chưa có dòng nào")
        self.assertTrue(any(re.match(r"\|\s*(Phase\s*)?4\b", l) for l in rows), "AC-P4-21: ai-usage-log chưa có dòng Phase 4")
        self.assertTrue([l for l in (read("docs/clarify.md") or "").splitlines() if re.match(r"\|\s*\d", l)], "AC-P4-21: clarify trống")

    def test_ac_p4_22_retro(self):
        t = read("docs/retro.md") or ""
        for head in ("Phase 2", "Phase 4"):
            m = re.search(rf"## {head}[^\n]*\n(.*?)(?=\n## |\Z)", t, re.S)
            self.assertIsNotNone(m, f"AC-P4-22: retro thiếu mục {head}")
            bullets = [b for b in m.group(1).splitlines() if b.strip().startswith("-")]
            self.assertTrue(bullets, f"AC-P4-22: mục {head} không có gạch đầu dòng")
            empty = [b for b in bullets if re.fullmatch(r"-\s*[^:]*:\s*", b.strip())]
            self.assertEqual(empty, [], f"AC-P4-22: mục {head} còn dòng chưa điền: {empty[:2]}")

    def test_ac_p4_23_phan_tu_ca_nhan(self):
        members = check_team.parse_team(read("TEAM.md") or "")
        self.assertEqual(len(members), 5)
        for m in members:
            h = m["handle"]
            t = read(f"docs/members/{h}.md")
            self.assertIsNotNone(t, f"AC-P4-23: thiếu docs/members/{h}.md")
            self.assertNotIn("<github-handle>", t, f"AC-P4-23 {h}: còn nguyên mẫu")
            words = len(re.findall(r"\S+", t))
            self.assertLessEqual(words, 220, f"AC-P4-23 {h}: {words} từ, vượt giới hạn ~200 từ")
            self.assertRegex(t, r"github\.com|commit|[0-9a-f]{7}", f"AC-P4-23 {h}: chưa dẫn commit/bằng chứng")

    def test_ac_p4_25_tag_cac_phase(self):
        p = subprocess.run(["git", "tag", "-l", "phase-*"], capture_output=True, text=True)
        if p.returncode != 0 or not p.stdout.strip():
            self.skipTest("không có tag cục bộ (clone nông hoặc chưa fetch --tags)")
        tags = set(p.stdout.split())
        self.assertEqual({f"phase-{i}" for i in range(1, 4)} - tags, set(), f"AC-P4-25: thiếu tag (có: {sorted(tags)})")

    @unittest.skipUnless("leaderboard" in (CONTRACT.get("extensions") or []), "không khai extensions.leaderboard")
    def test_ac_p4_28_leaderboard_cap_co(self):
        from helpers import run_headless
        with tempfile.TemporaryDirectory() as d:
            out, store = os.path.join(d, "o.jsonl"), os.path.join(d, "lb.json")
            self.assertEqual(run_headless("--mode", "day", "--seed", "1", "--ticks", "0", "--out", out, "--leaderboard", store)[0], 2,
                             "AC-P4-28: thiếu --player-name thì mã 2")
            self.assertEqual(run_headless("--mode", "gather", "--seed", "1", "--ticks", "0", "--out", out,
                                          "--leaderboard", store, "--player-name", "Út Sen")[0], 2, "AC-P4-28: sai mode thì mã 2")


if __name__ == "__main__":
    unittest.main()
