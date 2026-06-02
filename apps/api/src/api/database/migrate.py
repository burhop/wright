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
            INSERT INTO mcp_servers (server_id, name, type, command, is_active, status, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                "CalculiX Simulation",
                "stdio",
                '["uv", "run", "calculix-mcp"]',
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
            INSERT INTO mcp_servers (server_id, name, type, command, is_active, status, category, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "openscad-mcp-server",
                "OpenSCAD Geometry",
                "stdio",
                '["uv", "run", "--with", "git+https://github.com/quellant/openscad-mcp.git", "openscad-mcp"]',
                0,
                "inactive",
                "cad",
                int(time.time()),
                int(time.time())
            ))
            
        conn.commit()
        print("Database migrations applied successfully.")
    finally:
        conn.close()

if __name__ == "__main__":
    run_migrations()
