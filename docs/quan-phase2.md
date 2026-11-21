# Quán Phase 2 và giao diện bàn giao

TV3 phụ trách toàn bộ QuanSim theo TICKET-02 mục 1.3, 2 và 4.5. Dữ liệu quán nằm trong game.contract.json: B1/B2, T1–T4, sáu món. Lõi không bật cháy món.

## Dùng trong day

```python
sim = QuanSim(tuning, quan_template, streams, ids,
              inventory=actual_handoff,
              day_plan={"dishes": {"ca_keo_nuong": 2}},
              money=money, earned=earned, reputation=reputation)
```

Day coordinator phải tính kế hoạch/ingredients, chuyển pha và xác thực phần gốc day. `quan_template` không được có stock/reputation; inventory là kho thật khi mở quán, kể cả rỗng sau ngất. Fixture khách ngoài kế hoạch hoặc phần giữ quá kho thật sẽ bị từ chối lúc dựng sim. Lấy lại money/earned/reputation sau ca; shift_earned chỉ tính phần thu trong ca mới. Khách có thể tiếp tục gọi món thuộc kế hoạch sau khi vượt số suất dự kiến.

Standalone dùng cả 6 món, tiền/earned ban đầu bằng 0. Hai nguyên liệu mới được chấp nhận trong scenario.stock và --inventory; schema items không đổi. KINDS_P1 giữ riêng cho gather P1, KINDS_P2 dùng ở đường nhập quán. Người làm gather cần dùng tập P2 khi nâng gather.

## Pause

Session xử lý cạnh pause trước mọi gameplay: bước pause chỉ tăng tick ngoài; giữ sim_tick, lịch khách và mọi timer. Resume chạy gameplay ngay cùng bước. Cạnh interact phát trong pause không bị phát lại sau resume. Live API nhận pause; UI cần nối Esc/P và màn pause khi tích hợp giao diện.

## Kiểm chứng và phần còn lại

Chạy `python .agents/skills/quan-check/scripts/check.py`. Kết quả ở docs/proof/phase-2/quan-*. Test cũ schedule_menu_selection_and_determinism đổi từ một khách sang hai khách ở T1/T2 theo Ticket-02; bỏ fixture thêm T2 vì T2 đã có sẵn.

Chưa hoàn tất toàn game P2: day/Shop, kế hoạch D1–D5, gather P2, UI và manifest đầy đủ v1.1 cần tích hợp ở lát chung. Không đổi contract_version thành 1.1 khi CLI day vẫn chưa hỗ trợ. Không coi test API day là test trọn một ngày. Không chọn mở rộng burn thay nhóm.
