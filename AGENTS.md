# AGENTS.md — hướng dẫn chung cho mọi agent AI của nhóm

> Cập nhật file này qua các phase (lịch sử git phải cho thấy điều đó). Ngắn gọn, có lệnh chạy thật.

## Lệnh
- Kiểm tra thành viên: `python tools/check_team.py` (CI/Linux: `python3 tools/check_team.py`)
- Test (Linux/CI): `python3 tools/verify.py` (v1.3 và hồi quy v1.1 trong bản sao tạm)
- Test trên Windows (PowerShell): `python -X utf8 tools/verify.py` (thêm `--profile legacy` để chạy riêng hồi quy v1.1)
- Headless: `python -m chonoi.headless --mode day --days 1 --seed 1 --ticks 22200 --out out.jsonl`
- Bench/soak: `python -m chonoi.bench --seed 42 --duration 30 --out bench.json` và `python -m chonoi.soak --seed 7 --days 10 --out soak.json`
- Chơi thử trên trình duyệt: `python -m chonoi.live` (mở địa chỉ in ra; WASD, E, Space, H)

## Cấu trúc & quy ước
- (Starter Python là TÙY CHỌN; nhóm có thể dùng ngôn ngữ khác nếu giữ Test Contract.) Khung do giảng viên cấp: `chonoi/{headless,inputs,scenario,contract,rng,ids,jsonl,inventory,runner,live}.py` và `chonoi/web/`. Hạn chế sửa; nếu phải sửa thì báo cả nhóm và ghi lại lý do.
- Luật chơi của nhóm: `chonoi/sim/gather.py`, `chonoi/sim/quan.py` (tìm `TODO(nhóm)`).
- **Số liệu chỉ đọc từ `game.contract.json` / dữ liệu**, không hard-code trong luật.
- Mọi số ngẫu nhiên đi qua `Streams` (`chonoi/rng.py`); không dùng `random` toàn cục, không dùng đồng hồ hệ thống.
- Sắp danh sách thực thể bằng `ids.sort_by_id`; cấp id bằng `IdAllocator`.

## Nên tránh
- Không sửa `docs/contracts/`, `game.contract.json` (khóa contract) hoặc schema kho khi chưa báo cả nhóm (đổi hợp đồng ảnh hưởng mọi module).
- Không làm hỏng nhánh chính: trước khi đẩy, chạy test.
- Không bịa yêu cầu: chỗ mơ hồ thì ghi `docs/clarify.md` và hỏi PO (`dvq2609`).
- Không sửa test cho xanh khi luật sai; phải sửa luật hoặc ghi lý do đổi test trong commit.

## Quy tắc làm việc với agent
- Mỗi agent một việc rõ ràng (một lát). Cho agent đọc PRD/ticket đúng phase và hợp đồng kho trước.
- Agent làm xong phải chạy test và ghi kết quả vào mô tả commit hoặc `docs/proof/`; người đọc lại thay đổi trước khi đẩy.
- Sáng tạo thêm được khuyến khích nhưng phải tắt ở headless (xem README, mục "Tự do sáng tạo").

## Skills / hooks của nhóm
- `contract-check` (`.agents/skills/contract-check/SKILL.md`): Dùng trước mỗi lần commit/merge để rà quy tắc Test Contract, `Streams`, `sort_by_id`, và chạy kiểm tra thành viên + test.
- `phase-proof` (`.agents/skills/phase-proof/SKILL.md`): Dùng trước khi gắn tag `phase-1..4` để xuất log headless, kiểm tra tất định và điền `docs/verification/phase-n.md`.
