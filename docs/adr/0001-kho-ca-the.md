# ADR 0001 · Bàn giao kho cá thể

TICKET-03 chuyển file kho từ số lượng theo loại sang mảng `{id,kind,fresh}`. Adapter đọc theo phiên bản manifest. Bản 1.2 và 1.3 từ chối file đếm, còn lớp mô phỏng có nhánh 1.1 để kiểm tra hồi quy.

Thứ tự tích hợp là adapter và fixture, giỏ Gather, giữ chỗ và giá Quán, bàn giao Day, HUD, rồi benchmark và đóng gói. ID nguyên liệu dùng chung bộ cấp xuyên các Ngày. Trạng thái trong bộ nhớ tính hao bằng phân số. Snapshot và file xuất dùng số JSON đủ độ chính xác để hiển thị và bàn giao.

TV1 kiểm luồng Gather/Day và kho. TV2 kiểm giữ chỗ, giá và fixture. TV3 kiểm CLI/contract. TV4 kiểm HUD và benchmark. TV5 kiểm hồi quy và ma trận. Kết quả đo nằm trong `docs/proof/`.
