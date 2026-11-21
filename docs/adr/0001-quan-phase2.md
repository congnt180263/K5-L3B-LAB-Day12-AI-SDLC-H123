# ADR 0001 Dữ liệu quán Phase 2

Trạng thái: triển khai cục bộ để nhóm review; chưa commit/push hay thông báo ngoài chat.

Theo yêu cầu người dùng phụ trách toàn bộ quán, cập nhật phần quan/menu của game.contract.json đúng TICKET-02: 2 bếp, 4 bàn, 6 món. Thêm tập nguyên liệu P2 cho đọc kho quán; cấu trúc items không đổi. Bổ sung validation trong contract/scenario và pause trong runner/inputs/live vì thứ tự pause thuộc lớp chạy, không thuộc luật quán.

Giữ dữ liệu gather và nhãn contract_version hiện tại cho đến khi Integrator hoàn tất v1.1 toàn game. Nhánh này là phần quán P2, chưa phải bản nộp P2 hoàn chỉnh. Khi merge cần review các file khung và hợp nhất thay đổi contract với người phụ trách gather/day. Chi tiết API: docs/quan-phase2.md.
