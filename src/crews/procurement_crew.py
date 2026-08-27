"""Main Procurement Crew orchestrator managing end-to-end multi-agent execution and deliverables."""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from crewai import Crew

from src.core.config import Settings, get_settings
from src.core.exceptions import AgentExecutionError
from src.core.logging import logger
from src.crews.base import BaseCrew
from src.crews.builder import ProcurementCrewBuilder
from src.domain.procurement import ExecutionMetrics, ProcurementInput, ProcurementResult


class ProcurementCrew(BaseCrew):
    """End-to-end multi-agent procurement intelligence workflow runner."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        output_dir: Optional[str] = None,
        builder: Optional[ProcurementCrewBuilder] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.output_dir = output_dir or str(self.settings.resolved_output_path)
        
        # Build the Crew instance
        crew_builder = builder or ProcurementCrewBuilder(settings=self.settings).with_output_dir(
            self.output_dir
        )
        crew_instance = crew_builder.build()
        super().__init__(crew=crew_instance)

    def _assemble_result(
        self,
        inputs: ProcurementInput,
        raw_output: Any,
        start_time: float,
        started_at: datetime,
    ) -> ProcurementResult:
        """Collect output artifact paths, calculate metrics, and construct ProcurementResult DTO."""
        duration = round(time.time() - start_time, 2)
        completed_at = datetime.now(timezone.utc)

        # File paths to intermediate and final artifacts
        step_1_file = os.path.join(self.output_dir, "step_1_suggested_search_queries.json")
        step_2_file = os.path.join(self.output_dir, "step_2_search_results.json")
        step_3_file = os.path.join(self.output_dir, "step_3_search_results.json")
        step_4_file = os.path.join(self.output_dir, "step_4_procurement_report.html")

        metrics = ExecutionMetrics(
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
        )

        return ProcurementResult(
            status="completed",
            input_params=inputs,
            metrics=metrics,
            step_1_queries_file=step_1_file if os.path.exists(step_1_file) else None,
            step_2_search_file=step_2_file if os.path.exists(step_2_file) else None,
            step_3_products_file=step_3_file if os.path.exists(step_3_file) else None,
            step_4_report_html_file=step_4_file if os.path.exists(step_4_file) else None,
            raw_output=str(raw_output),
        )

    def run(self, inputs: Optional[ProcurementInput] = None) -> ProcurementResult:
        """Execute the procurement crew workflow synchronously."""
        inp = inputs or ProcurementInput()
        self.pre_run(inp)
        start_time = time.time()
        started_at = datetime.now(timezone.utc)

        try:
            crew_inputs = inp.to_crew_inputs()
            logger.info("Kickoff Crew execution with inputs: {}", crew_inputs)
            raw_output = self.crew.kickoff(inputs=crew_inputs)
            self.post_run(raw_output)
            return self._assemble_result(inp, raw_output, start_time, started_at)
        except Exception as exc:
            self.post_run(None, error=exc)
            raise AgentExecutionError(f"Procurement Crew execution failed: {exc}") from exc

    async def kickoff_async(self, inputs: Optional[ProcurementInput] = None) -> ProcurementResult:
        """Execute the procurement crew workflow asynchronously."""
        inp = inputs or ProcurementInput()
        self.pre_run(inp)
        start_time = time.time()
        started_at = datetime.now(timezone.utc)

        try:
            crew_inputs = inp.to_crew_inputs()
            logger.info("Kickoff Async Crew execution with inputs: {}", crew_inputs)
            raw_output = await self.crew.kickoff_async(inputs=crew_inputs)
            self.post_run(raw_output)
            return self._assemble_result(inp, raw_output, start_time, started_at)
        except Exception as exc:
            self.post_run(None, error=exc)
            raise AgentExecutionError(f"Procurement Crew async execution failed: {exc}") from exc
