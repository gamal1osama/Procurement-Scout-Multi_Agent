"""Web scraping client adapters implementing Strategy and Adapter patterns."""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from scrapegraph_py import ScrapeGraphAI

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError, ScrapingProviderError
from src.core.logging import logger


class BaseScraperClient(ABC):
    """Abstract base class for web scraping client adapters."""

    @abstractmethod
    def extract(self, prompt: str, url: str, **kwargs: Any) -> Any:
        """Extract structured information from a web page URL."""
        raise NotImplementedError


class ScrapeGraphClientAdapter(BaseScraperClient):
    """Adapter wrapping ScrapeGraphAI SDK with error handling, normalization, and logging."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.api_key = self.settings.scrapegraph_api_key or os.getenv("SCRAPEGRAPH_API_KEY")

        if not self.api_key:
            raise ConfigurationError(
                "SCRAPEGRAPH_API_KEY is not configured but ScrapeGraph client was requested."
            )

        self._client = ScrapeGraphAI(api_key=self.api_key)
        logger.debug("Initialized ScrapeGraphClientAdapter with ScrapeGraphAI SDK.")

    def extract(self, prompt: str, url: str, **kwargs: Any) -> Any:
        """Execute AI web scraping extraction using ScrapeGraphAI and return a clean dict."""
        try:
            logger.debug("Extracting data via ScrapeGraphAI from URL: '{}'", url)
            schema = kwargs.pop("schema", None)

            # ScrapeGraphAI extract call
            result = self._client.extract(
                prompt=prompt,
                url=url,
                schema=schema,
                **kwargs,
            )

            # Unpack ApiResult / ExtractResponse to plain dictionary
            if hasattr(result, "data") and result.data is not None:
                data_obj = result.data
                if hasattr(data_obj, "json_data") and data_obj.json_data:
                    return data_obj.json_data
                if hasattr(data_obj, "model_dump"):
                    return data_obj.model_dump()
                return str(data_obj)
            elif hasattr(result, "json_data") and result.json_data:
                return result.json_data
            elif hasattr(result, "model_dump"):
                return result.model_dump()
            elif isinstance(result, dict):
                return result

            return {
                "page_url": url,
                "is_available": False,
                "note": "Page extraction returned empty response from scraper.",
            }
        except Exception as exc:
            logger.warning("ScrapeGraphAI extraction error for URL '{}': {}", url, exc)
            return {
                "page_url": url,
                "is_available": False,
                "error": str(exc),
                "note": "Failed to scrape page content.",
            }


class MockScraperClient(BaseScraperClient):
    """Mock scraper client providing deterministic extracted product payload for unit testing."""

    def extract(self, prompt: str, url: str, **kwargs: Any) -> Any:
        logger.info("Using MockScraperClient for URL: '{}'", url)
        return {
            "page_url": url,
            "product_title": "Mock Extracted Espresso Machine 1.8L",
            "product_image_url": "https://example.com/mock-image.jpg",
            "product_url": url,
            "is_available": True,
            "product_current_price": 7999.0,
            "product_original_price": 8999.0,
            "product_discount_percentage": 11.0,
            "product_specs": [
                {"specification_name": "Wattage", "specification_value": "1450 W"},
                {"specification_name": "Pump Pressure", "specification_value": "15 Bar"},
                {"specification_name": "Capacity", "specification_value": "1.8 L"},
            ],
            "agent_recommendation_rank": 5,
            "agent_recommendation_notes": [
                "Top tier build quality with stainless steel finish.",
                "Excellent value with 11% discount.",
            ],
        }
