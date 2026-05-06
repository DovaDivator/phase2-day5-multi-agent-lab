"""Analyst agent skeleton."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`."""
        from multi_agent_research_lab.observability.tracing import trace_span
        
        with trace_span(self.name, {"research_notes_len": len(state.research_notes or "")}):
            if not state.research_notes:
                logger.warning("No research notes found for analysis.")
                state.analysis_notes = "No research notes provided for analysis."
                return state

            system_prompt = (
                "You are a strategic analyst. Your task is to process raw research "
                "notes and extract:\n"
                "1. Key Claims: Major facts and arguments discovered.\n"
                "2. Evidence Support: How strong is the evidence for each claim?\n"
                "3. Contradictions: Any conflicting information found across sources.\n"
                "4. Knowledge Gaps: What is still missing to fully answer the user query?\n\n"
                "Format your response as a structured analysis report."
            )

            user_context = (
                f"Original Query: {state.request.query}\n\n"
                f"Research Notes:\n{state.research_notes}"
            )

            response = self.llm.complete(system_prompt, user_context)
            state.record_usage(
                response.input_tokens or 0, 
                response.output_tokens or 0, 
                response.cost_usd or 0.0
            )
            state.analysis_notes = response.content
            
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content="Extracted key claims and identified knowledge gaps.",
                    metadata={"analysis_length": len(state.analysis_notes)}
                )
            )
            state.add_trace_event(
                "analyst_step", 
                {"analysis_notes_length": len(state.analysis_notes)}
            )
            
            return state
