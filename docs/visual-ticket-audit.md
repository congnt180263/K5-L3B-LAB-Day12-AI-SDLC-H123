# Đối chiếu ticket với bản chơi trình duyệt

| Ticket | Yêu cầu liên quan hình ảnh và giao diện | Trạng thái |
|---|---|---|
| TICKET-02 | Menu Chơi/Thoát, kế hoạch đầu ngày, chuyển buổi, kết quả ngày, Shop, tổng kết, pause | Đã nối vào `chonoi.live` chế độ `day`; menu, HUD và nút Shop dùng snapshot cùng mô phỏng headless. |
| TICKET-02 | HUD lặn/quán, cảnh báo oxy và thủy quái, trạng thái khách | Có bảng thông tin và cảnh báo chữ; cảnh lặn/quán dùng asset SVG. |
| TICKET-02 | Món và nguyên liệu D1–D5, cá sấu | Đã thêm SVG cho cá kèo, kèo nèo, cá sấu và ba món còn thiếu. |
| TICKET-03 | Độ tươi, hàng ươn, dòng chảy, đơn đặt trước | Chưa có trong mô phỏng v1.2 hiện tại; UI sẽ cần đọc các trường snapshot tương ứng khi luật được triển khai. |
| TICKET-04 | Cảnh báo dễ nhận biết, tương phản cao | Đã thêm thông báo chữ cho thủy quái, oxy cạn, khách sắp giận và nút tương phản cao trong Pause. |
| TICKET-04 | Benchmark render, đóng gói, release, SFX/phụ đề | Chưa thực hiện trong thay đổi giao diện này. Chưa có SFX nên chưa có phụ đề. |

Các hiệu ứng CSS/canvas dùng thời gian render, không ghi vào trạng thái mô phỏng. Bản chơi cần kiểm tra thêm ở trình duyệt 1280×720 trên máy đích để xác nhận mốc FPS của TICKET-02/04.
