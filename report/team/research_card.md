# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 · Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?*. URL: <<ĐIỀN, lấy từ thư viện tham khảo slide 68–69>>. Loại bằng chứng: nghiên cứu thực nghiệm phân loại lỗi trên trace của các hệ multi-agent |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lỗi của hệ multi-agent có thể gom thành các nhóm như lỗi đặc tả, lệch phối hợp giữa các agent, và lỗi kiểm chứng/kết thúc. <<Kiểm lại câu chữ với bài gốc trước khi nộp>> |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Kết luận của paper dựa trên các framework và task mà paper khảo sát. Nó không chứng minh gì về MockLLM hay bộ claim LogiX-VN. <<Điền tên framework/số trace theo bài gốc>> |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Trial fail của swarm ở seed 55 (T02) thuộc nhóm **lỗi kiểm chứng**: swarm tin số ngày trong ticket thay vì cột `delay_days` của đơn. Nếu đổi swarm → single (single chỉ đọc `delay_days` từ host), pass rate trên T02 tăng từ 4/5 lên 5/5 seed, và variance giữa các seed về 0 trên claim này |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định: MockLLM, tool đọc, seed `11,22,33,44,55`, corpus `data/public_claims.jsonl`, bảng giá `pricing.yaml`, grader. Biến duy nhất thay đổi: shape (swarm → single). Lưu ý: hai shape khác nhau ở cả topology lẫn nguồn của số ngày trễ, nên kết luận chỉ là "swarm ở seed 55 fail do kiểm chứng", không phải "single tốt hơn vì topology" |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: swarm trả 20.000 VND cho T02 ở seed 55 (lẽ ra `denied`). Đo bằng pass rate và pass^5 theo claim, seed min–max, variance; nguyên nhân đối chiếu qua event `model_override` trong trace của swarm |

## Kết quả ablation

- Lệnh đã chạy: `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `R-swarm-C-002-s55` (swarm trả `resolved`, trong khi đáp án là `denied`) và `R-single-C-002-s11`, `R-single-C-002-s22`, `R-single-C-002-s33`, `R-single-C-002-s44`, `R-single-C-002-s55` (single đều trả `denied`); kết quả tổng hợp tại `src/reports/benchmark.json`.
- Kết quả so với hypothesis: **đúng trên claim T02**. Single đạt 5/5 seed (pass rate 1.000); swarm đạt 4/5 (0.800) và sai ở seed 55 vì trả `resolved`. Trên toàn bộ 14 claim × 5 seed, single đạt 70/70 (pass rate 1.000, pass^5 1.000, variance 0); swarm đạt 69/70 (pass rate 0.986, pass^5 0.929, variance 0.000816). Kết quả phù hợp với nhận định rằng trial swarm seed 55 có lỗi kiểm chứng thông tin trong ticket. Đây là so sánh hai shape với nhiều khác biệt cùng lúc, nên không kết luận riêng tác động nhân quả của topology.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.


