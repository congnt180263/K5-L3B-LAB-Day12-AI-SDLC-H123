# Clarify — câu hỏi và câu trả lời (PO ghi, cả nhóm dùng chung)

| # | Ngày giờ | Câu hỏi | Trả lời / giả định | Ai quyết |
|---|---|---|---|---|
| 1 | 2026-11-21 10:17 | Khi giỏ gần đầy (ví dụ còn 1 chỗ) mà bắt `ca_linh` (`fish_yield = 3`) hoặc hái nút (`node_yield > 1`): nhận phần còn vừa sức chứa hay từ chối toàn bộ và phát `hold_full`? | Giả định tạm (Lát 2): cần đủ chỗ hoặc nhặt tối đa phần còn trống? Hiện cài đặt theo hướng: nếu giỏ không đủ chỗ cho ít nhất 1 món (hoặc chưa đủ `yield` — cần PO đối chiếu lại PRD-0) thì phát `hold_full`. Cần PO (`dvq2609`) kiểm tra lại mục 13.8 PRD-0 trên lab board. | Tạm thời: TV1 / chờ PO xác nhận |
| 2 | 2026-11-21 10:17 | Payload `data` chi tiết của các sự kiện `oxygen_empty`, `choke`, `faint`, `gather`, `fish_caught`, `hold_full` trong PRD-0 có thêm khóa nào ngoài `node_id`/`fish_id`/`kind`/`count`/`hp`/`pos` không? | Đang dùng các khóa tối thiểu bám sát `gather.py` (`pos`, `hp`, `node_id`, `fish_id`, `kind`, `count`, `capacity`). PO (`dvq2609`) đối chiếu PRD-0 và cập nhật lại bảng này + `docs/contracts/README.md`. | Tạm thời: TV1 / chờ PO xác nhận |
