"""Abstract base crew defining lifecycle hooks and execution template."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from crewai import Crew

from src.core.logging import logger
from src.domain.procurement import ProcurementInput, ProcurementResult
from src.infrastructure.telemetry.agentops_adapter import AgentOpsManager


class BaseCrew(ABC):
    """Abstract base class for all multi-agent workflows implementing Template Method Pattern."""

    def __init__(self, crew: Crew) -> None:
        self.crew = crew

    def pre_run(self, inputs: ProcurementInput) -> None:
        """Pre-execution hook: logging, validation, telemetry initialization."""
        logger.info(
            "Starting Procurement Workflow for product: '{}' across {} stores in {}",
            inputs.product_name,
            len(inputs.websites_list),
            inputs.country_name,
        )
        AgentOpsManager.initialize()

    def post_run(self, result: Any, error: Optional[Exception] = None) -> None:
        """Post-execution hook: telemetry finalization, cleanup, completion logging."""
        if error:
            logger.error("Procurement Workflow failed with error: {}", error)
            AgentOpsManager.end_session(end_state="Fail")
        else:
            logger.info("Procurement Workflow completed successfully.")
            AgentOpsManager.end_session(end_state="Success")

    @abstractmethod
    def run(self, inputs: ProcurementInput) -> ProcurementResult:
        """Execute the workflow synchronously."""
        raise NotImplementedError

    @abstractmethod
    async def kickoff_async(self, inputs: ProcurementInput) -> ProcurementResult:
        """Execute the workflow asynchronously."""
        raise NotImplementedError
