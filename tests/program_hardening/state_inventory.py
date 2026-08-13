"""Shared deterministic fixtures for program-state compatibility tests."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from pathlib import Path


PROGRAM_STATE_TABLES = (
    "catalog_snapshots",
    "catalog_state",
    "mcp_servers",
    "engineering_workspaces",
    "workspace_workflow_binding_sets",
    "workspace_workflow_run_manifests",
    "engineering_scenario_runs",
    "engineering_scenario_assertions",
    "model_catalog_snapshots",
    "model_content_objects",
    "model_installations",
    "model_capability_bindings",
    "model_references",
)


def table_counts(
    database: str | Path, tables: Iterable[str] = PROGRAM_STATE_TABLES
) -> dict[str, int]:
    """Return only row counts for an explicit table allowlist."""

    result: dict[str, int] = {}
    with sqlite3.connect(database) as connection:
        existing = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        for table in tables:
            if table in existing:
                result[table] = int(
                    connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                )
    return result
