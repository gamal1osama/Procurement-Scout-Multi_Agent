"""Domain models and schemas for product specifications and deep web scraping extraction.

NOTE: Field `title=` values are intentionally matched to the notebook's original schema.
ScrapeGraphAI uses the JSON schema `title` property as its extraction hint when scraping pages.
Using only `description=` causes ScrapeGraph to miss fields like price and availability.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductSpec(BaseModel):
    """Key-value pair representing a specific product specification or technical feature."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    specification_name: str
    specification_value: str


class SingleExtractedProduct(BaseModel):
    """Schema representing structured product details extracted via deep web scraping."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    # title= fields are the extraction hints ScrapeGraphAI reads from the JSON schema.
    # These match exactly the notebook's implementation that produced correct output.
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
        title="The current price of the product",
        default=None,
    )
    product_original_price: Optional[float] = Field(
        title="The original price of the product before discount. Set to None if no discount",
        default=None,
    )
    product_discount_percentage: Optional[float] = Field(
        title="The discount percentage of the product. Set to None if no discount",
        default=None,
    )

    product_specs: List[ProductSpec] = Field(
        ...,
        title="The specifications of the product. Focus on the most important specs to compare.",
        min_length=1,
        max_length=5,
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
    """Schema aggregating all extracted and scored products."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    products: List[SingleExtractedProduct] = Field(
        default_factory=list,
        description="List of extracted, structured products.",
    )
