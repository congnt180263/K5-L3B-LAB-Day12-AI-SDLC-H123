"""Bảng điểm cục bộ, giữ thứ tự ghi khi hai lượt bằng điểm."""

import json
import os
import tempfile
from pathlib import Path

from .errors import BadInput

DEFAULT_STORE = "leaderboard.json"
FIELDS = {"name", "score", "days_completed", "seed"}


def entries(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except ValueError as e:
        raise BadInput("file bảng xếp hạng không phải JSON hợp lệ") from e
    if not isinstance(data, dict) or set(data) != {"entries"} or not isinstance(data["entries"], list):
        raise BadInput("file bảng xếp hạng phải có mảng entries")
    for row in data["entries"]:
        if (not isinstance(row, dict) or set(row) != FIELDS
                or not isinstance(row["name"], str) or not row["name"].strip()
                or any(type(row[k]) is not int for k in ("score", "days_completed", "seed"))):
            raise BadInput("mục bảng xếp hạng không hợp lệ")
    return sorted(data["entries"], key=lambda row: -row["score"])[:10]


def _write(path, rows):
    path = Path(path).absolute()
    fd, temporary = tempfile.mkstemp(prefix=".leaderboard-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"entries": rows}, f, ensure_ascii=False)
            f.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def record(path, *, name, score, seed):
    path = Path(path)
    with path.with_name(f".{path.name}.lock").open("a+b") as lock:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        rows = entries(path)
        rows.append({"name": name, "score": score, "days_completed": 5, "seed": seed})
        _write(path, sorted(rows, key=lambda row: -row["score"])[:10])


def export(store, output):
    _write(output, entries(store))
