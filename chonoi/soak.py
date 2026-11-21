"""Chạy nhiều Ngày không render và ghi kết quả khi từng Shop đóng."""

import argparse
import json
import time
from pathlib import Path

from .contract import load_contract
from .inputs import InputState
from .runner import Session


def simulate(tuning, seed, days):
    start = time.perf_counter()
    session = Session("day", tuning, {}, seed, days=days)
    idle = InputState((0, 0), {}, set())
    max_day_ticks = (sum(round(tuning[phase]["duration_s"] * tuning["tick_hz"])
                         for phase in ("gather", "quan")) + tuning["shop"]["max_ticks"])
    results = []
    for _ in range(max_day_ticks * days):
        for event in session.step(idle):
            if event["name"] == "shop_end":
                snapshot = session.snapshot()
                results.append({"day": event["day"], **{k: snapshot[k]
                                for k in ("earned", "reputation", "score")}})
        if session.done:
            break
    return {"days": days, "days_completed": session.sim.days_completed,
            "crashes": 0, "results": results, "duration_s": time.perf_counter() - start}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Chạy kiểm chứng nhiều Ngày không render")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--days", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.days < 1:
        parser.error("--days phải là số nguyên dương")
    result = simulate(load_contract()["tuning"], args.seed, args.days)
    args.out.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0 if result["days_completed"] == args.days else 1


if __name__ == "__main__":
    raise SystemExit(main())
