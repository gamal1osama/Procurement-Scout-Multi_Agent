"""Search client adapters implementing the Strategy and Adapter patterns."""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from tavily import TavilyClient

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError, SearchProviderError
from src.core.logging import logger


class BaseSearchClient(ABC):
    """Abstract base class for search engine adapters."""

    @abstractmethod
    def search(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a web search query and return the raw search response."""
        raise NotImplementedError


class TavilySearchClientAdapter(BaseSearchClient):
    """Adapter wrapping the official TavilyClient with error handling and logging."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.api_key = self.settings.tavily_api_key or os.getenv("TAVILY_API_KEY")

        if not self.api_key:
            raise ConfigurationError(
                "TAVILY_API_KEY is not configured but Tavily search client was requested."
            )

        self._client = TavilyClient(api_key=self.api_key)
        logger.debug("Initialized TavilySearchClientAdapter successfully.")

    def search(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute search using Tavily API."""
        try:
            logger.debug("Executing Tavily search for query: '{}'", query)
            response = self._client.search(query=query, **kwargs)
            return response
        except Exception as exc:
            logger.error("Tavily search failed for query '{}': {}", query, exc)
            raise SearchProviderError(
                f"Tavily search failed for query '{query}': {exc}",
                details={"query": query, "error": str(exc)},
            ) from exc


class MockSearchClient(BaseSearchClient):
    """Mock search client providing deterministic search results for unit/offline testing."""

    def search(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        logger.info("Using MockSearchClient for query: '{}'", query)
        return {
            "query": query,
            "results": [
                {
                    "title": "Mock Coffee Machine 15-Bar",
                    "url": "https://www.amazon.eg/mock-coffee-machine/dp/B076DR3SW8",
                    "content": "Professional espresso and filter coffee maker with 15 bar pump pressure.",
                    "score": 0.88,
                },
                {
                    "title": "Mock Capsule Espresso Maker",
                    "url": "https://www.noon.com/egypt-en/mock-espresso/N36746397A/p",
                    "content": "Compact capsule espresso machine with milk frother.",
                    "score": 0.92,
                },
            ],
        }
