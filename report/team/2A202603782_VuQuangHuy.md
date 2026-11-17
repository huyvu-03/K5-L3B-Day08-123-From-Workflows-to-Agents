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

Commit liên quan: `1723d3e` (triển khai workflow), `f242fa4` (xử lý ID chỉ có khoảng trắng), `f2727a2` (thêm regression test và cập nhật bảng đóng góp).

## 4. Bằng chứng

- Mã nguồn: [`src/lab8/shapes/workflow.py`](../../src/lab8/shapes/workflow.py).
- Regression test: [`src/tests/test_workflow_whitespace_order_id.py`](../../src/tests/test_workflow_whitespace_order_id.py). Chạy riêng từ `src/` bằng `python -m pytest -q tests/test_workflow_whitespace_order_id.py`.
- `python -m pytest -q` và student test workflow `python -m pytest -q -m student -o addopts= -k workflow` đã pass trước khi thêm regression test (theo kết quả chạy trước đó). Cần chạy test regression mới để xác nhận thay đổi cuối.

## 5. Công cụ AI đã dùng

Đã dùng OpenAI Codex để giải thích mục tiêu lab, rà soát contract, hỗ trợ triển khai `workflow.py` và bổ sung regression test cho order ID chỉ có khoảng trắng. Tôi đối chiếu thay đổi với chữ ký hàm, business rules và contract; test mới cần được chạy để xác nhận. Quyết định và trách nhiệm đối với phần nộp thuộc về tôi.

## 6. Tự đánh giá

Tôi đã hoàn thành shape workflow theo contract chung, xử lý trường hợp order ID chỉ có khoảng trắng và thêm regression test cho hành vi này. Các test host và student workflow trước đó đã pass; regression test mới cần được chạy để xác nhận bản cuối. Tôi học được cách giữ ranh giới giữa việc tính quote trong shape và việc ghi tiền qua host, cũng như chỉ đưa dữ liệu cần thiết vào trace.
