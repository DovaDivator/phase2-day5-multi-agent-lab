import logging

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient

logger = logging.getLogger(__name__)

class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, llm: LLMClient | None = None, search_client: SearchClient | None = None):
        self.llm = llm or LLMClient()
        self.search_client = search_client or SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        from multi_agent_research_lab.observability.tracing import trace_span
        
        with trace_span(self.name, {"query": state.request.query}):
            logger.info(f"Researcher starting for query: {state.request.query}")
            
            # 1. Generate search query
            query_gen_prompt = (
                "You are a search expert. Given the user research request and current notes, "
                "generate a single effective search query to find more relevant information."
            )
            user_context = (
                f"User Request: {state.request.query}\n"
                f"Current Notes: {state.research_notes or 'None'}"
            )
            
            query_response = self.llm.complete(query_gen_prompt, user_context)
            state.record_usage(
                query_response.input_tokens or 0, 
                query_response.output_tokens or 0, 
                query_response.cost_usd or 0.0
            )
            search_query = query_response.content.strip().strip('"')
            
            # 2. Perform search
            new_sources = self.search_client.search(
                search_query, 
                max_results=state.request.max_sources
            )
            state.sources.extend(new_sources)
            
            # 3. Summarize findings
            summarize_prompt = (
                "You are a meticulous researcher. Summarize the following search results into "
                "concise research notes. Focus on facts, data, and citations. "
                "If there are existing notes, integrate new info into them."
            )
            sources_text = "\n\n".join([
                f"Source: {s.title}\nURL: {s.url}\nContent: {s.snippet}" 
                for s in new_sources
            ])
            full_context = (
                f"Existing Notes: {state.research_notes or 'None'}\n\n"
                f"New Search Results:\n{sources_text}"
            )
            
            summary_response = self.llm.complete(summarize_prompt, full_context)
            state.record_usage(
                summary_response.input_tokens or 0, 
                summary_response.output_tokens or 0, 
                summary_response.cost_usd or 0.0
            )
            state.research_notes = summary_response.content
            
            # Record result
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=f"Researched '{search_query}'. Found {len(new_sources)} sources.",
                    metadata={"search_query": search_query, "sources_count": len(new_sources)}
                )
            )
            state.add_trace_event("researcher_step", {"search_query": search_query})
            
            return state
