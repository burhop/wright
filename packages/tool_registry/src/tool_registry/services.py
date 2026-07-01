from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .db import (
    delete_server as db_delete_server,
    get_server,
    get_server_by_name,
    get_servers,
    get_tool,
    get_tools,
    insert_server,
    update_server as db_update_server,
    update_tool_enabled,
)
from .mcp_catalog import is_install_blocked, tier_sort_key
from .mcp_followups import write_followup_record
from .mcp_validation import classify_server
from .manager import McpEngine
from .models import EnvVarDefinition, McpServer, McpServerCreate, McpTool
from .secrets import delete_secrets, has_credentials, read_secrets, write_secrets
from .version_check import check_server_version, update_server as update_server_version


class McpServiceError(Exception):
    """Base exception for package-level MCP service operations."""


class McpNotFoundError(McpServiceError):
    pass


class McpConflictError(McpServiceError):
    pass


class McpInvalidOperationError(McpServiceError):
    pass


class McpOperationError(McpServiceError):
    pass


@dataclass(frozen=True)
class McpInstallResult:
    server: McpServer
    sync_session_id: str | None = None


def _server_not_found(server_id: str) -> McpNotFoundError:
    return McpNotFoundError(f"MCP Server '{server_id}' not found.")


def _require_server(db_path: str, server_id: str) -> McpServer:
    server = get_server(db_path, server_id)
    if not server:
        raise _server_not_found(server_id)
    return server


def list_registered_servers(db_path: str) -> list[McpServer]:
    servers = sorted(get_servers(db_path), key=tier_sort_key)
    for server in servers:
        if server.env_vars and isinstance(server.env_vars, list):
            var_names = [
                var.name for var in server.env_vars if isinstance(var, EnvVarDefinition)
            ]
            if var_names:
                server.credentials_configured = has_credentials(
                    server.server_id, var_names
                )
    return servers


def register_server(
    db_path: str,
    body: McpServerCreate,
    *,
    server_id: str | None = None,
    now: int | None = None,
) -> McpServer:
    existing = get_server_by_name(db_path, body.name)
    if existing:
        raise McpConflictError(
            f"An MCP server with the name '{body.name}' is already registered."
        )

    timestamp = int(time.time()) if now is None else now
    new_server = McpServer(
        server_id=server_id or str(uuid.uuid4()),
        name=body.name,
        type=body.type,
        command=body.command,
        is_active=False,
        status="inactive",
        error_message=None,
        category=body.category,
        created_at=timestamp,
        updated_at=timestamp,
        image_url=body.image_url,
        description=body.description,
        source_url=body.source_url,
        installed_version=body.installed_version,
        env_vars=body.env_vars,
        instructions=body.instructions,
        verification_state=body.verification_state,
        installability_tier=body.installability_tier,
        risk_level=body.risk_level,
        deployment_mode=body.deployment_mode,
        platform_support=body.platform_support,
        host_software_required=body.host_software_required,
        credentials_required=body.credentials_required,
        default_enabled=body.default_enabled,
        approval_gates=body.approval_gates,
        validation_result=body.validation_result,
        follow_up_url=body.follow_up_url,
        install_blocked_reason=body.install_blocked_reason,
    )
    insert_server(db_path, new_server)
    return new_server


async def toggle_server_activation(
    engine: McpEngine, server_id: str, is_active: bool
) -> McpServer:
    _require_server(engine.db_path, server_id)
    if is_active:
        return await engine.start_server(server_id)
    return await engine.stop_server(server_id)


async def install_server(
    engine: McpEngine,
    server_id: str,
    *,
    session_id: str | None = None,
    is_server_enabled_for_session: Callable[[McpServer], bool] | None = None,
) -> McpInstallResult:
    server = _require_server(engine.db_path, server_id)
    if is_install_blocked(server):
        reason = server.install_blocked_reason or (
            f"Server '{server.name}' is marked {server.installability_tier}."
        )
        raise McpInvalidOperationError(reason)

    db_update_server(
        engine.db_path,
        server_id,
        {"is_installed": True, "updated_at": int(time.time())},
    )

    updated = await engine.start_server(server_id)

    should_stop = True
    if session_id and is_server_enabled_for_session:
        should_stop = not is_server_enabled_for_session(updated)

    if should_stop:
        updated = await engine.stop_server(server_id)
        db_update_server(engine.db_path, server_id, {"is_installed": True})
        updated.is_installed = True

    return McpInstallResult(server=updated, sync_session_id=session_id)


async def uninstall_server(
    engine: McpEngine, server_id: str, *, session_id: str | None = None
) -> McpInstallResult:
    _require_server(engine.db_path, server_id)
    await engine.stop_server(server_id)
    updated = db_update_server(
        engine.db_path,
        server_id,
        {
            "is_installed": False,
            "is_active": False,
            "status": "inactive",
            "updated_at": int(time.time()),
        },
    )
    if not updated:
        raise _server_not_found(server_id)
    return McpInstallResult(server=updated, sync_session_id=session_id)


async def delete_registered_server(engine: McpEngine, server_id: str) -> McpServer:
    server = _require_server(engine.db_path, server_id)
    await engine.stop_server(server_id)
    db_delete_server(engine.db_path, server_id)
    delete_secrets(server_id)
    server.is_active = False
    return server


def list_registered_tools(db_path: str) -> list[McpTool]:
    return get_tools(db_path)


def set_tool_enabled(db_path: str, tool_id: str, is_enabled: bool) -> McpTool:
    tool = get_tool(db_path, tool_id)
    if not tool:
        raise McpNotFoundError(f"MCP Tool '{tool_id}' not found.")

    if not update_tool_enabled(db_path, tool_id, is_enabled):
        raise McpOperationError("Failed to update tool state in database.")

    tool.is_enabled = is_enabled
    return tool


def validate_registered_server(
    db_path: str,
    server_id: str,
    *,
    followup_dir: Path = Path("docs/mcp-catalog/followups"),
):
    server = _require_server(db_path, server_id)
    result = classify_server(server)
    follow_up_url = result.follow_up_url
    if result.status == "failed" or result.installability_tier == "non_working":
        follow_up_url = write_followup_record(
            followup_dir,
            result,
            source_url=server.source_url,
            verification_state=server.verification_state,
        )
        result.follow_up_url = follow_up_url

    db_update_server(
        db_path,
        server_id,
        {
            "validation_result": result.as_summary(),
            "installability_tier": result.installability_tier,
            "follow_up_url": follow_up_url,
        },
    )
    return result


def report_missing_server(
    db_path: str,
    *,
    name: str,
    source_url: str | None = None,
    notes: str | None = None,
    category: str = "utilities",
    now: int | None = None,
) -> McpServer:
    normalized = "".join(
        char.lower() if char.isalnum() else "-" for char in name.strip()
    ).strip("-")
    normalized = "-".join(part for part in normalized.split("-") if part)
    server_id = f"reported-{normalized or uuid.uuid4().hex[:8]}"

    existing = get_server(db_path, server_id)
    if existing:
        return existing

    timestamp = int(time.time()) if now is None else now
    server = McpServer(
        server_id=server_id,
        name=name,
        type="stdio",
        command=None,
        is_active=False,
        is_installed=False,
        status="inactive",
        category=category,
        created_at=timestamp,
        updated_at=timestamp,
        description=notes or "User-reported MCP candidate pending verification.",
        source_url=source_url,
        verification_state="user_reported_url_needed",
        installability_tier="blocked",
        risk_level="low",
        deployment_mode="unknown",
        default_enabled=False,
        install_blocked_reason=(
            "User-reported MCP candidate pending source and install verification."
        ),
    )
    insert_server(db_path, server)
    return server


async def check_registered_server_version(db_path: str, server_id: str) -> dict:
    server = _require_server(db_path, server_id)
    if server.type in ("sse", "webmcp"):
        raise McpInvalidOperationError(
            "Version check not applicable for network-type servers."
        )

    result = await check_server_version(server)
    if "error" in result and result["error"] is not None:
        if result["error"] == "unsupported_package_manager":
            return {
                "server_id": server_id,
                "installed": None,
                "latest": None,
                "update_available": False,
                "error": result["error"],
            }
        raise McpOperationError(f"Version check failed: {result['error']}")
    return result


async def update_registered_server_version(db_path: str, server_id: str) -> dict:
    server = _require_server(db_path, server_id)
    if server.type != "stdio":
        raise McpInvalidOperationError("Update not applicable for network-type servers.")

    result = await update_server_version(server)
    if result.get("error"):
        raise McpOperationError(f"Update failed: {result['error']}")

    db_update_server(
        db_path,
        server_id,
        {
            "installed_version": result["installed_version"],
            "updated_at": int(time.time()),
        },
    )

    return {
        "server_id": server_id,
        "installed_version": result["installed_version"],
        "success": True,
        "error": None,
    }


def get_credential_status(db_path: str, server_id: str) -> dict:
    server = _require_server(db_path, server_id)
    env_var_defs = []
    configured = {}
    if server.env_vars and isinstance(server.env_vars, list):
        env_var_defs = [
            var.model_dump() if isinstance(var, EnvVarDefinition) else var
            for var in server.env_vars
        ]
        var_names = [
            var.name for var in server.env_vars if isinstance(var, EnvVarDefinition)
        ]
        configured = has_credentials(server_id, var_names)

    return {
        "server_id": server_id,
        "env_vars": env_var_defs,
        "configured": configured,
    }


def save_server_credentials(
    db_path: str, server_id: str, credentials: dict[str, object]
) -> dict:
    _require_server(db_path, server_id)

    sanitized: dict[str, str] = {}
    for key, value in credentials.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise McpInvalidOperationError("Credential keys and values must be strings.")
        if value.strip():
            sanitized[key] = value

    if sanitized:
        existing = read_secrets(server_id)
        write_secrets(server_id, {**existing, **sanitized})

    return get_credential_status(db_path, server_id)


def delete_server_credentials(db_path: str, server_id: str) -> None:
    _require_server(db_path, server_id)
    delete_secrets(server_id)
