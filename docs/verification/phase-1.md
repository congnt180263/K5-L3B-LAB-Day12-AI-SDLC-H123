# Ma trận truy vết Phase 1

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-1/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| INV-01 | Kết thúc `gather` bằng cập bến. Nạp file kho vào `quan` và so với `stock` ở tick 0. | [Lượt thử chuyển kho](../proof/phase-1/quan-customers.md#quan-sát-headless) | Đạt |
| Khách từ scenario và khách theo lịch | Kiểm snapshot tick 0, trước và đúng tick đến, bỏ lượt khi kín bàn, tắt sinh khách và lặp cùng seed. | [Lượt thử headless và test Lát 3](../proof/phase-1/quan-customers.md) | Đạt, JSONL lặp lại giống từng byte |
| Chọn món và giữ chỗ nguyên liệu | Kiểm chọn từ các món đủ nguyên liệu, loại nguyên liệu đã giữ khỏi lựa chọn bàn khác, và nhả giữ chỗ trước lượt khách cùng tick. | [Log test Lát 3](../proof/phase-1/unittest.txt) | Đạt |
| Kiên nhẫn, `customer_left`, `no_dish` | Kiểm giảm kiên nhẫn, rời do hết kiên nhẫn hoặc đóng ca, hủy món trên bếp/tay và thử kho rỗng. | [Lượt thử headless và test Lát 3](../proof/phase-1/quan-customers.md) | Đạt |
| Kiểm tra fixture quán | Thử giữ chỗ quá tồn, giữ sai công thức, đơn `assigned` thiếu hoặc trùng món, khách `eating` thiếu boa và timer âm. | [Log test Lát 3](../proof/phase-1/unittest.txt) | Đạt, trả mã 2 trước khi ghi JSONL |
| Tích hợp Lát 4 | Trừ kho lúc bắt đầu nấu, giao món ở tick kiên nhẫn về 0 và thu tiền đúng thứ tự khi đóng ca. | Chờ lượt kiểm chứng sau khi gộp Lát 4 | Chưa kiểm chứng |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt:
- Điều cần chỉnh cho phase sau:
