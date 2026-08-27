"""Web Scraping Tool for extracting structured product details using ScrapeGraphAI."""

import json
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

    def _get_schema_representation(self) -> str:
        """Returns JSON schema string representation of the target product model."""
        if hasattr(SingleExtractedProduct, "model_json_schema"):
            schema_dict = SingleExtractedProduct.model_json_schema()
        else:
            schema_dict = SingleExtractedProduct.schema()
        return json.dumps(schema_dict, indent=2)

    def _run(self, page_url: str) -> Any:
        """Extract structured product details from the given URL."""
        if not self.scraper_client:
            return {"page_url": page_url, "error": "Scraper client is not initialized."}

        schema_json = self._get_schema_representation()
        extraction_prompt = f"Extract ```json\n{schema_json}\n```\nFrom the web page"

        details = self.execute_safely(
            operation_name="extract",
            fn=self.scraper_client.extract,
            prompt=extraction_prompt,
            url=page_url,
        )

        if details is None:
            details = {
                "page_url": page_url,
                "is_available": False,
                "note": "No details returned by scraper",
            }

        return {
            "page_url": page_url,
            "details": details,
        }
