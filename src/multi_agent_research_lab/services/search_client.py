import logging

import requests  # type: ignore[import-untyped]

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)


class SearchClient:
    """Provider-agnostic search client. Defaults to Mock if no API key is found."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_key = self.settings.tavily_api_key

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query."""
        if not self.api_key:
            logger.warning("No TAVILY_API_KEY found, using Mock results.")
            return self._mock_search(query, max_results)

        try:
            # Using direct API call to Tavily to avoid extra dependencies
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": max_results,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            results = []
            for result in data.get("results", []):
                results.append(
                    SourceDocument(
                        title=result.get("title", "No Title"),
                        url=result.get("url"),
                        snippet=result.get("content", ""),
                        metadata={"score": result.get("score")},
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Tavily search failed: {e}. Falling back to mock.")
            return self._mock_search(query, max_results)

    def _mock_search(self, query: str, max_results: int) -> list[SourceDocument]:
        """Return dummy data for development without API keys."""
        return [
            SourceDocument(
                title=f"Mock Result {i+1} for: {query}",
                url=f"https://example.com/mock-{i+1}",
                snippet=(
                    f"This is a mock search result number {i+1} containing some "
                    f"placeholder information about {query}."
                ),
                metadata={"source": "mock"},
            )
            for i in range(max_results)
        ]
