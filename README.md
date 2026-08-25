# 🛒 Enterprise Multi-Agent Procurement Intelligence System

A production-grade, modular, and extensible Multi-Agent Procurement System built with [CrewAI](https://crewai.com). The system automates product discovery, single-product web search, deep web scraping, structured data extraction, and executive HTML procurement report authoring.

---

## 🌟 Architecture & Key Design Patterns

- **Factory Pattern**: `LLMFactory`, `EmbeddingFactory`, `AgentFactory`, `TaskFactory`, and `ToolFactory` ensure zero vendor lock-in.
- **Strategy Pattern**: Pluggable search providers (Tavily / SerpAPI), scraping engines (ScrapeGraphAI / Playwright), and export sinks (HTML, JSON, S3).
- **Registry Pattern**: `ToolRegistry` allows dynamic discovery and registration of tools.
- **Builder Pattern**: `ProcurementCrewBuilder` constructs dynamic pipelines.
- **Declarative Configuration**: All agent roles, goals, backstories, and task descriptions are managed via YAML files (`config/agents.yaml`, `config/tasks.yaml`).

---

## 🚀 Quickstart

### 1. Installation
```bash
# Clone and enter workspace
cd abubakr-crewai

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and supply your API keys (OPENROUTER_API_KEY, TAVILY_API_KEY, SCRAPEGRAPH_API_KEY, AGENTOPS_API_KEY)
```

### 3. Run via CLI
```bash
# Run with default inputs
python -m src.main

# Run with custom parameters
python -m src.cli run --product "ergonomic office chair" --country "Egypt" --top-n 10
```

### 4. Run via REST API (FastAPI)
```bash
# Start FastAPI server
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

---

## 📂 Project Structure
Refer to [plan.md](plan.md) for the complete architectural breakdown and design specifications.
