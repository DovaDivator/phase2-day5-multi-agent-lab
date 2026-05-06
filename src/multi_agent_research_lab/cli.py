"""Command-line entrypoint for the lab starter."""

import warnings

warnings.filterwarnings("ignore", message="The default value of `allowed_objects` will change")
warnings.filterwarnings("ignore", category=DeprecationWarning)

import time  # noqa: E402
from typing import Annotated  # noqa: E402

import typer  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from multi_agent_research_lab.core.config import get_settings  # noqa: E402
from multi_agent_research_lab.core.schemas import ResearchQuery  # noqa: E402
from multi_agent_research_lab.core.state import ResearchState  # noqa: E402
from multi_agent_research_lab.evaluation.benchmark import run_benchmark  # noqa: E402
from multi_agent_research_lab.evaluation.report import render_markdown_report  # noqa: E402
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow  # noqa: E402
from multi_agent_research_lab.observability.logging import configure_logging  # noqa: E402
from multi_agent_research_lab.services.llm_client import LLMClient  # noqa: E402

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    
    # LangSmith automatic integration
    if settings.langsmith_api_key:
        import os
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    model: str = "gpt-4o-mini",
) -> None:
    """Run a real single-agent baseline."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    
    llm = LLMClient(model=model)
    
    console.print(f"[bold blue]Running single-agent baseline for:[/bold blue] {query}")
    
    start_time = time.perf_counter()
    response = llm.complete(
        system_prompt=(
            "You are a professional researcher. Research the user's query and provide "
            "a comprehensive, high-quality summary with citations if possible. "
            "Since you are a single agent, you must research and synthesize in one go."
        ),
        user_prompt=query
    )
    end_time = time.perf_counter()
    
    state.final_answer = response.content
    latency = end_time - start_time
    
    console.print(Panel(str(state.final_answer), title="Single-Agent Baseline Answer"))
    console.print(f"[green]Latency:[/green] {latency:.2f}s")
    console.print(
        f"[green]Tokens:[/green] {response.input_tokens} in / {response.output_tokens} out"
    )
    console.print(f"[green]Estimated Cost:[/green] ${response.cost_usd:.5f}")


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the full multi-agent research workflow."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    
    with console.status("[bold green]Working on your research..."):
        result = workflow.run(state)
    
    # 1. Print Steps
    console.print("\n[bold cyan]─── Research Execution Trace ───[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Step", style="dim")
    table.add_column("Agent", style="bold")
    table.add_column("Contribution")
    
    for i, res in enumerate(result.agent_results, 1):
        table.add_row(str(i), res.agent, res.content)
    console.print(table)
    
    # 2. Final Answer
    console.print("\n[bold green]─── Final Research Report ───[/bold green]")
    console.print(Panel(str(result.final_answer), title=f"Result for: {query}"))
    
    # 3. Usage
    tokens = result.total_input_tokens + result.total_output_tokens
    console.print(f"\n[dim]Total cost: ${result.total_cost_usd:.4f} | Tokens: {tokens}[/dim]")


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    output: str = "reports/benchmark_report.md",
) -> None:
    """Run both baseline and multi-agent and compare results."""

    _init()
    console.print(f"[bold magenta]🚀 Starting Benchmark for query:[/bold magenta] {query}")

    # 1. Baseline
    def baseline_runner(q: str) -> ResearchState:
        llm = LLMClient()
        state = ResearchState(request=ResearchQuery(query=q))
        resp = llm.complete("You are a professional researcher.", q)
        state.final_answer = resp.content
        state.record_usage(resp.input_tokens or 0, resp.output_tokens or 0, resp.cost_usd or 0.0)
        return state

    console.print("--- Running Baseline ---")
    state_b, metrics_b = run_benchmark("Single-Agent Baseline", query, baseline_runner)

    # 2. Multi-Agent
    def multi_agent_runner(q: str) -> ResearchState:
        workflow = MultiAgentWorkflow()
        state = ResearchState(request=ResearchQuery(query=q))
        return workflow.run(state)

    console.print("--- Running Multi-Agent Workflow ---")
    state_m, metrics_m = run_benchmark("Multi-Agent System", query, multi_agent_runner)

    # 3. Save Evidence (JSON)
    import json
    evidence = {
        "query": query,
        "baseline": {
            "metrics": metrics_b.model_dump(),
            "answer": state_b.final_answer,
            "usage": {
                "input_tokens": state_b.total_input_tokens, 
                "output_tokens": state_b.total_output_tokens, 
                "cost": state_b.total_cost_usd
            }
        },
        "multi_agent": {
            "metrics": metrics_m.model_dump(),
            "answer": state_m.final_answer,
            "usage": {
                "input_tokens": state_m.total_input_tokens, 
                "output_tokens": state_m.total_output_tokens, 
                "cost": state_m.total_cost_usd
            },
            "trace": state_m.trace
        }
    }
    
    json_path = output.replace(".md", ".json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2, ensure_ascii=False)

    # 4. Report
    report_md = render_markdown_report([metrics_b, metrics_m])
    
    with open(output, "w", encoding="utf-8") as f:
        f.write(report_md)
    
    console.print("\n[bold green]✅ Benchmark complete![/bold green]")
    console.print(f"Report saved to: [cyan]{output}[/cyan]")
    console.print(f"Evidence saved to: [cyan]{json_path}[/cyan]")
    console.print(Panel(report_md, title="Benchmark Summary"))


if __name__ == "__main__":
    app()
