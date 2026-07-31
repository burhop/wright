from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any

import yaml

from .engineering_catalog import ENGINEERING_CATALOG


def reconcile_engineering_catalog(database_path: str) -> int:
    """Reconcile Wright-owned catalog rows after schema readiness."""
    catalog_ids = [entry["server_id"] for entry in ENGINEERING_CATALOG]
    placeholders = ",".join("?" for _ in catalog_ids)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            f"""UPDATE mcp_servers
            SET is_installed = 0, is_active = 0, status = 'inactive',
                error_message = NULL, installed_version = NULL
            WHERE is_installed = 1 AND status = 'error'
              AND server_id IN ({placeholders})""",
            tuple(catalog_ids),
        )
        now = int(time.time())
        for entry in ENGINEERING_CATALOG:
            connection.execute(
                """INSERT OR IGNORE INTO mcp_servers
                    (server_id, name, type, command, is_active, is_installed, status,
                     category, created_at, updated_at, image_url, description,
                     source_url, instructions, installed_version, env_vars,
                     launch_env,
                     verification_state, installability_tier, risk_level,
                     deployment_mode, platform_support, host_software_required,
                     credentials_required, default_enabled, approval_gates,
                     validation_result, follow_up_url, install_blocked_reason)
                VALUES (?, ?, ?, ?, 0, 0, 'inactive', ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                _entry_values(entry, now),
            )
            connection.execute(
                """UPDATE mcp_servers SET
                    name = ?, type = ?, command = ?, category = ?, image_url = ?,
                    description = ?, source_url = ?, instructions = ?,
                    env_vars = COALESCE(?, env_vars), launch_env = ?,
                    verification_state = ?,
                    installability_tier = ?, risk_level = ?, deployment_mode = ?,
                    platform_support = ?, host_software_required = ?,
                    credentials_required = ?, default_enabled = ?, approval_gates = ?,
                    validation_result = ?, follow_up_url = ?, install_blocked_reason = ?
                WHERE server_id = ?""",
                _update_values(entry),
            )
        connection.commit()
        return len(ENGINEERING_CATALOG)
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def reconcile_installed_bundle(
    database_path: str,
    *,
    bundle_path: str | os.PathLike[str] | None = None,
    status_path: str | os.PathLike[str] | None = None,
    config_path: str | os.PathLike[str] | None = None,
) -> int:
    """Mark MCPs shipped in this Docker appliance as installed in the registry."""
    bundle_path = bundle_path or os.getenv("WRIGHT_MCP_BUNDLE")
    status_path = status_path or os.getenv("WRIGHT_MCP_STATUS")
    config_path = config_path or os.getenv("WRIGHT_MCP_HERMES_CONFIG")
    status = _read_json(status_path)
    if not status:
        return 0

    bundle = _read_yaml(bundle_path)
    generated_config = _read_yaml(config_path)
    generated_servers = generated_config.get("mcp_servers", {})
    if not isinstance(generated_servers, dict):
        generated_servers = {}

    bundle_servers = _bundle_entries_by_id(bundle, "mcp_servers")
    bundle_apps = _bundle_entries_by_id(bundle, "applications")
    bundle_id = str(
        status.get("bundle_id") or bundle.get("bundle_id") or "wright-mcp-appliance"
    )
    platform_key = _platform_key(bundle_id)
    now = int(time.time())
    upserted = 0

    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        for status_entry in status.get("mcp_servers", []):
            if not _accepted_local_entry(status_entry):
                continue
            server_id = str(status_entry["id"])
            manifest_entry = bundle_servers.get(server_id, {})
            generated_entry = generated_servers.get(server_id, {})
            command = _generated_command(generated_entry, manifest_entry)
            if not command:
                continue
            application_id = manifest_entry.get("application_id")
            app_entry = bundle_apps.get(application_id, {}) if application_id else {}
            launch_env = _workspace_launch_env(manifest_entry)
            env_vars = _static_launch_env(generated_entry)
            validation_result = {
                "status": "not_tested",
                "message": f"Installed from reviewed Wright MCP appliance bundle {bundle_id}.",
                "environment": bundle_id,
                "missing_dependencies": [],
            }
            connection.execute(
                """INSERT INTO mcp_servers (
                    server_id, name, type, command, is_active, is_installed, status,
                    error_message, category, created_at, updated_at, image_url,
                    description, source_url, installed_version, env_vars, launch_env,
                    instructions, verification_state, installability_tier, risk_level,
                    deployment_mode, platform_support, host_software_required,
                    credentials_required, default_enabled, approval_gates,
                    validation_result, follow_up_url, install_blocked_reason
                ) VALUES (?, ?, 'stdio', ?, 0, 1, 'inactive', NULL, ?, ?, ?, NULL,
                    ?, ?, ?, ?, ?, ?, 'verified_mcp', 'tested', ?, 'local-bundled',
                    ?, ?, ?, 1, ?, ?, NULL, NULL)
                ON CONFLICT(server_id) DO UPDATE SET
                    name = excluded.name,
                    type = excluded.type,
                    command = excluded.command,
                    is_installed = 1,
                    status = CASE
                        WHEN mcp_servers.is_active = 1 THEN mcp_servers.status
                        ELSE 'inactive'
                    END,
                    error_message = NULL,
                    category = excluded.category,
                    updated_at = excluded.updated_at,
                    description = excluded.description,
                    source_url = excluded.source_url,
                    installed_version = excluded.installed_version,
                    env_vars = excluded.env_vars,
                    launch_env = excluded.launch_env,
                    instructions = excluded.instructions,
                    verification_state = excluded.verification_state,
                    installability_tier = excluded.installability_tier,
                    risk_level = excluded.risk_level,
                    deployment_mode = excluded.deployment_mode,
                    platform_support = excluded.platform_support,
                    host_software_required = excluded.host_software_required,
                    credentials_required = excluded.credentials_required,
                    default_enabled = excluded.default_enabled,
                    approval_gates = excluded.approval_gates,
                    validation_result = excluded.validation_result,
                    install_blocked_reason = NULL""",
                (
                    server_id,
                    str(
                        status_entry.get("display_name")
                        or manifest_entry.get("display_name")
                        or server_id
                    ),
                    json.dumps(command),
                    _registry_category(app_entry, manifest_entry),
                    now,
                    now,
                    str(manifest_entry.get("docs_summary") or ""),
                    _source_url(manifest_entry),
                    _installed_version(manifest_entry),
                    json.dumps(env_vars),
                    json.dumps(launch_env),
                    str(manifest_entry.get("docs_summary") or ""),
                    _risk_level(server_id, manifest_entry),
                    json.dumps(_platform_support(platform_key, bundle_id)),
                    json.dumps(_host_software_required(app_entry, manifest_entry)),
                    json.dumps(_credentials_required(manifest_entry)),
                    json.dumps(["wright-mcp-appliance-bundle"]),
                    json.dumps(validation_result),
                ),
            )
            upserted += 1
        connection.commit()
        return upserted
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _entry_values(entry: dict, now: int) -> tuple:
    return (
        entry["server_id"],
        entry["name"],
        entry["type"],
        entry["command"],
        entry["category"],
        now,
        now,
        entry.get("image_url"),
        entry["description"],
        entry.get("source_url"),
        entry.get("instructions"),
        entry.get("env_vars"),
        entry.get("launch_env", "{}"),
        entry["verification_state"],
        entry["installability_tier"],
        entry["risk_level"],
        entry["deployment_mode"],
        json.dumps(entry["platform_support"]),
        json.dumps(entry["host_software_required"]),
        json.dumps(entry["credentials_required"]),
        1 if entry["default_enabled"] else 0,
        json.dumps(entry["approval_gates"]),
        json.dumps(entry["validation_result"]),
        entry.get("follow_up_url"),
        entry.get("install_blocked_reason"),
    )


def _read_json(path: str | os.PathLike[str] | None) -> dict[str, Any]:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.is_file():
        return {}
    payload = json.loads(candidate.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _read_yaml(path: str | os.PathLike[str] | None) -> dict[str, Any]:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.is_file():
        return {}
    payload = yaml.safe_load(candidate.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _bundle_entries_by_id(
    bundle: dict[str, Any], key: str
) -> dict[str, dict[str, Any]]:
    entries = bundle.get(key)
    if not isinstance(entries, list):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            result[entry["id"]] = entry
    return result


def _accepted_local_entry(entry: Any) -> bool:
    return (
        isinstance(entry, dict)
        and isinstance(entry.get("id"), str)
        and entry.get("availability") == "local_enabled"
        and entry.get("status") == "accepted"
    )


def _generated_command(
    generated_entry: Any, manifest_entry: dict[str, Any]
) -> list[str]:
    if isinstance(generated_entry, dict):
        command = generated_entry.get("command")
        if isinstance(command, str) and command:
            args = generated_entry.get("args")
            return (
                [command, *[str(item) for item in args]]
                if isinstance(args, list)
                else [command]
            )
    launch = manifest_entry.get("launch")
    if isinstance(launch, dict) and isinstance(launch.get("command"), list):
        return [str(item) for item in launch["command"]]
    return []


def _static_launch_env(generated_entry: Any) -> dict[str, str]:
    if not isinstance(generated_entry, dict):
        return {}
    env = generated_entry.get("env")
    if not isinstance(env, dict):
        return {}
    return {str(key): str(value) for key, value in env.items()}


def _workspace_launch_env(manifest_entry: dict[str, Any]) -> dict[str, str]:
    binding = manifest_entry.get("workspace_binding")
    if not isinstance(binding, dict):
        return {}
    env = binding.get("env")
    if not isinstance(env, dict):
        return {}
    return {str(key): str(value) for key, value in env.items()}


def _source_url(manifest_entry: dict[str, Any]) -> str | None:
    source = manifest_entry.get("mcp_source")
    if not isinstance(source, dict):
        return None
    for key in ("url", "repository", "default_url"):
        value = source.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _installed_version(manifest_entry: dict[str, Any]) -> str | None:
    source = manifest_entry.get("mcp_source")
    if not isinstance(source, dict):
        return None
    for key in ("package_version", "version", "tag", "ref", "default_ref"):
        value = source.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _registry_category(
    app_entry: dict[str, Any], manifest_entry: dict[str, Any]
) -> str:
    raw = str(app_entry.get("category") or manifest_entry.get("category") or "").lower()
    if "browser" in raw or "playwright" in raw:
        return "utilities"
    if "cad" in raw or "brep" in raw or "model" in raw or "solid" in raw:
        return "cad"
    return "utilities"


def _risk_level(server_id: str, manifest_entry: dict[str, Any]) -> str:
    text = f"{server_id} {manifest_entry.get('docs_summary', '')}".lower()
    if "playwright" in text or manifest_entry.get("availability") == "windows_only":
        return "medium"
    return "low"


def _platform_key(bundle_id: str) -> str | None:
    if "linux-arm64" in bundle_id:
        return "linux_arm64"
    if "linux-amd64" in bundle_id or "linux-x64" in bundle_id:
        return "linux_x64"
    if "windows" in bundle_id:
        return "windows_11_x64"
    return None


def _platform_support(
    current_platform: str | None, bundle_id: str
) -> dict[str, dict[str, object]]:
    support = {
        "windows_11_x64": {
            "status": "unknown",
            "tested": False,
            "notes": "not bundled in this image",
        },
        "linux_x64": {
            "status": "unknown",
            "tested": False,
            "notes": "not bundled in this image",
        },
        "linux_arm64": {
            "status": "unknown",
            "tested": False,
            "notes": "not bundled in this image",
        },
        "macos_x64": {
            "status": "unknown",
            "tested": False,
            "notes": "not bundled in this image",
        },
        "macos_arm64": {
            "status": "unknown",
            "tested": False,
            "notes": "not bundled in this image",
        },
    }
    if current_platform:
        support[current_platform] = {
            "status": "yes",
            "tested": True,
            "notes": f"Installed from {bundle_id}",
        }
    return support


def _host_software_required(
    app_entry: dict[str, Any], manifest_entry: dict[str, Any]
) -> list[str]:
    display_name = app_entry.get("display_name")
    return [str(display_name)] if isinstance(display_name, str) and display_name else []


def _credentials_required(manifest_entry: dict[str, Any]) -> list[str]:
    env_vars = manifest_entry.get("env_vars")
    if not isinstance(env_vars, list):
        return []
    return [
        str(item.get("name"))
        for item in env_vars
        if isinstance(item, dict) and item.get("required") and item.get("name")
    ]


def _update_values(entry: dict) -> tuple:
    return (
        entry["name"],
        entry["type"],
        entry["command"],
        entry["category"],
        entry.get("image_url"),
        entry["description"],
        entry.get("source_url"),
        entry.get("instructions"),
        entry.get("env_vars"),
        entry.get("launch_env", "{}"),
        entry["verification_state"],
        entry["installability_tier"],
        entry["risk_level"],
        entry["deployment_mode"],
        json.dumps(entry["platform_support"]),
        json.dumps(entry["host_software_required"]),
        json.dumps(entry["credentials_required"]),
        1 if entry["default_enabled"] else 0,
        json.dumps(entry["approval_gates"]),
        json.dumps(entry["validation_result"]),
        entry.get("follow_up_url"),
        entry.get("install_blocked_reason"),
        entry["server_id"],
    )
