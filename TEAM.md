# Team

## Thông tin nhóm

- **Tên nhóm:** 123
- **Lớp:** L3B
- **Repo nhóm:** K5-L3B-Day08-123-From-Workflows-to-Agents
- **URL repo:** https://github.com/huyvu-03/K5-L3B-Day08-123-From-Workflows-to-Agents
- **Nhánh nộp:** main
- **Commit chốt:** `78f888f`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
|---:|---|---|---|---|---|
| 1 | Đỗ Thị Thu Hằng | 2A202603840 | dothuhang2604@gmail.com | ThuHang2604 | Ledger, Testing + Documentation |
| 2 | Phùng Văn Thanh Cao | 2A202603741 | ptc99998888@gmail.com | ththanh8888 | B: Single Agent + Policy |
| 3 | Vũ Quang Huy | 2A202603782 | 26ai.huyvq6@vinuni.edu.vn | huyvu-03 | Workflow + Integration |
| 4 | Nguyễn Minh Đức | 2A202603751 | nmduc7904@gmail.com | Minhduc7904 | Orchestrator + Handoff (P3) |

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Đỗ Thị Thu Hằng (2A202603840) | Ledger, Testing + Documentation | `20265e7` (test(ledger): trace hygiene, T13/T14, conflict, replay, blank order_id); `601e461` (update decision_adr.md); `d43b825` (cập nhật commit hash trong ADR); `1b2f382` (group report) | `src/tests/test_ledger_extra.py` (70 test: trace hygiene 4 shape × 14 claim, T13/T14, conflict, replay, blank order_id) |
| Vũ Quang Huy (2A202603782) | Workflow + integration | `1723d3e` (workflow), `f242fa4` (blank order ID fix), `f2727a2` (test + bảng đóng góp), `76ec1cf` (research card ablation), `e400c59` (thông tin thành viên) | `src/tests/test_workflow_whitespace_order_id.py` — kiểm tra ID chỉ có khoảng trắng trả về `needs_info` và không ghi refund |
| Phùng Văn Thanh Cao | B: single agent + policy | `41f491f` (single.py: ReAct, quote đầy đủ, crash_at; test approval), `87bf9ca` (sửa blank order_id, gộp test approval trùng) | `src/tests/test_single_approval.py` (12 test approval + order_id khoảng trắng); bỏ xfail trong `test_ledger_extra.py` |
| Nguyễn Minh Đức (2A202603751) | Orchestrator + Handoff | `cbe652f` feat(orchestrator): shape C, read-only investigators, sanitized handoff; `01e8c48` (không ném exception lạ, không ghi mã đơn vào trace); `c7364d3` (sửa số liệu báo cáo, mục 3.3) | `src/tests/test_orchestrator_handoff.py` (mới); ma trận student `-k orchestrator` 62/62 |


### Bằng chứng

- Benchmark: `src/reports/benchmark.json`, 4 shape × 14 claim × 5 seed. Workflow, single, orchestrator đều pass 1.000, pass^5 1.000; swarm pass 0.986, pass^5 0.929.
- Crash safety: `src/reports/crash.json`, 20/20.
- Test cổng host `python -m pytest -q` (từ `src/`): 167 passed, 248 deselected.
- Ma trận student `python -m pytest -q -m student -o addopts=` (từ `src/`): 248 passed, 167 deselected.
- `python -m lab8.check_submission` (từ `src/`): 0 FAIL, 0 WARN (shape 3/3 OK, benchmark 4×14×5 OK, crash 20/20 OK, docs OK).
