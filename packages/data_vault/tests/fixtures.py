from __future__ import annotations

import sqlite3
from pathlib import Path


def create_partial_legacy_database(path: Path) -> Path:
    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE mcp_servers (
                server_id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL,
                command TEXT,
                is_active INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'inactive',
                error_message TEXT,
                category TEXT NOT NULL DEFAULT 'utilities',
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            INSERT INTO mcp_servers (
                server_id, name, type, command, created_at, updated_at
            ) VALUES ('custom-user-server', 'Custom User Server', 'stdio', 'custom', 1, 1);

            CREATE TABLE engineering_workspaces (
                workspace_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL UNIQUE,
                local_path TEXT NOT NULL,
                git_remote_url TEXT,
                git_username TEXT,
                git_token TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            INSERT INTO engineering_workspaces (
                workspace_id, session_id, local_path, created_at, updated_at
            ) VALUES ('workspace-one', 'session-one', '/workspace/one', 1, 1);
        """)
    return path


def corrupt_database(path: Path) -> Path:
    path.write_bytes(b"not a sqlite database")
    return path
