# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm:
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.

...

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

### 3.2 Shape B — single (ReAct)

*Phần của thành viên B. Các mục 3.1 (workflow) và 3.3 (orchestrator) do A và C viết.*

- **Luồng:** đọc claim bằng `get_claim_view`; `order_id` rỗng hoặc toàn khoảng trắng thì trả `needs_info`. Sau đó vòng ReAct (tối đa 8 bước) chạy tuần tự `lookup_order` → `compute_compensation` → `lookup_refund_history`, rồi trả quote. Một claim thường dùng 3 tool trong vòng lặp và 4 lần `decide`, thấp hơn trần 8.
- **Ranh giới code / model:** `decide()` là kịch bản cố định trong code, không phải model tự chọn tool. MockLLM được gọi mỗi bước chỉ để tính chi phí mô phỏng và soạn câu trả lời; kết quả của nó không ảnh hưởng tới tool hay số tiền. Shape B vì vậy gần với workflow chạy trong khung ReAct. Số tiền do `compute_compensation` tính. Sau vòng lặp, code của shape gọi `durability.issue_refund`. Shape không tự trừ phần đã hoàn: nó truyền **quote đầy đủ** và để host trừ, nên T13 (đã hoàn đủ) và T14 (hoàn phần chênh) đúng.
- **Ticket là dữ liệu:** ticket không được đưa vào observation của vòng ReAct và không ghi vào trace, nên shape không tin số ngày trễ ghi trong ticket (điểm yếu của swarm ở seed 55, claim T02).
- **Crash:** `crash_at` được truyền vào `issue_refund`, `InjectedCrash` chỉ được flush trace rồi ném lại.
- **Trace:** ghi kết quả `lookup_order` (đã qua allowlist), quote, kết quả `lookup_refund_history`, quyết định và lý do host từ chối. **Cố ý không ghi** ticket, claim row, order row thô, `parent_secret`, header.
- **Test approval:** 12 test trong `src/tests/test_single_approval.py`, phủ các nhánh: không có approval, approval không tồn tại, hết hạn, bị thu hồi, của claim khác, số tiền ≤ 0, approval thấp hơn quote, gọi lại sau khi bị từ chối, `order_id` rỗng hoặc toàn khoảng trắng; thêm một test kiểm kết quả không đổi trên 5 seed.
- **Số đo tham khảo (một lần chạy lẻ, C-001 seed 11):** single 5 model call, 4 tool call, 42,58 VND; swarm 3 model call, 5 tool call, 52,30 VND. Số chính thức xem mục 4.

...

### 3.3 Shape C — orchestrator + handoff

*Phần của thành viên P3 (Nguyễn Minh Đức).*

- **Luồng:** đọc claim bằng `get_claim_view` (thiếu `order_id` hoặc toàn khoảng trắng thì `needs_info`, không giao việc). Orchestrator lập kế hoạch rồi giao cho investigator qua `make_handoff`; investigator chỉ có `lookup_order` và `compute_compensation`. Đơn không thấy được thì `escalated`. Quote bằng 0 thì `denied` và không gọi host. Quote lớn hơn 0 thì orchestrator gọi `durability.issue_refund` với **quote đầy đủ** và `crash_at`.
- **Ranh giới code / model:** số tiền do `compute_compensation` tính trên dòng order trong database, không do MockLLM và không do ticket. MockLLM chỉ tạo chữ trả lời và tính chi phí mô phỏng. Chỉ orchestrator gọi nơi ghi tiền; investigator không có tool ghi.
- **Handoff:** gói theo `handoff.v1`, chỉ chứa field trong allowlist (`request_id`, `claim_id`, `task`, `allowed_tools`, `facts`...). `facts` luôn rỗng, nên không có giá trị nào từ claim hay ticket đi qua ranh giới. `make_handoff` từ chối tool ghi và từ chối payload còn chứa `CANARY_SECRET_`, `parent_secret` hoặc `raw_headers`. Chúng tôi dùng allowlist trong code thay vì tóm tắt bằng LLM, vì tóm tắt có thể mang theo secret hay câu chữ do người dùng viết.
- **Trace ghi:** `claim` (chỉ ghi có `order_id` hay không), `handoff` đã sanitize, `investigator` (kết quả `lookup_order` qua allowlist; nếu không thấy đơn chỉ ghi lý do), `quote`, `host` (ok, reason, conflict), `decision` hoặc `error` ở các nhánh sớm, `crash` trước khi ném lại `InjectedCrash`. **Cố ý không ghi** ticket, claim row, order row thô, parent context, secret.
- **Crash và retry:** `InjectedCrash` không bị bắt; trace được ghi trước khi ném lại. Resume hay gọi lại cùng claim vẫn ra một dòng ledger và một audit `refund_committed`. Mọi lỗi bất ngờ khác trả `failed` kèm trace, không ném exception.
- **Test:** `src/tests/test_orchestrator_handoff.py` (trong cổng host): handoff đúng allowlist và không có tool ghi, trace của 14 claim không có secret, PII hay ticket, bỏ qua số ngày trễ trong ticket (kể cả seed 55), claim không tồn tại, `needs_info`, replay, crash ba mốc rồi resume, phân biệt `order_id` rỗng và `order_id` bị đệm hay giống chữ, lỗi bất ngờ thành `failed`.
- **Số đo (từ `benchmark.json`):** pass 1.000, pass^5 1.000, cost/success 38.43 VND mô phỏng, 1.93 model call và 3.71 tool call mỗi trial. Chi phí cao hơn workflow (27.86) phần lớn do một lần đọc claim thừa trong `run_readonly_investigators` và 10 VND mỗi tool call; token chỉ chiếm vài phần trăm. `steps` là số event trace nên không so sánh được độ phức tạp giữa các shape.
- **Giới hạn:** handoff khá hình thức (`facts` rỗng, investigator đọc lại claim theo `claim_id`, kết quả các lần gọi MockLLM không được dùng), nên đây là workflow có thêm ranh giới handoff, không phải multi-agent thật. Chi phí token trong benchmark nhỏ nên không cho thấy chi phí truyền ngữ cảnh của multi-agent thật.

## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

...

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

...

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

...

## 8. Tài liệu tham khảo

...
