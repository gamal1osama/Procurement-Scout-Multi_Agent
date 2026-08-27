"""Unit tests for search and scraping tools and ToolRegistry."""

import pytest
from src.tools.registry import ToolRegistry
from src.tools.scraper_tool import WebScrapingTool
from src.tools.search_tool import SearchEngineTool


def test_search_engine_tool(mock_search_client):
    tool = SearchEngineTool(search_client=mock_search_client)
    res = tool._run(query="site:www.amazon.eg coffee machine")
    assert "results" in res
    assert len(res["results"]) > 0


def test_web_scraping_tool(mock_scraper_client):
    tool = WebScrapingTool(scraper_client=mock_scraper_client)
    res = tool._run(page_url="https://www.noon.com/egypt-en/p/123")
    assert "details" in res
    assert res["page_url"] == "https://www.noon.com/egypt-en/p/123"
    assert res["details"]["is_available"] is True


def test_tool_registry(test_tool_registry):
    tools = test_tool_registry.list_tools()
    assert "search_engine_tool" in tools
    assert "web_scraping_tool" in tools

    resolved = test_tool_registry.get_tools_for_agent(["search_engine_tool", "web_scraping_tool"])
    assert len(resolved) == 2

    with pytest.raises(KeyError):
        test_tool_registry.get("unregistered_tool_name")
