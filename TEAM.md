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
| 3 | Vũ Quang Huy | 2A202603782 | 26ai.huyvq6@vinuni.edu.vn | huyvu-03 | Workflow + Integration |
| 4 | Nguyễn Minh Đức | 2A202603751 | nmduc7904@gmail.com | Minhduc7904 | Orchestrator + Handoff (P3) |

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
|---|---|---|---|
| Đỗ Thị Thu Hằng (2A202603840) | Ledger, Testing + Documentation | `20265e7` (test(ledger): trace hygiene, T13/T14, conflict, replay, blank order_id); `d8c21a0` (update decision_adr.md) | Các test liên quan đến trace hygiene, T13/T14, conflict, replay và blank order_id. Cần bổ sung chính xác tên file test đã sửa/thêm. |
| Phùng Văn Thanh Cao | B: Single Agent + Policy | `41f491f` (single.py: ReAct, quote đầy đủ, crash_at; test approval) | `src/tests/test_single_approval.py` (36 test approval) |
| Vũ Quang Huy (2A202603782) | Workflow + Integration | [Bổ sung commit hash] | [Bổ sung tên test đã thêm hoặc sửa] |
| Nguyễn Minh Đức (2A202603751) | Orchestrator + Handoff | `cbe652f` (feat(orchestrator): shape C, read-only investigators, sanitized handoff) | `src/tests/test_orchestrator_handoff.py` (mới); ma trận student `-k orchestrator` (62/62) |