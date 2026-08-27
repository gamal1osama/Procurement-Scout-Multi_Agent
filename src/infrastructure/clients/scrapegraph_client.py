"""Web scraping client adapters implementing Strategy and Adapter patterns."""

import os
import re
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

    def _normalize_extracted_payload(self, raw_data: Any, page_url: str) -> Dict[str, Any]:
        """Normalize ScrapeGraph extracted payload, ensuring clean numerical prices, booleans, and specs."""
        if not isinstance(raw_data, dict):
            return {
                "page_url": page_url,
                "is_available": False,
                "product_current_price": None,
                "product_original_price": None,
                "product_discount_percentage": None,
                "product_specs": [],
            }

        # 1. Normalize current price
        raw_price = (
            raw_data.get("product_current_price")
            or raw_data.get("price")
            or raw_data.get("current_price")
        )
        cleaned_price: Optional[float] = None
        if raw_price is not None:
            if isinstance(raw_price, (int, float)):
                cleaned_price = float(raw_price)
            elif isinstance(raw_price, str):
                nums = re.findall(r"[\d,]+(?:\.\d+)?", raw_price.replace(" ", ""))
                if nums:
                    best_num = max(nums, key=len).replace(",", "")
                    try:
                        cleaned_price = float(best_num)
                    except ValueError:
                        pass

        # 2. Normalize original price
        raw_orig = (
            raw_data.get("product_original_price")
            or raw_data.get("original_price")
            or raw_data.get("list_price")
        )
        cleaned_orig: Optional[float] = None
        if raw_orig is not None:
            if isinstance(raw_orig, (int, float)):
                cleaned_orig = float(raw_orig)
            elif isinstance(raw_orig, str):
                nums = re.findall(r"[\d,]+(?:\.\d+)?", raw_orig.replace(" ", ""))
                if nums:
                    best_num = max(nums, key=len).replace(",", "")
                    try:
                        cleaned_orig = float(best_num)
                    except ValueError:
                        pass

        # 3. Calculate discount percentage if missing
        discount = raw_data.get("product_discount_percentage") or raw_data.get("discount")
        if isinstance(discount, (int, float)):
            discount = float(discount)
        elif isinstance(discount, str):
            nums = re.findall(r"[\d.]+", discount)
            if nums:
                try:
                    discount = float(nums[0])
                except ValueError:
                    discount = None
        elif discount is None and cleaned_price and cleaned_orig and cleaned_orig > cleaned_price:
            discount = round(((cleaned_orig - cleaned_price) / cleaned_orig) * 100, 1)

        # 4. Normalize availability
        avail = raw_data.get("is_available")
        if avail is None:
            avail_str = str(raw_data.get("availability", "")).lower()
            if (
                "out of stock" in avail_str
                or "currently unavailable" in avail_str
                or "غير متوفر" in avail_str
            ):
                avail = False
            elif (
                "in stock" in avail_str
                or "left in stock" in avail_str
                or "order soon" in avail_str
                or "available" in avail_str
                or "متوفر" in avail_str
            ):
                avail = True
            elif cleaned_price is not None and cleaned_price > 0:
                avail = True
            else:
                avail = False
        elif isinstance(avail, str):
            avail = avail.lower() in ["true", "yes", "1", "in stock", "available"]
        else:
            avail = bool(avail)

        # 5. Normalize specifications
        specs = raw_data.get("product_specs") or raw_data.get("specs") or []
        normalized_specs = []
        if isinstance(specs, dict):
            for k, v in specs.items():
                normalized_specs.append({"specification_name": str(k), "specification_value": str(v)})
        elif isinstance(specs, list):
            for s in specs:
                if isinstance(s, dict):
                    name = str(
                        s.get("specification_name")
                        or s.get("name")
                        or s.get("key")
                        or s.get("title")
                        or ""
                    ).strip()
                    val = str(
                        s.get("specification_value")
                        or s.get("value")
                        or s.get("val")
                        or ""
                    ).strip()
                    if name:
                        normalized_specs.append(
                            {"specification_name": name, "specification_value": val}
                        )

        # Title & Image fallbacks
        title = raw_data.get("product_title") or raw_data.get("title") or ""
        img_url = raw_data.get("product_image_url") or raw_data.get("image_url") or raw_data.get("image") or ""
        prod_url = raw_data.get("product_url") or page_url

        return {
            "page_url": page_url,
            "product_title": title,
            "product_image_url": img_url,
            "product_url": prod_url,
            "is_available": avail,
            "product_current_price": cleaned_price,
            "product_original_price": cleaned_orig,
            "product_discount_percentage": discount,
            "product_specs": normalized_specs[:10],
        }

    def extract(self, prompt: str, url: str, **kwargs: Any) -> Any:
        """Execute AI web scraping extraction using ScrapeGraphAI and return a normalized dict."""
        try:
            logger.debug("Extracting data via ScrapeGraphAI from URL: '{}'", url)
            schema = kwargs.pop("schema", None)

            result = self._client.extract(
                prompt=prompt,
                url=url,
                schema=schema,
                **kwargs,
            )

            raw_payload = {}
            if hasattr(result, "data") and result.data is not None:
                data_obj = result.data
                if hasattr(data_obj, "json_data") and data_obj.json_data:
                    raw_payload = data_obj.json_data
                elif hasattr(data_obj, "model_dump"):
                    raw_payload = data_obj.model_dump()
            elif hasattr(result, "json_data") and result.json_data:
                raw_payload = result.json_data
            elif hasattr(result, "model_dump"):
                raw_payload = result.model_dump()
            elif isinstance(result, dict):
                raw_payload = result

            return self._normalize_extracted_payload(raw_payload, page_url=url)
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
