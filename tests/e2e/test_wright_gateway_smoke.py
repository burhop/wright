def test_wright_gateway_happy_path_smoke(offline_api_client, gateway_smoke_seed):
    list_response = offline_api_client.get("/api/gateway/tools")

    assert list_response.status_code == 200
    tools = list_response.json()["tools"]
    assert tools == [
        {
            "name": gateway_smoke_seed["tool_name"],
            "description": "Ping smoke tool",
            "inputSchema": {"type": "object"},
        }
    ]

    call_response = offline_api_client.post(
        "/api/gateway/call",
        json={"name": gateway_smoke_seed["tool_name"], "arguments": {"ping": True}},
    )

    assert call_response.status_code == 200
    assert call_response.json() == {}
