from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from data_vault.migrations import MIGRATIONS, upgrade_database

LEGACY_CATALOG_SERVER_ID = "autodesk-aps-official"
CUSTOM_SERVER_ID = "custom-v12-sentinel"
ERROR_SERVER_ID = "error-v12-sentinel"
LEGACY_TOOL_ID = f"{LEGACY_CATALOG_SERVER_ID}:legacy-design"
WORKSPACE_ID = "workspace-v12-sentinel"


def create_capability_library_v12_database(path: Path) -> Path:
    """Create a realistic schema-12 database with user-owned MCP sentinels."""

    upgrade_database(path, migrations=MIGRATIONS[:12])
    credential_definition = json.dumps(
        [
            {
                "name": "APS_CLIENT_ID",
                "label": "APS client ID",
                "description": "Stored by the external secret provider",
                "required": True,
                "secret": True,
            }
        ]
    )
    custom_credential_definition = json.dumps(
        [
            {
                "name": "LOCAL_TOKEN",
                "label": "Local token",
                "description": "Prevents an unapproved connection during tests",
                "required": True,
                "secret": True,
            }
        ]
    )
    with sqlite3.connect(path) as connection:
        connection.executemany(
            """INSERT INTO mcp_servers (
                server_id, name, type, command, is_active, is_installed, status,
                error_message, category, created_at, updated_at, installed_version,
                env_vars, credentials_required, default_enabled
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                (
                    LEGACY_CATALOG_SERVER_ID,
                    "Legacy Autodesk APS",
                    "stdio",
                    '["legacy-aps", "--stdio"]',
                    0,
                    1,
                    "inactive",
                    None,
                    "cad",
                    101,
                    202,
                    "2.4.0",
                    credential_definition,
                    json.dumps(["APS_CLIENT_ID"]),
                    0,
                ),
                (
                    CUSTOM_SERVER_ID,
                    "Private V12 Geometry Server",
                    "sse",
                    "http://127.0.0.1:8765/sse",
                    0,
                    0,
                    "inactive",
                    None,
                    "cad",
                    102,
                    203,
                    None,
                    custom_credential_definition,
                    json.dumps(["LOCAL_TOKEN"]),
                    1,
                ),
                (
                    ERROR_SERVER_ID,
                    "Unresolved V12 Server",
                    "stdio",
                    '["missing-v12-server"]',
                    0,
                    0,
                    "error",
                    "legacy failure sentinel",
                    "simulation",
                    103,
                    204,
                    None,
                    None,
                    "[]",
                    1,
                ),
            ),
        )
        connection.execute(
            """INSERT INTO mcp_tools (
                tool_id, server_id, name, description, input_schema,
                is_enabled, created_at, title, output_schema, annotations, meta
            ) VALUES (?, ?, 'legacy_design', 'Legacy design tool', '{}', 0, 301,
                      'Legacy design', '{"type":"object"}',
                      '{"readOnlyHint":true}', '{"sentinel":"preserve"}')""",
            (LEGACY_TOOL_ID, LEGACY_CATALOG_SERVER_ID),
        )
        connection.execute(
            """INSERT INTO engineering_workspaces (
                workspace_id, session_id, local_path, enabled_tools,
                created_at, updated_at, workspace_name
            ) VALUES (?, 'session-v12-sentinel', 'D:/workspace/v12', ?, 401, 402,
                      'V12 preservation workspace')""",
            (
                WORKSPACE_ID,
                json.dumps([LEGACY_CATALOG_SERVER_ID, CUSTOM_SERVER_ID]),
            ),
        )
        connection.commit()
    return path
