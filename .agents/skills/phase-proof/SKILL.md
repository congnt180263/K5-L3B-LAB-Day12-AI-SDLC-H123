---
name: phase-proof
description: Quy trình chạy kiểm chứng headless, lưu bằng chứng vào docs/proof/phase-n/ và điền ma trận docs/verification/phase-n.md trước khi gắn tag.
---

# Phase Proof & Verification (H123)

Trước mỗi hạn gắn tag (`phase-1` .. `phase-4`), QA Lead (`nvcuong96`) và Integrator (`congnt180263`) thực hiện:

1. **Chạy toàn bộ bộ test tự động** và lưu log đầu ra vào `docs/proof/phase-<n>/unittest.txt`.
2. **Chạy kịch bản headless mẫu** cho cả `gather` và `quan` (kèm truyền file kho từ `gather` sang `quan`):
   - `python -m chonoi.headless --mode gather --seed 1 --ticks 600 --inventory-out docs/proof/phase-<n>/inv.json --out docs/proof/phase-<n>/gather.jsonl`
   - `python -m chonoi.headless --mode quan --seed 1 --ticks 600 --inventory docs/proof/phase-<n>/inv.json --out docs/proof/phase-<n>/quan.jsonl`
3. **Kiểm tra tính tất định (determinism):** chạy lại cùng seed/inputs 2 lần và xác nhận file JSONL đầu ra giống nhau từng byte.
4. **Cập nhật ma trận truy vết** `docs/verification/phase-<n>.md`: điền đủ từng AC, lệnh kiểm chứng, đường dẫn bằng chứng và kết quả trung thực (đạt / chưa đạt).
5. **Chỉ gắn tag** `phase-<n>` khi `main` xanh toàn bộ test và bằng chứng đã được commit.
