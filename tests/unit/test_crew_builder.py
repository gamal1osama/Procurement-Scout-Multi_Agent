"""Unit tests for AgentFactory, TaskFactory, and ProcurementCrewBuilder."""

from src.agents.factory import AgentFactory
from src.crews.builder import ProcurementCrewBuilder
from src.knowledge.loader import KnowledgeLoader
from src.tasks.factory import TaskFactory


def test_agent_factory(test_settings, mock_llm, test_tool_registry):
    factory = AgentFactory(
        settings=test_settings,
        llm=mock_llm,
        tool_registry=test_tool_registry,
    )
    agents = factory.create_all_agents()
    assert len(agents) == 4
    assert agents["search_engine_agent"].tools is not None
    assert agents["scraping_agent"].tools is not None


def test_task_factory(test_settings, mock_llm, test_tool_registry, temp_output_dir):
    agent_factory = AgentFactory(
        settings=test_settings,
        llm=mock_llm,
        tool_registry=test_tool_registry,
    )
    agents_map = agent_factory.create_all_agents()

    task_factory = TaskFactory(settings=test_settings, output_dir=str(temp_output_dir))
    tasks = task_factory.create_all_tasks(agents_map=agents_map)
    assert len(tasks) == 4
    assert tasks[0].output_json is not None
    assert tasks[1].output_json is not None
    assert tasks[2].output_json is not None


def test_knowledge_loader(test_settings):
    loader = KnowledgeLoader(settings=test_settings)
    company_src = loader.load_company_context()
    assert "Rankyx" in company_src.content


def test_crew_builder(test_settings, mock_llm, test_tool_registry, temp_output_dir):
    builder = (
        ProcurementCrewBuilder(settings=test_settings)
        .with_llm(mock_llm)
        .with_tool_registry(test_tool_registry)
        .with_output_dir(str(temp_output_dir))
    )
    crew = builder.build()
    assert len(crew.agents) == 4
    assert len(crew.tasks) == 4
    assert len(crew.knowledge_sources) >= 1
