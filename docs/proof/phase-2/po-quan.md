# Phase 2 — Kiểm chứng phần quán của PO

Nguồn yêu cầu là TICKET-02 mục 1.3, 2, 4.3 và 4.5. Chạy trên Windows, Python 3.14.9, với thay đổi Lát 3 trên nền `f240fff`.

| Phạm vi | Kết quả |
|---|---|
| Manifest và quán độc lập | AC-P2-02/23/24 đạt. Kiểm sáu công thức, giá và thời gian nấu trong dữ liệu, tọa độ hai bếp và bốn bàn, lịch khách 120/1020/1920/2820/3720 và tái sử dụng T1 sau khi khách rời cùng tick. |
| Kho món mới | Ba công thức đi qua `--inventory` và khách giữ đúng số lượng tại tick 0. AC-P2-27 còn phụ thuộc bước nấu. |
| Chọn món theo kế hoạch | AC-P2-31 đạt ở lớp `QuanSim`. Kiểm lọc món theo kế hoạch, gọi tiếp khi vượt số suất kế hoạch, `no_dish` nếu chỉ đủ món ngoài kế hoạch và từ chối khách fixture ngoài kế hoạch. |
| Hồi quy giảng viên | 20/20 smoke Phase 1 đạt, gồm chuyển kho `gather` → `quan`. |
| Ghép thử Lát 4 | 25/25 ca quán đạt ở bản sao tạm ghép TV3 `a1379c7`. Gồm chọn bếp và đơn, cả ba món mới phát `cook_started` đúng giá và `dish_ready` đúng tick, cùng các ca trả tiền, boa và đóng ca Phase 1. |

Log gồm [ma trận QA Phase 2](qa_tests.txt), [smoke Phase 1](smoke_p1.txt) và [kết quả ghép thử TV3](po-quan-l4.txt). Ma trận tự động chạy cả các lát đang làm nên còn 28 thất bại và 2 lỗi tổng cộng. Lượt ghép thử dùng bản sao riêng và giữ `day_plan` mới cùng thao tác sao chép scenario của TV3 khi xử lý xung đột tại hàm khởi tạo.

## Bàn giao tích hợp

- Khi chuyển từ `gather` sang `quan`, TV1 truyền kho thực và mục kế hoạch của Ngày đang chơi vào `QuanSim(..., inventory=stock, day_plan=entry)`. `entry` có `{day,dishes,ingredients}` sau khi áp ghi đè scenario. Quán độc lập dùng `day_plan=None`.
- Manifest dùng số chuẩn Phase 2 cho quán. Cờ phiên bản toàn bộ manifest chuyển sang 1.1 khi Integrator gộp cấu hình cá, kế hoạch và Shop với loader v1.1.
- Test hồi quy quán dùng số bàn đang chạy và dựng fixture kín tất cả các bàn vì TICKET-02 tăng một bàn lên bốn. AC-P2-23 kiểm độc lập số lượng và tọa độ nội thất theo chuẩn mới.
- Sau khi ghép TV3 và TV1, QA chạy lại toàn bộ ma trận và chạy `--mode day --days 1` với món trong và ngoài kế hoạch.

## Chơi từ bến sang quán trên trình duyệt

Tích hợp luật nấu, bưng, phục vụ và thu tiền của TV3 tại `3e563c6` vào bản làm việc. Thêm chuyển ca trong `chonoi.live` để màn hình kết thúc buổi sáng nhận cạnh E mới và mở một phiên quán với kho vừa bàn giao. Phím R mở lại lượt gốc.

Ca kiểm thử live xác nhận giữ phím E khi cập bến vẫn dừng ở màn hình kết ca, nhấn E lần nữa mở quán và đúng kho, sau đó nấu cá lóc ở B2, bưng đến T1, phục vụ và thu 72 gồm boa.

- [Test live, quán và smoke Phase 1](live-quan-tests.txt) đạt 54/54.
- [Hồi quy toàn bộ](live-quan-regression.txt) chạy 116 ca, 8 thất bại đã có ở phần Gather/hợp đồng Phase 1 và 16 bỏ qua.
