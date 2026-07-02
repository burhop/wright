"""Commands module for /wright slash commands."""

import asyncio
import os
import platform
import signal
import shutil
import subprocess
import sys
import webbrowser
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import httpx
import structlog

from .bridge import (
    check_api_health,
    detect_repo_dir,
    get_mcp_servers,
    get_workspaces,
    register_mcp_server,
    WRIGHT_API_BASE,
    WRIGHT_UI_URL,
)
from .catalog import CatalogLoader

IS_WINDOWS = platform.system() == "Windows"

logger = structlog.get_logger("hermes_plugin_wright.commands")
_HERMES_CONTEXT: Any = None
HERMES_API_BASE = os.environ.get("HERMES_API_BASE_URL", "http://127.0.0.1:8642").rstrip(
    "/"
)
HERMES_API_KEY = (
    os.environ.get("HERMES_API_KEY")
    or os.environ.get("API_SERVER_KEY")
    or "wright-local-dev"
)

WRIGHT_HELP_TEXT = """🔧 Wright Engineering Platform

Usage: /wright <command>

  Launcher:
    start              Build frontend, start API server, show Wright UI links
    stop               Stop the API server
    open               Open Wright UI in Hermes Desktop or the default browser
    doctor             Full health check of the Wright stack
    debug-context      Show available Hermes plugin context methods

  Catalog:
    catalog [domain]   Browse engineering tools (cad, fea, cfd, cam, ...)
    catalog search Q   Search the catalog
    info <id>          Show details for a catalog entry
    install <id>       Register a catalog entry in Wright

  Status:
    status             Show Wright connection, workspace, enabled tools

Repo: https://github.com/burhop/wright
"""


async def is_api_healthy() -> bool:
    """Quick health check against the Wright FastAPI server."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{WRIGHT_API_BASE}/api/health")
            return r.status_code == 200
    except Exception:
        return False


def _hermes_env_paths() -> List[str]:
    """Return Hermes env files used by Desktop and CLI builds."""
    paths = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        paths.append(os.path.join(local_app_data, "hermes", ".env"))
    paths.append(os.path.join(os.path.expanduser("~"), ".hermes", ".env"))
    return list(dict.fromkeys(paths))


def _upsert_env_file(path: str, values: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = []
    seen_keys = set()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f.read().splitlines():
                key = raw_line.split("=", 1)[0].strip() if "=" in raw_line else ""
                if key in values:
                    lines.append(f"{key}={values[key]}")
                    seen_keys.add(key)
                else:
                    lines.append(raw_line)
    for key, value in values.items():
        if key not in seen_keys:
            lines.append(f"{key}={value}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).rstrip() + "\n")


def _configure_hermes_gateway_env() -> None:
    values = {
        "API_SERVER_ENABLED": "true",
        "API_SERVER_HOST": "127.0.0.1",
        "API_SERVER_PORT": HERMES_API_BASE.rsplit(":", 1)[-1]
        if ":" in HERMES_API_BASE
        else "8642",
        "API_SERVER_KEY": HERMES_API_KEY,
    }
    for path in _hermes_env_paths():
        _upsert_env_file(path, values)


async def _is_hermes_gateway_healthy() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                f"{HERMES_API_BASE}/health",
                headers={"Authorization": f"Bearer {HERMES_API_KEY}"},
            )
            body_preview = response.text[:200].lower()
            if "<!doctype html" in body_preview or "<html" in body_preview:
                return False
            return response.status_code == 200
    except Exception:
        return False


def _gateway_log_path(repo_dir: str) -> str:
    log_dir = os.path.join(repo_dir, "tmp")
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, "hermes-gateway.log")


def _start_hermes_gateway(repo_dir: str) -> Optional[str]:
    hermes_path = shutil.which("hermes")
    if hermes_path is None:
        return "Hermes CLI was not found on PATH; cannot start `hermes gateway run`."

    log_path = _gateway_log_path(repo_dir)
    log_file = open(log_path, "a", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "API_SERVER_ENABLED": "true",
            "API_SERVER_HOST": "127.0.0.1",
            "API_SERVER_PORT": HERMES_API_BASE.rsplit(":", 1)[-1]
            if ":" in HERMES_API_BASE
            else "8642",
            "API_SERVER_KEY": HERMES_API_KEY,
        }
    )

    popen_kwargs = {
        "cwd": repo_dir,
        "env": env,
        "stdout": log_file,
        "stderr": subprocess.STDOUT,
    }
    if IS_WINDOWS:
        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
        create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if create_no_window:
            creationflags |= create_no_window
        popen_kwargs["creationflags"] = creationflags
    else:
        popen_kwargs["start_new_session"] = True

    try:
        process = subprocess.Popen([hermes_path, "gateway", "run"], **popen_kwargs)
        with open(
            os.path.join(repo_dir, "tmp", "hermes-gateway.pid"), "w", encoding="utf-8"
        ) as f:
            f.write(str(process.pid))
        return None
    except Exception as exc:
        return f"Failed to start Hermes Gateway: {exc}"
    finally:
        log_file.close()


async def _ensure_hermes_gateway(repo_dir: str) -> tuple[bool, str]:
    _configure_hermes_gateway_env()
    if await _is_hermes_gateway_healthy():
        return True, f"Hermes Gateway API is healthy at {HERMES_API_BASE}."

    error = _start_hermes_gateway(repo_dir)
    if error:
        return False, error

    for _ in range(15):
        await asyncio.sleep(1)
        if await _is_hermes_gateway_healthy():
            return True, f"Hermes Gateway API started at {HERMES_API_BASE}."

    return (
        False,
        "Hermes Gateway did not become healthy. Run `hermes gateway run` and check "
        f"{_gateway_log_path(repo_dir)}.",
    )


def is_in_docker() -> bool:
    """Detect if executing inside a Docker container context."""
    return os.path.exists("/.dockerenv")


def _run_npm(args: list, **kwargs) -> subprocess.CompletedProcess:
    """Run an npm command, handling Windows where npm is a .cmd file."""
    npm_path = shutil.which("npm")
    if npm_path is None:
        raise FileNotFoundError("npm not found on PATH. Install Node.js first.")
    return subprocess.run([npm_path] + args, **kwargs)


def _repo_venv_python(repo_dir: str) -> Optional[str]:
    if IS_WINDOWS:
        candidate = os.path.join(repo_dir, ".venv", "Scripts", "python.exe")
    else:
        candidate = os.path.join(repo_dir, ".venv", "bin", "python")
    return candidate if os.path.exists(candidate) else None


def _api_layout(repo_dir: str) -> tuple[str, Optional[str]]:
    """Return uvicorn app-dir and optional uv project for supported layouts."""
    apps_api_src = os.path.join(repo_dir, "apps", "api", "src")
    apps_api_project = os.path.join(repo_dir, "apps", "api")
    if os.path.isfile(os.path.join(apps_api_src, "api", "main.py")):
        return apps_api_src, apps_api_project

    top_level_api = os.path.join(repo_dir, "api")
    if os.path.isfile(os.path.join(top_level_api, "main.py")):
        return repo_dir, None

    return apps_api_src, apps_api_project


def _api_host() -> str:
    """Return a uvicorn host value, tolerating common env formatting mistakes."""
    host = os.environ.get("WRIGHT_API_HOST", "127.0.0.1").strip()
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0].strip()
    return host or "127.0.0.1"


def _api_launch_command(repo_dir: str) -> List[str]:
    """Build a server launch command that uses Wright's runtime, not Hermes'."""
    host = _api_host()
    app_dir, uv_project = _api_layout(repo_dir)
    uv_path = shutil.which("uv")
    if uv_path:
        command = [
            uv_path,
            "run",
        ]
        if uv_project:
            command.extend(["--project", uv_project])
        command.extend(
            [
                "uvicorn",
                "api.main:app",
                "--app-dir",
                app_dir,
                "--host",
                host,
                "--port",
                "8000",
            ]
        )
        return command

    repo_python = _repo_venv_python(repo_dir)
    python_exe = repo_python or sys.executable
    return [
        python_exe,
        "-m",
        "uvicorn",
        "api.main:app",
        "--app-dir",
        app_dir,
        "--host",
        host,
        "--port",
        "8000",
    ]


def _ensure_python_workspace_synced(repo_dir: str) -> subprocess.CompletedProcess:
    """Ensure monorepo workspace packages are installed before API launch."""
    uv_path = shutil.which("uv")
    if uv_path is None:
        return subprocess.CompletedProcess([], 0, "", "")

    app_dir, uv_project = _api_layout(repo_dir)
    probe = [
        uv_path,
        "run",
    ]
    if uv_project:
        probe.extend(["--project", uv_project])
    probe.extend(
        [
            "python",
            "-c",
            "import api.main",
        ]
    )

    probe_proc = subprocess.run(
        probe,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if probe_proc.returncode == 0:
        return probe_proc

    return subprocess.run(
        [uv_path, "sync", "--all-packages", "--all-groups"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _preview_markdown(url: str, title: str = "Wright") -> str:
    """Build a Hermes Desktop preview link for the right rail."""
    return f"[Preview: {title}](#preview/{quote(url, safe='')})"


def _use_hermes_preview() -> bool:
    """Detect whether this plugin is running inside Hermes Desktop."""
    ui_mode = os.environ.get("WRIGHT_UI_MODE", "").strip().lower()
    if ui_mode in {"preview", "desktop", "hermes"}:
        return True
    if ui_mode in {"browser", "external"}:
        return False
    return os.environ.get("HERMES_DESKTOP", "").strip().lower() in {"1", "true", "yes"}


def _open_browser(url: str) -> bool:
    """Open a URL in the default OS browser when explicitly requested."""
    try:
        return bool(webbrowser.open(url))
    except Exception:
        return False


async def _open_wright_ui(url: str) -> str:
    if _use_hermes_preview():
        return f"Hermes Preview: {_preview_markdown(url)}"
    if _open_browser(url):
        return f"Opened Wright UI in the default browser: {url}"
    return f"Could not open the default browser. Use: {url}"


def _context_debug_text() -> str:
    ctx = _HERMES_CONTEXT
    if ctx is None:
        return "Hermes plugin context is not available."

    def mask_value(name: str, value: Any) -> str:
        text = str(value)
        if any(part in name.lower() for part in ("key", "token", "secret", "password")):
            if not text:
                return ""
            return f"{text[:4]}...{text[-4:]}" if len(text) > 8 else "***"
        return text[:200]

    lines = [f"Hermes context type: {type(ctx).__module__}.{type(ctx).__name__}", ""]
    for label, obj in (
        ("ctx", ctx),
        ("ctx.browser", getattr(ctx, "browser", None)),
        ("ctx.desktop", getattr(ctx, "desktop", None)),
        ("ctx.ui", getattr(ctx, "ui", None)),
    ):
        if obj is None:
            continue
        methods = [
            name
            for name in dir(obj)
            if not name.startswith("_") and callable(getattr(obj, name, None))
        ]
        lines.append(f"{label}:")
        lines.extend(f"  - {name}" for name in methods[:80])
        if len(methods) > 80:
            lines.append(f"  ... {len(methods) - 80} more")
        lines.append("")

        attrs = []
        for name in dir(obj):
            if name.startswith("_"):
                continue
            try:
                value = getattr(obj, name)
            except Exception:
                continue
            if callable(value):
                continue
            attrs.append((name, mask_value(name, value)))
        if attrs:
            lines.append(f"{label} attributes:")
            for name, value in attrs[:80]:
                lines.append(f"  - {name}: {value}")
            if len(attrs) > 80:
                lines.append(f"  ... {len(attrs) - 80} more")
            lines.append("")

    env_prefixes = ("HERMES", "TUI", "DASHBOARD", "GATEWAY", "NOUS", "WRIGHT")
    env_items = sorted(
        (name, value)
        for name, value in os.environ.items()
        if name.upper().startswith(env_prefixes) or "SESSION" in name.upper()
    )
    if env_items:
        lines.append("environment:")
        for name, value in env_items:
            lines.append(f"  - {name}: {mask_value(name, value)}")
        lines.append("")
    return "\n".join(lines).strip()


def _newest_mtime(directory: str) -> float:
    """Find the newest file modification time under a directory."""
    newest = 0.0
    for root, _, files in os.walk(directory):
        for f in files:
            try:
                t = os.path.getmtime(os.path.join(root, f))
                if t > newest:
                    newest = t
            except OSError:
                pass
    return newest


async def handle_start() -> str:
    """Build frontend, start FastAPI, open Wright UI."""
    repo_dir_for_gateway = detect_repo_dir()
    gateway_message = (
        "Hermes Gateway was not checked because the Wright repo was not found."
    )
    if repo_dir_for_gateway:
        _, gateway_message = await _ensure_hermes_gateway(repo_dir_for_gateway)

    # 1. Already running?
    if await is_api_healthy():
        open_message = await _open_wright_ui(WRIGHT_UI_URL)
        return (
            "✅ Wright is already running at http://localhost:8000\n"
            f"   Hermes Gateway: {gateway_message}\n"
            f"   UI: {open_message}"
        )

    # If inside Docker and API is not running/unhealthy, abort with supervisor instructions
    if is_in_docker():
        return (
            "❌ Wright API is not running or unhealthy inside the container.\n"
            "   Please check supervisord logs or start supervisord services: supervisorctl status wright-api"
        )

    # 2. Find repo
    repo_dir = detect_repo_dir()
    if not repo_dir:
        return (
            "❌ Could not find the Wright repo.\n"
            "   Clone or copy it locally, then set WRIGHT_REPO_DIR to that path.\n"
            "   Example: setx WRIGHT_REPO_DIR C:\\wright\n"
            "   Then fully restart Hermes Desktop and run: /wright start"
        )

    sync_proc = _ensure_python_workspace_synced(repo_dir)
    if sync_proc.returncode != 0:
        details = (sync_proc.stderr or sync_proc.stdout or "").strip()
        return (
            "Wright Python dependencies are not ready.\n"
            "   `uv sync --all-packages --all-groups` failed.\n"
            f"   {details[:800]}"
        )

    # 3. Build frontend (npm run build in apps/web)
    web_dir = os.path.join(repo_dir, "apps", "web")
    dist_dir = os.path.join(web_dir, "dist")

    # Only rebuild if dist/ is missing or stale
    needs_build = not os.path.exists(dist_dir)
    if not needs_build:
        src_mtime = _newest_mtime(os.path.join(web_dir, "src"))
        dist_mtime = os.path.getmtime(dist_dir)
        needs_build = src_mtime > dist_mtime

    if needs_build:
        # Ensure node_modules exist
        if not os.path.exists(os.path.join(web_dir, "node_modules")):
            proc = _run_npm(
                ["install"], cwd=web_dir, capture_output=True, text=True, timeout=120
            )
            if proc.returncode != 0:
                return f"❌ npm install failed:\n{proc.stderr[:500]}"

        proc = _run_npm(
            ["run", "build"], cwd=web_dir, capture_output=True, text=True, timeout=120
        )
        if proc.returncode != 0:
            return f"❌ Frontend build failed:\n{proc.stderr[:500]}"

    # 4. Start FastAPI server (detached background process)
    log_dir = os.path.join(repo_dir, "tmp")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "wright-api.log")

    env = os.environ.copy()
    env["FRONTEND_DIST_DIR"] = dist_dir
    env["WRIGHT_LAUNCHED_BY_HERMES"] = "1"

    # Platform-specific detach: on POSIX use setsid, on Windows use
    # CREATE_NEW_PROCESS_GROUP so the child survives parent exit.
    log_file = open(log_path, "a")
    popen_kwargs = {
        "cwd": repo_dir,
        "env": env,
        "stdout": log_file,
        "stderr": subprocess.STDOUT,
    }
    if IS_WINDOWS:
        creationflags = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
        create_no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        if create_no_window:
            creationflags |= create_no_window
        popen_kwargs["creationflags"] = creationflags
    else:
        popen_kwargs["start_new_session"] = True

    try:
        server_proc = subprocess.Popen(
            _api_launch_command(repo_dir),
            **popen_kwargs,
        )
    finally:
        log_file.close()

    # 5. Wait for health check (up to 15 seconds)
    for attempt in range(15):
        if await is_api_healthy():
            break
        if server_proc.poll() is not None:
            return f"❌ Server process exited with code {server_proc.returncode}\n   Check logs: {log_path}"
        await asyncio.sleep(1)
    else:
        return f"❌ Server did not become healthy within 15 seconds.\n   Check logs: {log_path}"

    # 6. Open UI
    open_message = await _open_wright_ui(WRIGHT_UI_URL)

    # 7. Write PID file for /wright stop
    pid_path = os.path.join(log_dir, "wright-api.pid")
    with open(pid_path, "w") as f:
        f.write(str(server_proc.pid))

    return (
        "🚀 Wright is running!\n\n"
        f"   API:     http://localhost:8000\n"
        f"   Hermes:  {gateway_message}\n"
        f"   UI:      {open_message}\n"
        f"   Logs:    {log_path}\n"
        f"   PID:     {server_proc.pid}\n\n"
        "   Use `/wright stop` to shut down."
    )


async def handle_stop() -> str:
    """Stop the Wright FastAPI server."""
    repo_dir = detect_repo_dir()
    if not repo_dir:
        return "❌ Could not find the Wright repo."

    stopped_processes = []

    def stop_windows_backends() -> None:
        if not IS_WINDOWS:
            return
        ps_script = (
            "$repo = $args[0]; "
            "Get-CimInstance Win32_Process | "
            "Where-Object { $_.CommandLine -and $_.CommandLine.Contains($repo) -and "
            "($_.CommandLine -match 'uvicorn' -or $_.CommandLine -match 'api\\.main:app' -or $_.CommandLine -match 'apps\\\\api') } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; $_.ProcessId }"
        )
        try:
            proc = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_script, repo_dir],
                capture_output=True,
                text=True,
                timeout=10,
            )
            for line in proc.stdout.splitlines():
                line = line.strip()
                if line:
                    stopped_processes.append(line)
        except Exception as e:
            logger.debug("Failed to sweep Wright backend processes", error=str(e))

    pid_path = os.path.join(repo_dir, "tmp", "wright-api.pid")
    if not os.path.exists(pid_path):
        stop_windows_backends()
        if stopped_processes:
            return "✅ Wright server stopped."
        if not await is_api_healthy():
            return "ℹ️ Wright is not running."
        return "⚠️ Wright is running but no PID file found. Stop it manually."

    try:
        with open(pid_path, "r") as f:
            pid = int(f.read().strip())

        # Platform-specific termination: Windows has no SIGTERM;
        # use taskkill instead.
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
            )
        else:
            os.kill(pid, signal.SIGTERM)

        # Wait for process to exit (up to 5 seconds)
        for _ in range(10):
            try:
                os.kill(pid, 0)  # Check if still alive
                await asyncio.sleep(0.5)
            except OSError:
                break

        if os.path.exists(pid_path):
            os.remove(pid_path)
        stop_windows_backends()
        return "✅ Wright server stopped."
    except OSError:
        if os.path.exists(pid_path):
            os.remove(pid_path)
        stop_windows_backends()
        if stopped_processes:
            return "✅ Wright server stopped."
        return "ℹ️ Wright server was already stopped (stale PID file cleaned up)."
    except Exception as e:
        stop_windows_backends()
        if stopped_processes:
            return "✅ Wright server stopped."
        return f"❌ Failed to stop Wright: {e}"


async def handle_open(open_browser: bool = False) -> str:
    """Open the Wright UI."""
    if not await is_api_healthy():
        return "❌ Wright is not running.\n   Use `/wright start` to launch it first."
    if open_browser:
        if _open_browser(WRIGHT_UI_URL):
            return f"Opened Wright UI in the default browser: {WRIGHT_UI_URL}"
        return f"Could not open the default browser. Use: {WRIGHT_UI_URL}"

    open_message = await _open_wright_ui(WRIGHT_UI_URL)
    return f"Wright UI:\n{open_message}"
    return f"🌐 {open_message} (http://localhost:8000)"


async def handle_doctor() -> str:
    """Run a full health check of the Wright stack."""
    lines = ["🩺 Wright Doctor\n"]

    # 1. Repo detection
    repo_dir = detect_repo_dir()
    if repo_dir:
        lines.append(f"  ✅ Repo found:     {repo_dir}")
    else:
        lines.append(
            "  ❌ Repo not found — set WRIGHT_REPO_DIR to your local Wright checkout"
        )
        return "\n".join(lines)

    # 2. FastAPI server
    if await is_api_healthy():
        lines.append("  ✅ API server:     http://localhost:8000 (healthy)")
    else:
        lines.append("  ❌ API server:     not running — use /wright start")

    if await _is_hermes_gateway_healthy():
        lines.append(f"  Gateway API:    healthy at {HERMES_API_BASE}")
    else:
        lines.append(
            f"  Gateway API:    not reachable at {HERMES_API_BASE} - run /wright start or `hermes gateway run`"
        )

    # 3. Frontend build
    dist_dir = os.path.join(repo_dir, "apps", "web", "dist")
    if os.path.exists(dist_dir):
        lines.append(f"  ✅ Frontend build: {dist_dir}")
    else:
        lines.append("  ⚠️ Frontend build: missing — /wright start will build it")

    # 4. Database
    db_paths = [
        os.path.expanduser("~/.config/wright/wright.db"),
        os.path.join(repo_dir, "wright.db"),
    ]
    db_found = any(os.path.exists(p) for p in db_paths)
    if db_found:
        lines.append("  ✅ Database:       exists")
    else:
        lines.append(
            "  ⚠️ Database:       not yet created (will be created on first API start)"
        )

    # 5. Secrets store
    secrets_path = os.path.expanduser("~/.config/wright/mcp-secrets.json")
    if os.path.exists(secrets_path):
        perms = oct(os.stat(secrets_path).st_mode)[-3:]
        if perms == "600":
            lines.append(f"  ✅ Secrets store:  {secrets_path} (mode 0600)")
        else:
            lines.append(
                f"  ⚠️ Secrets store:  {secrets_path} (mode 0{perms} — should be 0600)"
            )
    else:
        lines.append(
            "  ℹ️ Secrets store:  not yet created (created on first credential save)"
        )

    # 6. Tool status (if API is up)
    if await is_api_healthy():
        try:
            res = await get_mcp_servers()
            if res.get("success"):
                servers = res.get("servers", [])
                installed = [s for s in servers if s.get("is_installed")]
                active = [s for s in servers if s.get("is_active")]
                lines.append(
                    f"  ✅ MCP servers:    {len(installed)} installed, {len(active)} active"
                )

                # Check for credential issues
                cred_issues = []
                for s in installed:
                    creds = s.get("credentials_configured", {})
                    missing = [k for k, v in creds.items() if not v]
                    if missing:
                        cred_issues.append(
                            f"     ⚠️ {s['name']}: missing {', '.join(missing)}"
                        )
                if cred_issues:
                    lines.append("  ⚠️ Credentials:")
                    lines.extend(cred_issues)
            else:
                lines.append("  ⚠️ MCP servers:    could not query")
        except Exception:
            lines.append("  ⚠️ MCP servers:    could not query")

    return "\n".join(lines)


async def handle_status() -> str:
    """Show Wright connection, workspace, enabled tools."""
    health = await check_api_health()
    if not health.get("connected"):
        return (
            "### 🌐 Wright Status\n"
            f"* **API Connection**: 🔴 Disconnected ({WRIGHT_API_BASE})"
        )

    gateway_status = (
        "connected"
        if await _is_hermes_gateway_healthy()
        else (
            f"not reachable at {HERMES_API_BASE}; run `/wright start` or `hermes gateway run`"
        )
    )

    # Query workspaces and servers
    workspaces_res = await get_workspaces()
    servers_res = await get_mcp_servers()

    # Active workspace
    active_ws = None
    if workspaces_res.get("success"):
        workspaces = workspaces_res.get("workspaces", [])
        if workspaces:
            active_ws = workspaces[0]

    if active_ws:
        ws_name = (
            active_ws.get("workspace_name")
            or active_ws.get("session_id")
            or "Unnamed Workspace"
        )
        ws_path = active_ws.get("local_path", "")
        workspace_line = f"* **Active Workspace**: {ws_name} (`{ws_path}`)"
    else:
        workspace_line = "* **Active Workspace**: None"

    # MCP Tools
    tools_lines = []
    if servers_res.get("success"):
        servers = servers_res.get("servers", [])
        installed_servers = [s for s in servers if s.get("is_installed")]
        for s in installed_servers:
            name = (s.get("server_id") or s.get("name") or "unnamed").lower()
            is_active = s.get("is_active", False)
            creds = s.get("credentials_configured") or {}
            missing_creds = [k for k, v in creds.items() if not v]

            if missing_creds:
                status_str = f"needs action - missing {', '.join(missing_creds)}"
                icon = "○"
            elif is_active:
                status_str = "active"
                icon = "●"
            else:
                status_str = "inactive"
                icon = "🔴"
            tools_lines.append(f"* {icon} **{name}** ({status_str})")

    if not tools_lines:
        tools_lines.append("* *No MCP servers installed.*")

    lines = [
        "### 🌐 Wright Status",
        f"* **API Connection**: ● Connected ({WRIGHT_API_BASE})",
        f"* **Hermes Gateway**: {gateway_status}",
        workspace_line,
        "",
        "#### 🛠️ Configured MCP Tools",
    ]
    lines.extend(tools_lines)
    return "\n".join(lines)


def handle_catalog_list(catalog: CatalogLoader, domain: Optional[str] = None) -> str:
    """Browse cataloged tools, optionally filtered by domain tag."""
    if domain:
        entries = catalog.get_by_domain(domain)
        header = f"🔧 Engineering Tools Catalog — {domain.upper()}"
    else:
        entries = catalog.get_all()
        header = "🔧 Engineering Tools Catalog"

    lines = [
        header,
        "",
        "| ID | Tool Name | Locality | Weight |",
        "|:---|:---|:---|:---|",
    ]
    for e in entries:
        lines.append(f"| `{e.id}` | {e.name} | {e.locality} | {e.weight} |")

    lines.append("")
    lines.append(
        "Use `/wright install <id>` to add a tool   |   `/wright info <id>` for details"
    )
    return "\n".join(lines)


def handle_catalog_search(catalog: CatalogLoader, query: str) -> str:
    """Search catalog entries by keyword query."""
    entries = catalog.search(query)
    lines = [
        f"🔍 Search Results for '{query}'",
        "",
        "| ID | Tool Name | Locality | Weight |",
        "|:---|:---|:---|:---|",
    ]
    for e in entries:
        lines.append(f"| `{e.id}` | {e.name} | {e.locality} | {e.weight} |")

    lines.append("")
    lines.append(
        "Use `/wright install <id>` to add a tool   |   `/wright info <id>` for details"
    )
    return "\n".join(lines)


def handle_info(catalog: CatalogLoader, entry_id: Optional[str]) -> str:
    """Show detailed info for a single catalog entry."""
    if not entry_id:
        return "❌ Missing tool ID. Usage: `/wright info <id>`"

    entry = next((e for e in catalog.get_all() if e.id == entry_id), None)
    if not entry:
        return f"❌ Tool '{entry_id}' not found in catalog."

    lines = [
        f"### 🛠️ {entry.name} (`{entry.id}`)",
        f"* **Vendor**: {entry.vendor}",
        f"* **Domains**: {', '.join(entry.domains)}",
        f"* **Locality**: {entry.locality} (Weight: {entry.weight})",
        f"* **Transport**: {entry.transport}",
        "",
        "#### Description",
        entry.description,
        "",
    ]
    if entry.command:
        lines.append("#### Execution Command")
        lines.append("```bash")
        lines.append(" ".join(entry.command))
        lines.append("```")
        lines.append("")

    if entry.env_vars:
        lines.append("#### Required Credentials")
        for v in entry.env_vars:
            req_str = "required" if v.required else "optional"
            sec_str = "secret" if v.secret else "plain"
            lines.append(
                f"- **{v.name}** ({v.label}): {v.description} ({req_str}, {sec_str})"
            )
        lines.append("")

    if entry.dependencies and (
        entry.dependencies.system
        or entry.dependencies.python
        or entry.dependencies.node
    ):
        lines.append("#### Dependencies")
        if entry.dependencies.system:
            lines.append(f"- **System**: {', '.join(entry.dependencies.system)}")
        if entry.dependencies.python:
            lines.append(f"- **Python**: {', '.join(entry.dependencies.python)}")
        if entry.dependencies.node:
            lines.append(f"- **Node**: {', '.join(entry.dependencies.node)}")

    return "\n".join(lines)


async def handle_install(catalog: CatalogLoader, entry_id: Optional[str]) -> str:
    if not entry_id:
        return "❌ Missing tool ID. Usage: `/wright install <id>`"

    entry = next((e for e in catalog.get_all() if e.id == entry_id), None)
    if not entry:
        return f"❌ Tool '{entry_id}' not found in catalog."

    res = await register_mcp_server(entry)
    if res.get("success"):
        return f"✅ Successfully installed '{entry.name}' ({entry.id})."
    else:
        return (
            f"❌ Failed to install '{entry.name}': {res.get('error', 'Unknown error')}"
        )


def register_commands(ctx: Any, catalog: CatalogLoader) -> None:
    """Register /wright slash commands with Hermes."""
    global _HERMES_CONTEXT
    _HERMES_CONTEXT = ctx

    async def handle_wright(raw_args: str, **kwargs) -> str:
        args = raw_args.strip().split()
        if not args:
            return WRIGHT_HELP_TEXT

        subcommand = args[0].lower()

        if subcommand == "start":
            return await handle_start()
        elif subcommand == "stop":
            return await handle_stop()
        elif subcommand == "open":
            return await handle_open()
        elif subcommand == "doctor":
            return await handle_doctor()
        elif subcommand == "status":
            return await handle_status()
        elif subcommand == "debug-context":
            return _context_debug_text()
        elif subcommand == "catalog":
            if len(args) > 1 and args[1].lower() == "search":
                query = " ".join(args[2:])
                return handle_catalog_search(catalog, query)
            domain = args[1] if len(args) > 1 else None
            return handle_catalog_list(catalog, domain)
        elif subcommand == "info":
            entry_id = args[1] if len(args) > 1 else None
            return handle_info(catalog, entry_id)
        elif subcommand == "install":
            entry_id = args[1] if len(args) > 1 else None
            return await handle_install(catalog, entry_id)
        else:
            return WRIGHT_HELP_TEXT

    ctx.register_command(
        name="wright",
        handler=handle_wright,
        description="Wright engineering platform: start, stop, open UI, browse catalog, install tools.",
        args_hint="<subcommand> [args...]",
    )
