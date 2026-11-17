# Báo cáo cá nhân — 2A202603782_VuQuangHuy

## 1. Thông tin thành viên

- Họ tên: Vũ Quang Huy
- MSSV: 2A202603782
- Email: 26ai.huyvq6@vinuni.edu.vn
- GitHub: huyvu-03

## 2. Phần việc phụ trách

Phụ trách Shape A — workflow: triển khai quy trình xử lý claim hoàn phí theo các bước Python cố định trong `src/lab8/shapes/workflow.py`.

## 3. Đóng góp cụ thể

- Hoàn thiện `run_claim` theo đúng chữ ký được yêu cầu; mở store và đọc claim/order bằng các read tool được cung cấp.
- Dùng dữ liệu order có cấu trúc để tính quote qua `compute_compensation`, không dựa vào nội dung ticket để quyết định số tiền.
- Xử lý các trường hợp claim không tồn tại, thiếu `order_id`, order không tìm thấy hoặc không thuộc principal, quote bằng 0, host từ chối, và refund thành công.
- Chuyển quote đầy đủ tới `durability.issue_refund`; chuyển tiếp `crash_at` để host xử lý approval, giới hạn theo order, idempotency và crash/resume.
- Không nuốt `InjectedCrash`; ghi trace an toàn cho kết quả bình thường và trước khi ném lại crash. Trace chỉ chứa các trường cần thiết, không ghi ticket hoặc dữ liệu nhạy cảm của order.
- Dùng `common.finish()` để tạo `RunResult` và lấy thông tin ledger/audit nhất quán.
- Sửa kiểm tra `order_id` để chuỗi rỗng hoặc chỉ có khoảng trắng trả về `needs_info`; ID không rỗng vẫn được chuyển nguyên giá trị vào bước tra cứu.
- Thêm regression test xác nhận ID chỉ có khoảng trắng trả `needs_info` và không ghi refund.
- Điền kết quả ablation R2 trong research card, đối chiếu run T02 giữa single và swarm theo benchmark public.

Commit liên quan: `1723d3e` (triển khai workflow), `f242fa4` (xử lý ID chỉ có khoảng trắng), `f2727a2` (thêm regression test và cập nhật bảng đóng góp), `e400c59` (báo cáo cá nhân), `76ec1cf` (kết quả ablation).

## 4. Bằng chứng

- Commit: `1723d3e` (workflow), `f242fa4` (xử lý order ID chỉ có khoảng trắng), `f2727a2` (regression test), `76ec1cf` (kết quả ablation).
- Mã nguồn: [`src/lab8/shapes/workflow.py`](../../src/lab8/shapes/workflow.py).
- Regression test: [`src/tests/test_workflow_whitespace_order_id.py`](../../src/tests/test_workflow_whitespace_order_id.py). Chạy riêng từ `src/` bằng `python -m pytest -q tests/test_workflow_whitespace_order_id.py`.
- Theo kết quả grading lại do thành viên cung cấp trên bản copy: student suite đạt 248 passed và `python -m lab8.check_submission` đạt `0 FAIL`; lượt này bao gồm regression test whitespace-only order ID. Kết quả được xác nhận trên bản copy, không phải lượt chạy trực tiếp trong môi trường hiện tại.
- Run ID / benchmark: [`src/reports/benchmark.json`](../../src/reports/benchmark.json); T02 dùng `R-single-C-002-s11`, `R-single-C-002-s22`, `R-single-C-002-s33`, `R-single-C-002-s44`, `R-single-C-002-s55` và `R-swarm-C-002-s55` để đối chiếu kết quả single 5/5 với lỗi swarm ở seed 55.

## 5. Công cụ AI đã dùng

Đã dùng OpenAI Codex để giải thích mục tiêu lab, rà soát contract, hỗ trợ triển khai `workflow.py`, bổ sung regression test cho order ID chỉ có khoảng trắng và hoàn thiện phần ablation trong research card. Tôi đối chiếu thay đổi với chữ ký hàm, business rules, contract và benchmark. Quyết định và trách nhiệm đối với phần nộp thuộc về tôi.

## 6. Tự đánh giá

Tôi đã hoàn thành shape workflow theo contract chung, xử lý trường hợp order ID chỉ có khoảng trắng, thêm regression test và ghi lại kết quả ablation liên quan. Grading lại trên bản copy báo student suite 248 passed và submission checker `0 FAIL`. Tôi học được cách giữ ranh giới giữa việc tính quote trong shape và việc ghi tiền qua host, cũng như chỉ đưa dữ liệu cần thiết vào trace.
