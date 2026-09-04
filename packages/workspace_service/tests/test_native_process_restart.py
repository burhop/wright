"""Actual OS process-death recovery with a clearly simulated blocking adapter."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import psutil

from core.native_process import language_contract, validate_definition
from data_vault.native_process_artifacts import NativeArtifactStore
from data_vault.native_process_runs import TERMINAL_STATES, NativeRunRepository
from data_vault.state_store import connect_state_db
from workspace_service.native_process_runtime import NativeRuntime
from workspace_service.native_process_service import NativeServiceError
from workspace_service.workspace_path import WorkspacePath

ROOT = Path(__file__).resolve().parents[3]
CHILD = Path(__file__).parent / "fixtures/native_restart_child.py"
WORKSPACE_ID = "restart-workspace"
SESSION_ID = "restart-session"
FIRST_CONTENT = b'{"restart":"first"}'


def _definition():
    value = {
        "format": "wright-native-process",
        "schema_version": "1.0.0",
        "id": "process-death-test",
        "title": "Actual process death, simulated adapter",
        "steps": [],
        "ports": [],
        "connections": [],
        "outputs": [],
    }
    previous = None
    for identity, operation, config in (
        ("source", "text.input@1", {"value": FIRST_CONTENT.decode()}),
        ("write", "artifact.write-text@1", {"filename": "retained.json"}),
        ("read", "artifact.read-text@1", {}),
        ("simulated-tool", "mcp.call@1", {}),
    ):
        value["steps"].append(
            {
                "id": identity,
                "title": identity,
                "operation": operation,
                "config": config,
            }
        )
        descriptor = next(
            item
            for item in language_contract()["operations"]
            if item["id"] == operation
        )
        for direction in ("input", "output"):
            for port in descriptor[direction + "s"]:
                port_id = identity + "-" + port["key"]
                value["ports"].append(
                    {
                        **port,
                        "id": port_id,
                        "step_id": identity,
                        "label": port["key"],
                        "direction": direction,
                    }
                )
                if direction == "input":
                    value["connections"].append(
                        {
                            "id": identity + "-edge",
                            "source_port_id": previous,
                            "target_port_id": port_id,
                        }
                    )
                else:
                    previous = port_id
    return value


async def _ready(child, path, log_path):
    async with asyncio.timeout(30):
        while not path.exists():
            assert child.poll() is None, log_path.read_text(encoding="utf-8")[-8000:]
            await asyncio.sleep(0.02)
    return json.loads(path.read_text(encoding="utf-8"))


def _stop_child(child):
    """Reap only this Popen process and descendants it created (venv redirectors)."""
    if child.poll() is None:
        try:
            descendants = psutil.Process(child.pid).children(recursive=True)
        except psutil.NoSuchProcess:
            descendants = []
        for process in reversed(descendants):
            try:
                process.kill()
            except psutil.NoSuchProcess:
                pass
        if child.poll() is None:
            child.kill()
        _, alive = psutil.wait_procs(descendants, timeout=10)
        assert not alive, "Disposable runtime children did not exit"
    child.wait(timeout=10)


def _stored_evidence(repository, run_id):
    with connect_state_db(repository.db_path, read_only=True) as connection:
        snapshot = connection.execute(
            "SELECT snapshot FROM native_process_runs WHERE workspace_id=? AND run_id=?",
            (WORKSPACE_ID, run_id),
        ).fetchone()[0]
        artifacts = connection.execute(
            """SELECT artifact_id,content_digest,storage_key,provenance
            FROM native_process_artifacts WHERE workspace_id=? AND run_id=?
            ORDER BY artifact_id""",
            (WORKSPACE_ID, run_id),
        ).fetchall()
    return snapshot, [tuple(row) for row in artifacts]


@pytest.mark.asyncio
async def test_actual_process_death_preserves_evidence_and_allows_linked_restart(
    tmp_path,
):
    data = _definition()
    (tmp_path / "definition.json").write_text(json.dumps(data), encoding="utf-8")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), *map(str, sorted((ROOT / "packages").glob("*/src")))]
    )
    environment["HERMES_CONFIG_PATH"] = str(tmp_path / "no-hermes-config.json")
    environment["HERMES_ENV_PATH"] = str(tmp_path / "no-hermes.env")
    environment["PYTHONUNBUFFERED"] = "1"
    log_path = tmp_path / "child.log"
    with log_path.open("wb") as log:
        child = subprocess.Popen(
            [sys.executable, str(CHILD), str(tmp_path)],
            cwd=tmp_path,
            env=environment,
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        try:
            ready = await _ready(child, tmp_path / "ready.json", log_path)
            # Windows venv launchers may spawn the actual interpreter. Verify
            # ancestry and exact disposable fixture command before targeting it.
            descendants = psutil.Process(child.pid).children(recursive=True)
            assert ready["pid"] in {child.pid, *(p.pid for p in descendants)}
            owner_process = psutil.Process(ready["pid"])
            assert str(CHILD) in owner_process.cmdline()
            assert str(tmp_path) in owner_process.cmdline()
            assert ready["adapter_mode"] == "simulated_blocking_adapter"
            run_id = ready["run_id"]
            repository = NativeRunRepository(str(tmp_path / "state.db"))
            workspace = WorkspacePath(tmp_path / "workspace")

            def resolver(session):
                return WORKSPACE_ID, workspace

            contender = NativeRuntime(repository, resolver)
            try:
                with pytest.raises(NativeServiceError) as denied:
                    contender.ensure_owner()
                assert denied.value.code == "NATIVE_RUNTIME_BUSY"
            finally:
                await contender.close()
            before = repository.inspect(WORKSPACE_ID, run_id)
            assert before["state"] == "running"
            assert before["steps"][-1]["state"] == "running"
            assert {s["state"] for s in before["steps"][:-1]} == {"succeeded"}
            evidence = _stored_evidence(repository, run_id)
            events = repository.events(WORKSPACE_ID, run_id)["events"]
            artifact = repository.artifact(
                WORKSPACE_ID, run_id, before["artifacts"][0]["artifact_id"]
            )
            store = NativeArtifactStore(workspace)
            assert store.read(artifact) == FIRST_CONTENT
            assert (
                artifact["content_digest"] == hashlib.sha256(FIRST_CONTENT).hexdigest()
            )
            assert artifact["provenance"]["mode"] == "local_computation"
            assert artifact["provenance"]["trace_id"] == before["trace_id"]
            unrelated = workspace.resolve(".wright/native/artifacts/user-note.bin")
            unrelated.write_bytes(b"retain unrelated file")

            # Terminate only the verified runtime process above. This is SIGKILL
            # on POSIX / TerminateProcess on Windows, with no owner.close.
            owner_process.kill()
            if owner_process.pid == child.pid:
                assert child.wait(timeout=10) != 0
            else:
                owner_process.wait(timeout=10)
                child.wait(timeout=10)
            assert not owner_process.is_running()
            assert repository.summary(WORKSPACE_ID, run_id)["state"] == "running"
        finally:
            _stop_child(child)

    calls = []

    class SimulatedSuccessfulAdapter:
        async def call(self, session_id, binding, arguments, timeout_seconds, trace_id):
            calls.append(arguments)
            return "simulated correction succeeded"

    restarted = NativeRuntime(repository, resolver, mcp=SimulatedSuccessfulAdapter())
    try:
        restarted.ensure_owner()
        interrupted = repository.inspect(WORKSPACE_ID, run_id)
        assert interrupted["state"] == "interrupted"
        assert interrupted["reason"]["code"] == "OWNER_INTERRUPTED"
        assert interrupted["snapshot"] == before["snapshot"]
        assert interrupted["artifacts"] == before["artifacts"]
        assert interrupted["steps"][:-1] == before["steps"][:-1]
        assert _stored_evidence(repository, run_id) == evidence
        after_events = repository.events(WORKSPACE_ID, run_id)["events"]
        assert after_events[: len(events)] == events
        assert after_events[-1]["kind"] == "run.interrupted"

        # Run the real reconciliation primitive only after obtaining ownership.
        # This test does not claim service startup automatically calls it.
        cleanup = store.reconcile(repository.indexed_artifact_keys(WORKSPACE_ID))
        assert set(cleanup["removed"]) == set(ready["orphan_keys"])
        assert cleanup["residue"] == []
        assert all(not workspace.resolve(key).exists() for key in ready["orphan_keys"])
        assert unrelated.read_bytes() == b"retain unrelated file"
        assert store.read(artifact) == FIRST_CONTENT

        data["steps"][0]["config"]["value"] = '{"restart":"corrected"}'
        saved = repository.save(
            WORKSPACE_ID,
            validate_definition(data),
            {},
            request_id="corrected-save",
            expected_token=before["snapshot"]["token"],
            trace_id="corrected-save-trace",
        )
        corrected_id = repository.create_run(
            WORKSPACE_ID,
            data["id"],
            session_id=SESSION_ID,
            expected_token=saved["token"],
            request_id="corrected-run",
            bindings={"simulated-tool": {"server_id": "simulated-restart-test"}},
            timeout_seconds=60,
            derived_from_run_id=run_id,
            actor="engineer",
            trace_id="corrected-run-trace",
        )["run_id"]
        restarted.enqueue(WORKSPACE_ID, SESSION_ID, corrected_id)
        async with asyncio.timeout(10):
            while (
                repository.summary(WORKSPACE_ID, corrected_id)["state"]
                not in TERMINAL_STATES
            ):
                await asyncio.sleep(0.02)
        corrected = repository.inspect(WORKSPACE_ID, corrected_id)
        assert corrected["state"] == "succeeded", corrected["reason"]
        assert corrected["derived_from_run_id"] == run_id
        assert corrected["semantic_digest"] != before["semantic_digest"]
        assert calls == [{"restart": "corrected"}]
        corrected_artifact = repository.artifact(
            WORKSPACE_ID, corrected_id, corrected["artifacts"][0]["artifact_id"]
        )
        assert store.read(corrected_artifact) == b'{"restart":"corrected"}'
        assert repository.inspect(WORKSPACE_ID, run_id) == interrupted
        assert _stored_evidence(repository, run_id) == evidence
        assert store.read(artifact) == FIRST_CONTENT
    finally:
        await restarted.close()
