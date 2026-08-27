"""FastAPI REST API routes and endpoints."""

import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse

from src.api.schemas import HealthResponse, ProcureRequest, ProcureResponse, ToolInfo
from src.core.config import Settings, get_settings
from src.core.logging import logger
from src.crews.procurement_crew import ProcurementCrew
from src.tools.registry import ToolRegistry

router = APIRouter(prefix="/api/v1", tags=["Procurement"])


@router.get("/health", response_model=HealthResponse, summary="Service Health Check")
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Returns application health, environment, and configured AI providers."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        app_env=settings.app_env,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        search_provider=settings.search_provider,
        scraper_provider=settings.scraper_provider,
    )


@router.get("/tools", response_model=List[ToolInfo], summary="List Available Tools")
async def list_tools(settings: Settings = Depends(get_settings)) -> List[ToolInfo]:
    """Returns all registered CrewAI tools in the ToolRegistry."""
    registry = ToolRegistry(settings=settings)
    tools: List[ToolInfo] = []
    for tool_name in registry.list_tools():
        try:
            tool_obj = registry.get(tool_name)
            tools.append(ToolInfo(name=tool_name, description=tool_obj.description))
        except Exception:
            tools.append(ToolInfo(name=tool_name, description="Tool registered in factory."))
    return tools


@router.post("/procure", response_model=ProcureResponse, summary="Execute Procurement Workflow")
async def execute_procurement(
    payload: ProcureRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> ProcureResponse:
    """Trigger the end-to-end multi-agent procurement workflow."""
    logger.info("Received procurement API request for: '{}'", payload.product_name)
    domain_input = payload.to_domain_input()

    try:
        crew_runner = ProcurementCrew(settings=settings)
        result = await crew_runner.kickoff_async(inputs=domain_input)
        
        base_url = str(request.base_url).rstrip("/")
        return ProcureResponse.from_domain_result(result, base_url=base_url)
    except Exception as exc:
        logger.error("API Procurement execution error: {}", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Procurement workflow execution failed: {str(exc)}",
        ) from exc


@router.get("/reports/{report_name}", summary="View or Download Generated Reports")
async def get_report(
    report_name: str,
    settings: Settings = Depends(get_settings),
):
    """Serve generated HTML report or JSON artifacts."""
    output_dir = settings.resolved_output_path
    file_path = output_dir / report_name

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report file '{report_name}' not found in outputs directory.",
        )

    if report_name.endswith(".html"):
        return FileResponse(file_path, media_type="text/html")
    elif report_name.endswith(".json"):
        return FileResponse(file_path, media_type="application/json")
    else:
        return FileResponse(file_path)
