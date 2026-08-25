"""Web scraping client adapters implementing Strategy and Adapter patterns.

Provides full forward/backward compatibility across scrapegraph-py SDK versions.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# Multi-version compatibility import for scrapegraph-py SDK
try:
    from scrapegraph_py import Client as ScrapeGraphSDKClient
except ImportError:
    try:
        from scrapegraph_py import ScrapeGraphAI as ScrapeGraphSDKClient
    except ImportError:
        ScrapeGraphSDKClient = None

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
    """Adapter wrapping ScrapeGraphAI Client with error handling, logging, and version compatibility."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.api_key = self.settings.scrapegraph_api_key or os.getenv("SCRAPEGRAPH_API_KEY")

        if not self.api_key:
            raise ConfigurationError(
                "SCRAPEGRAPH_API_KEY is not configured but ScrapeGraph client was requested."
            )

        if ScrapeGraphSDKClient is None:
            raise ConfigurationError("scrapegraph-py package is not installed.")

        self._client = ScrapeGraphSDKClient(api_key=self.api_key)
        logger.debug("Initialized ScrapeGraphClientAdapter successfully.")

    def extract(self, prompt: str, url: str, **kwargs: Any) -> Any:
        """Execute AI web scraping extraction using ScrapeGraphAI.
        
        Handles both modern smartscraper() and legacy extract() methods transparently.
        """
        try:
            logger.debug("Extracting data via ScrapeGraphAI from URL: '{}'", url)
            output_schema = kwargs.pop("output_schema", None)

            # Check if modern smartscraper method is available
            if hasattr(self._client, "smartscraper"):
                response = self._client.smartscraper(
                    user_prompt=prompt,
                    website_url=url,
                    output_schema=output_schema,
                    **kwargs,
                )
                if hasattr(response, "result"):
                    return response.result
                if isinstance(response, dict) and "result" in response:
                    return response["result"]
                return response

            # Fallback to extract method (legacy SDK or custom wrapper)
            elif hasattr(self._client, "extract"):
                return self._client.extract(prompt, url=url, **kwargs)

            else:
                raise ScrapingProviderError(
                    "ScrapeGraphAI client does not support 'smartscraper' or 'extract' method."
                )

        except Exception as exc:
            logger.error("ScrapeGraphAI extraction failed for URL '{}': {}", url, exc)
            raise ScrapingProviderError(
                f"ScrapeGraphAI extraction failed for URL '{url}': {exc}",
                details={"url": url, "error": str(exc)},
            ) from exc


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
