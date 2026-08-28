"""Domain models and schemas for product specifications and deep web scraping extraction.

Exact mirror of the notebook (Cell 18). Field title= values match the notebook exactly —
ScrapeGraphAI reads the JSON schema 'title' property as its extraction hint.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ── Exact notebook Cell 18 ────────────────────────────────────────────────────

class ProductSpec(BaseModel):
    specification_name: str
    specification_value: str


class SingleExtractedProduct(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    page_url: str = Field(..., title="The original url of the product page")

    product_title: str = Field(..., title="The title of the product")
    product_image_url: str = Field(..., title="The url of the product image")
    product_url: str = Field(..., title="The url of the product")

    is_available: bool = Field(
        ...,
        title=(
            "Whether the product is currently in stock / purchasable on the page. "
            "Set to False if the page shows 'Currently unavailable', 'Out of stock', or has no price."
        ),
    )

    product_current_price: Optional[float] = Field(
        title="The current price of the product", default=None
    )
    product_original_price: Optional[float] = Field(
        title="The original price of the product before discount. Set to None if no discount",
        default=None,
    )
    product_discount_percentage: Optional[float] = Field(
        title="The discount percentage of the product. Set to None if no discount",
        default=None,
    )

    # NOTE: notebook used Pydantic v1 min_items=1/max_items=5 on this field.
    # In Pydantic v2, min_length/max_length on List fields are enforced at validation time.
    # We keep it optional (default_factory) so the pipeline doesn't crash when ScrapeGraph
    # returns empty data due to credits/rate-limits. The LLM is still instructed to fill it.
    product_specs: List[ProductSpec] = Field(
        default_factory=list,
        title="The specifications of the product. Focus on the most important specs to compare.",
    )

    agent_recommendation_rank: int = Field(
        ...,
        title=(
            "The rank of the product to be considered in the final procurement report. "
            "(out of 5, Higher is Better) in the recommendation list ordering from the best to the worst"
        ),
    )
    agent_recommendation_notes: List[str] = Field(
        ...,
        title=(
            "A set of notes why would you recommend or not recommend this product "
            "to the company, compared to other products."
        ),
    )


class AllExtractedProducts(BaseModel):
    products: List[SingleExtractedProduct] = Field(default_factory=list)

