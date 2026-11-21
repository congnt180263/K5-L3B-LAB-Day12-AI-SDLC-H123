# Nhật ký dùng AI (theo phase và theo người)

| Phase | Người | Công cụ / model | Việc | Token / chi phí ước tính | Ghi chú (AI sai ở đâu?) |
|---|---|---|---|---|---|
| 1 | `congnt180263` | Antigravity (Gemini) | Kickoff (`TEAM.md`, `contracts`, `plan`, skills) + `gather.py` Lát 1 & 2 + `test_gather_rules.py` | ~25k tokens | AI dùng sai tên khóa payload (`count` thay vì `amount`/`yield`, `oxygen_empty` dùng `pos` thay vì `oxygen_ticks:0`), cho phép bắt một phần khi thiếu chỗ và đặt cooldown khi bắt hụt; đã phát hiện qua bộ test QA `test_qa_gather.py` và sửa lại đúng PRD-0. |
| 2 | `congnt180263` | Antigravity (Gemini) | Vá 6 lỗi `gather` P1 + nâng cấp `game.contract.json` v1.1 + cá bơi/sinh, Cá Sấu M1/M2, `DaySim` & Shop (`day.py`, `runner.py`, `headless.py`, `scenario.py`) + `test_gather_p2.py` | ~30k tokens | AI gõ thừa dấu ngoặc ở lệnh edit `headless.py` (đã sửa ngay); toàn bộ `test_qa_gather.py` (23/23) và `test_qa_p2.py` (12/12) đều xanh. |
