import json
import sqlite3
from typing import List, Optional, Union, Dict, Any
import logging
from .models import McpServer, McpTool

logger = logging.getLogger(__name__)

def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def _parse_command(cmd_str: Optional[str]) -> Optional[Union[List[str], str]]:
    if cmd_str is None:
        return None
    # Try parsing as JSON array
    if cmd_str.startswith("[") and cmd_str.endswith("]"):
        try:
            parsed = json.loads(cmd_str)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except Exception:
            pass
    return cmd_str

def _serialize_command(cmd: Optional[Union[List[str], str]]) -> Optional[str]:
    if cmd is None:
        return None
    if isinstance(cmd, list):
        return json.dumps(cmd)
    return cmd

def _row_to_server(row: sqlite3.Row) -> McpServer:
    return McpServer(
        server_id=row["server_id"],
        name=row["name"],
        type=row["type"],
        command=_parse_command(row["command"]),
        is_active=bool(row["is_active"]),
        status=row["status"],
        error_message=row["error_message"],
        category=row["category"],
        created_at=row["created_at"],
        updated_at=row["updated_at"]
    )

def _row_to_tool(row: sqlite3.Row) -> McpTool:
    input_schema = {}
    if row["input_schema"]:
        try:
            input_schema = json.loads(row["input_schema"])
        except Exception:
            pass
    return McpTool(
        tool_id=row["tool_id"],
        server_id=row["server_id"],
        name=row["name"],
        description=row["description"],
        input_schema=input_schema,
        is_enabled=bool(row["is_enabled"]),
        created_at=row["created_at"]
    )

def get_servers(db_path: str) -> List[McpServer]:
    with _get_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mcp_servers ORDER BY created_at DESC")
        return [_row_to_server(row) for row in cursor.fetchall()]

def get_server(db_path: str, server_id: str) -> Optional[McpServer]:
    with _get_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mcp_servers WHERE server_id = ?", (server_id,))
        row = cursor.fetchone()
        return _row_to_server(row) if row else None

def get_server_by_name(db_path: str, name: str) -> Optional[McpServer]:
    with _get_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mcp_servers WHERE name = ?", (name,))
        row = cursor.fetchone()
        return _row_to_server(row) if row else None

def insert_server(db_path: str, server: McpServer) -> None:
    with _get_conn(db_path) as conn:
        conn.execute(
            """
            INSERT INTO mcp_servers (
                server_id, name, type, command, is_active, status, error_message, category, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                server.server_id,
                server.name,
                server.type,
                _serialize_command(server.command),
                1 if server.is_active else 0,
                server.status,
                server.error_message,
                server.category,
                server.created_at,
                server.updated_at
            )
        )
        conn.commit()

def update_server(db_path: str, server_id: str, updates: Dict[str, Any]) -> Optional[McpServer]:
    if not updates:
        return get_server(db_path, server_id)
        
    set_clauses = []
    params = []
    for key, value in updates.items():
        if key == "is_active":
            set_clauses.append("is_active = ?")
            params.append(1 if value else 0)
        elif key in ("status", "error_message", "category", "updated_at"):
            set_clauses.append(f"{key} = ?")
            params.append(value)
        elif key == "command":
            set_clauses.append("command = ?")
            params.append(_serialize_command(value))
        elif key == "name":
            set_clauses.append("name = ?")
            params.append(value)

    if not set_clauses:
        return get_server(db_path, server_id)

    params.append(server_id)
    query = f"UPDATE mcp_servers SET {', '.join(set_clauses)} WHERE server_id = ?"
    
    with _get_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, tuple(params))
        conn.commit()
        
    return get_server(db_path, server_id)

def delete_server(db_path: str, server_id: str) -> bool:
    with _get_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM mcp_servers WHERE server_id = ?", (server_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_tools(db_path: str, server_id: Optional[str] = None) -> List[McpTool]:
    with _get_conn(db_path) as conn:
        cursor = conn.cursor()
        if server_id:
            cursor.execute("SELECT * FROM mcp_tools WHERE server_id = ? ORDER BY name ASC", (server_id,))
        else:
            cursor.execute("SELECT * FROM mcp_tools ORDER BY name ASC")
        return [_row_to_tool(row) for row in cursor.fetchall()]

def get_tool(db_path: str, tool_id: str) -> Optional[McpTool]:
    with _get_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM mcp_tools WHERE tool_id = ?", (tool_id,))
        row = cursor.fetchone()
        return _row_to_tool(row) if row else None

def insert_tools(db_path: str, tools: List[McpTool]) -> None:
    with _get_conn(db_path) as conn:
        for tool in tools:
            conn.execute(
                """
                INSERT OR REPLACE INTO mcp_tools (
                    tool_id, server_id, name, description, input_schema, is_enabled, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tool.tool_id,
                    tool.server_id,
                    tool.name,
                    tool.description,
                    json.dumps(tool.input_schema),
                    1 if tool.is_enabled else 0,
                    tool.created_at
                )
            )
        conn.commit()

def clear_server_tools(db_path: str, server_id: str) -> None:
    with _get_conn(db_path) as conn:
        conn.execute("DELETE FROM mcp_tools WHERE server_id = ?", (server_id,))
        conn.commit()

def update_tool_enabled(db_path: str, tool_id: str, is_enabled: bool) -> bool:
    with _get_conn(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE mcp_tools SET is_enabled = ? WHERE tool_id = ?", (1 if is_enabled else 0, tool_id))
        conn.commit()
        return cursor.rowcount > 0
