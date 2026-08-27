"""Unit tests for configuration manager and Settings model."""

import os
from pathlib import Path
from src.core.config import Settings, get_settings


def test_default_settings():
    settings = get_settings()
    assert settings.app_env in ["development", "production", "testing"]
    assert settings.llm_provider is not None
    assert isinstance(settings.resolved_output_path, Path)
    assert isinstance(settings.resolved_config_path, Path)


def test_settings_overrides(temp_output_dir):
    custom_settings = Settings(
        app_env="testing",
        log_level="DEBUG",
        output_dir=str(temp_output_dir),
        llm_provider="ollama",
        llm_model="ollama/llama3",
        search_provider="mock",
    )
    assert custom_settings.app_env == "testing"
    assert custom_settings.log_level == "DEBUG"
    assert custom_settings.llm_provider == "ollama"
    assert custom_settings.llm_model == "ollama/llama3"
    assert custom_settings.search_provider == "mock"
    assert custom_settings.resolved_output_path == temp_output_dir
