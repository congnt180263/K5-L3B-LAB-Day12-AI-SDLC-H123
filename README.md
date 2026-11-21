# Day 12 — AI SDLC: Quán Ăn Chợ Nổi

> **Làm theo nhóm 4–6 người** · Dùng AI để xây game 2D qua **4 phase** trong **3 giờ**: Út Sen lặn bắt cá, hái rau trên mặt nước rồi tối mở quán phục vụ khách.
> **Yêu cầu từng phase mở đúng mốc giờ tại lab board:** **[Chợ Nổi Lab](https://claude.ai/artifact/E35v787wSx2wDgPTNhMVDg)** (cần đăng nhập claude.ai; có trợ giảng AI cho từng phase).

## Bắt buộc (chỉ có thế)

Cách làm việc kỹ thuật là **tự do** (push thẳng, nhánh + PR, pair, có hay không CI…). Cái bắt buộc:

1. **Một repo chung:** trưởng nhóm **fork** repo này, đặt tên `K5-L3B-LAB-Day12-AI-SDLC-<ten-nhom>`, thêm mọi thành viên làm collaborator (*Settings → Collaborators*, quyền Write) và để repo **public** (giảng viên xem được, không cần mời).
2. **Cả nhóm cùng commit** bằng tài khoản GitHub của mình, mỗi người **≥ 3 commit có nội dung** (làm cặp thì ghi `Co-authored-by:`).
3. **Điền [`TEAM.md`](TEAM.md):** danh sách thành viên + thỏa thuận làm việc nhóm; sửa `team_size` trong [`game.contract.json`](game.contract.json). Commit của người không có trong `TEAM.md` không được tính.
4. **Gắn tag** `phase-1` … `phase-4` đúng hạn; chạy được tại từng tag.
5. **Ghi chép tối thiểu:** `docs/verification/phase-n.md`, `docs/clarify.md`, `docs/ai-usage-log.md`, `docs/retro.md`, `docs/members/<handle>.md`.

## Bắt đầu nhanh

Máy cần Python 3.10 trở lên và trình duyệt. Bản chơi dùng thư viện chuẩn Python.

```bash
git clone https://github.com/congnt180263/K5-L3B-LAB-Day12-AI-SDLC-H123.git
cd K5-L3B-LAB-Day12-AI-SDLC-H123
python3 -m chonoi.live
```

Mở địa chỉ terminal in ra và chọn **Chơi 5 ngày**. Dùng WASD hoặc mũi tên để di chuyển, E để hái, cập bến, nấu và phục vụ, Space để bắt cá, Esc để tạm dừng và H để bật tương phản cao. Trong quán, nấu ở bếp, lấy món khi chín và giao đúng bàn. Shop mở cuối Ngày. Điểm bằng tổng thu cộng 100 lần phần nguyên của uy tín.

### Kiểm chứng và đóng gói

```bash
python3 tools/verify.py
python3 -m chonoi.headless --mode day --days 1 --seed 42 --ticks 22200 --out day.jsonl
python3 -m chonoi.bench --seed 42 --duration 30 --out bench.json
python3 -m chonoi.soak --seed 7 --days 10 --out soak.json
python3 tools/package_release.py --out dist/cho-noi-v1.0.0.zip
```

Benchmark và bộ kiểm chứng đầy đủ cần Node.js 22 trở lên và Chrome, Chromium hoặc Edge. Đặt `CHONOI_BROWSER` nếu trình duyệt nằm ngoài vị trí mặc định. Bản phát hành `v1.0.0` dùng Test Contract v1.3. Ví dụ kho cá thể nằm trong [tài liệu hợp đồng](docs/contracts/README.md). [Ghi chú phát hành](RELEASE_NOTES.md)

### Bảng xếp hạng cục bộ

```bash
python3 -m chonoi.headless --mode day --days 5 --seed 42 --ticks 111000 --out day.jsonl --leaderboard leaderboard.json --player-name "Út Sen"
python3 -m chonoi.live --export-leaderboard scores.json --leaderboard leaderboard.json
```

## Sáng tạo của nhóm

Ngoài phần đề yêu cầu, nhóm được **thêm** nhân vật, loài cá/cây, sinh vật, món, bản đồ, cơ chế, câu chuyện, đồ họa, âm nhạc… với ba điều kiện: **không phá phần cố định** (tắt ở headless), ghi mục **"Sáng tạo của nhóm"** trong README của nhóm, và **làm lõi đúng trước**.

Giao diện trình duyệt có menu Chơi/Thoát, bảng kế hoạch của Má Tư, màn chuyển buổi, kết quả ngày, Shop, tổng kết, pause và chế độ tương phản cao. SVG cá kèo, kèo nèo, cá sấu và món ăn được bổ sung; cá, cây, bọt nước và Út Sen có chuyển động nhẹ trên canvas. Phần đồ họa chỉ đọc snapshot, không thay đổi kết quả headless.

Bảng xếp hạng là mở rộng được khai trong manifest. Bài kiểm tra xác nhận tối đa 10 mục và giữ thứ tự ghi khi đồng điểm. [Bằng chứng Phase 4](docs/verification/phase-4.md)

Điều khiển: WASD hoặc phím mũi tên để đi/bơi, `E` hái/cập bến/nấu/bưng, `Space` bắt cá, `Esc`/`P` tạm dừng. Shop dùng nút Mua và Kết thúc ngày. Chạy riêng một buổi bằng `python3 -m chonoi.live --mode gather` hoặc `--mode quan`.

## Lịch 3 giờ

| Mốc | Phase | Hạn tag |
|---|---|---|
| 0:00 | Phase 1 (PRD-0) | `phase-1` trước 1:00 |
| 1:00 | Phase 2 | `phase-2` trước 1:55 |
| 1:55 | Phase 3 | `phase-3` trước 2:30 |
| 2:30 | Phase 4 | `phase-4` + Release `v1.0.0` trước 3:00 |

Hết giờ mỗi phase thì gắn tag rồi đi tiếp; chỗ chưa xong ghi trung thực trong bằng chứng.

## Đánh giá (100 điểm)

| Hạng mục | Điểm |
|---|---|
| Test tự động ẩn (headless, gồm kiểm tra lại phase trước) | 25 |
| Làm việc nhóm (một repo chung, chia việc, tích hợp, đổi yêu cầu) | 25 |
| Kiểm chứng & bằng chứng | 15 |
| Harness AI (AGENTS.md, skill, nhật ký dùng AI) | 10 |
| Đánh giá & retro | 10 |
| Chất lượng sản phẩm (đúng yêu cầu, mở rộng/sáng tạo) | 10 |
| Demo | 5 |

## Quy định

- Dùng AI thoải mái; **không sao chép repo của nhóm khác**; bằng chứng phải thật.
- Nhân vật, bối cảnh là bản gốc của lab; asset ngoài chỉ dùng CC0/CC-BY/MIT hoặc tự tạo, ghi nguồn trong `CREDITS.md`. Không commit API key, token, `.env`.
