# Kiểm chứng Lát 3 — khách và giữ chỗ

Chạy trên Windows với Python 3.14.9. Bộ test hiện có và 7 ca Lát 3 đều qua, tổng cộng 43 ca. [Log unittest](unittest.txt)

## Chạy lại

```powershell
$env:PYTHONPATH = 'tests;.'
$env:PYTHONUTF8 = '1'
python3 -m unittest discover -s tests -v

'{"gather":{"hold":["ca_loc","bong_sung","bong_sung"]}}' | Set-Content -Encoding Ascii dock.json
'{"frames":[{"tick":0,"interact":true}]}' | Set-Content -Encoding Ascii dock-inputs.json
python3 -m chonoi.headless --mode gather --seed 1 --ticks 1 --scenario dock.json --inputs dock-inputs.json --inventory-out inv.json --out gather.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 121 --inventory inv.json --snapshot-every 1 --out quan.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 121 --inventory inv.json --snapshot-every 1 --out quan-repeat.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 121 --out quan-empty.jsonl
Get-FileHash -Algorithm SHA256 quan.jsonl,quan-repeat.jsonl
```

## Quan sát headless

| Lượt | Tick | Kết quả |
|---|---:|---|
| `gather` cập bến | 1 | `gather_end` với `reason: docked` và kho `{"items":{"bong_sung":2,"ca_loc":1}}`. |
| Quán nạp kho | 0, 119 | `stock` khớp file kho và bàn trống. |
| Quán nạp kho | 120, 121 | Tick 120 có `customer_arrived` cho `C1` tại `T1`, món `ca_loc_nuong_trui`. Khách giữ 1 `ca_loc`, `stock` vật lý vẫn giữ nguyên. Kiên nhẫn từ 3600 xuống 3599 ở tick 121. |
| Quán kho rỗng | 120 | `no_dish` với `data: {}`. |

Hai lượt quán cùng seed và dữ liệu cho JSONL giống từng byte, SHA-256 là `583a2f98b6ee7fc7a00025c38f667a89d8add1638dc7820c5b9ce2afab4aefb8`.

Các ca test xác nhận khách từ fixture giữ công thức, tắt khách tự sinh, bỏ lượt khi kín bàn, loại nguyên liệu đã giữ khỏi lựa chọn của bàn khác và nhả giữ chỗ trước khi xét khách mới trong cùng tick. Khi khách bỏ đi, món đã được gán bị hủy mà kho vật lý giữ nguyên. Fixture mâu thuẫn trả mã 2 trước khi tạo JSONL.

Trong bản triển khai này, kiên nhẫn chỉ giảm khi khách ở `waiting`. Trường này giữ giá trị đã chốt trong thời gian `eating`.

## Bàn giao cho Lát 4

- Bếp lấy đơn `reserved` theo `order_tick` rồi id bàn. Bắt đầu nấu thì trừ `customer["reserved"]` khỏi `stock`, xóa phần giữ và đặt `order_status: assigned`.
- Chạy thao tác phục vụ sau cập nhật timer, trước khi xử lý khách rời. Thanh toán và khách rời dùng thứ tự id bàn, hoàn tất trước khi xét lượt khách mới hoặc phát `quan_end`.
- Ca nghiệm thu giao món đúng tick hết kiên nhẫn, nhận tiền và khách ăn trả ngay lúc đóng ca cần chạy sau khi gộp Lát 4.
