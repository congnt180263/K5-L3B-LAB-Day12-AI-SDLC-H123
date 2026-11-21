# Changelog

## Phase 4 · v1.0.0 đã nghiệm thu

- Test Contract v1.3 khai báo benchmark canvas và soak 10 Ngày.
- HUD có cảnh báo bằng chữ và phím H bật tương phản cao. Bảng xếp hạng 5 Ngày lưu cục bộ.
- Thêm lệnh đóng gói ZIP, hướng dẫn chạy và hồ sơ kiểm chứng.

## Phase 3 · Test Contract v1.2

- **Breaking change về kho.** File kho chuyển từ `{"items":{"ca_loc":1}}` sang
  `{"items":[{"id":"I1","kind":"ca_loc","fresh":100}]}`. File đếm trả mã 2 từ v1.2.
- Đổi `gather.hold` và `quan.stock` trong fixture thành mảng cá thể. Đổi `customers[].reserved`
  thành mảng ID cá thể hoặc bỏ trường để quán tự cấp theo công thức.
- Hàng hao tươi theo pha. Giữ nguyên liệu tươi nhất, xử lý hàng vừa ươn rồi mới nấu và tính giá.
- ID nguyên liệu tiếp tục qua các pha và các Ngày. Kho bàn giao qua file hoặc bộ nhớ.

## Phase 2 · Test Contract v1.1

- Thêm cá bơi và sinh, Cá Sấu, vòng ngày, Shop và pause.
- Quán có 2 bếp, 4 bàn và 6 món. Khách chọn theo kế hoạch trong chế độ Ngày.

## Phase 1 · Test Contract v1.0

- Hai ca độc lập, lặn hái và bắt cá, nấu và phục vụ, bàn giao qua file kho đếm.
