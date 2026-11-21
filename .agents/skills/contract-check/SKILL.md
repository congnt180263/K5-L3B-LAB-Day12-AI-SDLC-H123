---
name: contract-check
description: Kiểm tra quy ước Test Contract, hợp đồng kho/sự kiện, tính tất định và thành viên trước khi commit hoặc gắn tag.
---

# Contract Check (H123)

Chạy kiểm tra nhanh trước mọi commit/PR lên `main`:

1. **Không vi phạm quy tắc vàng trong `AGENTS.md`:**
   - Không hard-code số liệu cân bằng game (`duration_s`, `swim_speed`, `hold_capacity`, `cook_s`, `price`, ...); luôn đọc từ `game.contract.json`.
   - Không dùng `random` toàn cục hay `time.time()`/`datetime` trong `chonoi/sim/*`; mọi ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`).
   - Mọi danh sách thực thể trước khi duyệt/xuất snapshot đều sắp bằng `ids.sort_by_id`.
   - Sáng tạo thêm (hiệu ứng, âm thanh, đồ họa) chỉ nằm ở UI/live và **tắt hoàn toàn** ở `headless`.
2. **Kiểm tra thành viên & test:**
   - Chạy `python tools/check_team.py` (trên Linux/CI dùng `python3`).
   - Chạy `PYTHONPATH=tests:. python -m unittest discover -s tests -v`.
   - Nếu đổi hợp đồng (`docs/contracts/README.md` hoặc `game.contract.json`), phải báo cả nhóm và tạo/cập nhật ADR trong `docs/adr/`.
