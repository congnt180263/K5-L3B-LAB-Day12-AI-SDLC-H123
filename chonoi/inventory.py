"""File kho v1.0 (Contract G): {"items": {id: số nguyên >= 0}}.

Đọc: từ chối sai schema / id lạ / số âm (BadInput -> mã 2).
Ghi: bỏ mục bằng 0, qua file tạm cùng thư mục rồi thay thế, byte-ổn-định.
"""

import json
import math
import os
import tempfile
from fractions import Fraction

from .errors import BadInput
from .ids import sort_by_id

KINDS_P1 = ("ca_loc", "ca_linh", "bong_dien_dien", "bong_sung")
KINDS_V11 = ("ca_loc", "ca_linh", "ca_keo", "bong_dien_dien", "bong_sung", "keo_neo")


def menu_ingredients(menu):
    """Các loại nguyên liệu quán hỗ trợ theo cấu hình menu đang chạy."""
    return frozenset(kind for dish in menu.values() for kind in dish["recipe"])


def validate_items(items, kinds=KINDS_P1):
    if not isinstance(items, dict):
        raise BadInput("items phải là object")
    out = {}
    for k, v in items.items():
        if k not in kinds:
            raise BadInput(f"nguyên liệu lạ: {k}")
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise BadInput(f"số lượng không hợp lệ cho {k}: {v!r}")
        if v > 0:
            out[k] = v
    return out


def individual_items(items, kinds=KINDS_V11):
    if not isinstance(items, list):
        raise BadInput("items phải là mảng cá thể")
    result, ids = [], set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "fresh"}:
            raise BadInput("cá thể phải có id, kind và fresh")
        ident, kind, fresh = item["id"], item["kind"], item["fresh"]
        if not isinstance(ident, str) or not ident or ident in ids:
            raise BadInput("id cá thể trùng hoặc không hợp lệ")
        if not isinstance(kind, str) or kind not in kinds:
            raise BadInput(f"nguyên liệu lạ: {kind}")
        if isinstance(fresh, bool) or not isinstance(fresh, (int, float, Fraction)) or not 0 <= fresh <= 100:
            raise BadInput("fresh phải là số hữu hạn trong [0, 100]")
        ids.add(ident)
        result.append(dict(item, fresh=Fraction(str(fresh))))
    return result


def item_rows(items, threshold=None):
    rows = []
    for item in items:
        fresh = item["fresh"]
        value = float(fresh)
        if value == threshold and fresh < threshold:
            value = math.nextafter(value, -math.inf)
        rows.append(dict(item, fresh=value))
    return rows


def age_items(items, decay, threshold, location, events):
    spoiled = []
    for item in items:
        before = item["fresh"]
        if before == 0:
            continue
        item["fresh"] = max(Fraction(0), before - decay)
        if before >= threshold > item["fresh"]:
            spoiled.append(item)
    for item in sort_by_id(spoiled):
        events.append(("spoiled", {"item_id": item["id"], "kind": item["kind"], "location": location}))
    return {item["id"] for item in spoiled}


def read_inventory(path: str, kinds=KINDS_V11, *, individual=False):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        raise BadInput(f"không đọc được file kho {path}: {e}")
    if not isinstance(data, dict) or set(data.keys()) != {"items"}:
        raise BadInput("file kho chỉ được có khóa gốc 'items'")
    validate = individual_items if individual else validate_items
    return validate(data["items"], kinds)


def hold_to_items(hold: list) -> dict:
    """Khoang (mảng id theo thứ tự nhặt) -> object đếm, sắp theo id nguyên liệu."""
    counts = {}
    for k in hold:
        counts[k] = counts.get(k, 0) + 1
    return {k: counts[k] for k in sorted(counts)}


def write_inventory(path: str, items):
    if isinstance(items, list):
        items = item_rows(sort_by_id(items))
    else:
        items = {k: items[k] for k in sorted(items) if items[k] > 0}
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".inv-", suffix=".tmp", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"items": items}, f, ensure_ascii=False, separators=(",", ":"))
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
