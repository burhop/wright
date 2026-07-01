def test_mcp_listing_smoke(offline_api_client):
    response = offline_api_client.get("/api/mcp/servers")

    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert any(
        server["server_id"] == "openscad-mcp-server" for server in data["servers"]
    )
