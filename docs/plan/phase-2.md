# Kế hoạch Phase 2 (TICKET-02, Test Contract v1.1)

> Bản nháp của QA/Scrum (TV5). Phân người là ĐỀ XUẤT theo doc phân việc, Scrum chốt ở phút 0–5.

- **Mục tiêu:** Chơi trọn vòng ngày theo TICKET-02: số chuẩn v1.1 (8 đàn cá bơi/sinh, Cá Sấu, 2 bếp/4 bàn/6 món), `--mode day` D1–D5 với Shop và pause, UI có menu/HUD. Nhóm 5 người làm **ít nhất 1 mục mở rộng**. Tag `phase-2` trước **1:55**. Hồi quy Phase 1 phải đạt với số chuẩn mới (test đổi thì ghi lý do).
- **Việc / người / phụ thuộc** (AC xem `docs/verification/phase-2.md`):
  - **TV1 `congnt180263` (gather, Integrator):** AC-P2-06..22, 28–38. Cá bơi/sinh, Cá Sấu, Máu/ngất, vòng `day` và Shop. Tích hợp và gắn tag. Phụ thuộc: chốt hợp đồng v1.1 (`docs/contracts/`) và giao diện chuyển pha.
  - **TV2 `dvq2609` (quan lát 3, PO):** AC-P2-23..27, 31. 2 bếp/4 bàn, 3 món mới, khách chọn món theo kế hoạch ngày. Hỏi Anh Năm các chỗ mơ hồ, ghi `docs/clarify.md`. Phụ thuộc: kế hoạch ngày từ TV1.
  - **TV3 `nguyentrunghai7` (quan lát 4, scenario, Harness):** AC-P2-01..05, 39. Kiểm contract v1.1, scenario `day`/`monsters`/`fish`, `pause`, `buy`, bếp/tiền ở quán mới. Cập nhật `AGENTS.md`. Phụ thuộc: khóa v1.1 do TV1 chốt.
  - **TV4 (client/ui, Demo):** AC-P2-44..48. Menu, DayIntro, EveningIntro, DayResult, Summary, pause, HUD sáng/tối, FPS. Phụ thuộc: snapshot `day`/`monsters`/`paused`.
  - **TV5 `dungtran16042003-afk` (qa, Scrum):** AC-P2-40..43, 49–51. Bảng AC-P2, test hộp đen cho v1.1, hồi quy Phase 1, smoke tích hợp phút 20, smoke `day --days 1`, bằng chứng, standup, retro nhanh. Dự phòng cho TV3. Phụ thuộc: code của cả bốn người.
  - **Mở rộng (cần chọn, chưa có người nhận):** đề xuất chọn mục nhỏ, ít đụng lõi, dễ test: **Cháy món (burn)** hoặc **Settings & âm thanh**. Quyết trong 5 phút đầu.
- **Mốc trong phase (55 phút):** 0–5 lên lại kế hoạch · 5–20 build · **20 smoke tích hợp + standup** · 20–35 build tiếp · 35–45 smoke `day`, hồi quy P1, bằng chứng, tag · 45–50 retro nhanh · 50–55 dự phòng.
- **Rủi ro & giảm thiểu:**
  - *`phase-1` chưa có tag trên remote, đã quá hạn 1:00.* TV1 gắn tag trên commit xanh gần nhất, ghi trung thực phần chưa xong, rồi đi tiếp.
  - *Test Phase 1 cũ vỡ vì số chuẩn đổi* (ví dụ `fish_initial` 6 lên 8, thêm bếp/bàn/món). QA cập nhật kèm lý do trong commit, không sửa cho xanh.
  - *`invuln_ticks` bị scenario từ chối ở v1.0 nhưng hợp lệ ở v1.1.* Chuyển `contract_version` sang 1.1 ngay đầu phase để test và luật cùng một chuẩn.
  - *Sai khác payload sự kiện* (gather còn lệch PRD-0 mục E). Sửa trước khi thêm sự kiện mới (`monster_hit`, `fish_spawned`, `bought`...).
  - *Hiệu năng `day` ≤ 20 s cho 22.200 tick.* Đo sớm bằng smoke `day --days 1`.
  - *Handle lệch giữa commit và `TEAM.md`* (TV2: `dvquyen2609` so với `dvq2609`; TV4: `cuong253` so với `nvcuong96`; vai TV4/TV5 ghi ngược). Sửa ngay để commit được tính.
