"""Disposable real runtime owner; the final adapter is deliberately simulated.

The parent test kills this process after the ready marker. No graceful runtime
close is used: interruption and recovery must be discovered by the next owner.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

from core.native_process import validate_definition
from data_vault.migrations import upgrade_database
from data_vault.native_process_artifacts import NativeArtifactStore
from data_vault.native_process_runs import NativeRunRepository
from data_vault.state_store import connect_state_db
from workspace_service.native_process_runtime import NativeRuntime
from workspace_service.workspace_path import WorkspacePath


async def main(root: Path) -> None:
    workspace = root / "workspace"
    workspace.mkdir()
    database = root / "state.db"
    upgrade_database(database)
    with connect_state_db(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id,session_id,local_path,created_at,updated_at)
            VALUES ('restart-workspace','restart-session',?,1,1)""",
            (str(workspace),),
        )
    repository = NativeRunRepository(str(database))
    store = NativeArtifactStore(WorkspacePath(workspace))
    run_id = ""

    class SimulatedBlockingAdapter:
        async def call(self, session_id, binding, arguments, timeout_seconds, trace_id):
            observed = repository.inspect("restart-workspace", run_id)
            assert observed["state"] == "running"
            assert len(observed["artifacts"]) == 1
            assert arguments == {"restart": "first"}
            # Real generated files mimic death between promotion and indexing,
            # plus death during staging. Both belong only to this test root.
            orphan = store.promote(
                run_id,
                b"unindexed crash residue",
                filename="orphan.txt",
                port_id="write-artifact",
                provenance={"mode": "simulated_crash_before_index"},
            )
            staging_key = f".wright/native/staging/{uuid.uuid4()}.tmp"
            WorkspacePath(workspace).resolve(staging_key).write_bytes(b"partial")
            marker = {
                "pid": os.getpid(),
                "run_id": run_id,
                "adapter_mode": "simulated_blocking_adapter",
                "orphan_keys": [orphan["storage_key"], staging_key],
            }
            temporary = root / "ready.tmp"
            temporary.write_text(json.dumps(marker), encoding="utf-8")
            temporary.replace(root / "ready.json")
            await asyncio.Event().wait()

    owner = NativeRuntime(
        repository,
        lambda session: ("restart-workspace", WorkspacePath(workspace)),
        mcp=SimulatedBlockingAdapter(),
    )
    owner.ensure_owner()
    document = validate_definition((root / "definition.json").read_bytes())
    saved = repository.save(
        "restart-workspace",
        document,
        {},
        request_id="child-save",
        expected_token=None,
        trace_id="actual-process-death-save",
    )
    run = repository.create_run(
        "restart-workspace",
        document.process_id,
        session_id="restart-session",
        expected_token=saved["token"],
        request_id="child-run",
        bindings={"simulated-tool": {"server_id": "simulated-restart-test"}},
        timeout_seconds=60,
        derived_from_run_id=None,
        actor="engineer",
        trace_id="actual-process-death-run",
    )
    run_id = run["run_id"]
    owner.enqueue("restart-workspace", "restart-session", run_id)
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main(Path(sys.argv[1]).resolve(strict=True)))
