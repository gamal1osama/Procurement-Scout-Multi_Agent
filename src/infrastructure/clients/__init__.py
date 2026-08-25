"""External service clients and adapters for search and scraping."""

from src.infrastructure.clients.tavily_client import (
    BaseSearchClient,
    TavilySearchClientAdapter,
    MockSearchClient,
)
from src.infrastructure.clients.scrapegraph_client import (
    BaseScraperClient,
    ScrapeGraphClientAdapter,
    MockScraperClient,
)

__all__ = [
    "BaseSearchClient",
    "TavilySearchClientAdapter",
    "MockSearchClient",
    "BaseScraperClient",
    "ScrapeGraphClientAdapter",
    "MockScraperClient",
]
