"""Abstract base class for LLM provider strategies."""

from abc import ABC, abstractmethod
from typing import Any, Optional
from crewai import LLM


class BaseLLMProvider(ABC):
    """Abstract interface for constructing LLM instances."""

    @abstractmethod
    def create_llm(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> LLM:
        """Create and return a configured CrewAI LLM instance."""
        raise NotImplementedError
