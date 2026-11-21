# Kiểm chứng Phase 4 · Đã nghiệm thu nội bộ

- Benchmark dùng Chromium, canvas thật 1280×720, đứng ở bến, seed 42, làm nóng 3 giây và đo 30 giây. [Kết quả bench](bench.json)
- Soak headless seed 7 hoàn thành 10/10 Ngày và 0 crash. Suite kiểm thêm hai lần cùng seed và bỏ trường đo thời gian khi so. [Kết quả soak](soak.json)
- Kiểm cảnh báo bằng Chromium ở 1280×720. Bấm H bật tương phản cao, dùng fixture gần Cá Sấu và oxy thấp ở Gather, rồi khách còn 14 giây kiên nhẫn ở Quán. [Ảnh Gather](canh-bao-lan.png) · [Ảnh Quán](canh-bao-quan.png)
- Quay vòng một Ngày bằng fixture và input tất định, đủ nấu, bưng, phục vụ, trả tiền và đóng Shop. [Scenario](demo-scenario.json) · [Inputs](demo-inputs.json) · [Kết quả](demo-result.json)
- Bảng xếp hạng ghi đúng một mục sau 5 Ngày chuẩn và xuất lại qua CLI. [Kết quả xuất](leaderboard.json)
- Kiểm ZIP giải nén sạch trên Windows, mở được menu và chạy hết một Ngày headless. [Kết quả](kiem-zip.json)
- Nhóm đã duyệt bản v1.0.0. Các bằng chứng kiểm thử được ghi trên bản làm việc dựa trên `8a48030`. Việc đối chiếu với commit gắn tag sẽ thực hiện khi bàn giao.

## Trình tự demo trực tiếp

1. Mở `python3 -m chonoi.live` và chọn Chơi. Bắt một cá lóc, cập bến bằng E và tiếp tục sang Quán. Đợi khách gọi món, dùng E ở bếp để nấu rồi lấy món, mang đến đúng bàn và dùng E để giao. Khi ca đóng, xem kết quả và đóng Shop.
2. Chạy `python3 tools/verify.py` hoặc mở log đã lưu để trình bày kết quả của cả hai phiên bản hợp đồng. [Log](verify.txt)
3. Mở ma trận nghiệm thu, dùng từng mã AC để trỏ tới bằng chứng và đối chiếu đóng góp qua commit của từng thành viên. [Phase 3](../../verification/phase-3.md) · [Phase 4](../../verification/phase-4.md) · [Thành viên](../../members/)

Nếu cần chạy lại ca mẫu với đầu vào cố định, dùng lệnh dưới đây và đối chiếu sự kiện kết thúc Shop cùng `earned = 70` trong JSONL.

```bash
python3 -m chonoi.headless --mode day --seed 42 --ticks 1202 --scenario docs/proof/phase-4/demo-scenario.json --inputs docs/proof/phase-4/demo-inputs.json --out demo.jsonl
```
