from __future__ import annotations

import json
import sqlite3
import time

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
                     verification_state, installability_tier, risk_level,
                     deployment_mode, platform_support, host_software_required,
                     credentials_required, default_enabled, approval_gates,
                     validation_result, follow_up_url, install_blocked_reason)
                VALUES (?, ?, ?, ?, 0, 0, 'inactive', ?, ?, ?, ?, ?, ?, ?, NULL, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                _entry_values(entry, now),
            )
            connection.execute(
                """UPDATE mcp_servers SET
                    name = ?, type = ?, command = ?, category = ?, image_url = ?,
                    description = ?, source_url = ?, instructions = ?,
                    env_vars = COALESCE(?, env_vars), verification_state = ?,
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
