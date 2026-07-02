from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_agent_commands_always_include_wright_command(client):
    response = await client.get("/api/agent/commands")

    assert response.status_code == 200
    commands = response.json()["commands"]
    assert commands[0] == {
        "name": "wright",
        "description": "Wright engineering platform: start, stop, open UI, doctor, catalog, info, install, and status",
        "prefix": "/",
    }


@pytest.mark.asyncio
async def test_agent_commands_do_not_duplicate_engine_wright_command(
    client, mock_agent_engine
):
    async def get_commands():
        return [
            SimpleNamespace(
                name="wright",
                description="Engine-provided Wright command",
            )
        ]

    mock_agent_engine.get_commands = get_commands

    response = await client.get("/api/agent/commands")

    assert response.status_code == 200
    commands = response.json()["commands"]
    wright_commands = [
        command
        for command in commands
        if command["prefix"] == "/" and command["name"] == "wright"
    ]
    assert wright_commands == [
        {
            "name": "wright",
            "description": "Engine-provided Wright command",
            "prefix": "/",
        }
    ]
