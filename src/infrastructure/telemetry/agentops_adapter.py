"""Observability and telemetry adapter for AgentOps session management."""

import os
from typing import Optional
from src.core.config import Settings, get_settings
from src.core.logging import logger


class AgentOpsManager:
    """Manager for initializing, tracking, and finalizing AgentOps telemetry sessions."""

    _initialized: bool = False

    @classmethod
    def initialize(cls, settings: Optional[Settings] = None) -> bool:
        """Initialize AgentOps tracking if enabled in settings."""
        if cls._initialized:
            logger.debug("AgentOps is already initialized.")
            return True

        cfg = settings or get_settings()
        api_key = cfg.agentops_api_key or os.getenv("AGENTOPS_API_KEY")

        if not cfg.agentops_enabled and not api_key:
            logger.info("AgentOps telemetry is disabled or AGENTOPS_API_KEY is not configured.")
            return False

        try:
            import agentops

            logger.info("Initializing AgentOps observability session...")
            agentops.init(
                api_key=api_key,
                skip_auto_end_session=True,
            )
            cls._initialized = True
            logger.info("AgentOps observability initialized successfully.")
            return True
        except Exception as exc:
            logger.warning("Failed to initialize AgentOps observability: {}", exc)
            return False

    @classmethod
    def end_session(cls, end_state: str = "Success") -> None:
        """End the current AgentOps tracking session."""
        if not cls._initialized:
            return

        try:
            import agentops

            logger.info("Ending AgentOps session with state: '{}'", end_state)
            agentops.end_session(end_state=end_state)
            cls._initialized = False
        except Exception as exc:
            logger.warning("Failed to end AgentOps session cleanly: {}", exc)
