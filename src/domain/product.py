"""Domain models and schemas for product specifications and deep web scraping extraction."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductSpec(BaseModel):
    """Key-value pair representing a specific product specification or technical feature."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    specification_name: str = Field(
        ...,
        description="The name or label of the specification (e.g., Wattage, Pump Pressure).",
    )
    specification_value: str = Field(
        ...,
        description="The value of the specification (e.g., 1450 W, 15 Bar).",
    )


class SingleExtractedProduct(BaseModel):
    """Schema representing structured product details extracted via deep web scraping."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    page_url: str = Field(..., description="The original URL of the product page.")
    product_title: str = Field(..., description="The title or full name of the product.")
    product_image_url: str = Field(..., description="The direct URL of the primary product image.")
    product_url: str = Field(..., description="The canonical or direct product purchase URL.")

    is_available: bool = Field(
        ...,
        description=(
            "Whether the product is currently in stock and purchasable. "
            "False if the page indicates 'Currently unavailable' or 'Out of stock'."
        ),
    )

    product_current_price: Optional[float] = Field(
        default=None,
        description="The current listed selling price of the product.",
    )
    product_original_price: Optional[float] = Field(
        default=None,
        description="The original price before discount. None if no discount.",
    )
    product_discount_percentage: Optional[float] = Field(
        default=None,
        description="The discount percentage (0-100). None if no discount.",
    )

    product_specs: List[ProductSpec] = Field(
        default_factory=list,
        description="Key specifications of the product to facilitate comparison.",
    )

    agent_recommendation_rank: int = Field(
        ...,
        ge=1,
        le=5,
        description="Agent recommendation rank (1 to 5, where 5 is best).",
    )
    agent_recommendation_notes: List[str] = Field(
        default_factory=list,
        description="Justification notes explaining why this product is recommended or not.",
    )


class AllExtractedProducts(BaseModel):
    """Schema aggregating all extracted and scored products."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    products: List[SingleExtractedProduct] = Field(
        default_factory=list,
        description="List of extracted, structured products.",
    )
