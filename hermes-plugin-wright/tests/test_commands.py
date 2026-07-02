import asyncio
import os
import subprocess
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hermes_plugin_wright.commands import register_commands, WRIGHT_HELP_TEXT
from hermes_plugin_wright.catalog import CatalogLoader


def test_api_launch_command_prefers_uv_runtime(monkeypatch):
    from hermes_plugin_wright.commands import _api_launch_command

    monkeypatch.delenv("WRIGHT_API_HOST", raising=False)
    monkeypatch.setattr(
        "hermes_plugin_wright.commands.shutil.which",
        lambda name: r"C:\tools\uv.exe" if name == "uv" else None,
    )

    command = _api_launch_command(r"C:\wright")

    assert command[:3] == [r"C:\tools\uv.exe", "run", "--project"]
    assert command[3] == os.path.join(r"C:\wright", "apps", "api")
    assert "uvicorn" in command
    assert "api.main:app" in command
    assert "--app-dir" in command
    assert command[command.index("--app-dir") + 1] == os.path.join(
        r"C:\wright", "apps", "api", "src"
    )
    assert "fastapi" not in command
    assert "--host" in command
    assert "127.0.0.1" in command


def test_api_launch_command_honors_host_override(monkeypatch):
    from hermes_plugin_wright.commands import _api_launch_command

    monkeypatch.setenv("WRIGHT_API_HOST", "0.0.0.0")
    monkeypatch.setattr(
        "hermes_plugin_wright.commands.shutil.which",
        lambda name: r"C:\tools\uv.exe" if name == "uv" else None,
    )

    command = _api_launch_command(r"C:\wright")

    assert "--host" in command
    assert command[command.index("--host") + 1] == "0.0.0.0"
    assert "--app-dir" in command


@pytest.mark.parametrize(
    ("raw_host", "expected"),
    [
        ("0.0.0.0 ", "0.0.0.0"),
        (" http://0.0.0.0:8000/ ", "0.0.0.0:8000"),
        ("", "127.0.0.1"),
    ],
)
def test_api_launch_command_sanitizes_host_override(monkeypatch, raw_host, expected):
    from hermes_plugin_wright.commands import _api_launch_command

    monkeypatch.setenv("WRIGHT_API_HOST", raw_host)
    monkeypatch.setattr(
        "hermes_plugin_wright.commands.shutil.which",
        lambda name: r"C:\tools\uv.exe" if name == "uv" else None,
    )

    command = _api_launch_command(r"C:\wright")

    assert command[command.index("--host") + 1] == expected


def test_api_launch_command_falls_back_to_repo_venv_python(monkeypatch, tmp_path):
    from hermes_plugin_wright.commands import _api_launch_command

    monkeypatch.delenv("WRIGHT_API_HOST", raising=False)
    repo_python = tmp_path / ".venv" / "Scripts" / "python.exe"
    repo_python.parent.mkdir(parents=True)
    repo_python.write_text("")
    monkeypatch.setattr("hermes_plugin_wright.commands.IS_WINDOWS", True)
    monkeypatch.setattr(
        "hermes_plugin_wright.commands.shutil.which", lambda _name: None
    )

    command = _api_launch_command(str(tmp_path))

    assert command[:3] == [str(repo_python), "-m", "uvicorn"]
    assert "api.main:app" in command
    assert "--app-dir" in command


def test_api_layout_supports_top_level_api(tmp_path):
    from hermes_plugin_wright.commands import _api_launch_command

    api_dir = tmp_path / "api"
    api_dir.mkdir()
    (api_dir / "main.py").write_text("app = object()")

    command = _api_launch_command(str(tmp_path))

    assert command[command.index("--app-dir") + 1] == str(tmp_path)


def test_ensure_python_workspace_synced_runs_sync_when_probe_fails(monkeypatch):
    from hermes_plugin_wright.commands import _ensure_python_workspace_synced

    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        return subprocess.CompletedProcess(command, 1 if len(calls) == 1 else 0, "", "")

    import subprocess

    monkeypatch.setattr(
        "hermes_plugin_wright.commands.shutil.which",
        lambda name: r"C:\tools\uv.exe" if name == "uv" else None,
    )
    monkeypatch.setattr("hermes_plugin_wright.commands.subprocess.run", fake_run)

    result = _ensure_python_workspace_synced(r"C:\wright")

    assert result.returncode == 0
    assert calls[0][:4] == [
        r"C:\tools\uv.exe",
        "run",
        "--project",
        os.path.join(r"C:\wright", "apps", "api"),
    ]
    assert calls[1] == [
        r"C:\tools\uv.exe",
        "sync",
        "--all-packages",
        "--all-groups",
    ]


def test_register_commands():
    ctx = MagicMock()
    catalog = MagicMock(spec=CatalogLoader)

    register_commands(ctx, catalog)

    ctx.register_command.assert_called_once()
    name, handler = (
        ctx.register_command.call_args[1]["name"],
        ctx.register_command.call_args[1]["handler"],
    )
    assert name == "wright"

    # Test help fallback
    handler_result = asyncio.run(handler(""))
    assert handler_result == WRIGHT_HELP_TEXT


@pytest.mark.asyncio
async def test_open_wright_ui_returns_preview_link_in_desktop_mode(monkeypatch):
    from hermes_plugin_wright import commands

    monkeypatch.setenv("WRIGHT_UI_MODE", "preview")
    monkeypatch.setattr(commands.webbrowser, "open", MagicMock())

    message = await commands._open_wright_ui("http://127.0.0.1:8000/")

    assert "[Preview: Wright](#preview/http%3A%2F%2F127.0.0.1%3A8000%2F)" in message
    commands.webbrowser.open.assert_not_called()


@pytest.mark.asyncio
async def test_open_wright_ui_opens_browser_by_default(monkeypatch):
    from hermes_plugin_wright import commands

    monkeypatch.delenv("WRIGHT_UI_MODE", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)
    mock_open = MagicMock(return_value=True)
    monkeypatch.setattr(commands.webbrowser, "open", mock_open)

    message = await commands._open_wright_ui("http://127.0.0.1:8000/")

    assert "default browser" in message
    mock_open.assert_called_once_with("http://127.0.0.1:8000/")


@pytest.mark.asyncio
async def test_handle_start_already_running(monkeypatch):
    from hermes_plugin_wright.commands import handle_start

    monkeypatch.delenv("WRIGHT_UI_MODE", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)

    with (
        patch("hermes_plugin_wright.commands._HERMES_CONTEXT", None),
        patch(
            "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
        ) as mock_health,
        patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open,
    ):
        mock_health.return_value = True
        mock_open.return_value = True
        res = await handle_start()
        assert "already running" in res
        assert "default browser" in res
        mock_open.assert_called_once_with("http://127.0.0.1:8000/")


@pytest.mark.asyncio
async def test_handle_start_already_running_desktop_uses_preview(monkeypatch):
    from hermes_plugin_wright.commands import handle_start

    monkeypatch.setenv("WRIGHT_UI_MODE", "preview")
    with (
        patch("hermes_plugin_wright.commands._HERMES_CONTEXT", None),
        patch(
            "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
        ) as mock_health,
        patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open,
    ):
        mock_health.return_value = True
        res = await handle_start()

        assert "already running" in res
        assert "#preview/http%3A%2F%2F127.0.0.1%3A8000%2F" in res
        mock_open.assert_not_called()


@pytest.mark.asyncio
async def test_handle_start_success(monkeypatch):
    from hermes_plugin_wright.commands import handle_start

    monkeypatch.delenv("WRIGHT_UI_MODE", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)

    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "apps", "web", "dist"), exist_ok=True)

        with (
            patch("hermes_plugin_wright.commands._HERMES_CONTEXT", None),
            patch(
                "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
            ) as mock_health,
            patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=tmpdir),
            patch(
                "hermes_plugin_wright.commands._ensure_python_workspace_synced"
            ) as mock_sync,
            patch(
                "hermes_plugin_wright.commands.shutil.which",
                return_value=r"C:\tools\uv.exe",
            ),
            patch("hermes_plugin_wright.commands.subprocess.Popen") as mock_popen,
            patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open,
        ):
            mock_health.side_effect = [False, True]
            mock_sync.return_value = subprocess.CompletedProcess([], 0, "", "")
            mock_open.return_value = True

            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.poll.return_value = None
            mock_popen.return_value = mock_proc

            res = await handle_start()
            assert "🚀 Wright is running!" in res
            assert "PID:     12345" in res
            assert mock_popen.call_count == 2
            api_call = mock_popen.call_args_list[1]
            command = api_call.args[0]
            assert command[:3] == [r"C:\tools\uv.exe", "run", "--project"]
            assert "api.main:app" in command
            assert "--app-dir" in command
            assert "fastapi" not in command
            assert api_call.kwargs["cwd"] == tmpdir
            assert "default browser" in res
            mock_open.assert_called_once_with("http://127.0.0.1:8000/")

            # Close the open log file handle to prevent file locking on Windows
            for call in mock_popen.call_args_list:
                stdout_file = call.kwargs.get("stdout")
                if stdout_file and hasattr(stdout_file, "close"):
                    stdout_file.close()

            pid_file = os.path.join(tmpdir, "tmp", "wright-api.pid")
            assert os.path.exists(pid_file)
            with open(pid_file, "r") as f:
                assert f.read() == "12345"


@pytest.mark.asyncio
async def test_handle_start_hides_windows_console(monkeypatch):
    from hermes_plugin_wright import commands
    from hermes_plugin_wright.commands import handle_start

    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, "apps", "web", "dist"), exist_ok=True)

        monkeypatch.setattr(commands, "IS_WINDOWS", True)
        monkeypatch.setenv("WRIGHT_UI_MODE", "preview")
        monkeypatch.setattr(
            commands.subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200, raising=False
        )
        monkeypatch.setattr(
            commands.subprocess, "DETACHED_PROCESS", 0x00000008, raising=False
        )
        monkeypatch.setattr(
            commands.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False
        )

        with (
            patch("hermes_plugin_wright.commands._HERMES_CONTEXT", None),
            patch(
                "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
            ) as mock_health,
            patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=tmpdir),
            patch(
                "hermes_plugin_wright.commands._ensure_python_workspace_synced"
            ) as mock_sync,
            patch(
                "hermes_plugin_wright.commands.shutil.which",
                return_value=r"C:\tools\uv.exe",
            ),
            patch("hermes_plugin_wright.commands.subprocess.Popen") as mock_popen,
        ):
            mock_health.side_effect = [False, True]
            mock_sync.return_value = subprocess.CompletedProcess([], 0, "", "")
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            mock_proc.poll.return_value = None
            mock_popen.return_value = mock_proc

            await handle_start()

            creationflags = mock_popen.call_args.kwargs["creationflags"]
            assert creationflags & commands.subprocess.CREATE_NO_WINDOW

            stdout_file = mock_popen.call_args[1].get("stdout")
            if stdout_file and hasattr(stdout_file, "close"):
                stdout_file.close()


@pytest.mark.asyncio
async def test_handle_start_missing_repo_mentions_env_override():
    from hermes_plugin_wright.commands import handle_start

    with (
        patch(
            "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
        ) as mock_health,
        patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=None),
    ):
        mock_health.return_value = False

        res = await handle_start()

        assert "Could not find the Wright repo" in res
        assert "WRIGHT_REPO_DIR" in res
        assert "restart Hermes Desktop" in res


@pytest.mark.asyncio
async def test_handle_stop_success():
    from hermes_plugin_wright.commands import handle_stop

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_dir = os.path.join(tmpdir, "tmp")
        os.makedirs(tmp_dir, exist_ok=True)
        pid_file = os.path.join(tmp_dir, "wright-api.pid")
        with open(pid_file, "w") as f:
            f.write("98765")

        with (
            patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=tmpdir),
            patch("hermes_plugin_wright.commands.os.kill") as mock_kill,
        ):
            mock_kill.side_effect = [None, None, ProcessLookupError()]

            res = await handle_stop()
            assert "stopped" in res
            assert not os.path.exists(pid_file)


@pytest.mark.asyncio
async def test_handle_open(monkeypatch):
    from hermes_plugin_wright.commands import handle_open

    with (
        patch("hermes_plugin_wright.commands._HERMES_CONTEXT", None),
        patch(
            "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
        ) as mock_health,
        patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open,
    ):
        monkeypatch.delenv("WRIGHT_UI_MODE", raising=False)
        monkeypatch.delenv("HERMES_DESKTOP", raising=False)

        # Unhealthy Case
        mock_health.return_value = False
        res_error = await handle_open()
        assert "not running" in res_error
        mock_open.assert_not_called()

        # Healthy browser Case
        mock_health.return_value = True
        mock_open.return_value = True
        res_success = await handle_open()
        assert "default browser" in res_success
        mock_open.assert_called_once_with("http://127.0.0.1:8000/")

        # Healthy Desktop Case
        mock_open.reset_mock()
        monkeypatch.setenv("WRIGHT_UI_MODE", "preview")
        res_desktop = await handle_open()
        assert "#preview/http%3A%2F%2F127.0.0.1%3A8000%2F" in res_desktop
        mock_open.assert_not_called()


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

        with (
            patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=tmpdir),
            patch(
                "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
            ) as mock_health,
            patch(
                "hermes_plugin_wright.commands.os.path.expanduser",
                lambda p: p.replace("~", tmpdir),
            ),
            patch("hermes_plugin_wright.commands.os.stat", mock_stat),
            patch(
                "hermes_plugin_wright.commands._is_hermes_gateway_healthy",
                new_callable=AsyncMock,
            ) as mock_gateway_health,
            patch(
                "hermes_plugin_wright.commands._check_hermes_model_route",
                new_callable=AsyncMock,
            ) as mock_route_check,
            patch(
                "hermes_plugin_wright.commands.get_mcp_servers", new_callable=AsyncMock
            ) as mock_servers,
        ):
            mock_health.return_value = True
            mock_gateway_health.return_value = True
            mock_route_check.return_value = {
                "ok": True,
                "message": "model: hermes responded",
            }
            mock_servers.return_value = {
                "success": True,
                "servers": [
                    {
                        "server_id": "test-mcp",
                        "name": "Test MCP",
                        "is_installed": True,
                        "is_active": True,
                        "credentials_configured": None,
                    },
                    {
                        "server_id": "onshape",
                        "is_installed": True,
                        "is_active": False,
                        "credentials_configured": {"ONSHAPE_API_KEY": False},
                    },
                ],
            }

            res = await handle_doctor()
            assert "🩺 Wright Doctor" in res
            assert "Repo found" in res
            assert "API server" in res
            assert "Hermes route" in res
            assert "model: hermes responded" in res
            assert "Frontend build" in res
            assert "Database" in res
            assert "Secrets store" in res
            assert "mode 0600" in res
            assert "2 installed, 1 active" in res
            assert "onshape: missing ONSHAPE_API_KEY" in res


@pytest.mark.asyncio
async def test_handle_doctor_reports_broken_hermes_model_route():
    from hermes_plugin_wright.commands import handle_doctor

    with tempfile.TemporaryDirectory() as tmpdir:
        with (
            patch("hermes_plugin_wright.commands.detect_repo_dir", return_value=tmpdir),
            patch(
                "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
            ) as mock_health,
            patch(
                "hermes_plugin_wright.commands._is_hermes_gateway_healthy",
                new_callable=AsyncMock,
            ) as mock_gateway_health,
            patch(
                "hermes_plugin_wright.commands._check_hermes_model_route",
                new_callable=AsyncMock,
            ) as mock_route_check,
            patch(
                "hermes_plugin_wright.commands.os.path.expanduser",
                lambda p: p.replace("~", tmpdir),
            ),
            patch(
                "hermes_plugin_wright.commands.get_mcp_servers", new_callable=AsyncMock
            ) as mock_servers,
        ):
            mock_health.return_value = True
            mock_gateway_health.return_value = True
            mock_route_check.return_value = {
                "ok": False,
                "message": "HTTP 404: The model qwen36-35b-moe does not exist.",
            }
            mock_servers.return_value = {"success": True, "servers": []}

            res = await handle_doctor()

            assert "❌ Hermes route" in res
            assert "qwen36-35b-moe" in res
            assert "hermes model" in res
            assert "hermes auth status openai-codex" in res


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
        weight="light",
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
        weight="light",
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
        dependencies={"system": ["pkg"], "python": [], "node": []},
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
        dependencies={"system": [], "python": [], "node": []},
    )
    catalog.get_all.return_value = [entry]

    # Missing ID
    res_missing_id = await handle_install(catalog, None)
    assert "Missing tool ID" in res_missing_id

    # Missing in catalog
    res_not_found = await handle_install(catalog, "other-id")
    assert "not found" in res_not_found

    # Success Case
    with patch(
        "hermes_plugin_wright.commands.register_mcp_server", new_callable=AsyncMock
    ) as mock_register:
        mock_register.return_value = {"success": True, "server_id": "test-id"}
        res_success = await handle_install(catalog, "test-id")
        assert "Successfully installed" in res_success
        mock_register.assert_called_once_with(entry)

    # Failure Case
    with patch(
        "hermes_plugin_wright.commands.register_mcp_server", new_callable=AsyncMock
    ) as mock_register:
        mock_register.return_value = {"success": False, "error": "API Error"}
        res_failure = await handle_install(catalog, "test-id")
        assert "Failed to install" in res_failure
        assert "API Error" in res_failure


@pytest.mark.asyncio
async def test_handle_status():
    from hermes_plugin_wright.commands import handle_status

    # Disconnected Case
    with patch(
        "hermes_plugin_wright.commands.check_api_health", new_callable=AsyncMock
    ) as mock_health:
        mock_health.return_value = {"connected": False}
        res = await handle_status()
        assert "Disconnected" in res

    # Connected Case
    with (
        patch(
            "hermes_plugin_wright.commands.check_api_health", new_callable=AsyncMock
        ) as mock_health,
        patch(
            "hermes_plugin_wright.commands.get_workspaces", new_callable=AsyncMock
        ) as mock_workspaces,
        patch(
            "hermes_plugin_wright.commands.get_mcp_servers", new_callable=AsyncMock
        ) as mock_servers,
    ):
        mock_health.return_value = {"connected": True}
        mock_workspaces.return_value = {
            "success": True,
            "workspaces": [
                {
                    "workspace_id": "ws-123",
                    "session_id": "session-abc",
                    "workspace_name": "My CAD Project",
                    "local_path": "/path/to/workspace",
                }
            ],
        }
        mock_servers.return_value = {
            "success": True,
            "servers": [
                {
                    "server_id": "freecad",
                    "name": "FreeCAD",
                    "is_installed": True,
                    "is_active": True,
                    "credentials_configured": {},
                },
                {
                    "server_id": "onshape",
                    "name": "Onshape",
                    "is_installed": True,
                    "is_active": False,
                    "credentials_configured": {"ONSHAPE_API_KEY": False},
                },
                {
                    "server_id": "calculix",
                    "name": "Calculix",
                    "is_installed": True,
                    "is_active": False,
                    "credentials_configured": {"API_KEY": True},
                },
            ],
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
async def test_handle_start_in_docker_healthy(monkeypatch):
    from hermes_plugin_wright.commands import handle_start

    monkeypatch.delenv("WRIGHT_UI_MODE", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)

    with (
        patch("hermes_plugin_wright.commands._HERMES_CONTEXT", None),
        patch(
            "hermes_plugin_wright.commands.is_in_docker", return_callable=lambda: True
        ),
        patch(
            "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
        ) as mock_health,
        patch("hermes_plugin_wright.commands.webbrowser.open") as mock_open,
    ):
        mock_health.return_value = True
        mock_open.return_value = True
        res = await handle_start()
        assert "already running" in res
        assert "default browser" in res
        mock_open.assert_called_once_with("http://127.0.0.1:8000/")


@pytest.mark.asyncio
async def test_handle_start_in_docker_unhealthy():
    from hermes_plugin_wright.commands import handle_start

    with (
        patch(
            "hermes_plugin_wright.commands.is_in_docker", return_callable=lambda: True
        ),
        patch(
            "hermes_plugin_wright.commands.is_api_healthy", new_callable=AsyncMock
        ) as mock_health,
    ):
        mock_health.return_value = False
        res = await handle_start()
        assert "unhealthy inside the container" in res
