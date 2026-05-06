import warnings

warnings.filterwarnings("ignore", category=PendingDeprecationWarning, module="langgraph")
import logging  # noqa: E402
from typing import Any, Literal, cast  # noqa: E402

from langgraph.graph import END, StateGraph  # noqa: E402

from multi_agent_research_lab.agents.analyst import AnalystAgent  # noqa: E402
from multi_agent_research_lab.agents.critic import CriticAgent  # noqa: E402
from multi_agent_research_lab.agents.researcher import ResearcherAgent  # noqa: E402
from multi_agent_research_lab.agents.supervisor import SupervisorAgent  # noqa: E402
from multi_agent_research_lab.agents.writer import WriterAgent  # noqa: E402
from multi_agent_research_lab.core.state import ResearchState  # noqa: E402

logger = logging.getLogger(__name__)

class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph."""

    def __init__(self) -> None:
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()
        self.critic = CriticAgent()
        self._graph = self.build()

    def build(self) -> Any:
        """Create a LangGraph graph."""
        
        builder = StateGraph(ResearchState)

        # Define nodes
        builder.add_node("supervisor", self.supervisor.run)
        builder.add_node("researcher", self.researcher.run)
        builder.add_node("analyst", self.analyst.run)
        builder.add_node("writer", self.writer.run)
        builder.add_node("critic", self.critic.run)

        # Define edges
        builder.set_entry_point("supervisor")

        # Supervisor routes to workers
        builder.add_conditional_edges(
            "supervisor",
            self._route_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "critic": "critic",
                "finish": END
            }
        )

        # Workers always go back to supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")
        builder.add_edge("critic", "supervisor")

        return builder.compile()

    def _route_decision(
        self, 
        state: ResearchState
    ) -> Literal["researcher", "analyst", "writer", "critic", "finish"]:
        """Helper to extract the last route from state history."""
        if not state.route_history:
            return "finish"
        res = state.route_history[-1]
        return cast(Literal["researcher", "analyst", "writer", "critic", "finish"], res)

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state."""
        logger.info("Starting multi-agent workflow.")
        
        # LangGraph run
        final_output = self._graph.invoke(state)
        
        # LangGraph might return a dict or the state object depending on version/config
        if isinstance(final_output, dict):
            return ResearchState.model_validate(final_output)
        return cast(ResearchState, final_output)
