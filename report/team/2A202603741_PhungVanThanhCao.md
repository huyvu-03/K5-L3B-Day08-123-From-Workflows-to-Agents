# Báo cáo cá nhân — 2A202603741_PhungVanThanhCao

## 1. Thông tin thành viên

- Họ tên: Phùng Văn Thanh Cao
- MSSV: 2A202603741
- Email: ptc99998888@gmail.com
- GitHub: ththanh8888

## 2. Phần việc phụ trách

Vai **B — Single agent + Policy**:

- Viết shape B (`src/lab8/shapes/single.py`): một agent ReAct, tối đa 8 bước, chỉ được chọn tool đọc.
- Viết test các nhánh approval cho shape B (`src/tests/test_single_approval.py`).
- Điền phiếu nghiên cứu `report/team/research_card.md` và mục Single/Policy trong `report/team/group_report.md`.

## 3. Đóng góp cụ thể

**Commit chính:** `41f491f` (nhánh `PhungCao`): "Implement single ReAct shape and approval branch tests".

**Code `single.py`:**

- Luồng: `get_claim_view` → (thiếu `order_id` thì `needs_info`) → vòng `run_react` gồm `lookup_order` → `compute_compensation` → `lookup_refund_history` → quyết định → `durability.issue_refund`.
- Số tiền do `compute_compensation` tính. Model (MockLLM) chỉ được gọi để đếm Budget và soạn câu trả lời, không quyết số tiền.
- Ticket không đưa vào observation và không ghi trace, nên shape không bao giờ tin số ngày trễ trong ticket (đây là lỗi của swarm ở seed chia hết cho 5).
- Gọi `issue_refund` với **quote đầy đủ**, không tự trừ phần đã hoàn. Host tự trừ, nên T13 và T14 đúng.
- Truyền `crash_at` vào `issue_refund`. Với `InjectedCrash` chỉ flush trace rồi `raise` lại, nên T12 xanh.
- Quote bằng 0 thì trả `denied` và không gọi `issue_refund`. Quote lớn hơn 0 mà host từ chối thì vẫn trả `denied` với `proposal_amount` là quote đầy đủ (host ghi audit `policy_denied`).
- `run_claim` không ném exception: `ToolRejected` và vượt 8 bước đều trả `failed`.

**Test đã thêm:** `src/tests/test_single_approval.py`, 36 test (8 tình huống × 5 seed 11, 22, 33, 44, 55 cho 7 tình huống đầu; riêng tình huống gọi lại chạy một lần). Phủ các nhánh: không có approval, approval không tồn tại, hết hạn, bị thu hồi, của claim khác, số tiền ≤ 0, approval thấp hơn quote, và gọi lại sau khi bị từ chối. Mỗi nhánh bị chặn kiểm: `status == denied`, `proposal_amount` là quote đầy đủ, không có dòng ledger, có audit `policy_denied` đúng lý do, trace không chứa `CANARY_SECRET`.

**Quyết định kỹ thuật:**

- Ghi vào trace chỉ kết quả `lookup_order` (đã qua allowlist), quote và lý do từ chối. Không ghi ticket, claim row, order row thô.
- Gọi `lookup_refund_history` chỉ để quan sát. Shape không dùng nó để tự từ chối, vì khi quote lớn hơn 0 phải gọi `issue_refund` để host ghi audit `policy_denied` (T13).

## 4. Bằng chứng

- Commit: `41f491f` trên nhánh `PhungCao`. Link commit: 
- Ma trận student (`python -m pytest -q -m student -o addopts=`): 62/62 test của shape single xanh, gồm T01–T14 × 5 seed, T11 và T12.
- `python -m pytest -q tests/test_single_approval.py`: 36 passed.
- Cổng host `python -m pytest -q`: 90 passed.
- Ví dụ đo một claim (`C-001`, seed 11): single dùng 5 model call, 4 tool call, cost mô phỏng 42,58 VND. Swarm cùng claim dùng 3 model call, 5 tool call, 52,30 VND. Đây là một lần chạy lẻ để minh họa, không phải số benchmark. Số chính thức lấy từ `src/reports/benchmark.json`.

## 5. Công cụ AI đã dùng

- Công cụ: Claude Code (Anthropic).
- Dùng vào việc: Hỗ trợ và check `single.py` và `test_single_approval.py.
- Cách tự kiểm tra: Đọc lại từng dòng code, tự chạy lại `pytest` và so với kết quả mong đợi trong CHECKPOINTS.md.

## 6. Tự đánh giá

Đã hoàn thành việc triển khai Single ReAct và xây dựng 36 test case kiểm thử các nhánh Approval. Kết quả kiểm thử đạt 100% ở cả ba cấp độ: Single Approval (36/36), Student Tests (62/62) và Host Tests (90/90).
