# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 3 | dvq2609 | Codex | Đọc TICKET-03, tích hợp kho cá thể, độ tươi, giữ chỗ và bàn giao. | Chưa đo | Kiểm thứ tự ươn và nấu bằng QA hộp đen. |
| 4 | dvq2609 | Codex | Benchmark canvas, soak, HUD tương phản, kiểm hồi quy và chuẩn bị gói phát hành. | Chưa đo | Benchmark ban đầu chờ Page API đến hết giờ, sau đó chạy lại với Page.enable và kiểm artifact thật. |
| 1 | `congnt180263` | Antigravity (Gemini) | Kickoff (`TEAM.md`, `contracts`, `plan`, skills) + `gather.py` Lát 1 & 2 + `test_gather_rules.py` | ~25k tokens | AI dùng sai tên khóa payload (`count` thay vì `amount`/`yield`, `oxygen_empty` dùng `pos` thay vì `oxygen_ticks:0`), cho phép bắt một phần khi thiếu chỗ và đặt cooldown khi bắt hụt; đã phát hiện qua bộ test QA `test_qa_gather.py` và sửa lại đúng PRD-0. |
| 2 | `congnt180263` | Antigravity (Gemini) | Vá 6 lỗi `gather` P1 + nâng cấp `game.contract.json` v1.1 + cá bơi/sinh, Cá Sấu M1/M2, `DaySim` & Shop (`day.py`, `runner.py`, `headless.py`, `scenario.py`) + `test_gather_p2.py` | ~30k tokens | AI gõ thừa dấu ngoặc ở lệnh edit `headless.py` (đã sửa ngay); toàn bộ `test_qa_gather.py` (23/23) và `test_qa_p2.py` (12/12) đều xanh. |
| 2 | dvq2609 | Codex | Đối chiếu TICKET-02, cập nhật clarify và cấu hình quán, nối chọn món theo kế hoạch ngày, chạy QA và ghép thử Lát 4. | Chưa đo | Lượt ghép thử cho thấy hàm khởi tạo quán cần giữ cả `day_plan` và thao tác sao chép scenario của TV3. |
