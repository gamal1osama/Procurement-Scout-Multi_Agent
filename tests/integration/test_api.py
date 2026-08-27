"""Integration tests for FastAPI endpoints."""

def test_api_health(api_client):
    response = api_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"


def test_api_list_tools(api_client):
    response = api_client.get("/api/v1/tools")
    assert response.status_code == 200
    tools = response.json()
    assert len(tools) >= 2
    tool_names = [t["name"] for t in tools]
    assert "search_engine_tool" in tool_names
    assert "web_scraping_tool" in tool_names


def test_api_get_report_not_found(api_client):
    response = api_client.get("/api/v1/reports/non_existent_report.html")
    assert response.status_code == 404
