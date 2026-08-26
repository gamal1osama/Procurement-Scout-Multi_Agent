"""Search Engine Tool for web querying and product discovery."""

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field

from src.core.config import Settings, get_settings
from src.infrastructure.clients.tavily_client import (
    BaseSearchClient,
    MockSearchClient,
    TavilySearchClientAdapter,
)
from src.tools.base import BaseProcurementTool


class SearchInputSchema(BaseModel):
    """Input argument schema for search_engine_tool."""

    query: str = Field(
        ...,
        description="Search query string with optional domain site: filters to execute against the search engine.",
    )


class SearchEngineTool(BaseProcurementTool):
    """Tool that executes queries against the configured web search engine."""

    name: str = "search_engine_tool"
    description: str = (
        "Useful for search-based queries. Use this to find current information "
        "about any query related pages using a search engine."
    )
    args_schema: Type[BaseModel] = SearchInputSchema
    search_client: Optional[BaseSearchClient] = None

    def __init__(
        self,
        search_client: Optional[BaseSearchClient] = None,
        settings: Optional[Settings] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if search_client is not None:
            self.search_client = search_client
        else:
            cfg = settings or get_settings()
            if cfg.search_provider == "mock" or not cfg.tavily_api_key:
                self.search_client = MockSearchClient()
            else:
                self.search_client = TavilySearchClientAdapter(settings=cfg)

    def _run(self, query: str) -> Any:
        """Execute the search query."""
        if not self.search_client:
            return {"error": "Search client is not initialized."}

        return self.execute_safely(
            operation_name="search",
            fn=self.search_client.search,
            query=query,
        )
