import pytest
import os
import tempfile
import yaml
import respx
import httpx
from hermes_plugin_wright.bridge import (
    detect_repo_dir,
    check_api_health,
    get_mcp_servers,
    register_mcp_server,
    get_workspaces,
    get_credential_status,
    WRIGHT_API_BASE,
)
from hermes_plugin_wright.schemas import CatalogEntry


def test_detect_repo_dir(monkeypatch):
    # Mock home directory using a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setenv("HOME", tmpdir)

        # Test case 1: profile config exists
        profile_dir = os.path.join(tmpdir, ".hermes", "profiles", "wright")
        os.makedirs(profile_dir, exist_ok=True)
        config_path = os.path.join(profile_dir, "config.yaml")

        mock_config = {
            "mcp_servers": {
                "wrightgateway": {
                    "args": ["run", "--project", "/home/burhop/repos/wright", "python"]
                }
            }
        }
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(mock_config, f)

        # Force detect_repo_dir to expand the mocked HOME path
        # By monkeypatching os.path.expanduser
        original_expanduser = os.path.expanduser
        monkeypatch.setattr(
            os.path,
            "expanduser",
            lambda path: path.replace("~", tmpdir) if path.startswith("~") else original_expanduser(path)
        )

        repo_dir = detect_repo_dir()
        assert repo_dir == "/home/burhop/repos/wright"

        # Test case 2: fall back to default config.yaml
        os.remove(config_path)
        default_config_path = os.path.join(tmpdir, ".hermes", "config.yaml")
        with open(default_config_path, "w", encoding="utf-8") as f:
            yaml.dump(mock_config, f)

        repo_dir = detect_repo_dir()
        assert repo_dir == "/home/burhop/repos/wright"

        # Test case 3: missing configs
        os.remove(default_config_path)
        repo_dir = detect_repo_dir()
        assert repo_dir is None


@respx.mock
@pytest.mark.asyncio
async def test_check_api_health():
    # Success Case
    route = respx.get(f"{WRIGHT_API_BASE}/api/health").mock(
        return_value=httpx.Response(200, json={"state": "connected", "latencyMs": 1.5})
    )
    result = await check_api_health()
    assert result["success"] is True
    assert result["connected"] is True
    assert result["state"] == "connected"
    assert result["latencyMs"] == 1.5
    assert route.called

    # Error Case
    route_error = respx.get(f"{WRIGHT_API_BASE}/api/health").mock(
        side_effect=httpx.ConnectError("Connection refused")
    )
    result_error = await check_api_health()
    assert result_error["success"] is False
    assert result_error["connected"] is False
    assert "Connection refused" in result_error["error"]


@respx.mock
@pytest.mark.asyncio
async def test_get_mcp_servers():
    mock_servers = [
        {"server_id": "test-id", "name": "Test Server", "type": "stdio", "is_active": True}
    ]
    route = respx.get(f"{WRIGHT_API_BASE}/api/mcp/servers").mock(
        return_value=httpx.Response(200, json={"servers": mock_servers})
    )
    result = await get_mcp_servers()
    assert result["success"] is True
    assert len(result["servers"]) == 1
    assert result["servers"][0]["name"] == "Test Server"


@respx.mock
@pytest.mark.asyncio
async def test_register_mcp_server():
    entry = CatalogEntry(
        id="test-tool",
        name="Test Tool",
        vendor="Test",
        description="A test tool",
        domains=["cad"],
        transport="stdio",
        command=["python", "test.py"],
        locality="local",
        weight="light",
    )
    route = respx.post(f"{WRIGHT_API_BASE}/api/mcp/servers").mock(
        return_value=httpx.Response(201, json={"server_id": "new-server-uuid"})
    )
    result = await register_mcp_server(entry)
    assert result["success"] is True
    assert result["server_id"] == "new-server-uuid"
    assert route.called

    # Check that payload contains serialized entry details
    request = route.calls.last.request
    import json

    payload = json.loads(request.content)
    assert payload["name"] == "Test Tool"
    assert payload["type"] == "stdio"


@respx.mock
@pytest.mark.asyncio
async def test_get_workspaces():
    mock_workspaces = [
        {"id": "ws-1", "name": "Workspace 1", "local_path": "/path/to/ws"}
    ]
    route = respx.get(f"{WRIGHT_API_BASE}/api/workspace/list").mock(
        return_value=httpx.Response(200, json={"workspaces": mock_workspaces})
    )
    result = await get_workspaces()
    assert result["success"] is True
    assert len(result["workspaces"]) == 1


@respx.mock
@pytest.mark.asyncio
async def test_get_credential_status():
    route = respx.get(f"{WRIGHT_API_BASE}/api/mcp/servers/test-id/credentials").mock(
        return_value=httpx.Response(200, json={"credentials": {"API_KEY": True}})
    )
    result = await get_credential_status("test-id")
    assert result["success"] is True
    assert result["credentials"]["API_KEY"] is True
