"""Agent Factory implementing the Factory Method pattern for creating decoupled CrewAI Agents."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from crewai import Agent, LLM

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError
from src.core.logging import logger
from src.infrastructure.llm.factory import LLMFactory
from src.tools.registry import ToolRegistry


class AgentFactory:
    """Factory responsible for instantiating and configuring CrewAI Agents from YAML definitions."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        llm: Optional[LLM] = None,
        tool_registry: Optional[ToolRegistry] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.tool_registry = tool_registry or ToolRegistry(settings=self.settings)
        self.llm = llm or LLMFactory.create(settings=self.settings)
        self._configs: Dict[str, Any] = self._load_agent_configs()

    def _load_agent_configs(self) -> Dict[str, Any]:
        """Load and parse the declarative agents.yaml configuration file."""
        config_path = self.settings.resolved_config_path / "agents.yaml"
        if not config_path.exists():
            raise ConfigurationError(f"Agent configuration file not found at: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                configs = yaml.safe_load(f) or {}
            logger.debug("Successfully loaded agent configurations from: '{}'", config_path)
            return configs
        except Exception as exc:
            raise ConfigurationError(
                f"Failed to parse agent YAML configuration '{config_path}': {exc}"
            ) from exc

    def create_agent(
        self,
        agent_key: str,
        llm_override: Optional[LLM] = None,
        extra_tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> Agent:
        """Create a single Agent instance by its configuration key."""
        if agent_key not in self._configs:
            available = ", ".join(self._configs.keys())
            raise ConfigurationError(
                f"Agent key '{agent_key}' not found in configuration. Available keys: [{available}]"
            )

        agent_cfg = self._configs[agent_key].copy()
        role = agent_cfg.get("role", "")
        goal = agent_cfg.get("goal", "")
        backstory = agent_cfg.get("backstory", "")
        verbose = agent_cfg.get("verbose", True)
        tool_names = agent_cfg.get("tools", [])

        # Resolve tools via ToolRegistry
        tools = self.tool_registry.get_tools_for_agent(tool_names)
        if extra_tools:
            tools.extend(extra_tools)

        # Determine LLM
        agent_llm = llm_override or self.llm

        logger.info("Instantiating Agent: key='{}', role='{}'", agent_key, role)
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=verbose,
            tools=tools,
            llm=agent_llm,
            **kwargs,
        )

    def create_all_agents(self) -> Dict[str, Agent]:
        """Instantiate and return all agents defined in the configuration."""
        agents: Dict[str, Agent] = {}
        for key in self._configs.keys():
            agents[key] = self.create_agent(key)
        return agents

    # Typed convenience getters for standard procurement workflow agents
    def get_search_queries_recommender(self, **kwargs: Any) -> Agent:
        return self.create_agent("search_queries_recommendation_agent", **kwargs)

    def get_search_engine_agent(self, **kwargs: Any) -> Agent:
        return self.create_agent("search_engine_agent", **kwargs)

    def get_scraping_agent(self, **kwargs: Any) -> Agent:
        return self.create_agent("scraping_agent", **kwargs)

    def get_procurement_report_author(self, **kwargs: Any) -> Agent:
        return self.create_agent("procurement_report_author_agent", **kwargs)
