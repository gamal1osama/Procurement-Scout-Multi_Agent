"""Central application configuration using Pydantic Settings."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # General Application Settings
    app_env: Literal["development", "production", "testing"] = Field(
        default="development",
        alias="APP_ENV",
        description="Current runtime environment",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Structured logging level",
    )
    output_dir: str = Field(
        default="./outputs",
        alias="OUTPUT_DIR",
        description="Directory where workflow artifacts (JSON, HTML) are saved",
    )
    config_dir: str = Field(
        default=str(BASE_DIR / "config"),
        alias="CONFIG_DIR",
        description="Directory containing YAML configurations and knowledge bases",
    )

    # LLM Settings
    llm_provider: str = Field(
        default="openrouter",
        alias="LLM_PROVIDER",
        description="LLM provider name (openrouter, openai, anthropic, ollama, azure)",
    )
    llm_model: str = Field(
        default="openrouter/stealth/ox-alpha",
        alias="LLM_MODEL",
        description="Model identifier (e.g. openrouter/stealth/ox-alpha, gpt-4o, claude-3-5-sonnet)",
    )
    llm_temperature: float = Field(
        default=0.0,
        alias="LLM_TEMPERATURE",
        description="Sampling temperature for LLM generation",
    )
    openrouter_api_key: Optional[str] = Field(
        default=None,
        alias="OPENROUTER_API_KEY",
        description="API key for OpenRouter provider",
    )
    openrouter_api_base: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_API_BASE",
        description="Base URL for OpenRouter API",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        alias="OPENAI_API_KEY",
        description="API key for OpenAI provider",
    )

    # Embeddings Settings
    embedding_provider: str = Field(
        default="openrouter",
        alias="EMBEDDING_PROVIDER",
        description="Provider for vector embeddings (openrouter, openai, custom)",
    )
    embedding_model: str = Field(
        default="nvidia/llama-nemotron-embed-vl-1b-v2:free",
        alias="EMBEDDING_MODEL",
        description="Model name used for embeddings",
    )

    # Search Provider Settings
    search_provider: Literal["tavily", "mock"] = Field(
        default="tavily",
        alias="SEARCH_PROVIDER",
        description="Search engine provider (tavily, mock)",
    )
    tavily_api_key: Optional[str] = Field(
        default=None,
        alias="TAVILY_API_KEY",
        description="API key for Tavily search",
    )

    # Web Scraping Provider Settings
    scraper_provider: Literal["scrapegraph", "mock"] = Field(
        default="scrapegraph",
        alias="SCRAPER_PROVIDER",
        description="Web scraping provider (scrapegraph, mock)",
    )
    scrapegraph_api_key: Optional[str] = Field(
        default=None,
        alias="SCRAPEGRAPH_API_KEY",
        description="API key for ScrapeGraphAI",
    )

    # Observability & Telemetry Settings
    agentops_enabled: bool = Field(
        default=False,
        alias="AGENTOPS_ENABLED",
        description="Whether AgentOps telemetry is enabled",
    )
    agentops_api_key: Optional[str] = Field(
        default=None,
        alias="AGENTOPS_API_KEY",
        description="API key for AgentOps observability",
    )

    # FastAPI Server Settings
    api_host: str = Field(
        default="0.0.0.0",
        alias="API_HOST",
        description="FastAPI binding host",
    )
    api_port: int = Field(
        default=8000,
        alias="API_PORT",
        description="FastAPI binding port",
    )

    @property
    def resolved_output_path(self) -> Path:
        """Returns the resolved absolute Path object for outputs."""
        path = Path(self.output_dir)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def resolved_config_path(self) -> Path:
        """Returns the resolved absolute Path object for config files."""
        path = Path(self.config_dir)
        if not path.is_absolute():
            path = BASE_DIR / path
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton getter for application settings."""
    return Settings()
