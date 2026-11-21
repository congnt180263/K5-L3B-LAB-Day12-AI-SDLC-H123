"""Chạy bản phát hành và hồi quy schema cũ trong bản sao cách ly."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY = ["test_smoke_p1", "test_qa_contract", "test_qa_gather", "test_qa_quan", "test_qa_p2",
          "test_gather_rules", "test_gather_p2", "test_quan_customers"]
CURRENT = ["test_live", "test_python_starter_units", "test_team_check", "test_qa_p3",
           "test_release_flow", "test_qa_p4.P4_Hop_dong", "test_qa_p4.P4_Bench", "test_qa_p4.P4_Soak"]
RELEASE_DOCS = ["readme", "changelog", "license_va_credits", "nhat_ky", "retro", "phan_tu_ca_nhan",
                "leaderboard_cap_co"]


def suite(root, cases):
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((str(root / "tests"), str(root))),
           "PYTHONUTF8": "1", "QA_P4_FULL": "1"}
    return subprocess.call([sys.executable, "-m", "unittest", "-v", *cases], cwd=root, env=env)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("all", "legacy", "current"), default="all")
    parser.add_argument("--published", action="store_true", help="kiểm cả tag Git đã công bố")
    args = parser.parse_args()
    result = 0
    if args.profile != "legacy":
        docs = [
            f"test_qa_p4.P4_Ho_so.test_ac_p4_{ac}_{name}" for ac, name in
            zip(("11", "13", "14", "21", "22", "23", "28"), RELEASE_DOCS)
        ]
        if args.published:
            docs.append("test_qa_p4.P4_Ho_so.test_ac_p4_25_tag_cac_phase")
        print("=== Test Contract v1.3 ===", flush=True)
        result |= suite(ROOT, CURRENT + docs)
    if args.profile != "current":
        print("=== Hồi quy v1.1: kho đếm trong bản sao tạm ===", flush=True)
        with tempfile.TemporaryDirectory(prefix="chonoi-v11-") as directory:
            root = Path(directory)
            for name in ("chonoi", "tests"):
                shutil.copytree(ROOT / name, root / name, ignore=shutil.ignore_patterns("__pycache__"))
            contract = json.loads((ROOT / "game.contract.json").read_text(encoding="utf-8"))
            contract["contract_version"] = "1.1"
            contract["tuning"].pop("freshness", None)
            (root / "game.contract.json").write_text(json.dumps(contract), encoding="utf-8")
            result |= suite(root, LEGACY)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
