"""Integration tests for ProcurementCrew end-to-end orchestration pipeline."""

import os
from unittest.mock import patch
from src.crews.builder import ProcurementCrewBuilder
from src.crews.procurement_crew import ProcurementCrew
from src.domain.procurement import ProcurementInput


def test_procurement_crew_mock_execution(test_settings, mock_llm, test_tool_registry, temp_output_dir):
    builder = (
        ProcurementCrewBuilder(settings=test_settings)
        .with_llm(mock_llm)
        .with_tool_registry(test_tool_registry)
        .with_output_dir(str(temp_output_dir))
    )

    crew_runner = ProcurementCrew(
        settings=test_settings,
        output_dir=str(temp_output_dir),
        builder=builder,
    )

    mock_html_content = (
        "<!DOCTYPE html><html><body><h1>Coffee Machine Procurement Report</h1></body></html>"
    )

    # Create dummy artifact files to verify file path resolution
    step_1 = temp_output_dir / "step_1_suggested_search_queries.json"
    step_1.write_text('{"queries": []}', encoding="utf-8")
    
    step_4 = temp_output_dir / "step_4_procurement_report.html"
    step_4.write_text(mock_html_content, encoding="utf-8")

    inp = ProcurementInput(
        product_name="coffee machine for office",
        websites_list=["www.amazon.eg"],
        country_name="Egypt",
    )

    with patch("crewai.Crew.kickoff", return_value=mock_html_content):
        result = crew_runner.run(inputs=inp)

    assert result.status == "completed"
    assert result.input_params.product_name == "coffee machine for office"
    assert result.step_1_queries_file == str(step_1)
    assert result.step_4_report_html_file == str(step_4)
    assert result.metrics.duration_seconds is not None
    assert "Procurement Report" in result.raw_output
