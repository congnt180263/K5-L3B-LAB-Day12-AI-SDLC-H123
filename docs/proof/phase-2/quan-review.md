# Bằng chứng quán Phase 2

Phạm vi: TV3 phụ trách toàn bộ quán theo TICKET-02, làm trong LAB12 - FINAL trên nhánh nguyentrunghai. Chưa commit/push.

Lệnh tái lập: `python .agents/skills/quan-check/scripts/check.py`.

| Yêu cầu Ticket | Kiểm chứng | Kết quả |
|---|---|---|
| 1.3: B1/B2, T1–T4, sáu món theo dữ liệu | test_quan_phase2: six_dishes, two_stoves, four_tables | Đạt |
| 1.3: giữ nguyên liệu, boa, trả tiền và đóng ca | Full regression và test_settlements; CLI B2/T4 | Đạt |
| 2: lọc món theo kế hoạch; được gọi lại khi vượt số suất | test_day_filter_* | Đạt ở API mô phỏng |
| 2: giữ money/earned/reputation, shift_earned riêng | test_settlements và test_day_filter_allows_repeat_orders | Đạt ở API mô phỏng |
| 4.2: pause đứng mọi timer, resume chạy ngay, không phát lại interact | test_pause_freezes_timers_and_consumes_interact_edge | Đạt ở Session; UI pause chờ TV4 |
| 4.3: kiểm fixture trên kho thực, từ chối món ngoài kế hoạch | test_day_rejects_fixture_* | Đạt ở API mô phỏng |
| Tính xác định và kho mới qua CLI | quan-smoke.txt; hai tiến trình so bytes | Đạt |
| Regression | quan-tests.txt | 67 test OK |
| Thành viên | quan-team.txt | 5 thành viên OK |
| Toàn bộ v1.1/day/Shop/gather P2/UI/hiệu năng 1 Ngày | Chưa nằm trong lát này | Chưa kiểm chứng |

Đổi test P1 có lý do: test_schedule_menu_selection_and_determinism kỳ vọng hai lượt khách vào T1/T2 theo bốn bàn P2. Test reserved_stock không tự thêm T2 nữa vì preset đã có bàn đó. Các luật bao gồm deadline, thứ tự tương tác và thanh toán không bị nới lỏng.

Các file khung sửa để quán nhận nguyên liệu mới và pause: inventory, scenario, contract, headless, live, inputs, runner. Thông tin review nằm trong ADR 0001; schema items không đổi. Cấu hình quán đã chuyển P2, chưa công bố toàn game v1.1.
