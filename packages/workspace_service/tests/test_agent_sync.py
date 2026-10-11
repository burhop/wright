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
    assert manager.gateway_refresh_pending is True
    assert manager.sync_workspace_tools("session-1") is True
    manager.mark_gateway_refreshed()
    assert manager.gateway_refresh_pending is False
    assert manager.sync_workspace_tools("session-1") is False


@pytest.mark.asyncio
@pytest.mark.parametrize("separate_readiness", [False, True])
async def test_concurrent_chat_turns_share_one_gateway_refresh(
    tmp_path, separate_readiness
) -> None:
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
        assert manager.gateway_refresh_in_progress is True
        refresh_started.set()
        await allow_refresh_to_finish.wait()

    ready_calls = 0

    async def ready():
        nonlocal ready_calls
        ready_calls += 1

    options = {"wait_ready": ready} if separate_readiness else {}
    first = asyncio.create_task(manager.refresh_gateway_if_needed(refresh, **options))
    await refresh_started.wait()
    second = asyncio.create_task(manager.refresh_gateway_if_needed(refresh, **options))
    allow_refresh_to_finish.set()

    assert await asyncio.gather(first, second) == [True, False]
    assert calls == 1
    assert ready_calls == int(separate_readiness)
    assert manager.gateway_refresh_in_progress is False
    assert manager.gateway_refresh_pending is False


@pytest.mark.asyncio
async def test_failed_gateway_refresh_exposes_error_and_stops_pending_state(
    tmp_path,
) -> None:
    def sync(_session_id: str, _db_path: str) -> bool:
        return True

    db_path = _workspace_db(tmp_path)
    manager = AgentSyncManager(db_path, workspace_sync=sync)
    assert manager.sync_workspace_tools("session-1") is True

    async def refresh() -> None:
        raise RuntimeError("restart failed")

    with pytest.raises(RuntimeError, match="restart failed"):
        await manager.refresh_gateway_if_needed(refresh)

    assert manager.gateway_refresh_in_progress is False
    assert manager.gateway_refresh_pending is False
    assert manager.gateway_refresh_error == "restart failed"


@pytest.mark.asyncio
async def test_readiness_timeout_rechecks_same_restart_without_restarting(tmp_path):
    changed = True

    def sync(_session_id, _db_path):
        nonlocal changed
        result, changed = changed, False
        return result

    manager = AgentSyncManager(_workspace_db(tmp_path), workspace_sync=sync)
    manager.sync_workspace_tools("session-1")
    restarts = 0
    observations = 0

    async def restart():
        nonlocal restarts
        restarts += 1

    async def wait_ready():
        nonlocal observations
        observations += 1
        if observations == 1:
            raise TimeoutError("Gateway still starting")

    with pytest.raises(TimeoutError, match="still starting"):
        await manager.refresh_gateway_if_needed(restart, wait_ready=wait_ready)
    assert manager.sync_workspace_tools("session-1") is True
    assert await manager.refresh_gateway_if_needed(restart, wait_ready=wait_ready)
    assert restarts == 1
    assert observations == 2
    assert manager.gateway_refresh_error is None
    assert manager.sync_workspace_tools("session-1") is False


@pytest.mark.asyncio
async def test_changed_binding_during_readiness_cannot_be_marked_refreshed(tmp_path):
    manager = AgentSyncManager(_workspace_db(tmp_path), workspace_sync=lambda *_: True)
    manager.sync_workspace_tools("session-1")
    restarts = 0

    async def restart():
        nonlocal restarts
        restarts += 1

    async def wait_ready():
        if restarts == 1:
            manager.sync_workspace_tools("session-1")

    with pytest.raises(RuntimeError, match="binding changed"):
        await manager.refresh_gateway_if_needed(restart, wait_ready=wait_ready)
    assert manager.gateway_refresh_error
    assert await manager.refresh_gateway_if_needed(restart, wait_ready=wait_ready)
    assert restarts == 2  # A new binding really does require another restart.
    assert manager.gateway_refresh_pending is False


@pytest.mark.asyncio
async def test_cancelled_observation_preserves_successful_restart(tmp_path):
    manager = AgentSyncManager(_workspace_db(tmp_path), workspace_sync=lambda *_: True)
    manager.sync_workspace_tools("session-1")
    restarts = 0

    async def restart():
        nonlocal restarts
        restarts += 1

    async def cancelled():
        raise asyncio.CancelledError

    async def ready():
        return None

    with pytest.raises(asyncio.CancelledError):
        await manager.refresh_gateway_if_needed(restart, wait_ready=cancelled)
    assert manager.gateway_refresh_in_progress is False
    assert await manager.refresh_gateway_if_needed(restart, wait_ready=ready)
    assert restarts == 1
