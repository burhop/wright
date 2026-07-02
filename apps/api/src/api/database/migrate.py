import os
import sys
import json
import time

# Ensure api package is importable when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from api.config import DATABASE_PATH

from data_vault import connect_state_db
from tool_registry.engineering_catalog import ENGINEERING_CATALOG


def run_migrations():
    print(f"Running database migrations on: {DATABASE_PATH}")
    conn = connect_state_db(DATABASE_PATH, ensure_parent=True)
    try:
        # 1. Create mcp_servers table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mcp_servers (
            server_id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL CHECK(type IN ('stdio', 'sse', 'webmcp')),
            command TEXT,
            is_active INTEGER NOT NULL DEFAULT 0 CHECK(is_active IN (0, 1)),
            is_installed INTEGER NOT NULL DEFAULT 0 CHECK(is_installed IN (0, 1)),
            status TEXT NOT NULL DEFAULT 'inactive' CHECK(status IN ('active', 'inactive', 'error')),
            error_message TEXT,
            category TEXT NOT NULL DEFAULT 'utilities',
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            image_url TEXT,
            description TEXT,
            source_url TEXT,
            installed_version TEXT,
            env_vars TEXT,
            instructions TEXT,
            verification_state TEXT DEFAULT 'user_reported_url_needed',
            installability_tier TEXT DEFAULT 'might_work',
            risk_level TEXT DEFAULT 'low',
            deployment_mode TEXT DEFAULT 'unknown',
            platform_support TEXT,
            host_software_required TEXT,
            credentials_required TEXT,
            default_enabled INTEGER DEFAULT 1,
            approval_gates TEXT,
            validation_result TEXT,
            follow_up_url TEXT,
            install_blocked_reason TEXT
        );
        """)

        # 2. Create mcp_tools table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS mcp_tools (
            tool_id TEXT PRIMARY KEY,
            server_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            input_schema TEXT NOT NULL,
            is_enabled INTEGER NOT NULL DEFAULT 1 CHECK(is_enabled IN (0, 1)),
            created_at INTEGER NOT NULL,
            FOREIGN KEY (server_id) REFERENCES mcp_servers(server_id) ON DELETE CASCADE
        );
        """)

        # 3.  One-time cleanup: remove junk / test entries
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(mcp_servers)")
        existing_mcp_columns = [col[1] for col in cursor.fetchall()]
        early_mcp_columns = [
            ("image_url", "TEXT"),
            ("description", "TEXT"),
            ("source_url", "TEXT"),
            ("installed_version", "TEXT"),
            ("env_vars", "TEXT"),
            ("instructions", "TEXT"),
            ("verification_state", "TEXT DEFAULT 'user_reported_url_needed'"),
            ("installability_tier", "TEXT DEFAULT 'might_work'"),
            ("risk_level", "TEXT DEFAULT 'low'"),
            ("deployment_mode", "TEXT DEFAULT 'unknown'"),
            ("platform_support", "TEXT"),
            ("host_software_required", "TEXT"),
            ("credentials_required", "TEXT"),
            ("default_enabled", "INTEGER DEFAULT 1"),
            ("approval_gates", "TEXT"),
            ("validation_result", "TEXT"),
            ("follow_up_url", "TEXT"),
            ("install_blocked_reason", "TEXT"),
        ]
        for col_name, col_def in early_mcp_columns:
            if existing_mcp_columns and col_name not in existing_mcp_columns:
                conn.execute(
                    f"ALTER TABLE mcp_servers ADD COLUMN {col_name} {col_def};"
                )

        conn.execute("DELETE FROM mcp_servers WHERE name LIKE 'Playwright Test%'")
        conn.execute("DELETE FROM mcp_servers WHERE name = 'Calcul mesh'")
        conn.execute("DELETE FROM mcp_servers WHERE name = 'Custom SSE Link'")

        # 4. Fix false is_installed flags.
        #    Reset catalog servers that are marked installed+error but are not
        #    usable. Do not reset custom user-added servers.
        catalog_ids = [entry["server_id"] for entry in ENGINEERING_CATALOG]
        placeholders = ",".join("?" for _ in catalog_ids)
        conn.execute(
            f"""
        UPDATE mcp_servers
        SET is_installed = 0,
            is_active = 0,
            status = 'inactive',
            error_message = NULL,
            installed_version = NULL
        WHERE is_installed = 1
          AND status = 'error'
          AND server_id IN ({placeholders})
        """,
            tuple(catalog_ids),
        )

        # 5. Seed the full engineering catalog
        now = int(time.time())
        for entry in ENGINEERING_CATALOG:
            conn.execute(
                """
            INSERT OR IGNORE INTO mcp_servers 
                (server_id, name, type, command, is_active, is_installed, status,
                 category, created_at, updated_at, image_url, description,
                 source_url, instructions, installed_version, env_vars,
                 verification_state, installability_tier, risk_level, deployment_mode,
                 platform_support, host_software_required, credentials_required,
                 default_enabled, approval_gates, validation_result, follow_up_url,
                 install_blocked_reason)
            VALUES (?, ?, ?, ?, 0, 0, 'inactive', ?, ?, ?, ?, ?, ?, ?, NULL, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
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
                ),
            )

        # 6. Update existing catalog entries to the latest metadata from the catalog
        for entry in ENGINEERING_CATALOG:
            conn.execute(
                """
            UPDATE mcp_servers
            SET name = ?,
                type = ?,
                command = ?,
                category = ?,
                image_url = ?,
                description = ?,
                source_url = ?,
                instructions = ?,
                env_vars = COALESCE(?, env_vars),
                verification_state = ?,
                installability_tier = ?,
                risk_level = ?,
                deployment_mode = ?,
                platform_support = ?,
                host_software_required = ?,
                credentials_required = ?,
                default_enabled = ?,
                approval_gates = ?,
                validation_result = ?,
                follow_up_url = ?,
                install_blocked_reason = ?
            WHERE server_id = ?
            """,
                (
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
                ),
            )

        # 7. Create engineering_workspaces table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS engineering_workspaces (
            workspace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            local_path TEXT NOT NULL,
            git_remote_url TEXT,
            git_username TEXT,
            git_token TEXT,
            enabled_tools TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL,
            workspace_name TEXT,
            workspace_prompt TEXT,
            git_large_file_threshold INTEGER DEFAULT 10485760
        );
        """)

        # Check if enabled_tools column exists, add it if not (for existing databases)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(engineering_workspaces)")
        columns = [col[1] for col in cursor.fetchall()]
        if columns and "enabled_tools" not in columns:
            conn.execute(
                "ALTER TABLE engineering_workspaces ADD COLUMN enabled_tools TEXT;"
            )
            print("Added enabled_tools column to engineering_workspaces table.")

        # Check if is_installed column exists in mcp_servers, add it if not (for existing databases)
        cursor.execute("PRAGMA table_info(mcp_servers)")
        mcp_columns = [col[1] for col in cursor.fetchall()]
        if mcp_columns and "is_installed" not in mcp_columns:
            conn.execute(
                "ALTER TABLE mcp_servers ADD COLUMN is_installed INTEGER NOT NULL DEFAULT 0 CHECK(is_installed IN (0, 1));"
            )
            print("Added is_installed column to mcp_servers table.")

        new_cols = [
            ("image_url", "TEXT"),
            ("description", "TEXT"),
            ("source_url", "TEXT"),
            ("installed_version", "TEXT"),
            ("env_vars", "TEXT"),
            ("instructions", "TEXT"),
            ("verification_state", "TEXT DEFAULT 'user_reported_url_needed'"),
            ("installability_tier", "TEXT DEFAULT 'might_work'"),
            ("risk_level", "TEXT DEFAULT 'low'"),
            ("deployment_mode", "TEXT DEFAULT 'unknown'"),
            ("platform_support", "TEXT"),
            ("host_software_required", "TEXT"),
            ("credentials_required", "TEXT"),
            ("default_enabled", "INTEGER DEFAULT 1"),
            ("approval_gates", "TEXT"),
            ("validation_result", "TEXT"),
            ("follow_up_url", "TEXT"),
            ("install_blocked_reason", "TEXT"),
        ]
        for col_name, col_def in new_cols:
            if mcp_columns and col_name not in mcp_columns:
                conn.execute(
                    f"ALTER TABLE mcp_servers ADD COLUMN {col_name} {col_def};"
                )
                print(f"Added {col_name} column to mcp_servers table.")

        # 8. Add workspace_name column if missing (007-workspace-dashboard-ux)
        cursor.execute("PRAGMA table_info(engineering_workspaces)")
        ws_columns = [col[1] for col in cursor.fetchall()]
        if ws_columns and "workspace_name" not in ws_columns:
            conn.execute(
                "ALTER TABLE engineering_workspaces ADD COLUMN workspace_name TEXT;"
            )
            print("Added workspace_name column to engineering_workspaces table.")

        if ws_columns and "workspace_prompt" not in ws_columns:
            conn.execute(
                "ALTER TABLE engineering_workspaces ADD COLUMN workspace_prompt TEXT;"
            )
            print("Added workspace_prompt column to engineering_workspaces table.")

        if ws_columns and "git_large_file_threshold" not in ws_columns:
            conn.execute(
                "ALTER TABLE engineering_workspaces ADD COLUMN git_large_file_threshold INTEGER DEFAULT 10485760;"
            )
            print(
                "Added git_large_file_threshold column to engineering_workspaces table."
            )

        # 9. Create agent_contexts table (007-workspace-dashboard-ux)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_contexts (
            workspace_id TEXT PRIMARY KEY,
            context_data TEXT,
            updated_at INTEGER NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
        );
        """)

        # 10. Create chat_messages table (008-quality-testing-observability)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            trace_id TEXT,
            created_at INTEGER NOT NULL
        );
        """)
        conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_chat_messages_session
            ON chat_messages(session_id, timestamp);
        """)

        # 11. Create system_settings table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        conn.commit()
        print(
            f"Database migrations applied successfully. Seeded {len(ENGINEERING_CATALOG)} engineering MCP servers."
        )
    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
