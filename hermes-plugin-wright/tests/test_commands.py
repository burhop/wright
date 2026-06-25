import pytest
import os
import tempfile
import yaml
import respx
import httpx
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from hermes_plugin_wright.commands import register_commands, WRIGHT_HELP_TEXT
from hermes_plugin_wright.catalog import CatalogLoader

def test_register_commands():
    ctx = MagicMock()
    catalog = MagicMock(spec=CatalogLoader)
    
    register_commands(ctx, catalog)
    
    ctx.register_command.assert_called_once()
    name, handler = ctx.register_command.call_args[1]["name"], ctx.register_command.call_args[1]["handler"]
    assert name == "wright"
    
    # Test help fallback
    handler_result = asyncio.run(handler(""))
    assert handler_result == WRIGHT_HELP_TEXT


@pytest.mark.asyncio
async def test_handle_start_already_running():
    from hermes_plugin_wright.commands import handle_start
    with patch("hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock) as mock_health, \
         patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open:
        
        mock_health.return_value = True
        res = await handle_start()
        assert "already running" in res
        mock_open.assert_called_once_with("http://localhost:8000")


@pytest.mark.asyncio
async def test_handle_start_success():
    from hermes_plugin_wright.commands import handle_start
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "apps", "web", "dist"), exist_ok=True)
        
        with patch("hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock) as mock_health, \
             patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=tmpdir), \
             patch("hermes_plugin_wright.commands.subprocess.Popen") as mock_popen, \
             patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open:
            
            mock_health.side_effect = [False, True]
            
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.poll.return_value = None
            mock_popen.return_value = mock_proc
            
            res = await handle_start()
            assert "🚀 Wright is running!" in res
            assert "PID:     12345" in res
            mock_popen.assert_called_once()
            mock_open.assert_called_once()

            # Close the open log file handle to prevent file locking on Windows
            if mock_popen.call_args:
                stdout_file = mock_popen.call_args[1].get("stdout")
                if stdout_file and hasattr(stdout_file, "close"):
                    stdout_file.close()
            
            pid_file = os.path.join(tmpdir, "tmp", "wright-api.pid")
            assert os.path.exists(pid_file)
            with open(pid_file, "r") as f:
                assert f.read() == "12345"


@pytest.mark.asyncio
async def test_handle_stop_success():
    from hermes_plugin_wright.commands import handle_stop
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = os.path.join(tmpdir, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        pid_file = os.path.join(tmp_dir, "wright-api.pid")
        with open(pid_file, "w") as f:
            f.write("98765")
            
        with patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=tmpdir), \
             patch("hermes_plugin_wright.commands.os.kill") as mock_kill:
            
            mock_kill.side_effect = [None, None, ProcessLookupError()]
            
            res = await handle_stop()
            assert "stopped" in res
            assert not os.path.exists(pid_file)


@pytest.mark.asyncio
async def test_handle_open():
    from hermes_plugin_wright.commands import handle_open
    with patch("hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock) as mock_health, \
         patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open:
        
        # Unhealthy Case
        mock_health.return_value = False
        res_error = await handle_open()
        assert "not running" in res_error
        mock_open.assert_not_called()
        
        # Healthy Case
        mock_health.return_value = True
        res_success = await handle_open()
        assert "Opened Wright UI" in res_success
        mock_open.assert_called_once_with("http://localhost:8000")


@pytest.mark.asyncio
async def test_handle_doctor():
    from hermes_plugin_wright.commands import handle_doctor
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up a fake secrets file
        config_dir = os.path.join(tmpdir, ".config", "wright")
        os.makedirs(config_dir, exist_ok=True)
        secrets_file = os.path.join(config_dir, "mcp-secrets.json")
        with open(secrets_file, "w") as f:
            f.write("{}")
        os.chmod(secrets_file, 0o600)
        
        # Set up a fake db file
        db_file = os.path.join(config_dir, "wright.db")
        with open(db_file, "w") as f:
            f.write("")
            
        # Set up a fake dist dir
        dist_dir = os.path.join(tmpdir, "apps", "web", "dist")
        os.makedirs(dist_dir, exist_ok=True)
        
        # Mock os.stat to return 0600 permissions for the secrets file
        mock_stat = MagicMock()
        mock_stat.return_value.st_mode = 0o100600

        with patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=tmpdir), \
             patch("hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock) as mock_health, \
             patch("hermes_plugin_wright.commands.os.path.expanduser", lambda p: p.replace("~", tmpdir)), \
             patch("hermes_plugin_wright.commands.os.stat", mock_stat), \
             patch("hermes_plugin_wright.commands.get_mcp_servers", new_callable=AsyncMock) as mock_servers:
            
            mock_health.return_value = True
            mock_servers.return_value = {
                "success": True,
                "servers": [
                    {
                        "server_id": "test-mcp",
                        "name": "Test MCP",
                        "is_installed": True,
                        "is_active": True,
                        "credentials_configured": {"API_KEY": True}
                    },
                    {
                        "server_id": "onshape",
                        "name": "Onshape MCP",
                        "is_installed": True,
                        "is_active": False,
                        "credentials_configured": {"ONSHAPE_API_KEY": False}
                    }
                ]
            }
            
            res = await handle_doctor()
            assert "🩺 Wright Doctor" in res
            assert "Repo found" in res
            assert "API server" in res
            assert "Frontend build" in res
            assert "Database" in res
            assert "Secrets store" in res
            assert "mode 0600" in res
            assert "2 installed, 1 active" in res
            assert "missing ONSHAPE_API_KEY" in res


def test_handle_catalog_list():
    from hermes_plugin_wright.commands import handle_catalog_list
    from hermes_plugin_wright.schemas import CatalogEntry
    catalog = MagicMock(spec=CatalogLoader)
    entry = CatalogEntry(
        id="test-id",
        name="Test Tool",
        vendor="Test Vendor",
        description="Test Description",
        domains=["cad"],
        transport="stdio",
        command=["python", "test.py"],
        locality="local",
        weight="light"
    )
    catalog.get_all.return_value = [entry]
    catalog.get_by_domain.return_value = [entry]
    
    res = handle_catalog_list(catalog)
    assert "Engineering Tools Catalog" in res
    assert "test-id" in res
    assert "Test Tool" in res
    
    res_domain = handle_catalog_list(catalog, "cad")
    assert "Engineering Tools Catalog — CAD" in res_domain
    assert "test-id" in res_domain


def test_handle_catalog_search():
    from hermes_plugin_wright.commands import handle_catalog_search
    from hermes_plugin_wright.schemas import CatalogEntry
    catalog = MagicMock(spec=CatalogLoader)
    entry = CatalogEntry(
        id="test-id",
        name="Test Tool",
        vendor="Test Vendor",
        description="Test Description",
        domains=["cad"],
        transport="stdio",
        command=["python", "test.py"],
        locality="local",
        weight="light"
    )
    catalog.search.return_value = [entry]
    
    res = handle_catalog_search(catalog, "test")
    assert "Search Results for 'test'" in res
    assert "test-id" in res


def test_handle_info():
    from hermes_plugin_wright.commands import handle_info
    from hermes_plugin_wright.schemas import CatalogEntry
    catalog = MagicMock(spec=CatalogLoader)
    entry = CatalogEntry(
        id="test-id",
        name="Test Tool",
        vendor="Test Vendor",
        description="Test Description",
        domains=["cad"],
        transport="stdio",
        command=["python", "test.py"],
        locality="local",
        weight="light",
        env_vars=[],
        dependencies={"system": ["pkg"], "python": [], "node": []}
    )
    catalog.get_all.return_value = [entry]
    
    res = handle_info(catalog, "test-id")
    assert "Test Tool (`test-id`)" in res
    assert "Test Vendor" in res
    assert "Test Description" in res
    
    res_missing = handle_info(catalog, "missing-id")
    assert "not found" in res_missing


@pytest.mark.asyncio
async def test_handle_install():
    from hermes_plugin_wright.commands import handle_install
    from hermes_plugin_wright.schemas import CatalogEntry
    catalog = MagicMock(spec=CatalogLoader)
    entry = CatalogEntry(
        id="test-id",
        name="Test Tool",
        vendor="Test Vendor",
        description="Test Description",
        domains=["cad"],
        transport="stdio",
        command=["python", "test.py"],
        locality="local",
        weight="light",
        env_vars=[],
        dependencies={"system": [], "python": [], "node": []}
    )
    catalog.get_all.return_value = [entry]
    
    # Missing ID
    res_missing_id = await handle_install(catalog, None)
    assert "Missing tool ID" in res_missing_id
    
    # Missing in catalog
    res_not_found = await handle_install(catalog, "other-id")
    assert "not found" in res_not_found
    
    # Success Case
    with patch("hermes_plugin_wright.commands.register_mcp_server", new_callable=AsyncMock) as mock_register:
        mock_register.return_value = {"success": True, "server_id": "test-id"}
        res_success = await handle_install(catalog, "test-id")
        assert "Successfully installed" in res_success
        mock_register.assert_called_once_with(entry)
        
    # Failure Case
    with patch("hermes_plugin_wright.commands.register_mcp_server", new_callable=AsyncMock) as mock_register:
        mock_register.return_value = {"success": False, "error": "API Error"}
        res_failure = await handle_install(catalog, "test-id")
        assert "Failed to install" in res_failure
        assert "API Error" in res_failure


@pytest.mark.asyncio
async def test_handle_status():
    from hermes_plugin_wright.commands import handle_status
    
    # Disconnected Case
    with patch("hermes_plugin_wright.commands.check_api_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = {"connected": False}
        res = await handle_status()
        assert "Disconnected" in res
        
    # Connected Case
    with patch("hermes_plugin_wright.commands.check_api_health", new_callable=AsyncMock) as mock_health, \
         patch("hermes_plugin_wright.commands.get_workspaces", new_callable=AsyncMock) as mock_workspaces, \
         patch("hermes_plugin_wright.commands.get_mcp_servers", new_callable=AsyncMock) as mock_servers:
         
        mock_health.return_value = {"connected": True}
        mock_workspaces.return_value = {
            "success": True,
            "workspaces": [
                {
                    "workspace_id": "ws-123",
                    "session_id": "session-abc",
                    "workspace_name": "My CAD Project",
                    "local_path": "/path/to/workspace"
                }
            ]
        }
        mock_servers.return_value = {
            "success": True,
            "servers": [
                {
                    "server_id": "freecad",
                    "name": "FreeCAD",
                    "is_installed": True,
                    "is_active": True,
                    "credentials_configured": {}
                },
                {
                    "server_id": "onshape",
                    "name": "Onshape",
                    "is_installed": True,
                    "is_active": False,
                    "credentials_configured": {"ONSHAPE_API_KEY": False}
                },
                {
                    "server_id": "calculix",
                    "name": "Calculix",
                    "is_installed": True,
                    "is_active": False,
                    "credentials_configured": {"API_KEY": True}
                }
            ]
        }
        
        res = await handle_status()
        assert "### 🌐 Wright Status" in res
        assert "Connected" in res
        assert "My CAD Project" in res
        assert "/path/to/workspace" in res
        assert "● **freecad** (active)" in res
        assert "○ **onshape** (needs action - missing ONSHAPE_API_KEY)" in res
        assert "🔴 **calculix** (inactive)" in res


@pytest.mark.asyncio
async def test_handle_start_in_docker_healthy():
    from hermes_plugin_wright.commands import handle_start
    with patch("hermes_plugin_wright.commands.is_in_docker", return_callable=lambda: True), \
         patch("hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock) as mock_health, \
         patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open:
        
        mock_health.return_value = True
        res = await handle_start()
        assert "already running" in res
        mock_open.assert_called_once_with("http://localhost:8000")


@pytest.mark.asyncio
async def test_handle_start_in_docker_unhealthy():
    from hermes_plugin_wright.commands import handle_start
    with patch("hermes_plugin_wright.commands.is_in_docker", return_callable=lambda: True), \
         patch("hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock) as mock_health:
        
        mock_health.return_value = False
        res = await handle_start()
        assert "unhealthy inside the container" in res





