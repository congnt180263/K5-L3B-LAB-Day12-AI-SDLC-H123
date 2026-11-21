"""Khởi chạy benchmark canvas với Node.js và Chromium."""

import argparse
import math
import subprocess
import sys
from pathlib import Path


def main(argv=None):
    parser = argparse.ArgumentParser(description="Đo hiệu năng render cảnh Lặn & Hái")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error("--duration phải là số hữu hạn dương")
    driver = Path(__file__).resolve().parent.parent / "tools" / "bench.mjs"
    try:
        return subprocess.call(["node", str(driver), sys.executable, str(args.seed),
                                str(args.duration), str(args.out.resolve())])
    except FileNotFoundError:
        parser.exit(1, "Benchmark cần Node.js 22 trở lên trong PATH.\n")


if __name__ == "__main__":
    raise SystemExit(main())
