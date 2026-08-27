"""Shared pytest fixtures and test doubles for unit and integration testing."""

import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import tempfile
from typing import Generator
import pytest
from crewai import LLM
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.core.config import Settings
from src.infrastructure.clients import MockScraperClient, MockSearchClient
from src.infrastructure.llm.base import BaseLLMProvider
from src.tools.registry import ToolRegistry


class DummyLLMProvider(BaseLLMProvider):
    """Test double LLM provider that avoids outbound network calls."""

    def create_llm(self, model_name=None, temperature=None, **kwargs) -> LLM:
        return LLM(
            model=model_name or "openrouter/stealth/ox-alpha",
            temperature=temperature or 0.0,
            api_key="mock-test-key",
            base_url="https://mock.llm.api/v1",
        )


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Provide an isolated temporary directory for test artifact outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_settings(temp_output_dir: Path) -> Settings:
    """Provide isolated application settings configured for test execution."""
    return Settings(
        app_env="testing",
        log_level="DEBUG",
        output_dir=str(temp_output_dir),
        search_provider="mock",
        scraper_provider="mock",
        agentops_enabled=False,
    )


@pytest.fixture
def mock_llm() -> LLM:
    """Provide a mock LLM instance."""
    return DummyLLMProvider().create_llm()


@pytest.fixture
def mock_search_client() -> MockSearchClient:
    """Provide a mock search engine client."""
    return MockSearchClient()


@pytest.fixture
def mock_scraper_client() -> MockScraperClient:
    """Provide a mock web scraper client."""
    return MockScraperClient()


@pytest.fixture
def test_tool_registry(
    test_settings: Settings,
    mock_search_client: MockSearchClient,
    mock_scraper_client: MockScraperClient,
) -> ToolRegistry:
    """Provide a ToolRegistry preloaded with mock tools."""
    registry = ToolRegistry(settings=test_settings)
    from src.tools.search_tool import SearchEngineTool
    from src.tools.scraper_tool import WebScrapingTool

    registry.register(SearchEngineTool(search_client=mock_search_client, settings=test_settings))
    registry.register(WebScrapingTool(scraper_client=mock_scraper_client, settings=test_settings))
    return registry


@pytest.fixture
def api_client(test_settings: Settings) -> TestClient:
    """Provide a FastAPI test client with test settings injected."""
    app = create_app(settings=test_settings)
    return TestClient(app)
