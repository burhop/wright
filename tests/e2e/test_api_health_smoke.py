def test_api_health_smoke(offline_api_client):
    response = offline_api_client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["state"] == "connected"
