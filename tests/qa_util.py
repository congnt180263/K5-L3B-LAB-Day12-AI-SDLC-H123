"""Tiện ích riêng của QA (TV5) cho test hộp đen. Chỉ chạy `headless_cmd`, không import code game.

Lớp tương thích schema kho (dùng cho hồi quy P1/P2, `compat=True`):
TICKET-03 đổi kho đếm `{kind: số}` thành kho cá thể `[{id,kind,fresh}]` từ contract 1.2. Test hồi quy P1/P2 vẫn
viết fixture dạng đếm cho dễ đọc; khi contract >= 1.2, `run(..., compat=True)` tự đổi fixture sang dạng cá thể và
chuẩn hóa output về dạng đếm để kiểm cùng luật cũ. Fixture cố tình sai (kind lạ, số âm, số thực...) KHÔNG đổi nên
vẫn bị từ chối mã 2. Test P3/P4 gọi `run` mặc định (compat=False) để đọc đúng output thô v1.2.
"""

import copy
import functools
import json
import math
import os

from helpers import Workdir, frames, read_jsonl, run_headless, write_json

KINDS = {"ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo"}


def contract_version():
    with open("game.contract.json", encoding="utf-8") as f:
        return tuple(int(x) for x in json.load(f)["contract_version"].split("."))


V12 = contract_version() >= (1, 2)


def price_after(list_price, fresh_avg):
    """Giá chốt khi nấu (TICKET-03): floor(giá niêm yết × TB fresh / 100). Trước v1.2 là giá niêm yết."""
    return math.floor(list_price * fresh_avg / 100) if V12 else list_price


QUAN_TICK_DECAY = 0.25 / 60  # kho quán hao 0.25/s (TICKET-03)


# ---------- fixture: dạng đếm -> dạng cá thể -------------------------------------------------------------
def _valid_counts(d):
    return isinstance(d, dict) and all(k in KINDS and isinstance(v, int) and not isinstance(v, bool) and v >= 0
                                       for k, v in d.items())


def items_from(counts_or_kinds, start=1):
    """{kind: n} hoặc [kind, ...] -> [{id: I<start..>, kind, fresh: 100}] theo thứ tự xuất hiện."""
    kinds = counts_or_kinds if isinstance(counts_or_kinds, list) else \
        [k for k, n in counts_or_kinds.items() for _ in range(n)]
    return [{"id": f"I{start + i}", "kind": k, "fresh": 100} for i, k in enumerate(kinds)]


def fx_block(mode, block):
    """Đổi khối scenario dạng đếm sang dạng cá thể khi contract >= 1.2 (giữ nguyên fixture cố tình sai)."""
    if not V12 or block is None:
        return block
    b = copy.deepcopy(block)
    if mode in ("gather", "day") and isinstance(b.get("hold"), list) and all(isinstance(k, str) for k in b["hold"]):
        b["hold"] = items_from(b["hold"])
    if mode in ("quan", "day") and _valid_counts(b.get("stock")):
        b["stock"] = items_from(b["stock"])
        free = list(b["stock"])
        for c in b.get("customers", []):
            r = c.get("reserved")
            if _valid_counts(r):
                ids = []
                for kind, n in r.items():
                    for _ in range(n):
                        it = next((x for x in free if x["kind"] == kind), None)
                        if it is None:
                            ids.append(f"I9{len(ids) + 90}")  # không đủ hàng: id không tồn tại -> vẫn là fixture sai
                        else:
                            free.remove(it)
                            ids.append(it["id"])
                c["reserved"] = ids
    elif mode in ("quan", "day") and "stock" not in b:
        for c in b.get("customers", []):
            if _valid_counts(c.get("reserved")) and c["reserved"]:
                c["reserved"] = [f"I9{90 + i}" for i in range(sum(c["reserved"].values()))]  # giữ chỗ mà không có kho
            elif c.get("reserved") == {}:
                c["reserved"] = []
    return b


def fx_stock(d):
    """Kho dạng đếm -> mảng cá thể khi contract >= 1.2 (cho test gọi QuanSim trực tiếp)."""
    return items_from(d) if V12 and _valid_counts(d) else d


def fx_inventory(inv):
    if V12 and isinstance(inv, dict) and set(inv) == {"items"} and _valid_counts(inv["items"]):
        return {"items": items_from(inv["items"])}
    return inv


# ---------- output: dạng cá thể -> dạng đếm --------------------------------------------------------------
def counts(items):
    if isinstance(items, dict):
        return {k: items[k] for k in sorted(items) if items[k] > 0}
    out = {}
    for x in items or []:
        k = x["kind"] if isinstance(x, dict) else x
        out[k] = out.get(k, 0) + 1
    return {k: out[k] for k in sorted(out)}


def kinds(items):
    return [x["kind"] if isinstance(x, dict) else x for x in items or []]


def _norm_rows(rows):
    for r in rows or []:
        if r["type"] == "snapshot":
            idkind = {x["id"]: x["kind"] for x in r.get("stock") or [] if isinstance(x, dict)}
            if isinstance(r.get("hold"), list):
                r["hold"] = kinds(r["hold"])
            if isinstance(r.get("stock"), list):
                r["stock"] = counts(r["stock"])
            for c in r.get("customers") or []:
                if isinstance(c.get("reserved"), list):
                    c["reserved"] = counts([idkind.get(i, "?") for i in c["reserved"]])
        elif r["type"] == "event":
            d = r.get("data") or {}
            inv = d.get("inventory")
            if isinstance(inv, dict) and isinstance(inv.get("items"), list):
                inv["items"] = counts(inv["items"])
            for key in ("lost", "items"):
                if isinstance(d.get(key), list) and d[key] and isinstance(d[key][0], dict):
                    d[key] = kinds(d[key])
    return rows


# ---------- chạy headless ---------------------------------------------------------------------------------
def run(mode, scenario=None, inputs=None, ticks=60, seed=1, every=1, inventory=None, inv_out=False, days=None,
        raw_scenario=None, compat=False):
    """Chạy headless một lần. Trả dict: code, err, rows, saved (nội dung file kho ghi ra hoặc None), files (tên file thừa).

    scenario: khối của mode (không cần bọc). inventory: dict `{"items": ...}` hoặc dữ liệu thô để thử sai schema.
    compat=True: dùng lớp tương thích schema kho (xem đầu file).
    """
    if compat:
        scenario = fx_block(mode, scenario)
        inventory = fx_inventory(inventory)
        if isinstance(raw_scenario, dict):
            raw_scenario = {k: fx_block(k, v) if isinstance(v, dict) else v for k, v in raw_scenario.items()}
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
    if compat:
        _norm_rows(rows)
        if isinstance(saved, dict) and isinstance(saved.get("items"), list):
            saved = {"items": counts(saved["items"])}
    return {"code": code, "err": err, "rows": rows, "saved": saved, "files": files}


run_compat = functools.partial(run, compat=True)  # dùng cho test hồi quy P1/P2


def snap(rows, tick):
    return next(s for s in rows if s["type"] == "snapshot" and s["tick"] == tick)


def ev(rows, name=None):
    return [r for r in rows if r["type"] == "event" and (name is None or r["name"] == name)]


def ev_at(rows, tick):
    return [r["name"] for r in rows if r["type"] == "event" and r["tick"] == tick]
