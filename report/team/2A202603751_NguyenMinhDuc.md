# Báo cáo cá nhân — 2A202603751_NguyenMinhDuc

## 1. Thông tin thành viên

- Họ tên: Nguyễn Minh Đức
- MSSV: 2A202603751
- Email: nmduc7904@gmail.com
- GitHub: Minhduc7904

## 2. Phần việc phụ trách

Shape C `orchestrator` và biên handoff (vai P3): `src/lab8/shapes/orchestrator.py`.

- Orchestrator đọc claim qua `get_claim_view`, lập kế hoạch rồi giao việc cho investigator chỉ có tool đọc (`lookup_order`, `compute_compensation`) thông qua `lab8.handoff.make_handoff`.
- Tiền do code tính (`compute_compensation` trên dòng order trong DB). Chỉ orchestrator ghi tiền, qua `durability.issue_refund` với **quote đầy đủ**; host tự kiểm approval, trần theo đơn và idempotency.
- Trace chỉ ghi handoff đã sanitize và kết quả tool đã qua allowlist. Không ghi ticket, claim row, parent context hay secret.

## 3. Đóng góp cụ thể

Commit chính: `cbe652f` (nhánh `NguyenMinhDuc`, đã merge qua PR #1). Commit sửa sau review độc lập: `01e8c48` (nhánh `NguyenMinhDuc-review-fixes`).

Test đã thêm: `src/tests/test_orchestrator_handoff.py` (nằm trong cổng host `python -m pytest -q`):

- handoff trong trace nằm trong allowlist, không có tool ghi;
- trace của cả 14 claim public không chứa secret, SĐT, địa chỉ, tên hàng, ghi chú nội bộ hay ticket (mọi token trong `forbid_substrings`);
- ticket nói sai số ngày trễ bị bỏ qua, kể cả seed 55 (nơi swarm bị lừa);
- claim không tồn tại trả `failed`, không ném exception;
- thiếu `order_id` trả `needs_info`, không giao việc, không ghi ledger;
- gọi lại cùng claim vẫn một dòng ledger và một audit `refund_committed`;
- crash ở cả ba mốc `crash_at` không bị nuốt, trace vẫn được ghi, resume xong vẫn đúng một refund;
- (sau review) nội dung ticket không xuất hiện trong trace dưới bất kỳ key nào, `handoff["facts"]` luôn rỗng;
- (sau review) `order_id` toàn khoảng trắng là `needs_info`, id bị đệm khoảng trắng hoặc giống chữ (Cyrillic O, chữ thường) là `escalated`, đều không ghi ledger;
- (sau review) lỗi bất ngờ trong shape trả `failed` chứ không ném exception, trace vẫn đúng contract;
- (sau review) mã đơn không tìm thấy không bị ghi vào trace.

Quyết định kỹ thuật:

- **Handoff dùng allowlist trong code, không dùng tóm tắt bằng LLM.** Tóm tắt có thể mang theo secret hay câu chữ do người dùng viết. `make_handoff` chỉ giữ field được phép và từ chối tool ghi, nên ranh giới này không phụ thuộc vào model.
- **Bỏ `lookup_policy` khỏi investigator** sau review: `compute_compensation` đã tự đọc policy hiện hành, nên tool này chỉ tốn thêm một lượt gọi.
- **Giữ `order_id` đệm khoảng trắng là `escalated`** (không chuẩn hóa). Host so khớp order id chính xác; chỉ id rỗng hoặc toàn khoảng trắng mới là `needs_info`.
- **Bỏ qua mọi số ngày trễ viết trong ticket**, nên không dính điểm yếu của swarm ở seed chia hết cho 5.
- **`run_claim` không ném exception lạ** (sau review lần 2): `InjectedCrash` vẫn được ném lại, mọi lỗi khác thành `failed` kèm trace sạch, giống workflow. Contract trong `docs/contracts.md` cấm `run_claim` ném exception.
- **Khi không tìm thấy đơn, trace chỉ ghi `visible` và `reason`**, không ghi mã đơn vì đó là chữ do người dùng nhập.

## 4. Bằng chứng

- Commit: `cbe652f` (shape + test), `01e8c48` (sửa sau review).
- `python -m pytest -q -m student -o addopts=` (cả 4 shape): 248 passed. Riêng orchestrator (`-k orchestrator`): 62 passed.
- `python -m pytest -q` (cổng host, nhánh `NguyenMinhDuc-review-fixes`): 190 passed, 1 xfailed. Xfail là test `test_blank_order_id_gets_same_status_on_all_team_shapes` của thành viên khác, do `single` chưa cắt khoảng trắng của `order_id`.
- `src/reports/benchmark.json` (14 claim × 5 seed, 4 shape), cột orchestrator: pass 1.000, pass^5 1.000, variance 0, cost/success 38.43 VND mô phỏng, mean steps 4.50, p95 steps 5, 1.93 model call và 3.71 tool call mỗi trial. So với workflow 27.86, single 36.58, swarm 49.57 (pass 0.986, pass^5 0.929).
- Crash suite `python -m lab8.crash_test --count 20`: `crash_safety 20/20`. Suite này chủ yếu gọi `issue_refund` trực tiếp nên kiểm host, không kiểm shape; phần shape được kiểm bằng T12 và test crash ba mốc trong `test_orchestrator_handoff.py`.
- Lưu ý khi trích số: `steps` là số event trong trace, không đo công việc thật (orchestrator 4.50 nhưng swarm 2.80 dù swarm gọi nhiều model và tool hơn). Chi phí gần như hoàn toàn là 10 VND mỗi tool call, token chỉ chiếm vài phần trăm. Phần chênh với workflow chủ yếu đến từ việc `run_readonly_investigators` đọc lại claim một lần nữa.

## 5. Công cụ AI đã dùng

- Claude Code: đọc đề, đề xuất khung code orchestrator, viết test, chạy kiểm tra và soạn bản nháp báo cáo.
- Review độc lập lần 1 (subagent Claude, chỉ đọc): 94/100, không có blocker hay major. Đã xử lý: bỏ `lookup_policy` thừa, thêm test PII, claim không tồn tại, `needs_info`, replay, crash ba mốc. Không chấp nhận đề xuất chuẩn hóa `order_id` vì lệch cách host so khớp.
- Review độc lập lần 2 trên `main` đã tích hợp (subagent mới, có thử đột biến mã): khoảng 90/100. Đã xử lý: `run_claim` không ném exception lạ, không ghi mã đơn chưa tìm thấy vào trace, thêm test cho các đột biến sống sót (ticket ở key khác, ticket trong `facts`, bỏ `.strip()`), sửa số liệu trong báo cáo này cho khớp `benchmark.json`, viết mục 3.3 của `group_report.md`.
- Tự kiểm tra: chạy lại ma trận student, cổng host, crash suite; tự chạy 3 đột biến (bỏ `.strip()`, ticket vào `facts`, ticket vào trace dưới key khác) và xác nhận test mới đều bắt được; đọc trace thật để xác nhận không có secret hay PII.

## 6. Tự đánh giá

- Làm tốt: ranh giới handoff và trace an toàn, tiền do code quyết, crash và retry chỉ ra một refund.
- Hạn chế:
  - Handoff trong shape này khá hình thức: `facts` rỗng, `principal_id` đi kèm ngoài handoff, investigator tự đọc lại claim theo `claim_id`, và kết quả của các lần gọi MockLLM (`plan`, `draft`) không được dùng. Nó thoả allowlist và tool chỉ đọc, nhưng thực chất là workflow có thêm một gói handoff, không nên trình bày như multi-agent thật.
  - `variance 0` và `pass^5 = 1.0` là do quyết định của shape không phụ thuộc seed, không phải bằng chứng về độ bền.
  - Số bước đo được cao hơn swarm do cách metric đếm event; MockLLM không phản ánh hành vi và độ dao động của model thật, nên kết luận chỉ có giá trị trên bộ public.
  - ADR của nhóm chọn workflow, nên orchestrator chủ yếu được chấm ở C1 và C5, không phải ở bộ hidden.
- Chưa làm: chưa tự kiểm trên `student_drop/` (chờ giảng viên phát sau 16:15).
