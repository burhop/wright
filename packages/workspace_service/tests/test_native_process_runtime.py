from __future__ import annotations

import asyncio
import hashlib
import json
import time
import threading
import uuid
from pathlib import Path

import pytest
import pytest_asyncio

from core.native_process import validate_definition, language_contract
from data_vault.migrations import upgrade_database
from data_vault.native_process_artifacts import NativeArtifactStore
from data_vault.native_process_runs import NativeRunRepository, TERMINAL_STATES
from data_vault.state_store import connect_state_db
from workspace_service.native_process_runtime import NativeRuntime
from workspace_service.native_process_service import NativeServiceError
from workspace_service.workspace_path import WorkspacePath

ROOT = Path(__file__).resolve().parents[3]
EXAMPLES = ROOT / "src/wright_engineering/static/native-processes"
ORACLES = json.loads((EXAMPLES / "oracles.json").read_text(encoding="utf-8"))["cases"]


@pytest_asyncio.fixture
async def runtime(tmp_path):
    db = tmp_path / "state.db"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    upgrade_database(db)
    with connect_state_db(db) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id,session_id,local_path,created_at,updated_at) VALUES ('one','session-one',?,1,1)""",
            (str(workspace),),
        )
    repository = NativeRunRepository(str(db))
    owner = NativeRuntime(repository, lambda session: ("one", WorkspacePath(workspace)))
    owner.ensure_owner()
    yield owner, repository, workspace
    await owner.close()


def definition(name):
    return json.loads((EXAMPLES / f"{name}.json").read_text(encoding="utf-8"))


def submit(
    runtime, data, *, saved=None, prior=None, timeout=60, enqueue=True, bindings=None
):
    owner, repository, _ = runtime
    document = validate_definition(data)
    saved = repository.save(
        "one",
        document,
        {},
        request_id=str(uuid.uuid4()),
        expected_token=saved["token"] if saved else None,
        trace_id="save-trace",
    )
    run = repository.create_run(
        "one",
        document.process_id,
        session_id="session-one",
        expected_token=saved["token"],
        request_id=str(uuid.uuid4()),
        bindings=bindings or {},
        timeout_seconds=timeout,
        derived_from_run_id=prior,
        actor="engineer",
        trace_id="actual-runtime-trace",
    )
    if enqueue:
        owner.enqueue("one", "session-one", run["run_id"])
    return saved, run["run_id"]


async def terminal(repository, run_id):
    async with asyncio.timeout(5):
        while repository.summary("one", run_id)["state"] not in TERMINAL_STATES:
            await asyncio.sleep(0.01)
    return repository.inspect("one", run_id)


@pytest.mark.asyncio
@pytest.mark.parametrize("oracle", ORACLES, ids=[item["id"] for item in ORACLES])
async def test_real_deterministic_examples_match_independent_output_oracles(
    runtime, oracle
):
    owner, repository, workspace = runtime
    _, run_id = submit(runtime, definition(oracle["id"]))
    result = await terminal(repository, run_id)
    assert result["state"] == "succeeded", result["reason"]
    assert {step["state"] for step in result["steps"]} == {"succeeded"}
    artifact = next(
        item for item in result["artifacts"] if item["filename"] == oracle["artifact"]
    )
    content = NativeArtifactStore(WorkspacePath(workspace)).read(
        repository.artifact("one", run_id, artifact["artifact_id"])
    )
    assert content == oracle["expected_text"].encode("utf-8")
    assert artifact["content_digest"] == hashlib.sha256(content).hexdigest()
    assert artifact["provenance"]["mode"] == "local_computation"
    assert (
        artifact["provenance"]["trace_id"]
        == result["trace_id"]
        == "actual-runtime-trace"
    )
    assert artifact["provenance"]["semantic_digest"] == result["semantic_digest"]
    assert not any("rivet" in step["operation"] for step in result["steps"])
    events = repository.events("one", run_id)["events"]
    assert {event["trace_id"] for event in events} == {result["trace_id"]}
    owner.enqueue("one", "session-one", run_id)
    assert repository.events("one", run_id)["events"] == events


@pytest.mark.asyncio
async def test_failed_mass_can_be_corrected_into_linked_success_without_rewriting_evidence(
    runtime,
):
    _, repository, _ = runtime
    failing = definition("mass-check-fails")
    saved, failed_id = submit(runtime, failing)
    failed = await terminal(repository, failed_id)
    assert (
        failed["state"] == "failed" and failed["reason"]["code"] == "ASSERTION_FAILED"
    )
    assert failed["artifacts"] == []
    assert any(step["state"] == "blocked" for step in failed["steps"])
    corrected = definition("mass-check")
    corrected["id"] = failing["id"]
    _, corrected_id = submit(runtime, corrected, saved=saved, prior=failed_id)
    passed = await terminal(repository, corrected_id)
    assert passed["state"] == "succeeded"
    assert passed["derived_from_run_id"] == failed_id
    assert passed["semantic_digest"] != failed["semantic_digest"]
    assert repository.inspect("one", failed_id) == failed


@pytest.mark.asyncio
async def test_document_and_package_negative_controls_fail_from_actual_output(runtime):
    _, repository, workspace = runtime
    brief = definition("concept-brief")
    next(step for step in brief["steps"] if "200 g" in str(step["config"]))["config"][
        "value"
    ] = "No stated mass requirement."
    _, brief_id = submit(runtime, brief)
    failed = await terminal(repository, brief_id)
    assert failed["state"] == "failed" and failed["artifacts"] == []
    package = definition("package-review")
    source = next(
        step for step in package["steps"] if step["operation"] == "text.input@1"
    )
    source["config"]["value"] = source["config"]["value"].replace("Units: mm\n", "")
    _, package_id = submit(runtime, package)
    result = await terminal(repository, package_id)
    assert (
        result["state"] == "failed" and result["reason"]["code"] == "ASSERTION_FAILED"
    )
    assert len(result["artifacts"]) == 1
    artifact = result["artifacts"][0]
    actual = NativeArtifactStore(WorkspacePath(workspace)).read(
        repository.artifact("one", package_id, artifact["artifact_id"])
    )
    assert b"Units: mm" not in actual


@pytest.mark.asyncio
async def test_second_coordinator_cannot_interrupt_the_owner_and_new_owner_recovers(
    runtime,
):
    owner, repository, workspace = runtime
    _, queued = submit(runtime, definition("concept-brief"), enqueue=False)
    other = NativeRuntime(repository, lambda session: ("one", WorkspacePath(workspace)))
    with pytest.raises(NativeServiceError) as error:
        other.ensure_owner()
    assert error.value.code == "NATIVE_RUNTIME_BUSY"
    assert repository.summary("one", queued)["state"] == "queued"
    await owner.close()
    other.ensure_owner()
    assert repository.summary("one", queued)["state"] == "interrupted"
    await other.close()


@pytest.mark.asyncio
async def test_queued_cancel_calls_no_operation(runtime, monkeypatch):
    owner, repository, _ = runtime
    called = []
    monkeypatch.setattr(owner, "_local_operation", lambda *args: called.append(args))
    _, run_id = submit(runtime, definition("concept-brief"), enqueue=False)
    result = await owner.cancel("one", run_id)
    owner.enqueue("one", "session-one", run_id)
    await asyncio.sleep(0)
    assert result["state"] == "cancelled" and called == []
    assert repository.inspect("one", run_id)["artifacts"] == []


@pytest.mark.asyncio
async def test_deadline_prevents_late_worker_artifact_publication(runtime, monkeypatch):
    _, repository, workspace = runtime
    original = NativeArtifactStore.promote

    def late_promotion(self, *args, **kwargs):
        time.sleep(1.3)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(NativeArtifactStore, "promote", late_promotion)
    _, run_id = submit(runtime, definition("concept-brief"), timeout=1)
    result = await terminal(repository, run_id)
    assert result["state"] == "timed_out" and result["artifacts"] == []
    await asyncio.sleep(0.6)
    assert repository.inspect("one", run_id)["artifacts"] == []
    assert list((workspace / ".wright/native/artifacts").glob("*/*.bin")) == []


@pytest.mark.asyncio
async def test_changed_workspace_binding_stops_execution_without_artifacts(runtime):
    owner, repository, workspace = runtime
    owner.scope_resolver = lambda session: (
        "different-workspace",
        WorkspacePath(workspace),
    )
    _, run_id = submit(runtime, definition("concept-brief"))
    result = await terminal(repository, run_id)
    assert result["state"] == "failed" and result["reason"]["code"] == "NATIVE_DENIED"
    assert result["artifacts"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("tool_timeout", [False, True])
async def test_mcp_runtime_deadline_and_trace_adapter_contract(runtime, tool_timeout):
    owner, repository, _ = runtime
    from core.native_process import language_contract

    contract = language_contract()
    data = {
        "format": "wright-native-process",
        "schema_version": "1.0.0",
        "id": "mock-mcp-process",
        "title": "Mocked adapter boundary",
        "steps": [],
        "ports": [],
        "connections": [],
        "outputs": [],
    }
    for identity, operation, config in (
        ("source-step", "text.input@1", {"value": '{"x":1}'}),
        ("tool-step", "mcp.call@1", {}),
    ):
        data["steps"].append(
            {
                "id": identity,
                "title": identity,
                "operation": operation,
                "config": config,
            }
        )
        descriptor = next(
            item for item in contract["operations"] if item["id"] == operation
        )
        for direction in ("input", "output"):
            for port in descriptor[direction + "s"]:
                data["ports"].append(
                    {
                        **port,
                        "id": identity + "-" + port["key"],
                        "step_id": identity,
                        "label": port["key"],
                        "direction": direction,
                    }
                )
    data["connections"].append(
        {
            "id": "tool-connection",
            "source_port_id": "source-step-value",
            "target_port_id": "tool-step-arguments",
        }
    )
    observed = []

    class MockAdapter:
        async def call(self, session_id, binding, arguments, timeout_seconds, trace_id):
            observed.append((session_id, arguments, timeout_seconds, trace_id))
            if tool_timeout:
                raise asyncio.TimeoutError
            return '{"value":1.25}'

    owner.mcp = MockAdapter()
    _, run_id = submit(
        runtime, data, timeout=1, bindings={"tool-step": {"server_id": "mock-server"}}
    )
    result = await terminal(repository, run_id)
    assert observed[0][0:2] == ("session-one", {"x": 1})
    assert 0 < observed[0][2] <= 1
    assert observed[0][3] == result["trace_id"]
    if tool_timeout:
        assert result["state"] == "failed"
        assert result["reason"]["code"] == "TOOL_DEADLINE_EXCEEDED"
    else:
        assert result["state"] == "succeeded"
        assert result["steps"][-1]["outputs"] == {"tool-step-result": '{"value":1.25}'}


def flow(operations):
    data = {
        "format": "wright-native-process",
        "schema_version": "1.0.0",
        "id": "review-process",
        "title": "Independent runtime review",
        "steps": [],
        "ports": [],
        "connections": [],
        "outputs": [],
    }
    previous = None
    for index, (operation, config) in enumerate(operations):
        identity = f"step-{index}"
        data["steps"].append(
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
                exact = identity + "-" + port["key"]
                data["ports"].append(
                    {
                        **port,
                        "id": exact,
                        "step_id": identity,
                        "label": port["key"],
                        "direction": direction,
                    }
                )
                if direction == "input" and previous:
                    data["connections"].append(
                        {
                            "id": f"edge-{index}",
                            "source_port_id": previous,
                            "target_port_id": exact,
                        }
                    )
                elif direction == "output":
                    previous = exact
    return data


@pytest.mark.asyncio
async def test_valid_unicode_write_read_roundtrip(runtime):
    _, repository, _ = runtime
    data = flow(
        [
            ("text.input@1", {"value": "é" * 3000}),
            ("artifact.write-text@1", {"filename": "review.txt"}),
            ("artifact.read-text@1", {}),
        ]
    )
    _, run_id = submit(runtime, data)
    result = await terminal(repository, run_id)
    assert result["state"] == "succeeded", result["reason"]


@pytest.mark.asyncio
async def test_valid_fractional_mcp_arguments_reach_adapter(runtime):
    owner, repository, _ = runtime
    calls = []

    class Adapter:
        async def call(self, *args):
            calls.append(args)
            return "ok"

    owner.mcp = Adapter()
    data = flow([("text.input@1", {"value": '{"value":0.5}'}), ("mcp.call@1", {})])
    _, run_id = submit(runtime, data, bindings={"step-1": {"server_id": "review"}})
    result = await terminal(repository, run_id)
    assert result["state"] == "succeeded", result["reason"]
    assert calls[0][2] == {"value": 0.5}


@pytest.mark.asyncio
async def test_valid_nfc_input_strings_may_join_to_decomposed_text(runtime):
    _, repository, _ = runtime
    data = flow(
        [
            ("text.input@1", {"value": "e"}),
            ("text.input@1", {"value": "\u0301"}),
            ("text.join@1", {}),
        ]
    )
    data["connections"] = [
        {
            "id": "edge-first",
            "source_port_id": "step-0-value",
            "target_port_id": "step-2-first",
        },
        {
            "id": "edge-second",
            "source_port_id": "step-1-value",
            "target_port_id": "step-2-second",
        },
    ]
    _, run_id = submit(runtime, data)
    result = await terminal(repository, run_id)
    assert result["state"] == "succeeded", result["reason"]
    assert result["steps"][-1]["outputs"] == {"step-2-text": "e\u0301"}


@pytest.mark.asyncio
async def test_cancelled_promotion_after_cleanup_before_terminal_is_removed(
    runtime, monkeypatch
):
    owner, repository, workspace = runtime
    promote_entered = threading.Event()
    release_promote = threading.Event()
    checked_state = threading.Event()
    original_promote = NativeArtifactStore.promote
    original_finish = repository.finish
    original_summary = repository.summary

    def paused_promote(self, *args, **kwargs):
        promote_entered.set()
        assert release_promote.wait(4)
        return original_promote(self, *args, **kwargs)

    def observe_summary(*args, **kwargs):
        result = original_summary(*args, **kwargs)
        if threading.current_thread() is not threading.main_thread():
            checked_state.set()
        return result

    def paused_finish(*args, **kwargs):
        if args[2] == "timed_out":
            # _execute's finally has already observed its empty promotion list;
            # the worker can finish while the terminal transaction is pending.
            release_promote.set()
            assert checked_state.wait(4)
        return original_finish(*args, **kwargs)

    monkeypatch.setattr(NativeArtifactStore, "promote", paused_promote)
    monkeypatch.setattr(repository, "summary", observe_summary)
    monkeypatch.setattr(repository, "finish", paused_finish)
    data = flow(
        [
            ("text.input@1", {"value": "review"}),
            ("artifact.write-text@1", {"filename": "review.txt"}),
        ]
    )
    _, run_id = submit(runtime, data, timeout=1)
    result = await terminal(repository, run_id)
    assert result["state"] == "timed_out" and result["artifacts"] == []
    await asyncio.sleep(0.1)
    assert list((workspace / ".wright/native/artifacts").glob("*/*.bin")) == []
