import pytest


@pytest.mark.asyncio
async def test_agent_health_includes_connection_details(client, mock_agent_engine):
    async def disconnected_health():
        return {
            "state": "disconnected",
            "latencyMs": 0.0,
            "baseUrl": "http://127.0.0.1:8642",
            "error": "connection refused",
        }

    mock_agent_engine.check_health = disconnected_health

    response = await client.get("/api/agent/health")

    assert response.status_code == 200
    assert response.json() == {
        "state": "disconnected",
        "latencyMs": 0.0,
        "baseUrl": "http://127.0.0.1:8642",
        "error": "connection refused",
    }
