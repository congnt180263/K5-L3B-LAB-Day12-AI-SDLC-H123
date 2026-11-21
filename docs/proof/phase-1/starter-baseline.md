# Kết quả chạy test starter trước Lát 3

- Ngày chạy 2026-11-21, trên Windows với Python 3.14.9.
- Mã nguồn tại `f0a1906`.
- Kết quả `Ran 32 tests in 7.092s`, `OK`.
- Ca tích hợp `test_inv_01_gather_writes_inventory_quan_reads_it` xác nhận kho do `gather` ghi được nạp vào snapshot tick 0 của `quan`.
- Các ca scenario quán hiện có xác nhận loader xử lý sai mode, vị trí ngoài biên, bàn thiếu hoặc sai và vận tốc người chơi hợp lệ.
- Bộ test starter chưa kiểm chứng chọn món, lịch đến, trả giữ chỗ, `customer_left` hoặc `no_dish`.

```powershell
$env:PYTHONPATH = 'tests;.'
python3 -m unittest discover -s tests -v
```

## Thử quán qua mốc khách đến đầu tiên

```powershell
python3 -m chonoi.headless --mode quan --seed 1 --ticks 121 --snapshot-every 1 --inventory docs/contracts/inventory.sample.json --out quan-stocked.jsonl
python3 -m chonoi.headless --mode quan --seed 1 --ticks 121 --snapshot-every 1 --out quan-empty.jsonl
```

Hai lượt đều thoát mã 0. Ở tick 120, preset đặt `first_customer_tick` tại mốc này và cả hai lượt có 0 khách. File có kho giữ nguyên `{"bong_sung":2,"ca_loc":1}`, file kho rỗng cho `{}`. Cả hai file có 0 dòng sự kiện. Các kết quả này ghi lại hành vi starter để đối chiếu sau khi triển khai.
