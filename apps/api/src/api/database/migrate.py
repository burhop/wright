import os
import sqlite3
import sys

# Ensure api package is importable when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from api.config import DATABASE_PATH

def run_migrations():
    print(f"Running database migrations on: {DATABASE_PATH}")
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        
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
            updated_at INTEGER NOT NULL
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
        
        # 3. Seed default mock CalculiX simulation tool if not already present
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mcp_servers WHERE name = 'CalculiX Simulation'")
        if cursor.fetchone()[0] == 0:
            import time
            import uuid
            conn.execute("""
            INSERT INTO mcp_servers (server_id, name, type, command, is_active, is_installed, status, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                "CalculiX Simulation",
                "stdio",
                '["uv", "run", "calculix-mcp"]',
                0,
                0,
                "inactive",
                "simulation",
                int(time.time()),
                int(time.time())
            ))
            
        # 4. Seed default OpenSCAD Geometry tool if not already present
        cursor.execute("SELECT COUNT(*) FROM mcp_servers WHERE name = 'OpenSCAD Geometry'")
        if cursor.fetchone()[0] == 0:
            import time
            conn.execute("""
            INSERT INTO mcp_servers (server_id, name, type, command, is_active, is_installed, status, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "openscad-mcp-server",
                "OpenSCAD Geometry",
                "stdio",
                '["uv", "run", "--with", "git+https://github.com/quellant/openscad-mcp.git", "openscad-mcp"]',
                0,
                0,
                "inactive",
                "cad",
                int(time.time()),
                int(time.time())
            ))
            
        # 5. Create engineering_workspaces table
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
            updated_at INTEGER NOT NULL
        );
        """)
        
        # Check if enabled_tools column exists, add it if not (for existing databases)
        cursor.execute("PRAGMA table_info(engineering_workspaces)")
        columns = [col[1] for col in cursor.fetchall()]
        if columns and "enabled_tools" not in columns:
            conn.execute("ALTER TABLE engineering_workspaces ADD COLUMN enabled_tools TEXT;")
            print("Added enabled_tools column to engineering_workspaces table.")
            
        # Check if is_installed column exists in mcp_servers, add it if not (for existing databases)
        cursor.execute("PRAGMA table_info(mcp_servers)")
        mcp_columns = [col[1] for col in cursor.fetchall()]
        if mcp_columns and "is_installed" not in mcp_columns:
            conn.execute("ALTER TABLE mcp_servers ADD COLUMN is_installed INTEGER NOT NULL DEFAULT 0 CHECK(is_installed IN (0, 1));")
            print("Added is_installed column to mcp_servers table.")

        # 6. Add workspace_name column if missing (007-workspace-dashboard-ux)
        cursor.execute("PRAGMA table_info(engineering_workspaces)")
        ws_columns = [col[1] for col in cursor.fetchall()]
        if ws_columns and "workspace_name" not in ws_columns:
            conn.execute("ALTER TABLE engineering_workspaces ADD COLUMN workspace_name TEXT;")
            print("Added workspace_name column to engineering_workspaces table.")

        # 7. Create agent_contexts table (007-workspace-dashboard-ux)
        conn.execute("""
        CREATE TABLE IF NOT EXISTS agent_contexts (
            workspace_id TEXT PRIMARY KEY,
            context_data TEXT,
            updated_at INTEGER NOT NULL,
            FOREIGN KEY (workspace_id) REFERENCES engineering_workspaces(workspace_id) ON DELETE CASCADE
        );
        """)

        # 8. Auto-detect installed tools based on binary availability on $PATH
        import shutil
        import shlex
        cursor.execute("SELECT server_id, command, type FROM mcp_servers")
        for row in cursor.fetchall():
            server_id, command_str, server_type = row
            if server_type != "stdio" or not command_str:
                continue
            try:
                import json as _json
                cmd_parts = _json.loads(command_str) if command_str.startswith("[") else shlex.split(command_str)
                binary = cmd_parts[0] if cmd_parts else None
                if binary and shutil.which(binary):
                    conn.execute("UPDATE mcp_servers SET is_installed = 1 WHERE server_id = ?", (server_id,))
            except Exception:
                pass

        conn.commit()
        print("Database migrations applied successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migrations()
