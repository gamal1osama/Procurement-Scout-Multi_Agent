"""Task Factory implementing Factory Method pattern for creating decoupled CrewAI Tasks."""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from crewai import Agent, Task
from pydantic import BaseModel

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError
from src.core.logging import logger
from src.domain.product import AllExtractedProducts
from src.domain.search import AllSearchResults, SuggestedSearchQueries


class TaskFactory:
    """Factory responsible for instantiating and configuring CrewAI Tasks from YAML definitions."""

    # Schema mapping registry from string identifiers to Pydantic domain models
    SCHEMA_MAP: Dict[str, Type[BaseModel]] = {
        "SuggestedSearchQueries": SuggestedSearchQueries,
        "AllSearchResults": AllSearchResults,
        "AllExtractedProducts": AllExtractedProducts,
    }

    def __init__(
        self,
        settings: Optional[Settings] = None,
        output_dir: Optional[str] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.output_dir = output_dir or str(self.settings.resolved_output_path)
        self._configs: Dict[str, Any] = self._load_task_configs()

    def _load_task_configs(self) -> Dict[str, Any]:
        """Load and parse the declarative tasks.yaml configuration file."""
        config_path = self.settings.resolved_config_path / "tasks.yaml"
        if not config_path.exists():
            raise ConfigurationError(f"Task configuration file not found at: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                configs = yaml.safe_load(f) or {}
            logger.debug("Successfully loaded task configurations from: '{}'", config_path)
            return configs
        except Exception as exc:
            raise ConfigurationError(
                f"Failed to parse task YAML configuration '{config_path}': {exc}"
            ) from exc

    def create_task(
        self,
        task_key: str,
        agent: Agent,
        output_dir_override: Optional[str] = None,
        **kwargs: Any,
    ) -> Task:
        """Create a single Task instance by key, binding it to the provided Agent."""
        if task_key not in self._configs:
            available = ", ".join(self._configs.keys())
            raise ConfigurationError(
                f"Task key '{task_key}' not found in configuration. Available keys: [{available}]"
            )

        task_cfg = self._configs[task_key].copy()
        description = task_cfg.get("description", "").strip()
        expected_output = task_cfg.get("expected_output", "").strip()
        output_file_name = task_cfg.get("output_file")
        schema_name = task_cfg.get("output_schema")

        # Resolve output file path
        target_output_dir = output_dir_override or self.output_dir
        os.makedirs(target_output_dir, exist_ok=True)
        output_file_path = (
            os.path.join(target_output_dir, output_file_name) if output_file_name else None
        )

        # Resolve output schema
        output_json_schema: Optional[Type[BaseModel]] = None
        if schema_name:
            output_json_schema = self.SCHEMA_MAP.get(schema_name)
            if not output_json_schema:
                logger.warning("Unrecognized output schema name '{}' in task '{}'", schema_name, task_key)

        logger.info("Instantiating Task: key='{}', output_file='{}'", task_key, output_file_name)
        task_kwargs: Dict[str, Any] = {
            "description": description,
            "expected_output": expected_output,
            "agent": agent,
            **kwargs,
        }

        if output_file_path:
            task_kwargs["output_file"] = output_file_path

        if output_json_schema:
            task_kwargs["output_json"] = output_json_schema

        return Task(**task_kwargs)

    def create_all_tasks(
        self,
        agents_map: Dict[str, Agent],
        output_dir_override: Optional[str] = None,
    ) -> List[Task]:
        """Create the standard sequential ordered list of tasks for the procurement workflow."""
        tasks: List[Task] = []
        task_order = [
            ("search_queries_recommendation_task", "search_queries_recommendation_agent"),
            ("search_engine_task", "search_engine_agent"),
            ("scraping_task", "scraping_agent"),
            ("procurement_report_author_task", "procurement_report_author_agent"),
        ]

        for task_key, agent_key in task_order:
            if agent_key not in agents_map:
                raise ConfigurationError(
                    f"Required agent '{agent_key}' not found in agents_map to construct task '{task_key}'"
                )
            agent = agents_map[agent_key]
            tasks.append(self.create_task(task_key, agent=agent, output_dir_override=output_dir_override))

        return tasks
