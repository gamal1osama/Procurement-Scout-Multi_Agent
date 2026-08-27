"""FastAPI Application Factory for the Procurement Intelligence Service."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.core.config import Settings, get_settings
from src.core.exceptions import ProcurementError
from src.core.logging import logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifespan events."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level)
    logger.info("Starting Procurement Intelligence API in {} mode...", settings.app_env)
    yield
    logger.info("Shutting down Procurement Intelligence API.")


def create_app(settings: Settings = None) -> FastAPI:
    """Create and configure the FastAPI application instance."""
    cfg = settings or get_settings()

    app = FastAPI(
        title="Procurement Intelligence Multi-Agent API",
        description=(
            "Enterprise Multi-Agent Procurement System built with CrewAI. "
            "Automates product discovery, single-product web search, deep web scraping, "
            "structured data extraction, and executive HTML procurement report authoring."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router)

    # Custom domain exception handler
    @app.exception_handler(ProcurementError)
    async def procurement_error_handler(request: Request, exc: ProcurementError) -> JSONResponse:
        logger.error("Handled ProcurementError: {}", exc)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": True,
                "message": exc.message,
                "details": exc.details,
            },
        )

    return app


# Default app instance for ASGI servers (uvicorn src.api.app:app)
app = create_app()
