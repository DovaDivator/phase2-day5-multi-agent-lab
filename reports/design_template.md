# Design Document: Multi-Agent Research System

## 1. Problem
Hệ thống cần giải quyết bài toán nghiên cứu chuyên sâu (Deep Research). Các câu hỏi từ người dùng thường phức tạp, đòi hỏi phải truy vấn nhiều nguồn, đối soát thông tin và viết báo cáo có trích dẫn. Một thực thể đơn lẻ (Single-agent) thường gặp khó khăn trong việc tự kiểm chứng lỗi sai của chính mình.

## 2. Why multi-agent?
Single-agent gặp các hạn chế sau:
- **Hallucination**: Không có bước phản biện độc lập.
- **Context Dilution**: Khi phải làm quá nhiều việc (search, phân tích, viết) trong một prompt, chất lượng đầu ra bị giảm.
- **Lack of Iteration**: Khó có thể tự nhận ra mình đang thiếu thông tin gì để quay lại tìm kiếm.

**Multi-agent** cho phép chia nhỏ trách nhiệm (Separation of Concerns), giúp mỗi Agent tập trung tối đa vào kỹ năng chuyên biệt của mình.

## 3. Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| **Supervisor** | Điều phối toàn bộ luồng chạy, quyết định bước tiếp theo. | State (history, notes) | Tên Agent tiếp theo | Loop vô hạn hoặc dừng quá sớm. |
| **Researcher** | Tạo search query và tổng hợp thông tin thô từ web. | Query, existing notes | Search results, raw notes | Tìm sai thông tin, search query quá hẹp. |
| **Analyst** | Phân tích notes, tìm điểm mâu thuẫn và lỗ hổng kiến thức. | Research notes | Structured insights, gaps | Bỏ sót các điểm mâu thuẫn quan trọng. |
| **Writer** | Tổng hợp báo cáo cuối cùng với văn phong chuyên nghiệp. | Notes, analysis | Final Markdown report | Quên trích dẫn, văn phong không phù hợp. |
| **Critic** | Kiểm định tính xác thực và chất lượng báo cáo cuối. | Final report, notes | Critique, Quality Score | Quá khắt khe hoặc quá dễ dãi. |

## 4. Shared State
- `request`: Lưu truy vấn gốc của người dùng.
- `research_notes`: Lưu trữ kiến thức tích lũy được từ Researcher.
- `analysis_notes`: Lưu kết quả phân tích sâu của Analyst.
- `final_answer`: Bản thảo báo cáo cuối cùng.
- `route_history`: Lịch sử di chuyển giữa các Agent để Supervisor theo dõi.
- `usage_stats`: Theo dõi cost và token cho benchmark.

## 5. Routing Policy
Hệ thống sử dụng **StateGraph** với logic:
1. `Supervisor` khởi tạo.
2. Nếu thiếu thông tin -> `Researcher`.
3. Nếu đã có thông tin -> `Analyst`.
4. Nếu đã có phân tích -> `Writer`.
5. Nếu đã có bản thảo -> `Critic`.
6. Nếu `Critic` hài lòng hoặc đạt `Max Iterations` -> `END`.

## 6. Guardrails
- **Max Iterations**: 6 vòng (tránh cháy tài khoản LLM).
- **Timeout**: 60s cho mỗi agent call.
- **Retry**: Sử dụng `tenacity` với exponential backoff cho API errors.
- **Validation**: Critic kiểm tra sự hiện diện của trích dẫn (Citations).

## 7. Benchmark Plan
- **Queries**: Các câu hỏi về công nghệ mới (GraphRAG, LLM agents).
- **Metrics**: Latency (s), Cost ($), Quality (0-10), Citations count.
- **Expected Outcome**: Multi-agent sẽ chậm và đắt hơn 3-5 lần nhưng điểm Quality và Citations sẽ cao hơn rõ rệt (> 8/10).
