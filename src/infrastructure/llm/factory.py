"""LLM Factory implementing Factory Method and Strategy patterns for interchangeable LLM providers."""

import os
from typing import Any, Dict, Optional, Type
from crewai import LLM

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError, LLMProviderError
from src.core.logging import logger
from src.infrastructure.llm.base import BaseLLMProvider


class OpenRouterLLMProvider(BaseLLMProvider):
    """LLM Provider for OpenRouter models."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api_key = self.settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
        self.api_base = self.settings.openrouter_api_base or "https://openrouter.ai/api/v1"

    def create_llm(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> LLM:
        model = model_name or self.settings.llm_model
        temp = temperature if temperature is not None else self.settings.llm_temperature

        if not self.api_key:
            raise ConfigurationError(
                "OPENROUTER_API_KEY is not set but OpenRouter LLM provider was requested."
            )

        # Set environment variable for LiteLLM / CrewAI internal resolution
        os.environ["OPENROUTER_API_KEY"] = self.api_key
        os.environ["OPENROUTER_API_BASE"] = self.api_base

        logger.info("Initializing OpenRouter LLM: model='{}', temp={}", model, temp)
        return LLM(
            model=model,
            temperature=temp,
            api_key=self.api_key,
            base_url=self.api_base,
            **kwargs,
        )


class OpenAILLMProvider(BaseLLMProvider):
    """LLM Provider for OpenAI native models."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.api_key = self.settings.openai_api_key or os.getenv("OPENAI_API_KEY")

    def create_llm(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> LLM:
        model = model_name or "openai/gpt-4o"
        temp = temperature if temperature is not None else self.settings.llm_temperature

        if not self.api_key:
            raise ConfigurationError(
                "OPENAI_API_KEY is not set but OpenAI LLM provider was requested."
            )

        os.environ["OPENAI_API_KEY"] = self.api_key
        logger.info("Initializing OpenAI LLM: model='{}', temp={}", model, temp)
        return LLM(
            model=model,
            temperature=temp,
            api_key=self.api_key,
            **kwargs,
        )


class OllamaLLMProvider(BaseLLMProvider):
    """LLM Provider for local Ollama instances."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create_llm(
        self,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> LLM:
        model = model_name or "ollama/llama3"
        temp = temperature if temperature is not None else self.settings.llm_temperature
        base_url = kwargs.pop("base_url", "http://localhost:11434")

        logger.info("Initializing Ollama LLM: model='{}', base_url='{}'", model, base_url)
        return LLM(
            model=model,
            temperature=temp,
            base_url=base_url,
            **kwargs,
        )


class LLMFactory:
    """Factory for creating LLM instances based on configuration or runtime overrides."""

    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "openrouter": OpenRouterLLMProvider,
        "openai": OpenAILLMProvider,
        "ollama": OllamaLLMProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_cls: Type[BaseLLMProvider]) -> None:
        """Register a custom LLM provider strategy at runtime."""
        cls._providers[name.lower()] = provider_cls
        logger.debug("Registered custom LLM provider strategy: '{}'", name.lower())

    @classmethod
    def create(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        settings: Optional[Settings] = None,
        **kwargs: Any,
    ) -> LLM:
        """Create and return a configured CrewAI LLM instance."""
        cfg = settings or get_settings()
        provider_name = (provider or cfg.llm_provider).lower()

        provider_cls = cls._providers.get(provider_name)
        if not provider_cls:
            supported = ", ".join(cls._providers.keys())
            raise LLMProviderError(
                f"Unsupported LLM provider '{provider_name}'. Supported providers: {supported}"
            )

        provider_instance = provider_cls(settings=cfg)
        return provider_instance.create_llm(
            model_name=model_name,
            temperature=temperature,
            **kwargs,
        )
