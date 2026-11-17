
# Báo cáo nhóm — Lab 8 

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- **Tên nhóm:** 123
- **Thành viên:** Xem `TEAM.md`.
- **Repository:** `K5-L3B-Day08-123-From-Workflows-to-Agents`
- **Commit chốt (trùng `report/team/decision_adr.md`):** [Bổ sung commit hash cuối cùng trên nhánh nộp]

---

## 2. Mục tiêu và cách tiếp cận

### 2.1. Mục tiêu

Nhóm thực hiện Lab 8 nhằm tìm hiểu và so sánh các cách tổ chức xử lý một yêu cầu hoàn phí (refund claim), từ workflow cố định đến các mô hình sử dụng AI Agent.

Bài toán LogiX-VN yêu cầu hệ thống xử lý claim dựa trên dữ liệu đơn hàng và business rules, đồng thời đảm bảo tính chính xác của số tiền hoàn, quyền thực hiện thao tác ghi, tính nhất quán của ledger và khả năng phục hồi khi xảy ra crash.

Nhóm tập trung vào ba shape tự triển khai:

- **Workflow:** Quy trình xử lý cố định bằng Python.
- **Single:** Một agent sử dụng vòng lặp ReAct để lựa chọn các công cụ đọc.
- **Orchestrator:** Agent điều phối và giao nhiệm vụ cho investigator thông qua handoff có kiểm soát.

Swarm được sử dụng làm shape đối chiếu trong public benchmark để đánh giá sự khác biệt về độ chính xác, số bước và chi phí.

### 2.2. Cách tiếp cận và phân công

Nhóm chia công việc theo các phần triển khai và kiểm thử:

| Thành viên | Phần phụ trách |
|---|---|
| Vũ Quang Huy | Shape A — Workflow và Integration |
| Phùng Văn Thanh Cao | Shape B — Single Agent và Policy |
| Nguyễn Minh Đức | Shape C — Orchestrator và Handoff |
| Đỗ Thị Thu Hằng | Ledger, Testing và Documentation |

Các shape được triển khai theo hướng có thể so sánh trên cùng bộ public benchmark. Trong quá trình thực hiện, nhóm đồng thời kiểm tra các yêu cầu chung về approval, refund quote, idempotency, trace hygiene và crash safety.

Nhóm ưu tiên phân tách rõ trách nhiệm giữa model và code: model hỗ trợ lựa chọn công cụ hoặc tạo nội dung trả lời, còn các quyết định nghiệp vụ quan trọng như tính tiền, kiểm tra approval và ghi nhận refund được kiểm soát bởi code và host.

---

## 3. Giải pháp

### 3.1. Shape A — Workflow

**Người phụ trách:** Vũ Quang Huy.

- **Luồng:** Shape đọc claim bằng `get_claim_view`, kiểm tra claim và `order_id`, sau đó sử dụng các read tool để lấy thông tin đơn hàng. Nếu thiếu `order_id`, hệ thống trả `needs_info`; nếu không tìm thấy đơn hàng hoặc không đủ điều kiện xử lý thì trả về trạng thái phù hợp. Khi có dữ liệu hợp lệ, `compute_compensation` tính quote và workflow chuyển quote đầy đủ tới `durability.issue_refund`.
- **Ranh giới code / model:** Workflow sử dụng các bước Python cố định, không để model tự quyết định số tiền hoàn. Quote được tính từ dữ liệu order và business rules, không dựa trên số ngày trễ hoặc số tiền do người dùng ghi trong ticket.
- **Host và refund:** Workflow gọi `issue_refund` để host kiểm tra approval, giới hạn hoàn tiền theo order và idempotency. Shape không tự xử lý phần tiền đã hoàn.
- **Crash:** Truyền tiếp `crash_at` cho host. `InjectedCrash` không bị nuốt; trace được ghi trước khi ném lại lỗi.
- **Trace:** Chỉ ghi các thông tin cần thiết cho việc theo dõi kết quả xử lý, không ghi ticket hoặc dữ liệu nhạy cảm của order.
- **Test:** Có kiểm thử các nhánh xử lý claim, order và trường hợp `order_id` chỉ chứa khoảng trắng. Trường hợp này phải trả `needs_info` và không thực hiện refund.

**Mã nguồn:** `src/lab8/shapes/workflow.py`.

### 3.2 Shape B — single (ReAct)

*Phần của thành viên B. Các mục 3.1 (workflow) và 3.3 (orchestrator) do A và C viết.*

- **Luồng:** đọc claim bằng `get_claim_view`; `order_id` rỗng hoặc toàn khoảng trắng thì trả `needs_info`. Sau đó vòng ReAct (tối đa 8 bước) chạy tuần tự `lookup_order` → `compute_compensation` → `lookup_refund_history`, rồi trả quote. Một claim thường dùng 3 tool trong vòng lặp và 4 lần `decide`, thấp hơn trần 8.
- **Ranh giới code / model:** `decide()` là kịch bản cố định trong code, không phải model tự chọn tool. MockLLM được gọi mỗi bước chỉ để tính chi phí mô phỏng và soạn câu trả lời; kết quả của nó không ảnh hưởng tới tool hay số tiền. Shape B vì vậy gần với workflow chạy trong khung ReAct. Số tiền do `compute_compensation` tính. Sau vòng lặp, code của shape gọi `durability.issue_refund`. Shape không tự trừ phần đã hoàn: nó truyền **quote đầy đủ** và để host trừ, nên T13 (đã hoàn đủ) và T14 (hoàn phần chênh) đúng.
- **Ticket là dữ liệu:** ticket không được đưa vào observation của vòng ReAct và không ghi vào trace, nên shape không tin số ngày trễ ghi trong ticket (điểm yếu của swarm ở seed 55, claim T02).
- **Crash:** `crash_at` được truyền vào `issue_refund`, `InjectedCrash` chỉ được flush trace rồi ném lại.
- **Trace:** ghi kết quả `lookup_order` (đã qua allowlist), quote, kết quả `lookup_refund_history`, quyết định và lý do host từ chối. **Cố ý không ghi** ticket, claim row, order row thô, `parent_secret`, header.
- **Test approval:** 12 test trong `src/tests/test_single_approval.py`, phủ các nhánh: không có approval, approval không tồn tại, hết hạn, bị thu hồi, của claim khác, số tiền ≤ 0, approval thấp hơn quote, gọi lại sau khi bị từ chối, `order_id` rỗng hoặc toàn khoảng trắng; thêm một test kiểm kết quả không đổi trên 5 seed.
- **Số đo tham khảo (một lần chạy lẻ, C-001 seed 11):** single 5 model call, 4 tool call, 42,58 VND; swarm 3 model call, 5 tool call, 52,30 VND. Số chính thức xem mục 4.

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

---

## 4. Kết quả

### 4.1. Public benchmark — So sánh 4 shapes

Số liệu được lấy từ `src/reports/benchmark.json`.

Benchmark chạy trên 14 claim IDs (`C-001` đến `C-014`), với 5 seeds (`11`, `22`, `33`, `44`, `55`), tổng cộng 70 trials cho mỗi shape.

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean steps | P95 steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| Workflow | 100.00% | 100.00% | 100.00%–100.00% | 0.000000 | 27.86 | 2.86 | 3 |
| Single | 100.00% | 100.00% | 100.00%–100.00% | 0.000000 | 36.58 | 3.57 | 5 |
| Orchestrator | 100.00% | 100.00% | 100.00%–100.00% | 0.000000 | 38.43 | 4.50 | 5 |
| Swarm | 98.57% | 92.86% | 92.86%–100.00% | 0.000816 | 49.57 | 2.80 | 3 |

**Nhận xét:**

- Workflow đạt pass rate 100%, có chi phí mô phỏng thấp nhất (27.86 VND/success).
- Single và Orchestrator đều đạt pass rate 100% trên bộ public benchmark.
- Orchestrator có mean steps cao nhất (4.50), trong khi Single là 3.57.
- Swarm có mean steps thấp nhất (2.80), nhưng pass rate chỉ đạt 98.57%, với một trial thất bại do `status resolved != denied`.
- Swarm có chi phí mô phỏng cao nhất (49.57 VND/success).
- Kết quả cho thấy không nên đánh giá hiệu quả chỉ dựa trên số steps. Cần xem đồng thời pass rate, độ ổn định giữa các seeds và chi phí.

**Điều kiện benchmark:**

- Model backend: `MockLLM`.
- Trials: 70 cho mỗi shape.
- Seeds: 11, 22, 33, 44, 55.
- Isolation: fresh SQLite per trial.
- Pricing: chi phí mô phỏng theo cấu hình trong benchmark, không phải giá API thực tế.
- Latency: unavailable.

### 4.2. Crash safety

Số liệu được lấy từ `src/reports/crash.json`.

- Tổng số scenarios: 20.
- Passed: 20/20.
- Crash safety: 100%.

| Crash scenario | Số lượng | Kết quả |
|---|---:|---|
| `before_effect` | 5 | 5/5 passed |
| `after_effect_before_checkpoint` | 7 | 7/7 passed |
| `after_checkpoint` | 5 | 5/5 passed |
| `amount_conflict_on_retry` | 1 | 1/1 passed |
| `retry_without_approval` | 1 | 1/1 passed |
| `swarm_after_effect_before_checkpoint` | 1 | 1/1 passed |
| **Total** | **20** | **20/20 passed** |

**Nhận xét:**

- Các tình huống crash trước effect, sau effect nhưng trước checkpoint và sau checkpoint đều vượt qua kiểm thử.
- Các tình huống retry với amount conflict và retry không có approval cũng được kiểm tra.
- Có thêm scenario kiểm tra Swarm crash sau effect nhưng trước checkpoint.
- Toàn bộ 20 scenarios trong crash test suite đều đạt yêu cầu.

**Lưu ý về phạm vi:** Kết quả 20/20 xác nhận các scenarios trong crash test suite đã chạy thành công; không đồng nghĩa với việc mọi tình huống crash ngoài thực tế đều được bảo đảm. Các kiểm thử crash/resume ở cấp shape được đánh giá riêng trong test tương ứng.

### 4.3. Điều kiện và giới hạn đánh giá

- Benchmark sử dụng `MockLLM`, không phản ánh đầy đủ hành vi và độ dao động của model thật.
- Chi phí được mô phỏng theo pricing cấu hình trong benchmark, không phải chi phí API thực tế.
- Latency không khả dụng nên chưa thể so sánh thời gian phản hồi giữa các shapes.
- `steps` được tính theo event trace; vì vậy không nên xem đây là thước đo trực tiếp về độ phức tạp của các kiến trúc khác nhau.
- Các kết quả chỉ có giá trị trong phạm vi public benchmark và crash scenarios đã chạy.

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`.

Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

---

## 5. Khó khăn và cách xử lý

Trong quá trình triển khai và kiểm thử, nhóm tập trung xử lý một số vấn đề kỹ thuật có ảnh hưởng trực tiếp đến tính chính xác và an toàn của hệ thống.

| Vấn đề | Cách xử lý |
|---|---|
| Không được sử dụng nội dung ticket làm căn cứ quyết định số tiền hoàn | Tính quote từ dữ liệu order và business rules thông qua `compute_compensation`; không đưa ticket vào observation hoặc trace ở các shape liên quan |
| Kiểm soát quyền thực hiện refund | Giới hạn investigator ở các read tool; thao tác ghi tiền được thực hiện qua `durability.issue_refund` |
| Approval và số tiền đã hoàn | Truyền quote đầy đủ cho host để kiểm tra approval, giới hạn hoàn tiền và xử lý T13/T14 |
| Retry có thể gây ghi nhận refund trùng lặp | Sử dụng cơ chế idempotency ở host và kiểm tra replay |
| Crash xảy ra giữa effect và checkpoint | Truyền `crash_at`, không nuốt `InjectedCrash`, kiểm tra trace và khả năng resume |
| Dữ liệu nhạy cảm có thể lọt vào trace hoặc handoff | Sử dụng allowlist, sanitize dữ liệu và bổ sung test kiểm tra secret, PII và ticket |
| `order_id` bị thiếu hoặc chỉ chứa khoảng trắng | Kiểm tra đầu vào trước khi giao việc hoặc thực hiện refund; trả `needs_info` khi không hợp lệ |

Những vấn đề trên được xử lý thông qua việc kết hợp kiểm tra bằng code, kiểm soát tool, kiểm thử các nhánh nghiệp vụ và đối chiếu kết quả với business rules.

---

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

| Thành viên | Phần phụ trách | Đóng góp chính | Bằng chứng |
|---|---|---|---|
| Vũ Quang Huy | Workflow + Integration | Triển khai Workflow, xử lý claim/order, quote, host refund và trường hợp `order_id` không hợp lệ | `src/lab8/shapes/workflow.py`; commit triển khai và test theo Git |
| Phùng Văn Thanh Cao | Single Agent + Policy | Triển khai Single ReAct, kiểm soát tool đọc và kiểm thử approval | Commit `41f491f`; `src/tests/test_single_approval.py` |
| Nguyễn Minh Đức | Orchestrator + Handoff | Triển khai Orchestrator, read-only investigator, handoff sanitize và crash/replay tests | Commit `cbe652f`; `src/tests/test_orchestrator_handoff.py` |
| Đỗ Thị Thu Hằng | Ledger, Testing + Documentation | Cập nhật ADR, tham gia kiểm thử trace hygiene, T13/T14, conflict, replay và blank order ID | Commit `d8c21a0`, `20265e7`; `decision_adr.md` và các file test liên quan |

**Lưu ý:** Commit triển khai Workflow của Huy cần đối chiếu trực tiếp với lịch sử Git để bổ sung hash chính xác nếu cần. Không sử dụng commit của thành viên khác để thay thế.

---

## 7. Hạn chế và hướng cải thiện

### 7.1. Hạn chế

- **MockLLM:** Kết quả benchmark chưa phản ánh đầy đủ hành vi của model sản xuất, đặc biệt là độ trễ, chất lượng quyết định và chi phí token thực tế.
- **Latency:** Benchmark ghi nhận `unavailable`, nên chưa thể đưa ra kết luận về tốc độ phản hồi.
- **Chi phí mô phỏng:** Mức cost hiện tại phụ thuộc vào pricing giả lập, không thể dùng trực tiếp để dự đoán chi phí triển khai thực tế.
- **Orchestrator handoff:** `facts` hiện để rỗng, investigator đọc lại dữ liệu theo `claim_id`; kết quả gọi MockLLM không được sử dụng. Vì vậy, cơ chế này mới thể hiện ranh giới điều phối và kiểm soát dữ liệu, chưa chứng minh được lợi ích của multi-agent thực sự.
- **Số bước:** `steps` là số event trace nên không thể dùng riêng lẻ để so sánh độ phức tạp giữa các shape.
- **Phạm vi kiểm thử:** Kết quả chỉ xác nhận những test case và crash scenarios đã chạy, chưa đại diện cho toàn bộ tình huống có thể phát sinh trong môi trường production.

### 7.2. Hướng cải thiện

1. Thử nghiệm với model thực tế để đánh giá thêm latency, chất lượng kết quả và chi phí API.
2. Bổ sung các tình huống benchmark đa dạng hơn, đặc biệt là các trường hợp dữ liệu đầu vào không đầy đủ hoặc có thông tin gây nhiễu.
3. Tiếp tục kiểm tra khả năng phục hồi của từng shape qua nhiều điểm crash và retry.
4. Nếu mở rộng Orchestrator thành multi-agent thực sự, cần thiết kế nhiệm vụ investigator có giá trị độc lập, đồng thời duy trì allowlist và kiểm soát dữ liệu handoff.
5. Bổ sung kiểm thử trên `student_drop/` khi có bộ dữ liệu và môi trường kiểm thử tương ứng.

---

## 8. Tài liệu tham khảo

- `README.md`
- `RULES.md`
- `business_rules.md`
- `contracts.md`
- `CHECKPOINTS.md`
- `docs/architecture.md`
- `report/team/decision_adr.md`
- `report/team/research_card.md`
- `src/reports/benchmark.json`
- `src/reports/crash.json`
- `TEAM.md`
