# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: `78f888f`
- Run id dẫn chứng: R-workflow-C-001-s11, R-workflow-C-002-s55 (src/reports/benchmark.json). Lệnh: python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000-1.000 / 0.000000
- Cost per success (mô phỏng, VND): 27.86
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 trên 14 claim public × 5 seed (benchmark 70/70 reason ok; src/tests/test_ledger_extra.py quét trace sạch; crash CR-19 retry_without_approval pass). student_drop: chưa tự kiểm

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Cùng 14 claim public, 5 seed (11, 22, 33, 44, 55), cùng bảng giá mô phỏng (20/80 VND mỗi 1k token vào/ra, 10 VND mỗi tool call), cùng MockLLM, mỗi trial một SQLite mới. Số lấy nguyên từ `src/reports/benchmark.json`:

| Shape | Pass rate | pass^5 | Variance | Cost/success (VND) | Model calls TB | Tool calls TB | p95 steps |
| --- | --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 0.000000 | 27.86 | 0.00 | 2.79 | 3 |
| single | 1.000 | 1.000 | 0.000000 | 36.58 | 4.36 | 3.43 | 5 |
| orchestrator | 1.000 | 1.000 | 0.000000 | 38.43 | 1.93 | 3.71 | 5 |
| swarm | 0.986 | 0.929 | 0.000816 | 49.57 | 3.00 | 4.66 | 3 |

Ba shape nhóm viết (workflow, single, orchestrator) đều đạt pass rate 1.000, pass^5 1.000 và variance 0, nên độ chính xác không phân biệt được giữa chúng. Khi độ chính xác ngang nhau, nhóm chọn shape ít tự chủ nhất mà vẫn làm được việc. Workflow có cost/success thấp nhất (27.86 VND) và không gọi model lần nào (mean_model_calls = 0). Số tiền do `compute_compensation` tính từ order row trong DB, việc ghi tiền đi qua `issue_refund` của host, nên model không có chỗ để chọn số tiền hay tự commit.

Swarm là shape duy nhất không đạt 1.000. Nó fail đúng một trial, `R-swarm-C-002-s55`: trả `resolved` trong khi đáp án là `denied`. Ở seed 55 (seed % 5 == 0), swarm tin số ngày trễ ghi trong ticket thay vì `delay_days` trong order row, tính lại quote nên ra số tiền dương. Trial này cũng tốn hơn (62.22 VND, 6 tool call so với 52.20 và 5 ở các seed khác). Cùng claim và seed đó, `R-workflow-C-002-s55` vẫn ra `denied` vì workflow không đọc ticket.

## Có đáng đổi lấy multi-agent không

Không, trên bộ public này. Orchestrator và swarm không cho pass rate cao hơn workflow, nhưng đắt hơn khoảng 38% và 78% mỗi lần thành công (38.43 và 49.57 so với 27.86). Single cũng đắt hơn khoảng 31% (36.58) vì vòng ReAct gọi model ở mỗi bước. Swarm còn có variance khác 0, tức kết quả phụ thuộc seed.

Quyết định sẽ đảo lại nếu:

1. Bộ hidden có ticket mơ hồ mà luật cố định không bao phủ, khiến workflow tụt dưới ngưỡng 0.75 trên student_drop.
2. Hệ thống chuyển sang model thật và cần đọc hiểu văn bản tự do (ví dụ phân loại lý do khiếu nại) chứ không chỉ tra cứu dòng order.
3. Claim cần nhiều bước điều tra độc lập có thể chạy song song để rút ngắn thời gian.

Với claim tuần tự và luật rõ như bài này, thêm agent chỉ thêm chi phí và rủi ro dao động.

## Trace và bằng chứng

Workflow ghi các event sau (theo `src/lab8/shapes/workflow.py` bản hiện tại):

| Event | Khi nào ghi | Payload |
| --- | --- | --- |
| `claim` | Luôn ghi, ngay sau `get_claim_view` | `found`, `claim_id`, `principal_id`, `order_id` |
| `decision` | Chỉ khi thiếu order_id | `status: needs_info` |
| `lookup_order` | Sau `lookup_order` | `visible`, `reason` (không ghi order row) |
| `quote` | Sau `compute_compensation` | Kết quả `compute_compensation` tính từ order row |
| `crash` | Khi có `InjectedCrash` | `at`; trace được ghi ra file rồi raise lại |
| `error` | Exception khác | `reason` = tên lớp exception, không ghi message |

Số event khớp với cột `steps` trong benchmark: claim được trả tiền hoặc bị từ chối có 3 event (claim, lookup_order, quote), C-004 (needs_info) có 2 (claim, decision), C-005 (escalated) có 2 (claim, lookup_order). Mọi nhánh return đều đi qua `finish()`, nên trace luôn được ghi ra `trace_path` kể cả khi dừng sớm.

Trace chỉ ghi các field đã qua allowlist của host (kết quả `get_claim_view`, `lookup_order`, `compute_compensation`). `principal_id` và `order_id` là định danh cần để đối chiếu trace với ledger, không phải dữ liệu cá nhân. Field cố ý không ghi: `parent_secret`, header, số điện thoại, địa chỉ, ghi chú nội bộ, tên hàng, nội dung ticket, và nguyên claim row hay order row.

Bằng chứng: `src/tests/test_ledger_extra.py` quét trace và mọi file `<run_id>*` cùng thư mục trên 4 shape × 14 claim public, tìm `CANARY_SECRET_`, `parent_secret` và mọi chuỗi trong `forbid_substrings`, rồi gọi `check_trace`. Cả 56 ca đều pass (toàn file có 70 test). File test còn kiểm conflict số tiền, T13 (denied, không ghi ledger, audit `order_already_refunded`), T14 (proposal 150000, ledger 120000) và replay một dòng ledger trên cả 4 shape. Nhóm không ghi file nào ngoài `trace_path` và không in dữ liệu claim ra stdout.

## Giới hạn

- MockLLM không phải model sản xuất. Nó cố định theo seed nên variance 0 ở đây không đảm bảo variance 0 với model thật. Workflow không gọi model nên không bị ảnh hưởng, nhưng so sánh với single và orchestrator thì có.
- Single và orchestrator dùng `decide()` và luồng handoff cố định; MockLLM không quyết định tool hay số tiền. Vì vậy pass rate 1.000 và variance 0 là do thiết kế, không chứng minh độ bền với model thật, và so sánh chi phí giữa các shape chỉ có giá trị trong thiết lập mô phỏng này.
- Latency để `unavailable`. Cost là giá mô phỏng (`simulated_not_real_api_price`), không phải giá API thật.
- Kết luận chỉ có giá trị trong phạm vi 14 claim public và bộ student_drop nhóm đã tự kiểm.
- Order_id rỗng hoặc toàn khoảng trắng: workflow, single và orchestrator đều trả `needs_info` và không ghi ledger (sửa ở `f242fa4`, `01e8c48`, `87bf9ca`). Test `test_blank_order_id_gets_same_status_on_all_team_shapes` đã bỏ `xfail` và pass. Không claim public nào có order_id như vậy nên số benchmark ở trên không đổi.
- Kết quả của host (`ok`, `reason`, `conflict`) không được ghi thành event riêng trong trace workflow. Status cuối và `error_reason` nằm trong `RunResult`.
- Mọi số trong file này lấy từ `src/reports/benchmark.json` và `src/reports/crash.json`, không sửa tay JSON cho đủ ngưỡng 0.75.
