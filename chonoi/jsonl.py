"""Ghi JSONL tất định: làm tròn 3 chữ số khi XUẤT (tính toán dùng giá trị chính xác)."""

import json
import os
import tempfile


def _clean(v):
    if isinstance(v, float):
        r = round(v, 3)
        return 0.0 if r == 0 else r  # tránh -0.0
    if isinstance(v, dict):
        return {k: x if k == "fresh" else _clean(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_clean(x) for x in v]
    return v


def dumps(obj) -> str:
    return json.dumps(_clean(obj), ensure_ascii=False, separators=(",", ":"))


class JsonlWriter:
    def __init__(self, path: str):
        self._path = os.path.abspath(path)
        fd, self._temporary = tempfile.mkstemp(prefix=".chonoi-", dir=os.path.dirname(self._path))
        self._f = os.fdopen(fd, "w", encoding="utf-8", newline="\n")

    def write(self, obj):
        self._f.write(dumps(obj) + "\n")

    def close(self, commit=True):
        try:
            self._f.close()
            if commit:
                os.replace(self._temporary, self._path)
        finally:
            if os.path.exists(self._temporary):
                os.unlink(self._temporary)
