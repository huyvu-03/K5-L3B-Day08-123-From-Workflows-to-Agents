# Team

## Thông tin nhóm

- **Tên nhóm:** 123
- **Lớp:** L3B
- **Repo nhóm:** K5-L3B-Day08-123-From-Workflows-to-Agents
- **URL repo:** https://github.com/huyvu-03/K5-L3B-Day08-123-From-Workflows-to-Agents
- **Nhánh nộp:** main
- **Commit chốt:** [Bổ sung commit hash]

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
|---:|---|---|---|---|---|
| 1 | Đỗ Thị Thu Hằng | 2A202603840 | dothuhang2604@gmail.com | ThuHang2604 | Ledger, Testing + Documentation |
| 2 | Phùng Văn Thanh Cao | 2A202603741 | ptc99998888@gmail.com | ththanh8888 | B: Single Agent + Policy |
| 3 | Vũ Quang Huy | 2A202603782 | 26ai.huyvq6@vinuni.edu.vn | huyvu-03 | Workflow |
| 4 | Nguyễn Minh Đức | 2A202603751 | nmduc7904@gmail.com | Minhduc7904 | Orchestrator + Handoff (P3) |

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Đỗ Thị Thu Hằng (2A202603840) | Ledger, Testing + Documentation | `20265e7` (test(ledger): trace hygiene, T13/T14, conflict, replay, blank order_id); `d8c21a0` (update decision_adr.md) | Các test liên quan đến trace hygiene, T13/T14, conflict, replay và blank order_id. Cần bổ sung chính xác tên file test đã sửa/thêm. |
| Vũ Quang Huy (2A202603782) | Workflow | `1723d3e` (workflow), `f242fa4` (blank order ID fix), `f2727a2` (regression test), `e400c59` (personal report), `76ec1cf` (ablation results) | `src/tests/test_workflow_whitespace_order_id.py` — ID chỉ có khoảng trắng trả về `needs_info` và không ghi refund; bản copy được grading lại: student suite 248 passed |
| Phùng Văn Thanh Cao | B: single agent + policy | `41f491f` (single.py: ReAct, quote đầy đủ, crash_at; test approval) | `src/tests/test_single_approval.py` (12 test approval + order_id khoảng trắng); bỏ xfail trong `test_ledger_extra.py` |
| Nguyễn Minh Đức (2A202603751) | Orchestrator + Handoff | `cbe652f` feat(orchestrator): shape C, read-only investigators, sanitized handoff | `src/tests/test_orchestrator_handoff.py` (mới); ma trận student `-k orchestrator` 62/62 |


### Bằng chứng

- Workflow và kiểm tra ID trống: `src/lab8/shapes/workflow.py`; regression test `src/tests/test_workflow_whitespace_order_id.py`.
- Benchmark/ablation: `src/reports/benchmark.json` và `report/team/research_card.md` (T02: single 5/5 seed, swarm 4/5; swarm lỗi tại seed 55).
- Báo cáo cá nhân: `report/team/2A202603782_VuQuangHuy.md`.
