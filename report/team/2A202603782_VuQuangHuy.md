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

Commit chính: phần triển khai đã được commit theo xác nhận của thành viên; bổ sung hash commit khi hoàn thiện báo cáo nhóm nếu cần đối chiếu lịch sử Git.

## 4. Bằng chứng

- Mã nguồn: [`src/lab8/shapes/workflow.py`](../../src/lab8/shapes/workflow.py).
- Đã chạy `python -m pytest -q` và các test đã pass (theo kết quả chạy của thành viên).
- Đã chạy bộ student test cho workflow: `python -m pytest -q -m student -o addopts= -k workflow`; kết quả pass (theo xác nhận của thành viên).

## 5. Công cụ AI đã dùng

Đã dùng OpenAI Codex để giải thích mục tiêu lab, phân rã yêu cầu workflow, rà soát contract và hỗ trợ triển khai `workflow.py`. Tôi đã kiểm tra chữ ký/hướng dẫn trong file, đối chiếu với tài liệu business rules và contract, rồi tự chạy các lệnh pytest nêu trên để kiểm tra kết quả. Quyết định và trách nhiệm đối với phần nộp thuộc về tôi.

## 6. Tự đánh giá

Tôi đã hoàn thành shape workflow theo contract chung và xác nhận các test host cùng test workflow đều pass. Điểm tôi học được là cần giữ ranh giới rõ giữa logic xác định quote và thao tác ghi tiền: shape chỉ gửi quote đầy đủ, còn host chịu trách nhiệm kiểm tra approval, cap theo order và idempotency. Tôi cũng chú ý rằng trace là một phần của ranh giới bảo mật, nên chỉ ghi dữ liệu tối thiểu đã được cho phép. Phần tích hợp cuối cùng và benchmark so sánh bốn shape cần được xác nhận cùng cả nhóm.
