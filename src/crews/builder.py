"""Builder for constructing configured CrewAI Crew instances with all dependencies injected."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from crewai import Agent, Crew, LLM, Process, Task
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

from src.agents.factory import AgentFactory
from src.core.config import Settings, get_settings
from src.core.logging import logger
from src.infrastructure.embeddings.factory import EmbeddingFactory
from src.infrastructure.llm.factory import LLMFactory
from src.knowledge.loader import KnowledgeLoader
from src.tasks.factory import TaskFactory
from src.tools.registry import ToolRegistry


class ProcurementCrewBuilder:
    """Builder pattern implementation to assemble and configure a production-ready Procurement Crew."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.output_dir: str = str(self.settings.resolved_output_path)
        self.llm: Optional[LLM] = None
        self.tool_registry: Optional[ToolRegistry] = None
        self.knowledge_sources: Optional[List[BaseKnowledgeSource]] = None
        self.embedder_config: Optional[Dict[str, Any]] = None
        self.process: Process = Process.sequential
        self.agents: Optional[List[Agent]] = None
        self.tasks: Optional[List[Task]] = None

    def with_settings(self, settings: Settings) -> "ProcurementCrewBuilder":
        self.settings = settings
        return self

    def with_output_dir(self, output_dir: str) -> "ProcurementCrewBuilder":
        self.output_dir = output_dir
        return self

    def with_llm(self, llm: LLM) -> "ProcurementCrewBuilder":
        self.llm = llm
        return self

    def with_tool_registry(self, registry: ToolRegistry) -> "ProcurementCrewBuilder":
        self.tool_registry = registry
        return self

    def with_knowledge_sources(
        self, sources: List[BaseKnowledgeSource]
    ) -> "ProcurementCrewBuilder":
        self.knowledge_sources = sources
        return self

    def with_embedder_config(self, embedder: Dict[str, Any]) -> "ProcurementCrewBuilder":
        self.embedder_config = embedder
        return self

    def with_process(self, process: Process) -> "ProcurementCrewBuilder":
        self.process = process
        return self

    def build(self) -> Crew:
        """Construct, validate, and return the fully assembled Crew instance."""
        logger.info("Building Procurement Crew pipeline...")

        # 1. Resolve LLM
        llm = self.llm or LLMFactory.create(settings=self.settings)

        # 2. Resolve Tool Registry
        tool_registry = self.tool_registry or ToolRegistry(settings=self.settings)

        # 3. Resolve Agents via AgentFactory
        agent_factory = AgentFactory(
            settings=self.settings,
            llm=llm,
            tool_registry=tool_registry,
        )
        agents_map = agent_factory.create_all_agents()
        agents_list = [
            agents_map["search_queries_recommendation_agent"],
            agents_map["search_engine_agent"],
            agents_map["scraping_agent"],
            agents_map["procurement_report_author_agent"],
        ]

        # 4. Resolve Tasks via TaskFactory
        task_factory = TaskFactory(
            settings=self.settings,
            output_dir=self.output_dir,
        )
        tasks_list = task_factory.create_all_tasks(
            agents_map=agents_map,
            output_dir_override=self.output_dir,
        )

        # 5. Resolve Knowledge Sources
        knowledge_sources = self.knowledge_sources
        if knowledge_sources is None:
            knowledge_loader = KnowledgeLoader(settings=self.settings)
            knowledge_sources = knowledge_loader.load_all_knowledge_sources()

        # 6. Resolve Knowledge Embedder Configuration
        embedder_config = self.embedder_config
        if embedder_config is None:
            try:
                embedder_config = EmbeddingFactory.create_crew_embedder_config(
                    settings=self.settings
                )
            except Exception as exc:
                logger.warning(
                    "Could not initialize custom embedding config ({}). Falling back to default.",
                    exc,
                )
                embedder_config = None

        crew_kwargs: Dict[str, Any] = {
            "agents": agents_list,
            "tasks": tasks_list,
            "process": self.process,
            "knowledge_sources": knowledge_sources,
        }

        if embedder_config:
            crew_kwargs["embedder"] = embedder_config

        logger.info(
            "Procurement Crew successfully assembled: {} agents, {} tasks, sequential process.",
            len(agents_list),
            len(tasks_list),
        )
        return Crew(**crew_kwargs)
