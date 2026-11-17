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

- **Luồng:** đọc claim bằng `get_claim_view`; thiếu `order_id` thì trả `needs_info`. Sau đó vòng ReAct (tối đa 8 bước) chạy tuần tự `lookup_order` → `compute_compensation` → `lookup_refund_history`, rồi trả quote. Một claim thường dùng 4 bước tool và 4 lần `decide`, thấp hơn trần 8.
- **Ranh giới code / model:** model (MockLLM) chỉ chọn tool đọc và soạn câu trả lời. Số tiền do `compute_compensation` tính. Sau vòng lặp, code của shape gọi `durability.issue_refund`. Shape không tự trừ phần đã hoàn: nó truyền **quote đầy đủ** và để host trừ, nên T13 (đã hoàn đủ) và T14 (hoàn phần chênh) đúng.
- **Ticket là dữ liệu:** ticket không được đưa vào observation của vòng ReAct và không ghi vào trace, nên shape không tin số ngày trễ ghi trong ticket (điểm yếu của swarm ở seed 55, claim T02).
- **Crash:** `crash_at` được truyền vào `issue_refund`, `InjectedCrash` chỉ được flush trace rồi ném lại.
- **Trace:** ghi kết quả `lookup_order` (đã qua allowlist), quote, kết quả `lookup_refund_history`, quyết định và lý do host từ chối. **Cố ý không ghi** ticket, claim row, order row thô, `parent_secret`, header.
- **Test approval:** 36 test trong `src/tests/test_single_approval.py`, chạy 5 seed, phủ các nhánh: không có approval, approval không tồn tại, hết hạn, bị thu hồi, của claim khác, số tiền ≤ 0, approval thấp hơn quote, gọi lại sau khi bị từ chối.
- **Số đo tham khảo (một lần chạy lẻ, C-001 seed 11):** single 5 model call, 4 tool call, 42,58 VND; swarm 3 model call, 5 tool call, 52,30 VND. Số chính thức xem mục 4.

...

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
