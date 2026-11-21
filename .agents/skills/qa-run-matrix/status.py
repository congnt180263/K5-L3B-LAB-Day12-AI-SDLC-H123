"""Chạy bộ test QA và in trạng thái từng AC (đạt / chưa đạt) để điền ma trận docs/verification/phase-n.md.

    python .agents/skills/qa-run-matrix/status.py --phase 1 [--log docs/proof/phase-1/qa_tests.txt]

Quy ước: test tên `test_ac_p<phase>_<NN>_...` thuộc AC-P<phase>-<NN>. AC đỏ nếu bất kỳ test (kể cả subTest) của nó đỏ.
Phase 2 tự đặt QA_P2=1 để bật test v1.1 (mặc định chúng bị bỏ qua khi contract_version còn 1.0).
Chỉ dùng thư viện chuẩn. Không sửa file nào trừ --log.
"""

import argparse
import io
import os
import re
import subprocess
import sys
import unittest
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def method_of(test):
    return getattr(getattr(test, "test_case", test), "_testMethodName", "")


def all_methods(suite):
    for t in suite:
        if isinstance(t, unittest.TestSuite):
            yield from all_methods(t)
        else:
            yield method_of(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="1")
    ap.add_argument("--log")
    a = ap.parse_args()
    os.chdir(ROOT)
    sys.path[:0] = ["tests", "."]
    if a.phase in ("2", "3", "4"):
        os.environ["QA_P" + a.phase] = "1"  # bật test v1.1 / v1.2 / v1.3 (mặc định bị bỏ qua khi contract chưa lên)
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_qa_*.py")
    methods = list(all_methods(suite))  # phải lấy TRƯỚC khi chạy: unittest giải phóng danh sách test sau khi chạy
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    pat = re.compile(rf"test_ac_p{a.phase}_(\d\d)")
    acs, red = {}, {}
    for m in methods:
        g = pat.match(m)
        if g:
            acs.setdefault(g.group(1), set()).add(m)
    for t, tb in result.failures + result.errors:
        g = pat.match(method_of(t))
        if g:
            red.setdefault(g.group(1), []).append(tb.strip().splitlines()[-1][:150])
    skipped = {pat.match(method_of(t)).group(1) for t, _ in result.skipped if pat.match(method_of(t))}
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    print(f"# Phase {a.phase} @ {commit}: {result.testsRun} test, {len(result.failures)} đỏ, {len(result.errors)} lỗi, {len(result.skipped)} bỏ qua\n")
    print("| AC | Kết quả | Ghi chú (dòng lỗi đầu) |\n|---|---|---|")
    for k in sorted(acs):
        state = "chưa đạt" if k in red else "bỏ qua" if k in skipped else "đạt"
        print(f"| AC-P{a.phase}-{k} | {state} | {(red.get(k) or [''])[0]} |")
    n = {s: sum(1 for k in acs if (("chưa đạt" if k in red else "bỏ qua" if k in skipped else "đạt") == s)) for s in ("đạt", "chưa đạt", "bỏ qua")}
    print(f"\nTổng AC có test: {len(acs)} — đạt {n['đạt']}, chưa đạt {n['chưa đạt']}, bỏ qua {n['bỏ qua']}. AC không có test thì ghi `chưa kiểm`.")
    if a.log:
        os.makedirs(os.path.dirname(a.log) or ".", exist_ok=True)
        with open(a.log, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# Log test QA phase {a.phase} @ {commit} ({datetime.now():%Y-%m-%d %H:%M})\n# Lệnh: python .agents/skills/qa-run-matrix/status.py --phase {a.phase}\n\n{stream.getvalue()}")
        print(f"Đã lưu log: {a.log}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
