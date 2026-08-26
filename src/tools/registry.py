"""Tool Registry implementing the Registry Pattern for dynamic discovery and injection of tools."""

from typing import Any, Callable, Dict, List, Optional
from crewai.tools import BaseTool

from src.core.config import Settings, get_settings
from src.core.logging import logger
from src.tools.search_tool import SearchEngineTool
from src.tools.scraper_tool import WebScrapingTool


class ToolRegistry:
    """Registry managing available CrewAI tools, supporting dynamic registration and dependency injection."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self._tools: Dict[str, BaseTool] = {}
        self._factories: Dict[str, Callable[[], BaseTool]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default out-of-the-box system tools."""
        self.register_factory("search_engine_tool", lambda: SearchEngineTool(settings=self.settings))
        self.register_factory("web_scraping_tool", lambda: WebScrapingTool(settings=self.settings))
        logger.debug("Default tools registered in ToolRegistry: search_engine_tool, web_scraping_tool")

    def register(self, tool: BaseTool, name: Optional[str] = None) -> None:
        """Register an instantiated BaseTool."""
        tool_name = name or getattr(tool, "name", str(tool))
        self._tools[tool_name] = tool
        logger.info("Registered tool instance: '{}'", tool_name)

    def register_factory(self, name: str, factory: Callable[[], BaseTool]) -> None:
        """Register a factory function for lazy tool instantiation."""
        self._factories[name] = factory
        logger.debug("Registered tool factory: '{}'", name)

    def get(self, name: str) -> BaseTool:
        """Retrieve a tool by name, instantiating from factory if necessary."""
        if name in self._tools:
            return self._tools[name]

        if name in self._factories:
            tool_instance = self._factories[name]()
            self._tools[name] = tool_instance
            return tool_instance

        available = ", ".join(self.list_tools())
        raise KeyError(f"Tool '{name}' not found in ToolRegistry. Available tools: [{available}]")

    def get_tools_for_agent(self, tool_names: List[str]) -> List[BaseTool]:
        """Resolve and return a list of tool instances for specified tool names."""
        resolved: List[BaseTool] = []
        for name in tool_names:
            resolved.append(self.get(name))
        return resolved

    def list_tools(self) -> List[str]:
        """List all available tool names in the registry."""
        names = set(self._tools.keys()).union(set(self._factories.keys()))
        return sorted(list(names))
