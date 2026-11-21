# Kế hoạch Phase 4 (TICKET-04, phát hành v1.0.0, Test Contract v1.3)

> Bản nháp của QA/Scrum (TV5). Phân người là ĐỀ XUẤT, Scrum chốt ở đầu phase. Hạn tag `phase-4` và Release `v1.0.0` là 3:00 theo đồng hồ lab.

- **Mục tiêu:** bàn giao bản chạy được từ clone sạch (≤ 3 lệnh), `contract_version:"1.3"` khai `bench_cmd` và `soak_cmd`, benchmark có render ra `bench.json`, ba cảnh báo dễ nhận biết (thủy quái gần, oxy sắp hết, khách sắp giận) kèm chế độ tương phản cao, hồi quy P1–P3 đạt, hồ sơ và retro đầy đủ, rồi tag `phase-4` cùng Release `v1.0.0` từ một commit trên `main`.

## Hiện trạng đầu phase (đã kiểm bằng chạy thật, `main@186a795`)

| Hạng mục | Tình trạng |
|---|---|
| Contract | `1.1`. Chưa có v1.2 (kho cá thể, độ tươi) và v1.3 |
| `bench_cmd`, `soak_cmd` | **Chưa có** trong repo |
| Hồi quy | P1: 38/38 AC đạt; P2: 15/15 AC có test đạt; P3: chưa bật (code v1.2 chưa có) |
| Tag | Chỉ có `phase-1` |
| Hồ sơ | `LICENSE` chưa có; `CHANGELOG.md`, `CREDITS.md` gần như rỗng; README là bản giảng viên (chưa có bench, "Sáng tạo của nhóm"); chưa có file nào trong `docs/members/`; `retro.md` chưa điền |
| Mở rộng | Nhóm 5 người cần ≥ 1 mục, chưa ai nhận |

## Việc, người, phụ thuộc (đề xuất theo doc phân việc và vai của TICKET-04)

| Vai (ticket) | Người | Việc | Phụ thuộc |
|---|---|---|---|
| Bench/QA | **TV5 `dungtran16042003-afk`** | Bảng `AC-P4-xx` và `tests/test_qa_p4.py`; chạy bench và regression P1–P3 trên commit bàn giao; lưu artifact vào `docs/proof/phase-4/`; hoàn thiện `docs/verification/phase-4.md`; standup và retro nhanh | Cần `bench_cmd`, `soak_cmd`, code v1.2 từ TV1 và TV4 |
| Release/Integrator | **TV1 `congnt180263`** | `soak_cmd`, contract v1.3, kho cá thể và độ tươi (v1.2), release notes, `CHANGELOG`, tag `phase-2/3/4`, công bố Release | Bàn giao kho và `day` của chính TV1 |
| Đóng gói | TV4 `nvcuong96` + người nhận README | `bench_cmd` có render (1280×720, làm nóng 3 s, đo 30 s), cảnh báo + tương phản cao, thử clone sạch, bản đóng gói, `README.md` (≤ 3 lệnh, môi trường, điều khiển, test, headless, bench), `CREDITS.md`, `LICENSE` | Snapshot từ TV1/TV2/TV3 |
| Điều phối retro | TV3 `nguyentrunghai7` (đề xuất) + TV5 | Rà hành động P2, tổng hợp bằng chứng đóng góp, `docs/retro.md`, `ai-usage-log.md`; gộp nhánh `nguyentrunghai` | Từng người điền phản tư |
| Quán/PO | TV2 `dvq2609` | Hỏi Anh Năm các chỗ mơ hồ, `docs/clarify.md`; quán theo v1.2 (giữ theo id, giá theo tươi); hỗ trợ lát trễ | Kho cá thể từ TV1 |
| Cả nhóm | mọi người | `docs/members/<handle>.md` (≤ 200 từ), tự commit bằng tài khoản của mình | — |
| Mở rộng | cả nhóm chọn | Đề xuất **Phụ đề SFX** (ít đụng lõi, dễ kiểm) hoặc Leaderboard; nếu không kịp, khai trung thực trong README | — |

## Mốc trong phase (30 phút)
0–15 đo bench, cảnh báo + tương phản, thử clone sạch, hồi quy, chuẩn bị Release song song · **15–25 retro, phản tư cá nhân, phút 20 standup** · 25–30 dự phòng, kiểm commit/artifact/tag/Release. Đóng băng tính năng mới ở phút 2:40.

## Rủi ro
- **Khối lượng chưa làm quá lớn so với 30 phút:** v1.2 (kho cá thể + độ tươi) chưa có mà Phase 4 đã đòi bench/soak theo v1.2. Ưu tiên theo điểm: (1) tag + Release từ `main` xanh, (2) `bench_cmd` tạo đúng `bench.json` (điểm chấm dựa trên chạy được lệnh và đúng cấu trúc), (3) clone sạch ≤ 3 lệnh, (4) hồ sơ và retro. Làm trung thực: chỗ chưa xong ghi vào Release notes ("giới hạn đã biết").
- **Chưa có tag `phase-2`, `phase-3`:** TV1 gắn trên commit xanh gần nhất tương ứng, ghi rõ phần chưa xong.
- **Nhánh `nguyentrunghai` chưa gộp và xung đột với `main`:** Hải `git pull origin main` rồi gộp trước giờ đóng băng.
- **Benchmark cần cửa sổ/GPU:** có thể không chạy trong môi trường không có màn hình; thử sớm, ghi lại giới hạn.
- **`LICENSE` chưa có:** thêm trước khi phát hành (ticket yêu cầu rà `LICENSE`).
- **Test Phase 3 chưa bật:** `tests/test_qa_p3.py` tự bật khi contract lên 1.2; nếu v1.2 không kịp thì ghi `chưa kiểm` trong `verification/phase-4.md`, không ghi đạt.
