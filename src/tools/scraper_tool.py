"""Web Scraping Tool for extracting structured product details using ScrapeGraphAI."""

from typing import Any, Dict, Optional, Type
from pydantic import BaseModel, Field

from src.core.config import Settings, get_settings
from src.domain.product import SingleExtractedProduct
from src.infrastructure.clients.scrapegraph_client import (
    BaseScraperClient,
    MockScraperClient,
    ScrapeGraphClientAdapter,
)
from src.tools.base import BaseProcurementTool


class ScraperInputSchema(BaseModel):
    """Input argument schema for web_scraping_tool."""

    page_url: str = Field(
        ...,
        description="The full HTTP/HTTPS URL of the single product web page to scrape.",
    )


class WebScrapingTool(BaseProcurementTool):
    """Tool that extracts structured product data and specifications from an ecommerce URL."""

    name: str = "web_scraping_tool"
    description: str = (
        "An AI Tool to help an agent to scrape a web page and extract structured product details. "
        "Provide page_url (e.g., https://www.amazon.eg/dp/...)"
    )
    args_schema: Type[BaseModel] = ScraperInputSchema
    scraper_client: Optional[BaseScraperClient] = None

    def __init__(
        self,
        scraper_client: Optional[BaseScraperClient] = None,
        settings: Optional[Settings] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if scraper_client is not None:
            self.scraper_client = scraper_client
        else:
            cfg = settings or get_settings()
            if cfg.scraper_provider == "mock" or not cfg.scrapegraph_api_key:
                self.scraper_client = MockScraperClient()
            else:
                self.scraper_client = ScrapeGraphClientAdapter(settings=cfg)

    def _run(self, page_url: str) -> Any:
        """Extract structured product details from a target web page."""
        if not self.scraper_client:
            return {"page_url": page_url, "error": "Scraper client is not initialized."}

        prompt = "Extract ```json\n" + SingleExtractedProduct.schema_json() + "```\nFrom the web page"

        details = self.execute_safely(
            operation_name="extract",
            fn=self.scraper_client.extract,
            prompt=prompt,
            url=page_url,
        )

        return {
            "page_url": page_url,
            "details": details,
        }
