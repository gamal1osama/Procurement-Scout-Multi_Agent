"""Web scraping client adapters implementing Strategy and Adapter patterns."""

import os
import re
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from scrapegraph_py import ScrapeGraphAI
from scrapegraph_py.schemas import ExtractResponse, ApiResult

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError
from src.core.logging import logger


class BaseScraperClient(ABC):
    """Abstract base class for web scraping client adapters."""

    @abstractmethod
    def extract(self, prompt: str, url: str, **kwargs: Any) -> Any:
        """Extract structured information from a web page URL."""
        raise NotImplementedError


class ScrapeGraphClientAdapter(BaseScraperClient):
    """Adapter wrapping ScrapeGraphAI SDK — mirrors notebook usage exactly.

    The notebook does:
        details = scrape_client.extract(
            "Extract ```json\\n" + SingleExtractedProduct.schema_json() + "```\\nFrom the web page",
            url=page_url
        )

    ScrapeGraphAI.extract() returns ApiResult[ExtractResponse].
    ExtractResponse.json_data contains the structured dict ScrapeGraph extracted.
    We unpack json_data and return it as-is, with only minimal price/availability
    cleanup to handle currency strings and text availability phrases.
    """

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.api_key = self.settings.scrapegraph_api_key or os.getenv("SCRAPEGRAPH_API_KEY")

        if not self.api_key:
            raise ConfigurationError(
                "SCRAPEGRAPH_API_KEY is not configured but ScrapeGraph client was requested."
            )

        self._client = ScrapeGraphAI(api_key=self.api_key)
        logger.debug("Initialized ScrapeGraphClientAdapter.")

    @staticmethod
    def _parse_price(raw: Any) -> Optional[float]:
        """Parse a price value that may be a float already or a currency string like 'EGP 8,249.00'."""
        if raw is None:
            return None
        if isinstance(raw, (int, float)):
            return float(raw) if raw > 0 else None
        if isinstance(raw, str):
            # Strip currency symbols/text and commas, extract the number
            nums = re.findall(r"[\d,]+(?:\.\d+)?", raw.replace("\u200f", "").replace("\xa0", " "))
            if nums:
                best = max(nums, key=len).replace(",", "")
                try:
                    val = float(best)
                    return val if val > 0 else None
                except ValueError:
                    pass
        return None

    @staticmethod
    def _parse_availability(raw_avail: Any, raw_avail_text: Any, price: Optional[float]) -> bool:
        """Resolve is_available from ScrapeGraph's extracted value or availability text."""
        # Already a boolean
        if isinstance(raw_avail, bool):
            return raw_avail
        # String boolean
        if isinstance(raw_avail, str):
            low = raw_avail.lower().strip()
            if low in ("true", "yes", "1", "in stock", "available", "متوفر"):
                return True
            if low in ("false", "no", "0", "out of stock", "unavailable", "غير متوفر"):
                return False

        # Fall back to availability text field
        avail_str = str(raw_avail_text or "").lower()
        if any(kw in avail_str for kw in ("out of stock", "currently unavailable", "غير متوفر")):
            return False
        if any(kw in avail_str for kw in ("in stock", "left in stock", "order soon", "available", "متوفر")):
            return True

        # Last resort: if we got a price, the product is available
        if price is not None and price > 0:
            return True

        return False

    def _unpack_result(self, result: ApiResult) -> Dict[str, Any]:
        """Unpack an ApiResult[ExtractResponse] to the inner json_data dict."""
        if result.status == "error" or result.data is None:
            logger.warning("ScrapeGraph returned error status: {}", result.error)
            return {}

        data: ExtractResponse = result.data

        # Log warnings (e.g. bot_blocked, spa_shell) from ScrapeGraph metadata
        if hasattr(data, "metadata") and isinstance(data.metadata, dict):
            warnings = data.metadata.get("warnings") or []
            for w in warnings:
                reason = w.get("reason") if isinstance(w, dict) else str(w)
                logger.warning("ScrapeGraph fetch warning for URL: reason={}", reason)

        if data.json_data and isinstance(data.json_data, dict):
            return data.json_data

        logger.warning("ScrapeGraph returned empty json_data. raw snippet: {}", str(getattr(data, "raw", ""))[:200])
        return {}

    def extract(self, prompt: str, url: str, **kwargs: Any) -> Any:
        """Extract structured data from a URL — mirrors the notebook's scrape_client.extract() call.

        Adds retry logic (up to 3 attempts) with exponential backoff to handle ScrapeGraph
        rate limiting. A 2-second base delay is inserted before each request to avoid hammering
        the API when the scraping agent calls this tool many times in sequence.
        """
        # Small delay before every call to avoid rate limiting when scraping many URLs
        time.sleep(2)

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug("ScrapeGraphAI extracting URL: '{}' (attempt {}/{})", url, attempt, max_retries)

                result: ApiResult = self._client.extract(
                    prompt=prompt,
                    url=url,
                    **kwargs,
                )

                # Fast-fail on credit exhaustion — retrying won't help
                if result.status == "error" and result.error and "insufficient credits" in (result.error or "").lower():
                    logger.error("ScrapeGraph insufficient credits for URL '{}': {}", url, result.error)
                    return {"page_url": url, "is_available": False, "error": result.error}

                # Retry on rate limiting
                if result.status == "error" and result.error and "rate limit" in (result.error or "").lower():
                    wait = 2 ** attempt
                    logger.warning("ScrapeGraph rate limited for '{}'. Waiting {}s before retry...", url, wait)
                    time.sleep(wait)
                    continue

                raw: Dict[str, Any] = self._unpack_result(result)

                logger.info(
                    "ScrapeGraph raw payload keys for '{}': {}",
                    url,
                    list(raw.keys()) if raw else "EMPTY",
                )

                if not raw:
                    return {"page_url": url, "error": "ScrapeGraph returned empty payload"}

                # ── Minimal cleanup only ──────────────────────────────────────────────
                # 1. Price fields — parse currency strings to floats
                price = self._parse_price(
                    raw.get("product_current_price")
                    or raw.get("price")
                    or raw.get("current_price")
                    or raw.get("product_price")
                )
                orig_price = self._parse_price(
                    raw.get("product_original_price")
                    or raw.get("original_price")
                    or raw.get("list_price")
                )

                # 2. Discount percentage
                discount = raw.get("product_discount_percentage") or raw.get("discount")
                if isinstance(discount, str):
                    nums = re.findall(r"[\d.]+", discount)
                    discount = float(nums[0]) if nums else None
                elif isinstance(discount, (int, float)):
                    discount = float(discount)
                elif discount is None and price and orig_price and orig_price > price:
                    discount = round(((orig_price - price) / orig_price) * 100, 1)

                # 3. Availability
                is_avail = self._parse_availability(
                    raw.get("is_available"),
                    raw.get("availability") or raw.get("stock_status"),
                    price,
                )

                # ── Return the cleaned payload (all other fields passed through as-is) ─
                cleaned = dict(raw)  # preserve everything ScrapeGraph extracted
                cleaned["page_url"] = url
                cleaned["product_current_price"] = price
                cleaned["product_original_price"] = orig_price
                cleaned["product_discount_percentage"] = discount
                cleaned["is_available"] = is_avail
                if not cleaned.get("product_url"):
                    cleaned["product_url"] = url

                logger.info(
                    "Extracted '{}': price={}, orig={}, available={}",
                    url, price, orig_price, is_avail,
                )
                return cleaned

            except Exception as exc:
                logger.error("ScrapeGraphAI extraction error on attempt {}/{} for '{}': {}", attempt, max_retries, url, exc)
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                else:
                    return {"page_url": url, "is_available": False, "error": str(exc)}

        return {"page_url": url, "is_available": False, "error": "Max retries exceeded"}



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
