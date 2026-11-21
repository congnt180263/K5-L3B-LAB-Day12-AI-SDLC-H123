# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| INV-01 | Chạy smoke test tích hợp. Kết thúc `gather`, đọc file kho bằng `quan` và so với `stock` của snapshot tick 0. | [Kết quả test starter](../proof/phase-1/starter-baseline.md) | Đạt với fixture có sẵn |
| Khách từ scenario và khách theo lịch | Đối chiếu schema PRD-0. Kiểm snapshot tick 0, trước và đúng tick đến, bàn có khách, cùng seed lặp lại. | [Lượt thử quán trên starter](../proof/phase-1/starter-baseline.md#thử-quán-qua-mốc-khách-đến-đầu-tiên) | Chưa đạt trên starter, không có khách ở mốc đầu tiên |
| Chọn món và giữ chỗ nguyên liệu | Tạo fixture có nhiều món nấu được và fixture có hai đơn tranh một phần nguyên liệu. Đối chiếu kho với Lát 4 tại tick bắt đầu nấu. | Chờ bổ sung | Chưa kiểm chứng |
| Kiên nhẫn, `customer_left`, `no_dish` | Kiểm từng sự kiện và snapshot liền sau. Thử ca hết kiên nhẫn đúng tick có tương tác và ca đến lịch khi không đủ nguyên liệu cho món nào. | [Lượt thử quán trên starter](../proof/phase-1/starter-baseline.md#thử-quán-qua-mốc-khách-đến-đầu-tiên) | Kho rỗng chưa phát `no_dish`. Kiên nhẫn và `customer_left` chưa kiểm chứng |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
