# Hợp đồng phát hành (v1.3)

Quy ước v1.3 giữ gameplay và schema kho v1.2. File kho có đúng khóa `items` chứa mảng cá thể `{id,kind,fresh}`, ví dụ [inventory.sample.json](inventory.sample.json). Mảng rỗng là `{"items":[]}`. Hai tiến trình headless trao kho qua file, còn chế độ `day` trao cùng tick qua bộ nhớ. Một lần `gather_end` ghi file nguyên tử đúng một lần.

Snapshot dùng `gather.hold`, `quan.stock` và `shop.stock` theo mảng cá thể. `customers[].reserved` chứa ID nguyên liệu. `cook_started.items` chứa cá thể đã dùng, `spoiled` phát đúng khi độ tươi đi qua ngưỡng. Vòng đời khách, món và giá dùng cùng một lớp mô phỏng ở live và headless. [Quyết định đổi kho](../adr/0001-kho-ca-the.md)

# Hợp đồng tích hợp (Phase 1 — baseline từ starter, đối chiếu thêm PRD-0)

## 1. Schema file kho (Contract G)
- Định dạng JSON một dòng, UTF-8, sắp khóa tăng dần, lược bỏ nguyên liệu có số lượng `0`:
  ```json
  {"items":{"bong_sung":2,"ca_loc":1}}
  ```
- Khóa gốc duy nhất: `"items"` (object ánh xạ `kind -> số nguyên > 0`).
- Nguyên liệu hợp lệ P1 (`chonoi/inventory.py`, `KINDS_P1`): `ca_loc`, `ca_linh`, `bong_dien_dien`, `bong_sung`.
- Quy tắc ghi: `chonoi.runner.Session.write_inventory_if_done` chỉ ghi **một lần** khi có `gather_end` (nếu hết `--ticks` trước khi kết thúc buổi thì không tạo/ghi đè file kho). Nếu ngất (`reason: "fainted"`), giỏ bị xóa sạch nên file kho là `{"items":{}}`.
- Ví dụ ở trên ghi theo hợp đồng kho đếm v1.0.

## 2. Giao diện giữa `sim/*` và `client/ui`
- **Chiều đọc (`GET /state` hoặc `Session.snapshot()`):**
  - Chung mọi mode: `type`, `tick`, `sim_tick`, `mode`, `phase`, `phase_tick`, `state` (`"playing" | "finished"`), `time_left_ticks`, `money`, `earned`, `reputation`, `score`, kèm `meta` (`tuning[mode]`), `events`, `finished`, `reason`, `error`.
  - `gather`: `player` (`pos`, `vel`, `heading_deg`, `oxygen_ticks`, `oxygen_max_ticks`, `hp`, `hp_max`, `zero_oxy_ticks`, `invuln_ticks`, `catch_cd_ticks`, `at_surface`), `hold` (mảng thứ tự nhặt, cuối mảng là mới nhất), `hold_count`, `hold_capacity`, `nodes` (`id`, `pos`, `kind`, `ready`, `regrow_ticks`), `fish` (`id`, `pos`, `kind`, `heading_deg`).
  - `quan`: `player` (`pos`), `stock`, `hand`, `stoves` (`id`, `pos`, `state`, `dish`, `cook_ticks_left`, `ready_ticks`), `tables` (`id`, `pos`, `customer_id`), `customers`.
- **Chiều ghi (`POST /input`, `POST /restart`):**
  - `POST /input`: `{"move": [dx, dy], "interact": bool, "catch": bool}` (`dx, dy ∈ [-1, 1]`; `gather`: `dy > 0` là lặn xuống; `quan`: `dy > 0` là đi lên phía bắc `z+`).
  - Client **chỉ đọc snapshot** và không nhân đôi logic mô phỏng; mọi hiệu ứng/âm thanh mở rộng phải tắt khi chạy `headless`.

## 3. Danh sách sự kiện (`type: "event"`, `tick`, `phase`, `name`, `data`)
- **`gather` (phát bởi `GatherSim`):**
  - `dive` (`{"pos": [x, d]}`): từ mặt nước (`d <= surface_depth`) xuống dưới nước.
  - `surface` (`{"pos": [x, d]}`): từ dưới nước lên mặt nước.
  - `oxygen_empty` (`{"oxygen_ticks": 0}`): oxy giảm từ dương xuống `0`.
  - `choke` (`{"hp": int}`): hết chu kỳ ngạt `choke_interval_ticks`, mất `1` Máu.
  - `faint` (`{"cause": "choke" | "monster", "lost": [...], "hp": 0}`): Máu về `0`, mất toàn bộ giỏ theo thứ tự LIFO.
  - `gather` (`{"node_id": str, "kind": str, "amount": int}`): hái nút ở mặt nước.
  - `node_regrown` (`{"node_id": str}`): nút mọc lại xong (`regrow_ticks` về `0`).
  - `fish_caught` (`{"fish_id": str, "kind": str, "yield": int}`): bắt đàn cá bằng `catch` dưới nước.
  - `hold_full` (`{"action": "gather" | "catch", "node_id" | "fish_id": str, "required": int, "free": int}`): giỏ không đủ chỗ khi hái hoặc bắt cá.
  - `gather_end` (`{"reason": "docked" | "time" | "fainted", "inventory": {"items": ...}}`): kết thúc buổi sáng.
- **`quan` (phát bởi `QuanSim` — chốt chi tiết theo PRD-0 mục E/F):**
  - `customer_arrived`, `no_dish`, `customer_left`, `cook_started`, `dish_ready`, `dish_picked`, `served`, `paid`, `quan_end`.

> Khi đổi hợp đồng sau này (Phase 2+): báo cả nhóm trên kênh chung và ghi ADR trong `docs/adr/`.
