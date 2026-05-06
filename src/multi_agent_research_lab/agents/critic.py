"""Critic agent for fact-checking and report quality validation."""

import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

class CriticAgent(BaseAgent):
    """Fact-checking and safety-review agent."""

    name = "critic"

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings."""
        from multi_agent_research_lab.observability.tracing import trace_span
        
        with trace_span(self.name, {"answer_len": len(state.final_answer or "")}):
            if not state.final_answer:
                logger.warning("No final answer found for critique.")
                return state

            system_prompt = (
                "You are a rigorous Fact-Checker and Quality Auditor. Your goal is to review the "
                "research report produced by the Writer and identify any issues.\n"
                "Evaluate based on:\n"
                "1. Factual Accuracy: Does it contradict the research notes?\n"
                "2. Citation Quality: Are all claims backed by sources from the research notes?\n"
                "3. Tone and Structure: Is it professional and well-organized?\n"
                "4. Hallucinations: Does it include information not found in the notes?\n\n"
                "Provide your feedback as a list of 'Critiques' and a 'Score' from 1 to 10."
            )

            user_context = (
                f"Original Query: {state.request.query}\n\n"
                f"Research Notes:\n{state.research_notes}\n\n"
                f"Analysis:\n{state.analysis_notes}\n\n"
                f"Report to Review:\n{state.final_answer}"
            )

            response = self.llm.complete(system_prompt, user_context)
            state.record_usage(
                response.input_tokens or 0, 
                response.output_tokens or 0, 
                response.cost_usd or 0.0
            )
            
            # Record result
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.CRITIC,
                    content=response.content,
                    metadata={"critique_length": len(response.content)}
                )
            )
            state.add_trace_event("critic_step", {"critique_length": len(response.content)})
            
            return state
