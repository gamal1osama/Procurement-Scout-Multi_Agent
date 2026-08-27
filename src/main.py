"""Main application entrypoint executing the default procurement intelligence workflow."""

import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.core.config import get_settings
from src.core.logging import logger, setup_logging
from src.crews.procurement_crew import ProcurementCrew
from src.domain.procurement import ProcurementInput


def main() -> None:
    """Execute the procurement workflow with default inputs matching the notebook."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level)

    logger.info("Initializing Enterprise Multi-Agent Procurement System...")

    # Default parameters mirroring the notebook workflow
    inputs = ProcurementInput(
        product_name="coffee machine for office",
        websites_list=["www.amazon.eg", "www.jumia.com.eg", "www.noon.com/egypt-en"],
        country_name="Egypt",
        no_keywords=10,
        language="English",
        score_th=0.3,
        top_recommendations_no=15,
    )

    try:
        runner = ProcurementCrew(settings=settings)
        result = runner.run(inputs=inputs)

        logger.info("=" * 60)
        logger.info("PROCUREMENT INTELLIGENCE WORKFLOW COMPLETED")
        logger.info("=" * 60)
        logger.info("Status: {}", result.status)
        logger.info("Execution Time: {}s", result.metrics.duration_seconds)
        logger.info("Step 1 (Queries): {}", result.step_1_queries_file)
        logger.info("Step 2 (Search Results): {}", result.step_2_search_file)
        logger.info("Step 3 (Extracted Products): {}", result.step_3_products_file)
        logger.info("Step 4 (HTML Report): {}", result.step_4_report_html_file)
        logger.info("=" * 60)

    except Exception as exc:
        logger.critical("Fatal error executing procurement workflow: {}", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
