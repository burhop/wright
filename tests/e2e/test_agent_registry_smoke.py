from agent_adapters import default_agent_registry


def test_agent_registry_default_smoke(offline_api_client):
    assert default_agent_registry().default_provider().name == "hermes"

    response = offline_api_client.get("/api/agent/active")

    assert response.status_code == 200
    assert response.json() == {"agent": "hermes"}
