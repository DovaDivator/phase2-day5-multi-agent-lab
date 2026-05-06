# Lab 20: Multi-Agent Research System Starter

Starter repo cho bài lab **Multi-Agent Systems**: xây dựng hệ thống nghiên cứu gồm **Supervisor + Researcher + Analyst + Writer** và benchmark với single-agent baseline.

> Mục tiêu của repo này là cung cấp **production-grade skeleton** để học viên phát triển code cá nhân. Các phần logic quan trọng được để ở dạng `TODO` để học viên tự triển khai.

## Learning outcomes

Sau 2 giờ lab, học viên cần có thể:

1. Thiết kế role rõ ràng cho nhiều agent.
2. Xây dựng shared state đủ thông tin cho handoff.
3. Thêm guardrail tối thiểu: max iterations, timeout, retry/fallback, validation.
4. Trace được luồng chạy và giải thích agent nào làm gì.
5. Benchmark single-agent vs multi-agent theo quality, latency, cost.
(Hỗ trợ Python >= 3.10)

## Architecture mục tiêu

```text
User Query
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> research_notes
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

## Cấu trúc repo

```text
.
├── src/multi_agent_research_lab/
│   ├── agents/              # Agent interfaces + skeletons
│   ├── core/                # Config, state, schemas, errors
│   ├── graph/               # LangGraph workflow skeleton
│   ├── services/            # LLM, search, storage clients
│   ├── evaluation/          # Benchmark/evaluation skeleton
│   ├── observability/       # Logging/tracing hooks
│   └── cli.py               # CLI entrypoint
├── configs/                 # YAML configs for lab variants
├── docs/                    # Lab guide, rubric, design notes
├── tests/                   # Unit tests for skeleton behavior
├── notebooks/               # Optional notebook entrypoint
├── scripts/                 # Helper scripts
├── .env.example             # Environment variables template
├── pyproject.toml           # Python project config
├── Dockerfile               # Containerized dev/runtime
└── Makefile                 # Common commands
```

## Quickstart (Windows/PowerShell)

### 1. Tạo môi trường ảo
Mở PowerShell tại thư mục dự án:
```powershell
# Tạo venv
python -m venv venv
.\venv\Scripts\activate

# Cập nhật pip (quan trọng để hỗ trợ pyproject.toml)
python -m pip install --upgrade pip

# Cài đặt thư viện
pip install -r requirements.txt
pip install -e .
copy .env.example .env
```

> [!TIP]
> Nếu bạn gặp lỗi `ModuleNotFoundError: No module named 'multi_agent_research_lab'`, đó là do Python không tìm thấy thư mục `src`. Hãy đảm bảo bạn chạy lệnh thiết lập `PYTHONPATH` trước khi chạy app (xem bước 3).

### 2. Cấu hình API keys
Mở file `.env` và điền `OPENAI_API_KEY`. Các key khác như `TAVILY_API_KEY` (tìm kiếm web) và `LANGSMITH_API_KEY` (theo dõi trace) là tùy chọn.

### 3. Chạy Baseline (Single-Agent)
```powershell
$env:PYTHONPATH="src"; $env:PYTHONIOENCODING="utf-8"
python -m multi_agent_research_lab.cli baseline --query "What is GraphRAG?"
```

### 4. Chạy Multi-Agent Workflow
```powershell
python -m multi_agent_research_lab.cli multi-agent --query "What is GraphRAG?"
```

### 5. Chạy Benchmark & So sánh
Lệnh này sẽ chạy cả Baseline và Multi-Agent để so sánh hiệu suất và tạo báo cáo tự động (song ngữ):
```powershell
python -m multi_agent_research_lab.cli benchmark --query "What is GraphRAG?"
```
Báo cáo sẽ được lưu tại `reports/benchmark_report.md` và bằng chứng thực thi tại `reports/benchmark_report.json`.

## Các lệnh hữu ích trên Windows

- **Tìm các phần cần làm (TODO):**
  ```powershell
  Get-ChildItem -Recurse src, tests, docs | Select-String "TODO(student)"
  ```
- **Chạy Tests:**
  ```powershell
  $env:PYTHONPATH="src"; venv\Scripts\pytest.exe
  ```
- **Kiểm tra Lint (Sửa lỗi trình bày):**
  ```powershell
  $env:PYTHONPATH="src"; venv\Scripts\ruff.exe check src tests --fix
  ```
- **Kiểm tra Typecheck (Kiểm tra kiểu):**
  ```powershell
  $env:PYTHONPATH="src"; venv\Scripts\mypy.exe src
  ```
- **Xử lý lỗi hiển thị (Unicode):** Nếu terminal hiển thị lỗi emoji hoặc ký tự lạ, hãy chạy lệnh này trước:
  ```powershell
  $env:PYTHONIOENCODING="utf-8"
  ```

## Deliverables

Học viên nộp:

1. GitHub repo cá nhân.
2. Screenshot trace hoặc link trace (LangSmith/Langfuse).
3. `reports/benchmark_report.md` so sánh single vs multi-agent.
4. Một đoạn giải thích failure mode và cách fix.

## References

- Anthropic: Building effective agents — https://www.anthropic.com/engineering/building-effective-agents
- OpenAI Agents SDK orchestration/handoffs — https://developers.openai.com/api/docs/guides/agents/orchestration
- LangGraph concepts — https://langchain-ai.github.io/langgraph/concepts/
- LangSmith tracing — https://docs.smith.langchain.com/
- Langfuse tracing — https://langfuse.com/docs
