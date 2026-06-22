"""Commands module for /wright slash commands."""
import asyncio
import os
import sys
import subprocess
import signal
import webbrowser
import httpx
import structlog
from typing import List, Optional, Dict, Any

from .bridge import (
    detect_repo_dir,
    check_api_health,
    get_mcp_servers,
    register_mcp_server,
    get_workspaces,
    get_credential_status,
    WRIGHT_API_BASE,
    WRIGHT_UI_URL,
)
from .catalog import CatalogLoader

logger = structlog.get_logger("hermes_plugin_wright.commands")

WRIGHT_HELP_TEXT = """🔧 Wright Engineering Platform

Usage: /wright <command>

  Launcher:
    start              Build frontend, start API server, open browser
    stop               Stop the API server
    open               Open Wright UI in browser
    doctor             Full health check of the Wright stack

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
    """Build frontend, start FastAPI, open browser."""
    # 1. Already running?
    if await is_api_healthy():
        webbrowser.open(WRIGHT_UI_URL)
        return (
            "✅ Wright is already running at http://localhost:8000\n"
            "   Browser opened."
        )

    # 2. Find repo
    repo_dir = detect_repo_dir()
    if not repo_dir:
        return (
            "❌ Could not find the Wright repo.\n"
            "   Clone it first:\n"
            "   git clone https://github.com/burhop/wright.git\n"
            "   Then run: /wright start"
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
            proc = subprocess.run(
                ["npm", "install"],
                cwd=web_dir,
                capture_output=True, text=True, timeout=120
            )
            if proc.returncode != 0:
                return f"❌ npm install failed:\n{proc.stderr[:500]}"

        proc = subprocess.run(
            ["npm", "run", "build"],
            cwd=web_dir,
            capture_output=True, text=True, timeout=120
        )
        if proc.returncode != 0:
            return f"❌ Frontend build failed:\n{proc.stderr[:500]}"

    # 4. Start FastAPI server (detached background process)
    log_dir = os.path.join(repo_dir, "tmp")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "wright-api.log")

    env = os.environ.copy()
    env["FRONTEND_DIST_DIR"] = dist_dir

    server_proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "api.main:app",
            "--host", "127.0.0.1",
            "--port", "8000",
        ],
        cwd=repo_dir,
        env=env,
        stdout=open(log_path, "a"),
        stderr=subprocess.STDOUT,
        start_new_session=True,  # Detach from Hermes process tree
    )

    # 5. Wait for health check (up to 15 seconds)
    for attempt in range(15):
        if await is_api_healthy():
            break
        if server_proc.poll() is not None:
            return f"❌ Server process exited with code {server_proc.returncode}\n   Check logs: {log_path}"
        await asyncio.sleep(1)
    else:
        return f"❌ Server did not become healthy within 15 seconds.\n   Check logs: {log_path}"

    # 6. Open browser
    webbrowser.open(WRIGHT_UI_URL)

    # 7. Write PID file for /wright stop
    pid_path = os.path.join(log_dir, "wright-api.pid")
    with open(pid_path, "w") as f:
        f.write(str(server_proc.pid))

    return (
        "🚀 Wright is running!\n\n"
        f"   API:     http://localhost:8000\n"
        f"   UI:      http://localhost:8000 (browser opened)\n"
        f"   Logs:    {log_path}\n"
        f"   PID:     {server_proc.pid}\n\n"
        "   Use `/wright stop` to shut down."
    )


async def handle_stop() -> str:
    """Stop the Wright FastAPI server."""
    repo_dir = detect_repo_dir()
    if not repo_dir:
        return "❌ Could not find the Wright repo."

    pid_path = os.path.join(repo_dir, "tmp", "wright-api.pid")
    if not os.path.exists(pid_path):
        if not await is_api_healthy():
            return "ℹ️ Wright is not running."
        return "⚠️ Wright is running but no PID file found. Stop it manually."

    try:
        with open(pid_path, "r") as f:
            pid = int(f.read().strip())

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
        return "✅ Wright server stopped."
    except OSError:
        if os.path.exists(pid_path):
            os.remove(pid_path)
        return "ℹ️ Wright server was already stopped (stale PID file cleaned up)."
    except Exception as e:
        return f"❌ Failed to stop Wright: {e}"


async def handle_open() -> str:
    """Open the Wright UI in the default browser."""
    if not await is_api_healthy():
        return (
            "❌ Wright is not running.\n"
            "   Use `/wright start` to launch it first."
        )
    webbrowser.open(WRIGHT_UI_URL)
    return "🌐 Opened Wright UI at http://localhost:8000"


async def handle_doctor() -> str:
    """Run a full health check of the Wright stack."""
    lines = ["🩺 Wright Doctor\n"]
    
    # 1. Repo detection
    repo_dir = detect_repo_dir()
    if repo_dir:
        lines.append(f"  ✅ Repo found:     {repo_dir}")
    else:
        lines.append("  ❌ Repo not found — clone https://github.com/burhop/wright.git")
        return "\n".join(lines)
    
    # 2. FastAPI server
    if await is_api_healthy():
        lines.append("  ✅ API server:     http://localhost:8000 (healthy)")
    else:
        lines.append("  ❌ API server:     not running — use /wright start")
    
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
        lines.append("  ⚠️ Database:       not yet created (will be created on first API start)")
    
    # 5. Secrets store
    secrets_path = os.path.expanduser("~/.config/wright/mcp-secrets.json")
    if os.path.exists(secrets_path):
        perms = oct(os.stat(secrets_path).st_mode)[-3:]
        if perms == "600":
            lines.append(f"  ✅ Secrets store:  {secrets_path} (mode 0600)")
        else:
            lines.append(f"  ⚠️ Secrets store:  {secrets_path} (mode 0{perms} — should be 0600)")
    else:
        lines.append("  ℹ️ Secrets store:  not yet created (created on first credential save)")
    
    # 6. Tool status (if API is up)
    if await is_api_healthy():
        try:
            res = await get_mcp_servers()
            if res.get("success"):
                servers = res.get("servers", [])
                installed = [s for s in servers if s.get("is_installed")]
                active = [s for s in servers if s.get("is_active")]
                lines.append(f"  ✅ MCP servers:    {len(installed)} installed, {len(active)} active")
                
                # Check for credential issues
                cred_issues = []
                for s in installed:
                    creds = s.get("credentials_configured", {})
                    missing = [k for k, v in creds.items() if not v]
                    if missing:
                        cred_issues.append(f"     ⚠️ {s['name']}: missing {', '.join(missing)}")
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
        ws_name = active_ws.get("workspace_name") or active_ws.get("session_id") or "Unnamed Workspace"
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
    lines.append("Use `/wright install <id>` to add a tool   |   `/wright info <id>` for details")
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
    lines.append("Use `/wright install <id>` to add a tool   |   `/wright info <id>` for details")
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
            lines.append(f"- **{v.name}** ({v.label}): {v.description} ({req_str}, {sec_str})")
        lines.append("")
        
    if entry.dependencies and (entry.dependencies.system or entry.dependencies.python or entry.dependencies.node):
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
        return f"❌ Failed to install '{entry.name}': {res.get('error', 'Unknown error')}"

def register_commands(ctx: Any, catalog: CatalogLoader) -> None:
    """Register /wright slash commands with Hermes."""
    
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
        args_hint="<subcommand> [args...]"
    )
