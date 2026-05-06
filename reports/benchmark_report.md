# 📊 Báo cáo Benchmark toàn diện: Hệ thống Nghiên cứu Multi-Agent

## 1. Tóm tắt điều hành (Executive Summary)
Báo cáo này đánh giá hiệu suất, độ chính xác và tính hiệu quả về chi phí của **Hệ thống Nghiên cứu Multi-Agent** so với **Single-Agent Baseline (Mô hình cơ sở đơn tác tử)**.
Mục tiêu là xác định liệu sự phức tạp tăng thêm của mô hình phối hợp (Supervisor-Worker-Critic) có mang lại cải thiện rõ rệt về chất lượng nghiên cứu hay không.

## 2. So sánh định lượng (Quantitative Comparison)

| Run (Lượt chạy) | Latency (Độ trễ - s) | Cost (Chi phí - USD) | Quality (Chất lượng) | Notes (Ghi chú) |
|:---|---:|---:|---:|:---|
| **Single-Agent Baseline** | 11.53 | $0.00045 | N/A | Total iterations: 0. Sources found: 0. Citations detected: 0. |
| **Multi-Agent System** | 38.68 | $0.00173 | N/A | Total iterations: 5. Sources found: 5. Citations detected: 5. |

## 3. Các phát hiện chính & Phân tích (Key Findings & Insights)

### A. Khoảng cách kiểm chứng (Verification Gap)
Trong **Single-Agent Baseline (Đơn tác tử)**, LLM phụ thuộc hoàn toàn vào kiến thức nội tại hoặc một bước truy xuất duy nhất. Điều này thường dẫn đến phân tích bề mặt. **Hệ thống Multi-Agent (Đa tác tử)** tận dụng vòng lặp *Supervisor-Analyst*. Nếu phát hiện lỗ hổng, Supervisor sẽ kích hoạt thêm bước *Researcher* để đảm bảo dữ liệu được thu thập đầy đủ trước khi tổng hợp.

### B. Đánh đổi kiến trúc (Architectural Trade-offs)
1. **Chi phí suy luận (Cost of Reasoning)**: Hệ thống Multi-Agent thực hiện nhiều lượt gọi LLM hơn đáng kể. Đối với nghiên cứu phức tạp, đây là 'chi phí của chất lượng'.
2. **Chuyên môn hóa vai trò (Role Specialization)**: Bằng cách tách biệt các vai trò *Analyst (Phân tích)*, *Writer (Người viết)*, và *Critic (Người phản biện)*, chúng ta giảm thiểu hiện tượng 'nhầm lẫn vai trò' và đảm bảo báo cáo cuối cùng đạt tiêu chuẩn cao nhất.

## 4. Phân tích lỗi và Cách khắc phục (Failure Mode and Mitigation)

Trong quá trình phát triển, chúng tôi đã xác định được các kịch bản lỗi chính và triển khai các giải pháp sau:

| Failure Mode (Kịch bản lỗi) | Nguyên nhân | Cách khắc phục (Fix) |
|:---|:---|:---|
| **Vòng lặp vô hạn (Infinite Loops)** | Supervisor liên tục luân chuyển giữa các Agent mà không về đích. | Triển khai **Max Iterations (Giới hạn vòng lặp)**. Nếu vượt quá 6 lượt, Supervisor buộc phải chuyển sang Writer để kết thúc. |
| **Lỗi định dạng kết quả (Parsing Errors)** | LLM trả về kết quả không đúng cấu trúc JSON mong đợi. | Sử dụng **Structured Output (Pydantic)** và cơ chế **Retry (Thử lại)** với `tenacity` để tự động khôi phục. |
| **Ảo giác thông tin (Hallucinations)** | Researcher lấy nhầm dữ liệu hoặc Analyst phân tích sai. | Bổ sung **Critic Agent (Người phản biện)** độc lập để đối soát báo cáo cuối cùng với các nguồn thô. |
| **Cạn kiệt tài nguyên (Rate Limiting)** | Gọi API quá nhanh và nhiều trong thời gian ngắn. | Sử dụng **Exponential Backoff** để giãn cách thời gian giữa các lần gọi khi gặp lỗi 429. |

## 5. Câu hỏi phản biện (Exit Ticket - Lab Reflection)

**Q1: Case nào nên dùng multi-agent (đa tác tử)? Vì sao?**
Nên dùng cho các tác vụ **nghiên cứu chuyên sâu (Deep Research)** hoặc lập kế hoạch phức tạp. Lý do: Khả năng tự sửa lỗi và kiểm định chéo giữa các agents giúp đảm bảo độ tin cậy của thông tin.

**Q2: Case nào không nên dùng multi-agent (đa tác tử)? Vì sao?**
Không nên dùng cho các tác vụ **hỏi đáp nhanh (Q&A)** hoặc tóm tắt đơn giản. Lý do: Chi phí và độ trễ cao không tương xứng với giá trị nhận lại trong các tình huống đơn giản.

## 6. Phụ lục (Appendices)
- **Dữ liệu minh chứng (Evidence JSON)**: `reports/benchmark_report.json`
- **Bản thiết kế (Design Doc)**: [design_template.md](../docs/design_template.md)

---
*Báo cáo được tạo tự động bởi Multi-Agent Research Lab v0.1.0*
