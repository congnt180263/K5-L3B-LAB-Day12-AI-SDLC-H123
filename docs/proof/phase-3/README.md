# Kiểm chứng Phase 3

TICKET-03 chuyển kho sang cá thể từ v1.2. Bản v1.0.0 đã được nhóm duyệt, dùng Test Contract v1.3 và giữ schema cùng luật độ tươi này. Bộ test mới và hồi quy kho đếm chạy qua `python3 tools/verify.py`. [Log kiểm chứng](../phase-4/verify.txt)

Smoke seed 42 dựng cá lóc `I1` ở fresh 100, cập bến ở frame 0, đọc file vừa ghi bằng `quan --ticks 0`. Snapshot quán giữ nguyên id, loại và fresh sau một tick hao của Gather. Hai lần chạy Gather sinh file kho và JSONL giống từng byte. [Kết quả bàn giao](ban-giao-kho.json)

Test vòng Ngày kiểm stock quán ở cùng tick với `gather_end`, hao lần đầu ở bước Quán kế tiếp, và mẫu ID `I7` ở Ngày 1 chuyển thành `I8` ở Ngày 2. Demo chạy hết một Ngày, nấu và giao món rồi đóng Shop, hai lần cho cùng hash. [Kết quả demo](../phase-4/demo-result.json)
