"""Base tool classes extending CrewAI BaseTool with error handling and logging."""

from typing import Any, Dict, Optional, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from src.core.logging import logger


class BaseProcurementTool(BaseTool):
    """Abstract base tool for procurement multi-agent operations with logging and error containment."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    def execute_safely(self, operation_name: str, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """Helper to run tool operations safely with logging."""
        try:
            logger.debug("Executing tool '{}' operation with args={}, kwargs={}", self.name, args, kwargs)
            result = fn(*args, **kwargs)
            logger.debug("Tool '{}' completed successfully.", self.name)
            return result
        except Exception as exc:
            logger.error("Error in tool '{}': {}", self.name, exc)
            return {
                "error": True,
                "tool": self.name,
                "message": str(exc),
            }
