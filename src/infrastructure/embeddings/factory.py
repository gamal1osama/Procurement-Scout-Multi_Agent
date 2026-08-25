"""Embedding function factory for vector stores and CrewAI knowledge sources."""

import os
from typing import Any, Dict, Optional
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError, EmbeddingError
from src.core.logging import logger


class EmbeddingFactory:
    """Factory for creating vector embedding functions and CrewAI embedder configurations."""

    @classmethod
    def create_embedding_function(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> Any:
        """Create a ChromaDB-compatible embedding function."""
        cfg = settings or get_settings()
        prov = (provider or cfg.embedding_provider).lower()
        model = model_name or cfg.embedding_model

        if prov == "openrouter":
            api_key = cfg.openrouter_api_key or os.getenv("OPENROUTER_API_KEY")
            api_base = cfg.openrouter_api_base or "https://openrouter.ai/api/v1"
            if not api_key:
                raise ConfigurationError(
                    "OPENROUTER_API_KEY is required for OpenRouter embedding function."
                )
            logger.info("Initializing OpenRouter Chroma EmbeddingFunction with model='{}'", model)
            return OpenAIEmbeddingFunction(
                api_key=api_key,
                api_base=api_base,
                model_name=model,
            )

        elif prov == "openai":
            api_key = cfg.openai_api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ConfigurationError("OPENAI_API_KEY is required for OpenAI embedding function.")
            logger.info("Initializing OpenAI Chroma EmbeddingFunction with model='{}'", model)
            return OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name=model or "text-embedding-3-small",
            )

        else:
            raise EmbeddingError(f"Unsupported embedding provider: '{prov}'")

    @classmethod
    def create_crew_embedder_config(
        cls,
        provider: Optional[str] = None,
        model_name: Optional[str] = None,
        settings: Optional[Settings] = None,
    ) -> Dict[str, Any]:
        """Create the embedder dictionary configuration expected by CrewAI."""
        embedding_fn = cls.create_embedding_function(
            provider=provider,
            model_name=model_name,
            settings=settings,
        )
        return {
            "provider": "custom",
            "config": {
                "embedder": embedding_fn,
            },
        }
