import asyncio
import sqlite3

import pytest

from workspace_service.agent_sync import AgentSyncManager


def _workspace_db(tmp_path) -> str:
    db_path = str(tmp_path / "state.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE system_settings (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            """
            CREATE TABLE engineering_workspaces (
                workspace_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL UNIQUE,
                workspace_name TEXT,
                local_path TEXT NOT NULL,
                enabled_tools TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT INTO engineering_workspaces
                (workspace_id, session_id, workspace_name, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', 'Workspace', ?, 1, 1)
            """,
            (str(tmp_path),),
        )
    return db_path


def test_gateway_restart_remains_pending_until_chat_refreshes_it(tmp_path) -> None:
    calls = []

    def sync(session_id: str, db_path: str) -> bool:
        calls.append((session_id, db_path))
        return len(calls) == 1

    db_path = _workspace_db(tmp_path)
    manager = AgentSyncManager(db_path, workspace_sync=sync)

    assert manager.sync_workspace_tools("session-1") is True
    assert manager.sync_workspace_tools("session-1") is True
    manager.mark_gateway_refreshed()
    assert manager.sync_workspace_tools("session-1") is False


@pytest.mark.asyncio
async def test_concurrent_chat_turns_share_one_gateway_refresh(tmp_path) -> None:
    def sync(_session_id: str, _db_path: str) -> bool:
        return True

    db_path = _workspace_db(tmp_path)
    manager = AgentSyncManager(db_path, workspace_sync=sync)
    assert manager.sync_workspace_tools("session-1") is True

    calls = 0
    refresh_started = asyncio.Event()
    allow_refresh_to_finish = asyncio.Event()

    async def refresh() -> None:
        nonlocal calls
        calls += 1
        refresh_started.set()
        await allow_refresh_to_finish.wait()

    first = asyncio.create_task(manager.refresh_gateway_if_needed(refresh))
    await refresh_started.wait()
    second = asyncio.create_task(manager.refresh_gateway_if_needed(refresh))
    allow_refresh_to_finish.set()

    assert await asyncio.gather(first, second) == [True, False]
    assert calls == 1
