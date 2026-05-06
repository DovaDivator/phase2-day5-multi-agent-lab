"""Writer agent skeleton."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

class WriterAgent(BaseAgent):
    """Synthesizes final research report."""

    name = "writer"

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`."""
        from multi_agent_research_lab.observability.tracing import trace_span
        
        with trace_span(self.name, {"sources_count": len(state.sources)}):
            system_prompt = (
                "You are a professional technical writer. Your task is to synthesize research "
                "notes and analysis into a high-quality, professional report for the user.\n"
                "Rules:\n"
                "- Use Markdown formatting.\n"
                "- Include a 'Sources' section at the end with links.\n"
                "- Ensure the tone is objective and informative.\n"
                "- Tailor the depth to the original query."
            )

            user_context = (
                f"Original Query: {state.request.query}\n\n"
                f"Research Notes:\n{state.research_notes}\n\n"
                f"Analysis:\n{state.analysis_notes}"
            )

            response = self.llm.complete(system_prompt, user_context)
            state.record_usage(
                response.input_tokens or 0, 
                response.output_tokens or 0, 
                response.cost_usd or 0.0
            )
            state.final_answer = response.content
            
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.WRITER,
                    content="Synthesized final report.",
                    metadata={"final_length": len(state.final_answer)}
                )
            )
            state.add_trace_event("writer_step", {"final_answer_length": len(state.final_answer)})
            
            return state
