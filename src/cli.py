"""Command Line Interface for the Procurement Intelligence System."""

import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from typing import List, Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.config import get_settings
from src.core.logging import logger, setup_logging
from src.crews.procurement_crew import ProcurementCrew
from src.domain.procurement import ProcurementInput
from src.tools.registry import ToolRegistry

app = typer.Typer(
    name="procure",
    help="Enterprise Multi-Agent Procurement Intelligence System CLI",
    add_completion=False,
)
console = Console()


@app.command(name="run")
def run_procurement(
    product: str = typer.Option(
        "coffee machine for office",
        "--product",
        "-p",
        help="Target product name or equipment to search and procure.",
    ),
    country: str = typer.Option(
        "Egypt",
        "--country",
        "-c",
        help="Target country market.",
    ),
    websites: str = typer.Option(
        "www.amazon.eg,www.jumia.com.eg,www.noon.com/egypt-en",
        "--websites",
        "-w",
        help="Comma-separated target e-commerce store domains.",
    ),
    keywords: int = typer.Option(
        10,
        "--keywords",
        "-k",
        help="Maximum search keywords to generate.",
    ),
    language: str = typer.Option(
        "English",
        "--language",
        "-l",
        help="Language for search queries and reporting.",
    ),
    score_th: float = typer.Option(
        0.3,
        "--score-th",
        "-s",
        help="Confidence score threshold for search results.",
    ),
    top_n: int = typer.Option(
        15,
        "--top-n",
        "-n",
        help="Number of top product recommendations.",
    ),
    output_dir: str = typer.Option(
        "./outputs",
        "--output-dir",
        "-o",
        help="Directory to save generated artifacts.",
    ),
) -> None:
    """Execute the multi-agent procurement workflow."""
    settings = get_settings()
    setup_logging(log_level=settings.log_level)

    website_list = [w.strip() for w in websites.split(",") if w.strip()]

    console.print(
        Panel.fit(
            f"[bold blue]Procurement Intelligence System[/bold blue]\n"
            f"[green]Product:[/green] {product}\n"
            f"[green]Target Market:[/green] {country}\n"
            f"[green]Stores:[/green] {', '.join(website_list)}\n"
            f"[green]Output Directory:[/green] {output_dir}",
            title="🛒 Multi-Agent Workflow Kickoff",
            border_style="blue",
        )
    )

    procurement_input = ProcurementInput(
        product_name=product,
        websites_list=website_list,
        country_name=country,
        no_keywords=keywords,
        language=language,
        score_th=score_th,
        top_recommendations_no=top_n,
    )

    try:
        crew_runner = ProcurementCrew(settings=settings, output_dir=output_dir)
        result = crew_runner.run(inputs=procurement_input)

        console.print("\n[bold green]✅ Procurement Workflow Completed Successfully![/bold green]")
        
        table = Table(title="Generated Deliverables & Artifacts", show_header=True, header_style="bold magenta")
        table.add_column("Step", style="dim")
        table.add_column("Artifact Description")
        table.add_column("File Path", style="cyan")

        if result.step_1_queries_file:
            table.add_row("Step 1", "Suggested Search Queries (JSON)", result.step_1_queries_file)
        if result.step_2_search_file:
            table.add_row("Step 2", "Single-Product Search Results (JSON)", result.step_2_search_file)
        if result.step_3_products_file:
            table.add_row("Step 3", "Extracted & Ranked Products (JSON)", result.step_3_products_file)
        if result.step_4_report_html_file:
            table.add_row("Step 4", "Executive Procurement Report (HTML)", result.step_4_report_html_file)

        console.print(table)
        if result.metrics.duration_seconds:
            console.print(f"\n[dim]Total Execution Time: {result.metrics.duration_seconds}s[/dim]")

    except Exception as exc:
        console.print(f"\n[bold red]❌ Execution Error:[/bold red] {exc}")
        sys.exit(1)


@app.command(name="list-tools")
def list_tools() -> None:
    """List all registered tools in the dynamic ToolRegistry."""
    registry = ToolRegistry()
    table = Table(title="Registered Multi-Agent Tools", show_header=True, header_style="bold blue")
    table.add_column("Tool Identifier", style="bold green")
    table.add_column("Description")

    for tool_name in registry.list_tools():
        try:
            tool_obj = registry.get(tool_name)
            table.add_row(tool_name, tool_obj.description)
        except Exception:
            table.add_row(tool_name, "Registered in ToolRegistry factory")

    console.print(table)


@app.command(name="validate-config")
def validate_config() -> None:
    """Validate system configuration, YAML prompt files, and knowledge sources."""
    settings = get_settings()
    console.print("[bold blue]Validating system configuration and declarative files...[/bold blue]")

    agents_yaml = settings.resolved_config_path / "agents.yaml"
    tasks_yaml = settings.resolved_config_path / "tasks.yaml"
    context_txt = settings.resolved_config_path / "knowledge" / "company_context.txt"

    table = Table(title="Configuration Validation Summary", show_header=True)
    table.add_column("Component", style="bold")
    table.add_column("Status")
    table.add_column("Path / Details", style="dim")

    table.add_row("Agents Config", "✅ Found" if agents_yaml.exists() else "❌ Missing", str(agents_yaml))
    table.add_row("Tasks Config", "✅ Found" if tasks_yaml.exists() else "❌ Missing", str(tasks_yaml))
    table.add_row("Company Context", "✅ Found" if context_txt.exists() else "❌ Missing", str(context_txt))
    table.add_row("LLM Provider", f"✅ {settings.llm_provider}", settings.llm_model)
    table.add_row("Search Provider", f"✅ {settings.search_provider}", "Tavily" if settings.tavily_api_key else "Mock/Missing Key")
    table.add_row("Scraper Provider", f"✅ {settings.scraper_provider}", "ScrapeGraphAI" if settings.scrapegraph_api_key else "Mock/Missing Key")

    console.print(table)


if __name__ == "__main__":
    app()
