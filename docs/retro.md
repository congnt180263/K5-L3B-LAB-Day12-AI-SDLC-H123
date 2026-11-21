# Retro nhóm

## Phase 2 (nhanh)
- Đã chạy được chuyển kho từ Gather sang Quán và kiểm thử luồng nấu, phục vụ, thu tiền trên nhánh tích hợp.
- Quán và bộ kiểm tra kho tiến triển ở các nhánh khác nhau. Một lượt chạy trước đó có fixture không khớp hợp đồng đang bật.
- TV1 và TV2 thống nhất schema kho cá thể cùng một smoke test hai tiến trình trước khi đổi manifest.

## Phase 4 (cuối)
- Hành động Phase 2 đã có quyết định trong ADR và smoke kiểm ID, loại, độ tươi qua file lẫn vòng Ngày.
- Bộ hồi quy v1.1 chạy trong thư mục tạm. Nhờ vậy có thể kiểm lại các fixture kho đếm song song với suite v1.3.
- Commit và bằng chứng theo người được dẫn trong `docs/members/`. Chi phí token chưa được đo.
- Lần đầu AI bật benchmark khi chưa đăng ký Page API và bị hết giờ. Chạy lệnh với thời lượng ngắn phát hiện lỗi, sau đó đo lại đủ 30 giây.
- Hành động tiếp theo của Integrator là cố định commit bàn giao và chạy lại các artefact trên commit đó trước khi tạo tag.
