# Ma trận truy vết Phase 4 (TICKET-04, phát hành v1.0.0, Test Contract v1.3)

> Nguồn AC: TICKET-04. Ticket không đánh số sẵn nên QA tự đặt `AC-P4-xx`, kèm mục gốc. Người chịu trách nhiệm là ĐỀ XUẤT (xem `docs/plan/phase-4.md`).
> Bộ test `tests/test_qa_p4.py` tự bật khi `contract_version` là 1.3; ép chạy: `QA_P4=1` (thêm `QA_P4_FULL=1` để chạy soak 10 Ngày). Skill: `python .agents/skills/qa-run-matrix/status.py --phase 4`.
> Kết quả dưới đây là lần chạy thử đầu phase: nhiều AC chưa thể đạt vì `bench_cmd`, `soak_cmd`, contract 1.3 chưa có. Chạy lại trên commit bàn giao; artifact lưu ở `docs/proof/phase-4/`.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-4/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P4-01: `contract_version:"1.3"`; `bench_cmd` và `soak_cmd` khai ở gốc `game.contract.json`; gameplay, tuning, kho, JSONL theo v1.2 (1; TV1) | đọc `game.contract.json` | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-02: `bench_cmd --seed 42 --duration D --out bench.json` chạy được, thoát 0, tạo file (1, Benchmark; TV4) | chạy lệnh | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-03: `bench.json` có đủ `avg_fps`, `p1_low_fps`, `frames`, `measured_s`, `load_ms` đúng kiểu; `avg_fps = frames / measured_s`; `p1_low_fps ≤ avg_fps` (1, Benchmark; TV4) | đọc JSON, tính lại | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-04: báo cáo mốc avg ≥ 60 FPS, 1% low ≥ 30 FPS, load ≤ 10 s; lưu `bench.json` từ commit nộp vào `docs/proof/phase-4/` (chỉ để báo cáo, không chặn) (1; TV4+TV5) | chạy `bench_cmd --seed 42 --duration 30` | | chưa kiểm |
| AC-P4-05: cảnh đo đúng: buổi sáng lõi có độ tươi, cá bơi, Cá Sấu, hiệu ứng mặc định; Út Sen đứng yên ở bến; 1280×720; làm nóng 3 s, đo 30 s, seed 42 (1; TV4) | đọc mã/README | | chưa kiểm |
| AC-P4-06: cảnh báo thủy quái gần bằng chữ hoặc biểu tượng (1, Cảnh báo; TV4) | chơi thử, ảnh chụp | | chưa kiểm |
| AC-P4-07: cảnh báo oxy sắp hết bằng chữ hoặc biểu tượng (1, Cảnh báo; TV4) | chơi thử, ảnh chụp | | chưa kiểm |
| AC-P4-08: cảnh báo khách sắp giận bằng chữ hoặc biểu tượng (1, Cảnh báo; TV4) | chơi thử, ảnh chụp | | chưa kiểm |
| AC-P4-09: chế độ tương phản cao hoạt động; chơi thử cả ba cảnh báo ở chế độ đó (1, Cảnh báo; TV4) | chơi thử, ảnh chụp | | chưa kiểm |
| AC-P4-10: từ clone sạch chạy được bản có giao diện bằng tối đa 3 lệnh trên macOS/Linux theo README (1, Đóng gói; TV4) | clone repo mới vào thư mục tạm, làm theo README | | chưa kiểm |
| AC-P4-11: `README.md` ghi môi trường, điều khiển, lệnh test, lệnh headless, benchmark và mục "Sáng tạo của nhóm" (1, Đóng gói; chưa có người nhận) | đọc README | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm (README vẫn là bản giảng viên) |
| AC-P4-12: GitHub Release `v1.0.0` có bản đóng gói chạy được và release notes (điểm mới, cách chạy, giới hạn đã biết) (1; TV1) | `gh release view v1.0.0` | | chưa kiểm |
| AC-P4-13: `CHANGELOG.md` ghi theo từng phase (P1–P4), có breaking change kho cá thể v1.2 (1; TV1) | đọc file | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm (CHANGELOG còn rỗng) |
| AC-P4-14: rà `CREDITS.md` và `LICENSE` cho tài sản đã dùng (1; TV4+TV1) | đọc file | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm (chưa có `LICENSE`) |
| AC-P4-15: `soak_cmd --seed S --days N --out soak.json` nhận đúng ba cờ; `soak.json` có `days`, `days_completed`, `crashes`, `results`, `duration_s`; mỗi `results[]` có `day`, `earned`, `reputation`, `score` (2; TV1) | chạy lệnh | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-16: soak đạt khi `days_completed = days` và `crashes = 0` (giảng viên chạy 10 Ngày, seed 7) (2; TV1) | chạy `--days 10` (`QA_P4_FULL=1`) | | chưa kiểm |
| AC-P4-17: soak tất định: hai lần cùng seed cho các trường gameplay giống nhau, bỏ số đo thời gian thực (2; TV1) | chạy 2 lần, so | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-18: Ngày 6–10 lặp kế hoạch D1–D5; tiền, `earned`, uy tín, cấp nâng cấp, số Ngày, id cá thể liên tục (2; TV1) | đọc `results[]` | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-19: hồi quy P1–P3 còn hiệu lực đạt; test đổi có lý do (DoD; TV5) | `python .agents/skills/qa-run-matrix/status.py --phase 1`, `2`, `3` | [phase-2/qa_status_v11.txt](../proof/phase-2/qa_status_v11.txt) | một phần: P1 38/38 và P2 15/15 đạt trên v1.1; P3 chưa bật (chưa có code v1.2) |
| AC-P4-20: `docs/verification/phase-4.md` và bằng chứng khớp commit gắn tag (DoD; TV5) | đối chiếu hash | | chưa kiểm |
| AC-P4-21: `docs/clarify.md` và `docs/ai-usage-log.md` được cập nhật (4; TV2, TV3) | đọc file | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-22: `docs/retro.md` rà hành động P2, ghi điều tốt/tệ/hành động; nêu một lỗi AI và cách xác minh (4; TV3+TV5) | đọc file | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm (mục P2 còn rỗng) |
| AC-P4-23: `docs/members/<handle>.md` đủ 5 người, ≤ 200 từ, dẫn commit hoặc bằng chứng (4; từng người) | đếm từ, tìm liên kết | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-24: bằng chứng đóng góp từng người trong repo chung (≥ 3 commit có nội dung, đúng tài khoản GitHub) (4; từng người) | `git log` theo tài khoản | | chưa kiểm (Hải chưa có commit trên `main`) |
| AC-P4-25: tag `phase-2` và `phase-3` đã gắn trên `main` (các phase trước bàn giao) (4; TV1) | `git tag` | | chưa đạt: chỉ có `phase-1` |
| AC-P4-26: tag `phase-4` và Release `v1.0.0` cùng trỏ một commit trên `main`, chậm nhất 3:00 (DoD; TV1) | so hash tag và Release | | chưa kiểm |
| AC-P4-27: nếu làm mở rộng: có bài kiểm và bằng chứng, ghi README (3; cả nhóm) | chỉ khi chọn mục này | | chưa kiểm (chưa ai nhận) |
| AC-P4-28: nếu làm Leaderboard: `--export-leaderboard`, `--leaderboard`, `--player-name`; ghi đúng một mục khi chạy đủ 5 Ngày chuẩn; thiếu một cờ trong cặp hoặc sai mode thì mã 2; sắp điểm giảm dần, hòa theo mục ghi trước (3) | chỉ khi khai `extensions.leaderboard` | [test_qa_p4.py](../../tests/test_qa_p4.py) | chưa kiểm |
| AC-P4-29: nếu làm Phụ đề SFX: hiện đúng lúc, thử với âm thanh tắt (3; TV4) | chơi thử | | chưa kiểm |
| AC-P4-30: checklist Demo: chơi một Ngày đến khi đóng Shop; chạy test cho thấy đạt; chỉ ra bằng chứng chia việc và đóng góp; mở ma trận truy vết (Demo sau 3:00; cả nhóm) | luyện trước | | chưa kiểm |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: đầu phase, hầu hết AC chưa kiểm vì `bench_cmd`, `soak_cmd`, contract 1.3, README, LICENSE, CHANGELOG, retro và `docs/members/` chưa có. Hồi quy P1 và P2 đạt trên v1.1; P3 chưa bật.
- Điều cần chỉnh: ưu tiên tag + Release từ `main` xanh, `bench.json` đúng cấu trúc và clone sạch ≤ 3 lệnh; chỗ chưa xong ghi trung thực trong Release notes.
