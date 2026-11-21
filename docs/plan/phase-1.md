# Kế hoạch Phase 1 (PRD-0)

- **Mục tiêu:** Hoàn thành lõi mô phỏng `gather` + `quan` + kiểm tra `scenario` theo đúng PRD-0 và Test Contract v1.0, giao diện chơi thử đọc snapshot mượt mà, có bộ test + bằng chứng chạy thật và gắn tag `phase-1` trước **1:00**.
- **Việc / người / phụ thuộc:**
  - **TV1 (`congnt180263` — `sim/gather`, Integrator):** Chốt hợp đồng kickoff (`TEAM.md`, `docs/contracts/README.md`, `plan/phase-1.md`), code Lát 1 (oxy, ngạt, ngất, giỏ LIFO, dive/surface) & Lát 2 (hái nút, bắt cá) trong `chonoi/sim/gather.py` + unit test `gather`. Phụ thuộc: PRD-0.
  - **TV2 (`dvq2609` — `sim/quan`, PO):** Hỏi giảng viên & ghi `docs/clarify.md`; code Lát 3 trong `chonoi/sim/quan.py` (khách từ scenario, lịch đến, chọn món, giữ chỗ nguyên liệu, kiên nhẫn, `customer_left`, `no_dish`). Phụ thuộc: chốt cấu trúc `customer` với TV3.
  - **TV3 (`nguyentrunghai7` — `sim/quan-interact` + `scenario`, Harness):** Code Lát 4 trong `chonoi/sim/quan.py` (`interact` bếp/bàn, nấu/lấy/bưng/phục vụ, `paid`, boa, uy tín, `quan_end`), kiểm mâu thuẫn mức luật trong `chonoi/scenario.py`, quản lý `AGENTS.md` + `docs/ai-usage-log.md`. Phụ thuộc: cấu trúc `customer`/`stove` với TV2.
  - **TV4 (`dungtran16042003-afk` — `client/ui`, Demo Lead):** Nâng cấp `chonoi/web/index.html` (HUD, hình ảnh chợ nổi, hiệu ứng) đọc từ `GET /state`, chạy thử `python -m chonoi.live` để kiểm tra trải nghiệm & phát hiện lỗi luật. Phụ thuộc: snapshot từ TV1/TV2/TV3.
  - **TV5 (`nvcuong96` — `qa`, QA/Scrum):** Viết test hộp đen & unit test theo từng AC của PRD-0, tổ chức standup giữa phase (`docs/standup.md`), thu bằng chứng `docs/proof/phase-1/` và hoàn thiện `docs/verification/phase-1.md`. Phụ thuộc: TV1, TV2, TV3 xong từng lát.
- **Rủi ro & giảm thiểu:**
  - *Xung đột khi TV2 và TV3 sửa chung `quan.py`:* Chốt sớm interface dữ liệu ở kickoff, TV2 làm khối khách trước hoặc tách helper.
  - *Sai lệch payload sự kiện hoặc edge-case so với PRD-0:* PO (`dvq2609`) đối chiếu ngay PRD-0 trên lab board và ghi rõ vào `docs/clarify.md`.
  - *Lệnh `python3` trên Windows trỏ vào MS Store alias:* Cài đặt alias/Python đúng trên máy thành viên, không sửa `python3` trong `game.contract.json` để giữ tương thích CI Linux.
