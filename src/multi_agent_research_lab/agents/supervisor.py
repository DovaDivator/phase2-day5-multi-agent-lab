import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self, llm: LLMClient | None = None):
        self.llm = llm or LLMClient()
        self.settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        from multi_agent_research_lab.observability.tracing import trace_span
        
        with trace_span(self.name, {"iteration": state.iteration}):
            # Guardrail: Check max iterations
            if state.iteration >= self.settings.max_iterations:
                logger.warning(
                    f"Max iterations ({self.settings.max_iterations}) reached. Routing to writer."
                )
                state.record_route("writer")
                return state

            system_prompt = (
                "You are the Supervisor of a Research Team. Your goal is to coordinate "
                "specialists:\n"
                "1. Researcher: Searches for raw information and takes notes.\n"
                "2. Analyst: Processes notes, finds contradictions, and extracts key claims.\n"
                "3. Writer: Synthesizes the final answer for the user.\n"
                "4. Critic: Reviews the final answer for facts and quality.\n\n"
                "You must decide who should work next based on the current state.\n"
                "Rules:\n"
                "- If the query is new or more info is needed, call 'researcher'.\n"
                "- If we have research notes but haven't analyzed them yet, call 'analyst'.\n"
                "- If we have analysis and are ready to draft, call 'writer'.\n"
                "- If we have a draft but haven't reviewed it, call 'critic'.\n"
                "- If the report is reviewed and high quality, call 'finish'.\n\n"
                "Respond ONLY with one of these words: researcher, analyst, writer, critic, finish."
            )

            critic_present = any(r.agent == "critic" for r in state.agent_results)
            user_prompt = (
                f"Query: {state.request.query}\n"
                f"Current Iteration: {state.iteration}\n"
                f"Route History: {state.route_history}\n"
                f"Research Notes: {'Present' if state.research_notes else 'Missing'}\n"
                f"Analysis Notes: {'Present' if state.analysis_notes else 'Missing'}\n"
                f"Final Answer: {'Present' if state.final_answer else 'Missing'}\n"
                f"Critique: {'Present' if critic_present else 'Missing'}\n"
                "Who should go next?"
            )

            response = self.llm.complete(system_prompt, user_prompt)
            state.record_usage(
                response.input_tokens or 0, 
                response.output_tokens or 0, 
                response.cost_usd or 0.0
            )
            next_step = response.content.strip().lower()

            # Validate response
            valid_steps = ["researcher", "analyst", "writer", "critic", "finish"]
            if next_step not in valid_steps:
                logger.error(f"Invalid supervisor decision: {next_step}. Defaulting to writer.")
                next_step = "writer"

            state.record_route(next_step)
            state.add_trace_event(
                "supervisor_decision", 
                {"next_step": next_step, "reasoning": response.content}
            )
            
            return state
