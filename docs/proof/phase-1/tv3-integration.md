# TV3 Phase 1 trên code TV2

Repo: congnt180263/K5-L3B-LAB-Day12-AI-SDLC-H123, nhánh nguyentrunghai (gốc 98674ce, cùng main khi tích hợp).
Đã đọc AGENTS.md, TEAM.md, plan/phase-1.md, PRD-0.md và contract.
Giữ lịch khách, phần giữ chỗ và RNG customer_order của TV2; bổ sung lát 4 theo PRD F.
Sửa scenario.py để từ chối cập nhật bàn/bếp sai id, trường lạ, tọa độ ngoài miền, cờ random sai kiểu và uy tín ngoài miền; không đổi schema kho hay contract.

- Full suite: 58 tests OK (tv3-tests.txt), bao gồm test TV2.
- tools/check_team.py: OK 5 thành viên.
- Headless phục vụ ở tick đóng ca: served -> paid -> quan_end; tiền 60, reason time (tv3-closing.jsonl).
- git diff --check: đạt.

Thư mục LAB12 cũ không có .git và bị khóa. Bản làm việc tại LAB12-team-staging; TV3 bàn giao qua nhánh nguyentrunghai. Không dùng kết quả của repo cá nhân làm bằng chứng cho repo này.
