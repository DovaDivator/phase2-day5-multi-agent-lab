"""Benchmark skeleton for single-agent vs multi-agent."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import AgentName, BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str, 
    query: str, 
    runner: Runner
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency, cost, and citation coverage for a run."""

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    
    # 2. Extract metrics from state
    # Simple citation coverage check: count [1], [2], etc. in final_answer
    citations_count = state.final_answer.count("[") if state.final_answer else 0
    
    # Try to extract quality score from critic result
    quality_score = None
    for res in state.agent_results:
        if res.agent == AgentName.CRITIC:
            # Look for "Score: X/10" or "Score: X"
            import re
            match = re.search(r"Score:\s*(\d+)", res.content)
            if match:
                quality_score = float(match.group(1))
            break

    metrics = BenchmarkMetrics(
        run_name=run_name,
        latency_seconds=latency,
        estimated_cost_usd=state.total_cost_usd,
        quality_score=quality_score,
        notes=(
            f"Total iterations: {state.iteration}. "
            f"Sources found: {len(state.sources)}. "
            f"Citations detected: {citations_count}."
        )
    )
    return state, metrics
