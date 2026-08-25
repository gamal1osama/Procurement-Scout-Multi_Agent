"""Domain models and DTOs for procurement workflow inputs, execution state, and final deliverables."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class ProcurementInput(BaseModel):
    """Input parameters required to execute a procurement intelligence workflow."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    product_name: str = Field(
        default="coffee machine for office",
        description="The target product or equipment category to search and procure.",
    )
    websites_list: List[str] = Field(
        default_factory=lambda: ["www.amazon.eg", "www.jumia.com.eg", "www.noon.com/egypt-en"],
        description="Target e-commerce store domains to restrict queries and searches to.",
    )
    country_name: str = Field(
        default="Egypt",
        description="Target country or geographic market for product availability and currency.",
    )
    no_keywords: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum number of varied search keywords/queries to formulate.",
    )
    language: str = Field(
        default="English",
        description="Language for search keywords and reporting context.",
    )
    score_th: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Relevance score threshold below which search results are discarded.",
    )
    top_recommendations_no: int = Field(
        default=15,
        ge=1,
        le=100,
        description="Maximum number of top products to extract, score, and include in the final report.",
    )

    def to_crew_inputs(self) -> Dict[str, Any]:
        """Convert input model to dictionary mapping expected by CrewAI task placeholders."""
        return {
            "product_name": self.product_name,
            "websites_list": self.websites_list,
            "country_name": self.country_name,
            "no_keywords": self.no_keywords,
            "language": self.language,
            "score_th": self.score_th,
            "top_recommendations_no": self.top_recommendations_no,
        }


class ExecutionMetrics(BaseModel):
    """Execution telemetry and timing metrics for a workflow run."""

    model_config = ConfigDict(extra="ignore")

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(default=None)
    duration_seconds: Optional[float] = Field(default=None)
    total_queries_generated: int = Field(default=0)
    total_search_results_found: int = Field(default=0)
    total_products_extracted: int = Field(default=0)


class ProcurementResult(BaseModel):
    """Complete deliverable returned upon completion of the procurement workflow."""

    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="completed", description="Execution status: completed, failed, etc.")
    input_params: ProcurementInput
    metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
    
    # Generated artifact file paths
    step_1_queries_file: Optional[str] = Field(default=None)
    step_2_search_file: Optional[str] = Field(default=None)
    step_3_products_file: Optional[str] = Field(default=None)
    step_4_report_html_file: Optional[str] = Field(default=None)
    
    raw_output: Optional[str] = Field(default=None, description="Raw text output from the final agent/crew.")
