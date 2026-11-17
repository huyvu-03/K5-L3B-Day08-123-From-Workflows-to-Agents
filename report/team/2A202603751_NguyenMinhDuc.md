# Báo cáo cá nhân — 2A202603751_NguyenMinhDuc

## 1. Thông tin thành viên

- Họ tên: Nguyễn Minh Đức
- MSSV: 2A202603751
- Email:
- GitHub: Minhduc7904

## 2. Phần việc phụ trách

Shape C `orchestrator` và biên handoff (vai P3): `src/lab8/shapes/orchestrator.py`.

- Orchestrator đọc claim qua `get_claim_view`, lập kế hoạch rồi giao việc cho investigator chỉ có tool đọc (`lookup_order`, `compute_compensation`) thông qua `lab8.handoff.make_handoff`.
- Tiền do code tính (`compute_compensation` trên dòng order trong DB). Chỉ orchestrator ghi tiền, qua `durability.issue_refund` với **quote đầy đủ**; host tự kiểm approval, trần theo đơn và idempotency.
- Trace chỉ ghi handoff đã sanitize và kết quả tool đã qua allowlist. Không ghi ticket, claim row, parent context hay secret.

## 3. Đóng góp cụ thể

Commit chính: `cbe652f` (nhánh `NguyenMinhDuc`).

Test đã thêm: `src/tests/test_orchestrator_handoff.py` (nằm trong cổng host `python -m pytest -q`):

- handoff trong trace nằm trong allowlist, không có tool ghi;
- trace của cả 14 claim public không chứa secret, SĐT, địa chỉ, tên hàng, ghi chú nội bộ hay ticket (mọi token trong `forbid_substrings`);
- ticket nói sai số ngày trễ bị bỏ qua, kể cả seed 55 (nơi swarm bị lừa);
- claim không tồn tại trả `failed`, không ném exception;
- thiếu `order_id` trả `needs_info`, không giao việc, không ghi ledger;
- gọi lại cùng claim vẫn một dòng ledger và một audit `refund_committed`;
- crash ở cả ba mốc `crash_at` không bị nuốt, trace vẫn được ghi, resume xong vẫn đúng một refund.

Quyết định kỹ thuật:

- **Handoff dùng allowlist trong code, không dùng tóm tắt bằng LLM.** Tóm tắt có thể mang theo secret hay câu chữ do người dùng viết. `make_handoff` chỉ giữ field được phép và từ chối tool ghi, nên ranh giới này không phụ thuộc vào model.
- **Bỏ `lookup_policy` khỏi investigator** sau review: `compute_compensation` đã tự đọc policy hiện hành, nên tool này chỉ tốn thêm một lượt gọi.
- **Giữ `order_id` đệm khoảng trắng là `escalated`** (không chuẩn hóa). Host so khớp order id chính xác; chỉ id rỗng hoặc toàn khoảng trắng mới là `needs_info`.
- **Bỏ qua mọi số ngày trễ viết trong ticket**, nên không dính điểm yếu của swarm ở seed chia hết cho 5.

## 4. Bằng chứng

- Commit: `cbe652f`.
- `python -m pytest -q -m student -o addopts= -k orchestrator`: 62 passed.
- `python -m pytest -q` (cổng host): 76 passed.
- Benchmark public (orchestrator, seed 11–55), đo bởi reviewer độc lập: pass 1.000, pass^5 1.000. Swarm: pass 0.986, pass^5 0.929.
- Crash suite `python -m lab8.crash_test --count 20`: `crash_safety 20/20`. Suite này gọi `issue_refund` trực tiếp nên kiểm host; phần shape được kiểm bằng T12 và test crash ở trên.
- Số bước của orchestrator (4.50) cao hơn swarm (2.80) vì metric đếm số event trong trace, không đo công việc thật; chi phí trên mỗi lần thành công thấp hơn swarm (47.71 so với 49.57, VND mô phỏng).

## 5. Công cụ AI đã dùng

- Claude Code dùng để đọc đề, đề xuất khung code orchestrator, viết test và chạy kiểm tra.
- Một subagent Claude khác được giao review độc lập (chỉ đọc, không sửa file), chấm 94/100, không có lỗi blocker hay major. Tôi đã đánh giá từng nhận xét: bỏ `lookup_policy` thừa, bổ sung test PII, crash ba mốc, claim không tồn tại, `needs_info` và replay; không chấp nhận đề xuất chuẩn hóa `order_id` vì làm lệch cách host so khớp.
- Tự kiểm tra bằng ma trận student 62/62, cổng host, crash suite, và đọc trace thật để xác nhận không chứa secret hay PII.

## 6. Tự đánh giá

- Làm tốt: ranh giới handoff và trace an toàn, tiền do code quyết, crash và retry chỉ ra một refund.
- Hạn chế: số bước đo được cao hơn swarm do cách metric đếm event; MockLLM không phản ánh hành vi và độ dao động của model thật nên kết luận chỉ có giá trị trong phạm vi bộ public.
- Chưa làm: chưa tự kiểm trên `student_drop/` (chờ giảng viên phát sau 16:15).
