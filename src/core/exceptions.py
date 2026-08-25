"""Domain and infrastructure exception hierarchy for the Procurement System."""

from typing import Optional


class ProcurementError(Exception):
    """Base exception for all domain-specific errors in the procurement system."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ConfigurationError(ProcurementError):
    """Raised when application or environment configuration is invalid or missing."""


class LLMProviderError(ProcurementError):
    """Raised when an LLM provider fails to initialize or generate responses."""


class EmbeddingError(ProcurementError):
    """Raised when embedding model or knowledge source processing encounters an error."""


class SearchProviderError(ProcurementError):
    """Raised when web search operations fail or return unexpected status codes."""


class ScrapingProviderError(ProcurementError):
    """Raised when deep web extraction/scraping fails or schema extraction is invalid."""


class AgentExecutionError(ProcurementError):
    """Raised when an agent encounters an unrecoverable failure during execution."""


class TaskExecutionError(ProcurementError):
    """Raised when task execution or output validation fails."""


class ExportError(ProcurementError):
    """Raised when exporting deliverables (JSON, HTML, S3) encounters an error."""
