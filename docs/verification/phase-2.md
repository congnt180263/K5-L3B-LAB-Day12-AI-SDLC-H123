# Ma trận truy vết Phase 2 (TICKET-02, Test Contract v1.1)

> Nguồn AC: TICKET-02. Ticket không đánh số sẵn nên QA tự đặt `AC-P2-xx`, kèm mục gốc. Người chịu trách nhiệm là ĐỀ XUẤT (xem `docs/plan/phase-2.md`).
> Bộ test hộp đen `tests/test_qa_p2.py` đã có cho 15 AC (contract v1.1, quái, quán 2 bếp/4 bàn, ngày, pause, byte-giống-nhau, hiệu năng). Test tự bật khi `contract_version` là 1.1; ép chạy: `QA_P2=1`. Các AC còn lại chưa có test. Kết quả sẽ chạy lại trên commit bàn giao, bằng chứng lưu ở `docs/proof/phase-2/`.

| AC | Cách kiểm chứng | Bằng chứng (link `docs/proof/phase-2/...`) | Kết quả (đạt / chưa đạt — ghi trung thực) |
|---|---|---|---|
| AC-P2-01: `contract_version:"1.1"`; tuning chuẩn, đủ khóa mới (`fish_*`, `gather.monsters`, `day_plan`, `shop`) (4.1; TV1) | test hộp đen đọc `game.contract.json` | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-02: 6 nguyên liệu, 6 món đúng công thức, thời gian nấu, giá (1.3; TV2) | so từng món với bảng thực đơn | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-03: `--mode day --days N`: N∈1..5, mặc định 1, ngoài dải hoặc dùng với mode khác thoát mã 2 (4.1; TV3) | test tham số | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-04: nút mới `pause`, `shop_done`, chuỗi `buy`; nút sai pha hoặc mở rộng chưa bật bị bỏ qua; giữ nút qua đổi pha không tạo cạnh (4.2; TV3) | test inputs theo pha | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-05: scenario v1.1: khối `day`, cấm `quan.stock`/`quan.reputation` khi chạy `day`, `gather.player.invuln_ticks` hợp lệ, `fish[].age_ticks`, `monsters[]`; mâu thuẫn mã 2 (4.3; TV3) | fixture hợp lệ và sai | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-06: nút N5/N6 (kèo nèo) ở `d=0`; yield cá linh 3, cá lóc 1, cá kèo 2 (1.1; TV1) | snapshot tick 0, bắt từng loài | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-07: đầu ca 8 đàn ở 8 điểm sinh khác nhau, đúng độ sâu theo loài (1.1; TV1) | snapshot tick 0, nhiều seed | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-08: cá bơi 1.5 m/s trong `x∈[4,96]`, đúng dải độ sâu theo loài (1.1; TV1) | quỹ đạo từng loài | | chưa kiểm |
| AC-P2-09: đổi hướng theo seed ở bước bơi 120, 240… trước khi di chuyển (1.1; TV1) | quan sát `heading_deg` quanh bước 120 | | chưa kiểm |
| AC-P2-10: phản xạ mép: phần quãng còn lại, đảo thành phần vuông góc, chạm góc đảo cả hai (1.1; TV1) | fixture cá sát mép và sát góc | | chưa kiểm |
| AC-P2-11: sinh cá tại `phase_tick = 360k` sau khi cá bơi: tối đa một đàn, trần 12, cách mọi đàn > 1 m, bỏ lượt khi hết điểm, trọng số 40/30/30 chuẩn hóa, `fish_spawned{id,kind,pos}`, cá mới tham gia từ bước sau (1.1, 4.4; TV1) | đếm sự kiện nhiều seed, fixture đủ trần | | chưa kiểm |
| AC-P2-12: bắt cá dùng vị trí cá TRƯỚC khi bơi (4.5; TV1) | fixture đàn đang bơi ra khỏi bán kính | | chưa kiểm |
| AC-P2-13: `random_fish:false` tắt bơi và sinh, cá fixture đứng yên; khai `fish` khi cờ bật thì thay đàn ban đầu nhưng vẫn bơi/sinh; `age_ticks` (4.3; TV1) | fixture 2 chế độ | | chưa kiểm |
| AC-P2-14: ngạt xuyên bất tử và không làm rơi hàng; reset nhịp khi oxy > 0 hoặc lên mặt (1.1; TV1) | fixture bất tử + oxy 0 | | chưa kiểm |
| AC-P2-15: Cá Sấu: M1 `[60,24]`↔`[64,24]` từ Ngày 1; M2 `[85,18]`↔`[89,18]` từ Ngày 3; `gather` độc lập dùng bố trí Ngày 1 (1.2; TV1) | snapshot `monsters[]` theo ngày | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-16: `patrol` 1.0 m/s, đổi mục tiêu ở bước sau khi đến waypoint (1.2; TV1) | quỹ đạo | | chưa kiểm |
| AC-P2-17: `chase`: người chơi `d≥10` và cách ≤ 10 m thì 3.0 m/s; về `patrol` khi cách > 16 m hoặc `d<10`; chặn theo biên và dải độ sâu của loài (1.2; TV1) | fixture ngưỡng 10/16 m, `d=10` | | chưa kiểm |
| AC-P2-18: chạm: ≤ 1.5 m, `d≥10`, hết bất tử: -1 Máu, bỏ `floor(n/2)` LIFO, bất tử 90 tick, `monster_hit{monster_id,hp,lost,pos}`; tối đa một hit/bước, chọn gần nhất, hòa theo id (1.2, 4.4; TV1) | fixture giỏ lẻ/chẵn, 2 quái | | chưa kiểm |
| AC-P2-19: trong bất tử không hit và không chuyển `recoil` do chạm (1.2; TV1) | fixture `invuln_ticks` | | chưa kiểm |
| AC-P2-20: `recoil` 60 bước từ bước sau, lùi 2/60 m theo hướng chốt lúc chạm (trùng tâm dùng +x), chặn mép, không hit, hết thì `patrol` (1.2; TV1) | quỹ đạo, `recoil_dir` | | chưa kiểm |
| AC-P2-21: Máu về 0 do quái: `faint{cause:"monster",lost,hp:0}` rồi `gather_end(fainted)` ngay, bỏ các bước còn lại; quán vẫn mở với kho rỗng (1.2, 4.4, 4.5; TV1) | fixture `hp=1` cạnh quái | | chưa kiểm |
| AC-P2-22: snapshot gather có `monsters[]` và `player.invuln_ticks` (4.4; TV1) | đọc JSONL | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-23: quán có B1 `[2,8]`, B2 `[5,8]`, T1 `[9,2]`, T2 `[13,2]`, T3 `[9,6]`, T4 `[13,6]` (1.3; TV2) | snapshot tick 0 | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-24: khách: lượt đầu tick 120, sau đó `120+900k` nếu có bàn trống, ngồi ghế trống id nhỏ nhất (1.3; TV2) | đếm `customer_arrived`, `table_id` | | chưa kiểm |
| AC-P2-25: bếp lấy đơn `reserved` cũ nhất (`order_tick`, rồi id bàn); `interact` chọn gần nhất, hòa bếp trước bàn rồi id; tay cầm 1 món (1.3; TV2/TV3) | fixture 2 khách, 2 bếp | | chưa kiểm |
| AC-P2-26: boa, uy tín, đóng ca giữ như v1.0 với số chuẩn (hồi quy) (1.3; TV3) | chạy lại test lát 4 | | chưa kiểm |
| AC-P2-27: 3 món mới: canh chua (8 s, 90), cá kèo nướng (6 s, 70), lẩu mắm (12 s, 200) nấu và tính giá đúng (1.3; TV2) | fixture từng món | | chưa kiểm |
| AC-P2-28: chuyển pha: `day_start`, `day_plan`, `phase_start(gather)`; sau `gather_end` dựng quán và `phase_start(quan)` cùng tick kể cả khi ngất; sau `quan_end` dựng Shop và `phase_start(shop)` (4.5; TV1) | thứ tự event theo tick | | chưa kiểm |
| AC-P2-29: kế hoạch D1–D5 công bố đúng `dishes`, `ingredients` (tính từ công thức) (2; TV1) | so với bảng kế hoạch | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-30: bàn giao `gather` sang `quan` trong bộ nhớ khớp schema kho; ngất thì kho rỗng và vẫn mở quán (1.2, 4.1; TV1) | `day` với fixture ngất | | chưa kiểm |
| AC-P2-31: trong `day`, khách chọn đều theo seed trong món thuộc kế hoạch đủ nguyên liệu (trừ giữ chỗ), vẫn gọi tiếp khi đã bán đủ suất (2, 4.5; TV2) | kho hạn chế, nhiều khách | | chưa kiểm |
| AC-P2-32: giữ qua Ngày: tiền, `earned`, uy tín, cấp nâng cấp; oxy/Máu hồi đầy theo cấp hiệu lực; giỏ mới; kho dư bỏ sau Shop (2; TV1) | `day --days 2` | | chưa kiểm |
| AC-P2-33: Shop: `oxygen` (200→2.700 tick; 400→3.600), `hp` (250→4 Máu; 500→5); đủ đúng giá vẫn mua; một lần mỗi cấp; trừ `money`, giữ `earned`; `bought{upgrade,level,price,money}` (2, 4.4; TV1) | fixture tiền = đúng giá | | chưa kiểm |
| AC-P2-34: `buy_failed{action,reason}` với `funds`/`max_level`/`out_of_stock`/`unknown`; tiền và cấp giữ nguyên (2, 4.4; TV1) | từng lý do | | chưa kiểm |
| AC-P2-35: cấp vừa mua hiện ngay ở `upgrades`, sang `active_upgrades` chỉ khi dựng Ngày kế (4.4, 4.5; TV1) | snapshot trước/sau đổi Ngày | | chưa kiểm |
| AC-P2-36: Shop đóng bằng `shop_done` hoặc sau 600 tick: `shop_end{reason}`; xử lý một `buy` trước `shop_done` kể cả bước cuối; `days_completed` tăng; Ngày cuối hoàn tất khi Shop đóng (2, 4.5; TV1) | fixture bước cuối | | chưa kiểm |
| AC-P2-37: `end` của `day`: `days_completed`, `reason:"days_complete"`; một Ngày không pause ≤ 22.200 tick (2, 4.4; TV1) | `day --days 5` | | chưa kiểm |
| AC-P2-38: snapshot `day`: `day`, `day_plan`, `upgrades`, `active_upgrades`, `phase` gather/quan/shop; đổi pha thì `phase_tick:0`; event có `day` (4.4; TV1) | đọc JSONL | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-39: `pause` ở cả 3 mode và trong Shop: xét trước; `state:"paused"`, `paused`; `sim_tick`, `phase_tick`, lịch, timer đứng yên; bỏ qua cạnh hành động và `buy`; cạnh lên kế tiếp phát `resumed` và chạy gameplay ngay (4.2; TV3) | inputs pause giữa ca | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-40: cùng seed cho JSONL giống từng byte ở `day` nhiều Ngày (Test Contract; TV5) | chạy 2 lần | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-41: hiệu năng: headless một Ngày không pause ≤ 20 s trên máy chấm (2; TV5) | đo thời gian `day --days 1` | [test_qa_p2.py](../../tests/test_qa_p2.py) (tự bật khi `contract_version` là 1.1, hoặc `QA_P2=1`) | chưa đạt: chưa có code v1.1; test đã sẵn sàng, chạy ép `QA_P2=1` thì đỏ hết (Phase 2 mới bắt đầu) |
| AC-P2-42: hồi quy Phase 1: AC-P1 còn hiệu lực đạt với số chuẩn; test đổi có lý do trong commit (5; TV5) | chạy bộ test P1 | | chưa kiểm |
| AC-P2-43: smoke tích hợp `gather --inventory-out` rồi `quan --inventory`, snapshot kho tick 0 khớp, lưu `docs/proof/phase-2/integration.*` ở phút 20 (5; TV5) | chạy luồng 2 tiến trình | | chưa kiểm |
| AC-P2-44: menu chính (Chơi/Thoát), DayIntro (tự chuyển sau 4 s hoặc phím), EveningIntro, DayResult, Summary (2; TV4) | chơi thử, ảnh chụp | | chưa kiểm |
| AC-P2-45: pause menu (Tiếp tục, Về menu), làm mờ nền, dừng đồng hồ và mọi timer kể cả trong Shop (2; TV4) | chơi thử | | chưa kiểm |
| AC-P2-46: HUD sáng: Máu, oxy (< 25% đổi màu/nhấp nháy), thời gian (≤ 30 s đổi màu), độ sâu, giỏ theo loại, danh sách cần lấy, hồi bắt, gợi ý hái/cập bến, "Thủy quái!" cùng viền tím, "Hết hơi!" (2; TV4) | chơi thử, ảnh chụp | | chưa kiểm |
| AC-P2-47: HUD quán: đồng hồ ca, tiền ca, uy tín, món và kiên nhẫn từng bàn (đổi màu < 25%), tiến độ bếp, món đang cầm, kho khả dụng (2; TV4) | chơi thử, ảnh chụp | | chưa kiểm |
| AC-P2-48: chữ không chân ≥ 18 px ở 1280×720; bản chơi thường ≥ 30 FPS trung bình (2; TV4) | đo FPS | | chưa kiểm |
| AC-P2-49: nhóm 5 người hoàn thành ≥ 1 mục mở rộng, khai trong README (và `extensions` ở manifest nếu có mã), có test/bằng chứng (3; cả nhóm) | đọc README, chạy test mục đã chọn | | chưa kiểm |
| AC-P2-50: ghi chép: `verification/phase-2`, `proof/phase-2`, `clarify`, `ai-usage-log`, retro nhanh có một hành động có người nhận (5; cả nhóm) | đọc file | | chưa kiểm |
| AC-P2-51: tag `phase-2` trên `main` xanh, chậm nhất 1:55 (DoD; TV1) | `git tag`, chạy test | | chưa kiểm |

## Đánh giá ngắn
- Yêu cầu nào đạt / chưa đạt: 15 AC có test đều chưa đạt vì chưa có code v1.1 (đầu phase); 36 AC còn lại chưa kiểm.
- Điều cần chỉnh cho phase sau:
