---
name: quan-check
description: Kiểm chứng quán khi sửa luật khách, giữ nguyên liệu, nấu, phục vụ, pause hoặc giao diện với day; lưu regression và smoke headless Phase 2.
---

# Kiểm chứng quán

Đọc TICKET-02, `AGENTS.md` và `docs/quan-phase2.md` trước khi đổi luật quán.

Chạy từ gốc repo:

```powershell
python .agents/skills/quan-check/scripts/check.py
```

Script dùng chính Python đang chạy, bật UTF-8, chạy full suite + kiểm thành viên rồi smoke quán bằng hai tiến trình headless độc lập. So JSONL từng byte, kiểm nguyên liệu mới, B2/T4 và phục vụ đúng tick đóng ca. Lưu log ở `docs/proof/phase-2/quan-*`; trả mã khác 0 nếu bất kỳ bước nào lỗi.

Khi test cũ sai do đổi từ 1 bàn sang 4 bàn, đối chiếu Ticket rồi ghi lý do đổi test vào bằng chứng. Không thay luật để duy trì kỳ vọng Phase 1 đã bị Ticket thay thế.

Đối với `day`, test trực tiếp `QuanSim(..., day_plan=..., inventory=..., money=..., earned=..., reputation=...)`. Bắt buộc thử cả món ngoài kế hoạch lẫn kho bàn giao không đủ phần giữ. Không coi API này là bằng chứng CLI `--mode day` đã hoàn thiện.

Không tự commit, push hoặc gắn tag từ skill. Chỉ báo kết quả và phần phụ thuộc còn thiếu.
