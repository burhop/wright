import os
from typing import Any, Dict, Optional

import httpx
import yaml

from .schemas import CatalogEntry

WRIGHT_API_BASE = "http://127.0.0.1:8000"
WRIGHT_UI_URL = "http://127.0.0.1:8000/"


def _is_wright_repo(directory: str) -> bool:
    """Check if a directory looks like the Wright repo root."""
    api_dir = os.path.join(directory, "api")
    apps_api_dir = os.path.join(directory, "apps", "api")
    return (
        os.path.isdir(directory)
        and os.path.isfile(os.path.join(directory, "pyproject.toml"))
        and (os.path.isdir(api_dir) or os.path.isdir(apps_api_dir))
        and os.path.isdir(os.path.join(directory, "apps", "web"))
    )


def detect_repo_dir() -> Optional[str]:
    """Auto-detect the Wright repo directory.

    Search order:
      1. WRIGHT_REPO_DIR environment variable (explicit override)
      2. Hermes config.yaml mcp_servers.wrightgateway --project flag
      3. Common filesystem locations (platform-aware)
    """
    # 1. Environment variable override — highest priority
    env_dir = os.environ.get("WRIGHT_REPO_DIR")
    if env_dir and _is_wright_repo(env_dir):
        return env_dir

    # 2. Hermes config.yaml (existing logic)
    config_paths = [
        os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml"),
    ]
    for path in config_paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
            mcp_servers = config.get("mcp_servers", {})
            gateway = mcp_servers.get("wrightgateway", {})
            args = gateway.get("args", [])
            # Find --project flag value
            for i, arg in enumerate(args):
                if arg == "--project" and i + 1 < len(args):
                    candidate = args[i + 1]
                    if _is_wright_repo(candidate):
                        return candidate
        except Exception:
            continue

    # 3. Common filesystem locations
    candidates = [
        # Windows common locations
        r"C:\wright",
        os.path.join(os.path.expanduser("~"), "wright"),
        os.path.join(os.path.expanduser("~"), "repos", "wright"),
        # Linux/macOS common locations
        os.path.expanduser("~/wright"),
        os.path.expanduser("~/repos/wright"),
        "/opt/wright",
    ]

    for candidate in candidates:
        if _is_wright_repo(candidate):
            return candidate

    return None


async def check_api_health() -> Dict[str, Any]:
    """Performs an async health check via GET /api/health."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{WRIGHT_API_BASE}/api/health")
            r.raise_for_status()
            data = r.json()
            return {
                "success": True,
                "connected": True,
                "state": data.get("state", "connected"),
                "latencyMs": data.get("latencyMs", 0.0),
            }
    except Exception as e:
        return {
            "success": False,
            "connected": False,
            "error": str(e),
        }


async def get_mcp_servers() -> Dict[str, Any]:
    """Retrieves list of registered MCP servers via GET /api/mcp/servers."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{WRIGHT_API_BASE}/api/mcp/servers")
            r.raise_for_status()
            data = r.json()
            return {
                "success": True,
                "servers": data.get("servers", []),
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def register_mcp_server(entry: CatalogEntry) -> Dict[str, Any]:
    """Registers an MCP server from a CatalogEntry via POST /api/mcp/servers."""
    command = entry.command
    if entry.transport == "webmcp" and command == []:
        command = None

    payload = {
        "name": entry.name,
        "type": entry.transport,
        "command": command,
        "category": entry.domains[0] if entry.domains else "utilities",
        "image_url": entry.image_url,
        "description": entry.description,
        "source_url": entry.source_url,
        "env_vars": [v.model_dump() for v in entry.env_vars]
        if entry.env_vars
        else None,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{WRIGHT_API_BASE}/api/mcp/servers", json=payload)
            r.raise_for_status()
            data = r.json()
            return {
                "success": True,
                "server_id": data.get("server_id"),
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def get_workspaces() -> Dict[str, Any]:
    """Retrieves list of workspaces via GET /api/workspace/list."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{WRIGHT_API_BASE}/api/workspace/list")
            r.raise_for_status()
            data = r.json()
            return {
                "success": True,
                "workspaces": data.get("workspaces", []),
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def get_credential_status(server_id: str) -> Dict[str, Any]:
    """Checks missing/configured credentials for a server via GET /api/mcp/servers/{id}/credentials."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(
                f"{WRIGHT_API_BASE}/api/mcp/servers/{server_id}/credentials"
            )
            r.raise_for_status()
            data = r.json()
            return {
                "success": True,
                "credentials": data.get("credentials", {}),
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
