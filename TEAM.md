# Team

## Thông tin nhóm

- Tên nhóm:
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-TenNhom-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt:

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 |        |      |       |        |         |
|   2 | Phùng Văn Thanh Cao | 2A202603741 | ptc99998888@gmail.com | ththanh8888 | B: single agent + policy |
|   3 | Vũ Quang Huy | 2A202603782 | 26ai.huyvq6@vinuni.edu.vn | huyvu-03 | Workflow + integration |
|   4 | Nguyễn Minh Đức | 2A202603751 | nmduc7904@gmail.com | Minhduc7904 | Orchestrator + Handoff (P3) |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Vũ Quang Huy (2A202603782) | Workflow + integration | `1723d3e` (workflow), `f242fa4` (blank order ID fix) | `src/tests/test_workflow_whitespace_order_id.py` — kiểm tra ID chỉ có khoảng trắng trả về `needs_info` và không ghi refund |
| Phùng Văn Thanh Cao | B: single agent + policy | `41f491f` (single.py: ReAct, quote đầy đủ, crash_at; test approval) | `src/tests/test_single_approval.py` (36 test approval) |
| Nguyễn Minh Đức (2A202603751) | Orchestrator + Handoff | `cbe652f` feat(orchestrator): shape C, read-only investigators, sanitized handoff | `src/tests/test_orchestrator_handoff.py` (mới); ma trận student `-k orchestrator` 62/62 |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
