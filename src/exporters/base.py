"""Abstract base class for artifact exporters implementing the Strategy pattern."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseExporter(ABC):
    """Abstract interface for exporting workflow artifacts and deliverables."""

    @abstractmethod
    def export(self, data: Any, destination: str, **kwargs: Any) -> str:
        """Export data payload to the target destination path or storage sink.

        Returns the resolved path or URI of the exported artifact.
        """
        raise NotImplementedError
