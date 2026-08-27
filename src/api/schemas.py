"""API Request and Response schemas for the FastAPI REST interface."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.domain.procurement import ProcurementInput, ProcurementResult


class ProcureRequest(BaseModel):
    """Request payload to initiate a multi-agent procurement workflow."""

    product_name: str = Field(
        default="coffee machine for office",
        description="Target product or equipment name to search and evaluate.",
    )
    websites_list: List[str] = Field(
        default_factory=lambda: ["www.amazon.eg", "www.jumia.com.eg", "www.noon.com/egypt-en"],
        description="List of target store domains to search across.",
    )
    country_name: str = Field(
        default="Egypt",
        description="Target country market.",
    )
    no_keywords: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum search keywords to generate.",
    )
    language: str = Field(
        default="English",
        description="Language for search and context.",
    )
    score_th: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Relevance score threshold.",
    )
    top_recommendations_no: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Number of top products to include in final procurement report.",
    )

    def to_domain_input(self) -> ProcurementInput:
        """Convert API request to domain input DTO."""
        return ProcurementInput(
            product_name=self.product_name,
            websites_list=self.websites_list,
            country_name=self.country_name,
            no_keywords=self.no_keywords,
            language=self.language,
            score_th=self.score_th,
            top_recommendations_no=self.top_recommendations_no,
        )


class ProcureResponse(BaseModel):
    """Response payload returned upon completion of procurement run."""

    status: str
    product_name: str
    duration_seconds: Optional[float] = None
    step_1_queries_file: Optional[str] = None
    step_2_search_file: Optional[str] = None
    step_3_products_file: Optional[str] = None
    step_4_report_html_file: Optional[str] = None
    report_download_url: Optional[str] = None

    @classmethod
    def from_domain_result(cls, result: ProcurementResult, base_url: str = "") -> "ProcureResponse":
        report_url = None
        if result.step_4_report_html_file:
            report_url = f"{base_url}/api/v1/reports/step_4_procurement_report.html"

        return cls(
            status=result.status,
            product_name=result.input_params.product_name,
            duration_seconds=result.metrics.duration_seconds,
            step_1_queries_file=result.step_1_queries_file,
            step_2_search_file=result.step_2_search_file,
            step_3_products_file=result.step_3_products_file,
            step_4_report_html_file=result.step_4_report_html_file,
            report_download_url=report_url,
        )


class HealthResponse(BaseModel):
    """System health check response payload."""

    status: str = "healthy"
    version: str = "1.0.0"
    app_env: str
    llm_provider: str
    llm_model: str
    search_provider: str
    scraper_provider: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ToolInfo(BaseModel):
    """Tool metadata descriptor."""

    name: str
    description: str
