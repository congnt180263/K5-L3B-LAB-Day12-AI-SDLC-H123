# Kế hoạch Phase 3 (TICKET-03 "Mùa Nước Nổi", Test Contract v1.2)

> Bản nháp của QA/Scrum (TV5). Phân người là ĐỀ XUẤT, Scrum chốt ở 7 phút đầu. Nội dung là change request nên có phân tích tác động và quyết định đổi schema kho.

- **Mục tiêu:** Chuyển kho đếm theo loại sang **kho cá thể** `{id,kind,fresh}`, thêm độ tươi (giỏ hao 0.5/s, kho quán 0.25/s, ươn khi `fresh < 30`), giữ chỗ theo id, giá theo độ tươi, `contract_version:"1.2"`. Bàn giao kho cá thể qua file và trong `day`. Nhóm 5 người làm ít nhất 1 mục mở rộng (`current` hoặc `reservations`, hoặc mục đã chọn ở Phase 2). Tag `phase-3` trước **2:30** trên `main` chạy được.

## Phân tích tác động (schema kho đếm → kho cá thể)

| Module | File cần đổi | Test bị ảnh hưởng | Người phụ trách (đề xuất) |
|---|---|---|---|
| Adapter / kho | `chonoi/inventory.py` (đọc/ghi theo `contract_version`, cấp id `I1`...), `chonoi/runner.py` | `test_smoke_p1.py` (INV-01, kho sai, kho + stock), `test_python_starter_units.py`, `tests/test_qa_contract.py` (AC-P1-26..28) | TV1 (Integrator) |
| Contract / scenario | `game.contract.json` (`contract_version:"1.2"`, `freshness`), `chonoi/contract.py`, `chonoi/scenario.py` (`hold`, `stock`, `reserved` là mảng cá thể/id; kiểm mã 2) | `test_qa_contract.py` (AC-P1-04), `test_qa_quan.py` (AC-P1-43), fixture dùng `stock`/`hold` dạng đếm | TV3 |
| Lặn | `chonoi/sim/gather.py` (giỏ cá thể, id, hao tươi đầu bước, `spoiled`, `lost`/`faint` dạng cá thể) | `test_gather_rules.py`, `test_qa_gather.py` (hold là chuỗi kind, `lost`) | TV1 |
| Quán | `chonoi/sim/quan.py` (kho cá thể, giữ theo id tươi nhất, thử giữ lại một lần, giá theo tươi, hao kho quán, `cook_started.items`) | `test_quan_customers.py`, `test_qa_quan.py` (reserved dạng map, `stock` đếm) | TV2 (khách, giữ chỗ), TV3 (bếp, giá) |
| `day` | chuyển pha trong cùng tick, id xuyên pha và Ngày | `test_qa_p2.py` (AC-P2-30, 32) | TV1 |
| HUD | `chonoi/web/index.html` (độ tươi hoặc nhãn ươn bằng số, thanh, biểu tượng) | không có test tự động, kiểm bằng chơi thử | TV4 |
| QA | `tests/test_qa_p3.py`, `docs/verification/phase-3.md`, `docs/proof/phase-3/`, chạy lại hồi quy P1–P2 | tự cập nhật test cũ bằng bản theo `contract_version` kèm lý do | TV5 |

## Quyết định đổi schema và thứ tự tích hợp (để `main` vẫn chạy được)

1. **Adapter trước, tất cả sau.** TV1 làm đọc/ghi kho **theo `contract_version`** (1.0 đọc/ghi dạng đếm, 1.2 dạng cá thể, kho đếm ở 1.2 trả mã 2). Cả hai phiên bản cùng tồn tại trong lúc chuyển (TICKET-03 cho phép) nên `main` không vỡ.
2. **Lặn, Quán, HUD song song** theo schema đã chốt ở adapter, mỗi người làm sau cờ phiên bản.
3. **Chỉ bật `contract_version:"1.2"` khi cả hai đầu (Lặn ghi, Quán đọc) đã sẵn sàng**, rồi chạy smoke bàn giao kho và `day`.
4. Test cũ đổi theo phiên bản, mỗi chỗ đổi ghi lý do trong commit; ghi breaking change vào `CHANGELOG.md`.

## Mốc trong phase (35 phút)
0–7 phân tích tác động và chia việc · 7–25 build song song, **phút 20 smoke kho + standup** · 25–32 bật v1.2, smoke hai tiến trình và `day`, hồi quy, `CHANGELOG`, bằng chứng, tag, retro nhanh · 32–35 dự phòng.

## Rủi ro
- **Nhóm đang chậm:** `phase-1` và `phase-2` chưa có tag, code còn ở v1.0 (gather lệch payload PRD-0, chưa có v1.1). Đổi schema kho khi nền chưa chắc rất rủi ro. Ưu tiên: gắn tag `phase-1` ngay, chốt phạm vi Phase 2 còn làm được, rồi mới làm kho cá thể.
- **Đổi schema phá nhiều test cùng lúc.** Giảm thiểu bằng adapter theo phiên bản và bật v1.2 sau cùng.
- **So sánh ngưỡng 30 và `floor` giá.** Dùng phép tính chính xác (ví dụ 240 đơn vị mỗi điểm tươi, trừ 2/tick ở gather và 1/tick ở quán) để khỏi sai số số thực; test QA đã dựng fixture đúng ngưỡng.
- **Hết thời gian cho mở rộng:** làm lõi đúng trước; nếu mở rộng chưa xong, khai trung thực trong README.
- **Handle/vai trong `TEAM.md` vẫn lệch** (xem `docs/plan/phase-2.md`); sửa để commit được tính.
