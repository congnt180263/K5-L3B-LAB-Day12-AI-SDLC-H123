"""Tiện ích riêng của QA (TV5) cho test hộp đen. Chỉ chạy `headless_cmd`, không import code game."""

import json
import os

from helpers import Workdir, frames, read_jsonl, run_headless, write_json


def run(mode, scenario=None, inputs=None, ticks=60, seed=1, every=1, inventory=None, inv_out=False, days=None, raw_scenario=None):
    """Chạy headless một lần. Trả dict: code, err, rows, saved (nội dung file kho ghi ra hoặc None), files (tên file thừa).

    scenario: khối của mode (không cần bọc). inventory: dict `{"items": ...}` hoặc dữ liệu thô để thử sai schema.
    """
    with Workdir() as w:
        out = w.path("o.jsonl")
        args = ["--mode", mode, "--seed", str(seed), "--ticks", str(ticks), "--snapshot-every", str(every), "--out", out]
        if scenario is not None:
            args += ["--scenario", write_json(w.path("sc.json"), {mode: scenario})]
        if raw_scenario is not None:  # nguyên file scenario (ví dụ khối `day` + `gather` của mode day)
            args += ["--scenario", write_json(w.path("sc.json"), raw_scenario)]
        if days is not None:
            args += ["--days", str(days)]
        if inputs:
            args += ["--inputs", write_json(w.path("in.json"), frames(*inputs))]
        if inventory is not None:
            args += ["--inventory", write_json(w.path("inv_in.json"), inventory)]
        if inv_out:
            args += ["--inventory-out", w.path("inv.json")]
        code, err = run_headless(*args)
        rows = read_jsonl(out) if os.path.exists(out) else None
        saved = None
        if inv_out and os.path.exists(w.path("inv.json")):
            with open(w.path("inv.json"), encoding="utf-8") as f:
                saved = json.load(f)
        files = sorted(os.listdir(os.path.dirname(out)))
        return {"code": code, "err": err, "rows": rows, "saved": saved, "files": files}


def snap(rows, tick):
    return next(s for s in rows if s["type"] == "snapshot" and s["tick"] == tick)


def ev(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


def ev_at(rows, tick):
    return [r["name"] for r in rows if r["type"] == "event" and r["tick"] == tick]
