# Báo cáo cá nhân — Đỗ Thị Thu Hằng

## 1. Thông tin thành viên

- **Họ tên:** Đỗ Thị Thu Hằng
- **MSSV:** 2A202603840
- **Email:** dothuhang2604@gmail.com
- **GitHub:** ThuHang2604

## 2. Phần việc phụ trách

Trong Lab Day 08 — From Workflows to Agents, mình tham gia hoàn thiện các tài liệu và kiểm thử liên quan đến khả năng xử lý workflow, ledger và tính an toàn của hệ thống LogiX-VN.

Các phần công việc đã thực hiện:

- Cập nhật tài liệu `decision_adr.md`, bổ sung và hoàn thiện nội dung về quyết định kiến trúc.
- Tham gia kiểm thử các tình huống liên quan đến ledger, refund và trace hygiene.
- Kiểm tra các trường hợp replay, conflict và xử lý `order_id` bị bỏ trống.
- Theo dõi các thay đổi trên Git, thực hiện commit trên nhánh cá nhân `thuhang` và merge các PR của cả nhóm vào `dev` và `main`.

## 3. Đóng góp cụ thể

### 3.1. Cập nhật tài liệu kiến trúc

- Hoàn thiện và cập nhật nội dung trong `decision_adr.md`.
- Ghi nhận các quyết định kỹ thuật và lập luận lựa chọn kiến trúc.
- Commit: `601e461` — `update decision_adr.md`.

### 3.2. Kiểm thử và kiểm tra tính an toàn

Tham gia bổ sung/cập nhật các kiểm thử liên quan đến:

- **Trace hygiene:** Kiểm tra dữ liệu nhạy cảm không bị ghi vào trace.
- **T13/T14:** Kiểm tra các tình huống liên quan đến refund quote và lịch sử hoàn tiền.
- **Conflict:** Kiểm tra tình huống xung đột trong quá trình xử lý.
- **Replay:** Kiểm tra khả năng xử lý khi một yêu cầu được gọi lại.
- **Blank order_id:** Kiểm tra trường hợp thiếu mã đơn hàng.

File test: `src/tests/test_ledger_extra.py` (70 test). File này quét trace và các file `<run_id>*` trên 4 shape × 14 claim public, tìm `CANARY_SECRET_`, `parent_secret` và các chuỗi trong `forbid_substrings`; kiểm tra conflict số tiền, T13, T14, replay một dòng ledger và trường hợp `order_id` rỗng hoặc toàn khoảng trắng.

Commit liên quan:

`20265e7` — `test(ledger): trace hygiene, T13/T14, conflict, replay, blank order_id (xfail)`.

**Tác động của test blank order_id:** test này ban đầu đánh dấu `xfail` vì ba shape trả trạng thái khác nhau cho `order_id` toàn khoảng trắng (workflow và single ra `escalated`, orchestrator ra `needs_info`). Sau các sửa `f242fa4` (workflow), `01e8c48` (orchestrator) và `87bf9ca` (single), cả ba shape cùng trả `needs_info`, không ghi ledger, và test đã bỏ `xfail`.

### 3.3. Tích hợp và quản lý nhánh

Mình merge các nhánh cá nhân và nhánh `dev` vào `main`: PR #6, #7, #9, #10, #11, #12, #14, #15, #16, #19 và #20, cùng các merge `dev` vào nhánh cá nhân của Huy, Cao và mình. Mình cũng cập nhật báo cáo nhóm (`1b2f382`, `bc54f5b`) và báo cáo cá nhân (`b09e29c`).

## 4. Bằng chứng

Các bằng chứng đóng góp trên Git:

| Nội dung | Commit hash |
|---|---|
| Cập nhật decision_adr.md | `601e461` |
| Cập nhật commit hash trong ADR | `d43b825` |
| Kiểm thử ledger và các tình huống liên quan | `20265e7` |
| Cập nhật báo cáo | `b09e29c` |
| Chỉnh sửa báo cáo nhóm | `1b2f382`, `bc54f5b` |
| Merge PR vào `dev`/`main` | PR #6, #7, #9, #10, #11, #12, #14, #15, #16, #19, #20 |

- **Git branch:** `thuhang`
- **Repository:** K5-L3B-Day08-123-From-Workflows-to-Agents
- **Các file liên quan:** `decision_adr.md`, `src/tests/test_ledger_extra.py`.

## 5. Công cụ AI đã dùng

- **ChatGPT:** Hỗ trợ phân tích yêu cầu bài lab, giải thích các khái niệm về workflow, agent, ledger, idempotency và các tình huống kiểm thử. Hỗ trợ rà soát nội dung tài liệu và cấu trúc báo cáo.
- **Claude:** Hỗ trợ trao đổi và tham khảo cách xử lý các vấn đề trong quá trình thực hiện bài lab.

**Cách tự kiểm tra kết quả:**

- Đối chiếu nội dung AI đề xuất với `README.md`, `RULES.md`, `business_rules.md` và `contracts.md`.
- Kiểm tra lại nội dung tài liệu và thay đổi trước khi commit.
- Sử dụng Git để kiểm tra lịch sử commit và xác nhận các thay đổi.
- Sử dụng pytest để kiểm tra các trường hợp liên quan đến logic và tính an toàn của hệ thống.

Các nội dung do AI hỗ trợ đều được xem xét và đối chiếu với yêu cầu của bài lab trước khi sử dụng.

## 6. Tự đánh giá

Qua Lab Day 08, mình hiểu rõ hơn sự khác biệt giữa Workflow, Single Agent, Orchestrator và Swarm, cũng như cách lựa chọn kiến trúc phù hợp với từng bài toán.

Mình học được tầm quan trọng của việc kiểm soát quyền sử dụng tool, bảo vệ dữ liệu nhạy cảm, đảm bảo tính nhất quán của ledger và xử lý các tình huống crash hoặc replay bằng cơ chế idempotency.

Bên cạnh việc thực hiện các thay đổi về tài liệu và kiểm thử, mình nhận thấy cần cải thiện thêm khả năng phân tích kiến trúc, đọc hiểu code có sẵn và chủ động kiểm chứng kết quả thay vì phụ thuộc vào đề xuất của AI.

Mình cũng nhận thấy ADR do mình viết đã lỗi thời sau các sửa `order_id` của ba shape (còn mô tả test `xfail` và hash cũ). Mình đã cập nhật lại ADR cho khớp với `main`.

Nhìn chung, Lab Day 08 giúp mình hiểu rõ hơn cách xây dựng hệ thống AI Agent có kiểm soát, có khả năng phục hồi và đảm bảo an toàn trong môi trường thực tế.
