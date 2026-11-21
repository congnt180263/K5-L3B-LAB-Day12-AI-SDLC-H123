---
name: qa-run-matrix
description: Chạy bộ test QA, tính trạng thái đạt/chưa đạt của từng AC và lưu log để điền ma trận docs/verification/phase-n.md. Dùng ở phút 20, trước khi tag và mỗi khi nhóm đẩy code mới.
---

# QA Run Matrix (TV5, QA Lead / Scrum)

Mục tiêu: ma trận truy vết luôn khớp với lần chạy thật trên commit hiện tại, không điền tay.

## Khi nào dùng
- Có commit mới của TV1/TV2/TV3 (sau khi `git pull`).
- Phút 20 mỗi phase (smoke tích hợp), và trước hạn tag `phase-n`.

## Các bước
1. `git pull --ff-only origin main` (không ép gộp; có xung đột thì báo chủ file).
2. Chạy: `python .agents/skills/qa-run-matrix/status.py --phase <n> --log docs/proof/phase-<n>/qa_tests.txt`
   - Quy ước test: `test_ac_p<n>_<NN>_...` thuộc `AC-P<n>-<NN>`. AC đỏ nếu bất kỳ test hoặc subTest của nó đỏ.
   - Test ghép nhiều AC (ví dụ `test_ac_p2_06_07_...`) chỉ được tính cho AC đầu; AC còn lại tự đối chiếu tay.
   - Phase 2 tự bật `QA_P2=1` để chạy test v1.1 (mặc định bị bỏ qua khi `contract_version` còn 1.0).
3. Chạy thêm smoke của giảng viên: `PYTHONPATH=tests:. python -m unittest discover -s tests -p test_smoke_p1.py -v`, lưu log vào `docs/proof/phase-<n>/smoke_p1.txt`.
4. Điền cột "Kết quả" trong `docs/verification/phase-<n>.md` theo bảng script in ra. Dẫn link log ở cột "Bằng chứng". AC chưa có test ghi `chưa kiểm`.
5. Gửi chủ lát danh sách AC đỏ của họ (không tự sửa luật của người khác).

## Quy tắc
- Không sửa test cho xanh khi luật sai. Test đổi vì luật mới (ví dụ số chuẩn Phase 2) thì ghi lý do trong commit.
- Kết quả ghi trung thực: đỏ là `chưa đạt`, test bỏ qua không được tính là `đạt`.
- Chỉ commit bằng tài khoản GitHub của chính mình.
