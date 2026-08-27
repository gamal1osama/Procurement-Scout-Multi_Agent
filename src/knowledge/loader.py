"""Knowledge loader for CrewAI knowledge sources and domain context."""

import os
from pathlib import Path
from typing import List, Optional
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource

from src.core.config import Settings, get_settings
from src.core.logging import logger


class KnowledgeLoader:
    """Loader for enterprise domain context and knowledge sources."""

    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()

    def load_company_context(self) -> StringKnowledgeSource:
        """Load company profile and context knowledge source."""
        context_file = self.settings.resolved_config_path / "knowledge" / "company_context.txt"

        if context_file.exists():
            with open(context_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
            logger.debug("Loaded company context from file: '{}'", context_file)
        else:
            content = (
                "Rankyx is a company that provides AI solutions to help websites refine their "
                "search and recommendation systems."
            )
            logger.warning("Company context file not found at '{}', using default fallback.", context_file)

        return StringKnowledgeSource(content=content)

    def load_all_knowledge_sources(self) -> List[BaseKnowledgeSource]:
        """Load all configured knowledge sources for the procurement crew."""
        sources: List[BaseKnowledgeSource] = []
        sources.append(self.load_company_context())
        return sources
