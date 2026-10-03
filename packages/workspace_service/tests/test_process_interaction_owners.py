"""Interaction views compose real recorder/review/input owners without execution."""

import hashlib
import json
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from core.process_interactions import (
    InputSnapshot,
    ProcessRef,
    StartReceipt,
    ValueBinding,
)
from core.process_validation import canonical_digest
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.service import (
    ProcessInterfaceService,
    ProcessScope,
)
from packages.workspace_service.tests.test_workflow_approval_execution import setup_case
from packages.workspace_service.tests.test_workflow_artifact_review import run_review
from packages.data_vault.tests.test_process_validation_repository import request
from workspace_service.process_validation.application import ValidationApplication
from workspace_service.workflow_results import (
    EngineeringResult,
    Provenance,
    Representation,
)


def application(service, root, *, database="state.db", workspace="ws"):
    service.db_path = root / database
    service.repository = SimpleNamespace(
        get_by_id=lambda key: {"local_path": str(root)} if key == workspace else None
    )
    service.ensure_workspace_path_safe = lambda path: None
    return ProcessInterfaceService(service)


def scope(**changes):
    return ProcessScope(
        **{
            "principal_id": "test-user",
            "workspace_id": "ws",
            "capabilities": frozenset(
                {"process.read", "process.review", "process.action"}
            ),
            **changes,
        }
    )


def reference(root, path):
    return ProcessRef(
        workspace_id="ws",
        source_path=path,
        source_digest=hashlib.sha256((root / path).read_bytes()).hexdigest(),
    )


@pytest.mark.asyncio
async def test_run_projection_uses_current_checkpoint_and_never_executes(tmp_path):
    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    process = reference(tmp_path, case.checkpoint.workflow_id)
    before = (tmp_path / case.result["run_log_path"]).read_bytes()
    calls = list(case.calls)
    view = await app.get_snapshot(scope(), process, run_id=case.result["run_id"])
    assert view.state == "waiting_human"
    assert view.context.run_id == case.result["run_id"]
    assert view.interactions[0].checkpoint_id == case.checkpoint.checkpoint_id
    assert view.interactions[0].subject_digest == case.checkpoint.subject_digest
    assert view.interactions[0].state == "waiting"
    actions = {item.operation: item for item in view.actions}
    assert actions["review"].enabled and not actions["action"].enabled
    assert view.observations[0].progress_percent is None
    assert view.context.input_snapshot_id is None
    assert case.calls == calls
    assert (tmp_path / case.result["run_log_path"]).read_bytes() == before


@pytest.mark.asyncio
async def test_run_projection_obeys_scope_and_stale_owner_evidence(tmp_path):
    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    process = reference(tmp_path, case.checkpoint.workflow_id)
    view = await app.get_snapshot(
        scope(capabilities=frozenset({"process.read"})),
        process,
        run_id=case.result["run_id"],
    )
    assert all(not item.enabled for item in view.actions)
    (tmp_path / "brief.md").write_text("changed input", encoding="utf-8")
    view = await app.get_snapshot(scope(), process, run_id=case.result["run_id"])
    assert view.interactions[0].state == "stale"
    assert all(not item.enabled for item in view.actions)
    assert view.actions[0].reasons[0].code == "SUBJECT_STALE"
    with pytest.raises(ProcessInterfaceError):
        await app.get_snapshot(
            scope(workspace_id="other"), process, run_id=case.result["run_id"]
        )


@pytest.mark.asyncio
async def test_unknown_owner_blocks_checkpoint_mutations(tmp_path):
    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    path = tmp_path / case.result["run_log_path"]
    record = json.loads(path.read_bytes())
    record.update(status="running", owner={"host": "another-host", "lease": "foreign"})
    path.write_text(json.dumps(record), encoding="utf-8")
    view = await app.get_snapshot(
        scope(),
        reference(tmp_path, case.checkpoint.workflow_id),
        run_id=case.result["run_id"],
    )
    assert view.state == "reconciliation_required"
    assert all(not item.enabled for item in view.actions)


@pytest.mark.asyncio
async def test_terminal_review_projection_rechecks_actual_files(tmp_path):
    result, service, calls, _ = await run_review(tmp_path)
    app = application(service, tmp_path, database="state.sqlite3")
    process = reference(tmp_path, result["review"]["workflow_path"])
    before = list(calls)
    view = await app.get_snapshot(scope(), process, run_id=result["run_id"])
    interaction = view.interactions[0]
    assert interaction.kind == "review" and interaction.state == "waiting"
    assert interaction.evidence and interaction.evidence[0].sha256
    assert any(item.enabled and item.operation == "review" for item in view.actions)
    (tmp_path / "draft.html").write_text("changed artifact", encoding="utf-8")
    view = await app.get_snapshot(scope(), process, run_id=result["run_id"])
    assert view.interactions[0].state == "stale"
    assert all(not item.enabled for item in view.actions)
    assert calls == before


@pytest.mark.asyncio
async def test_frozen_input_receipt_is_not_current_preparation_or_run_status(tmp_path):
    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    process = reference(tmp_path, case.checkpoint.workflow_id)
    snapshot = InputSnapshot.create(
        snapshot_id="frozen",
        process=process,
        created_at="2026-09-30T12:00:00Z",
        bindings=(ValueBinding(input_id="brief", value="prepared value"),),
    )
    receipt = StartReceipt(
        principal_id="test-user",
        process=process,
        request_id="first",
        payload_digest=canonical_digest(snapshot.bindings),
        input_snapshot_id=snapshot.snapshot_id,
        input_digest=snapshot.digest,
        run_id=case.result["run_id"],
        created_at="2026-09-30T12:00:00Z",
    )
    app.inputs.reserve_start(snapshot, receipt)
    view = await app.get_snapshot(scope(), process, run_id=case.result["run_id"])
    assert (
        view.context.input_snapshot_id == "frozen"
        and view.context.input_digest == snapshot.digest
    )
    assert (
        view.state == "waiting_human"
    )  # The receipt's initial state cannot replace the recorder.


@pytest.mark.asyncio
async def test_run_projection_reads_real_082_assessment_and_supersession(tmp_path):
    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    process = reference(tmp_path, case.checkpoint.workflow_id)
    run_id = case.result["run_id"]
    req, profile = request(workspace="ws")
    subject = req.subjects[0]
    subject = type(subject).model_validate(
        {
            **subject.model_dump(),
            "result_id": f"{run_id}:producer:result",
            "producer": {**subject.producer.model_dump(), "run_id": run_id},
        }
    )
    req = type(req).model_validate(
        {**req.model_dump(), "run_id": run_id, "subjects": [subject]}
    )
    validation = ValidationApplication(app.db_path, "ws", str(tmp_path))
    validation.repository.register_output("ws", subject)
    first = validation.service.evaluate(req, profile)
    native = EngineeringResult(
        subject.result_id,
        "structured",
        "Measured identity",
        (
            Representation(
                "value", "steps/producer/result", "json", sha256=subject.sha256
            ),
        ),
        Provenance(run_id, "producer", "result"),
    )
    path = tmp_path / case.result["run_log_path"]
    record = json.loads(path.read_bytes())
    record["result"]["results"].append(asdict(native))
    record["partial_results"][native.id] = asdict(native)
    path.write_text(json.dumps(record), encoding="utf-8")
    view = await app.get_snapshot(scope(), process, run_id=run_id)
    output = next(item for item in view.outputs if item.result_id == native.id)
    assert output.assessments[0].assessment_id == first.assessment.id
    assert output.assessments[0].currentness == "current"
    second = validation.service.evaluate(
        type(req).model_validate({**req.model_dump(), "idempotency_key": "second"}),
        profile,
    )
    view = await app.get_snapshot(scope(), process, run_id=run_id)
    output = next(item for item in view.outputs if item.result_id == native.id)
    actual = {item.assessment_id: item.currentness for item in output.assessments}
    assert actual == {first.assessment.id: "stale", second.assessment.id: "current"}


@pytest.mark.asyncio
async def test_changed_source_keeps_original_run_and_blocks_mutations(tmp_path):
    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    original = reference(tmp_path, case.checkpoint.workflow_id)
    path = tmp_path / case.checkpoint.workflow_id
    path.write_bytes(path.read_bytes() + b"\n")
    current = reference(tmp_path, case.checkpoint.workflow_id)
    view = await app.get_snapshot(scope(), current, run_id=case.result["run_id"])
    assert view.context.process == original and view.context.process != current
    assert all(not item.enabled for item in view.actions)


@pytest.mark.asyncio
@pytest.mark.parametrize("run_bound", [False, True])
async def test_exact_historical_review_remains_readable_but_cannot_decide(
    tmp_path, run_bound
):
    result, service, _, calls = await run_review(tmp_path)
    app = application(service, tmp_path, database="state.sqlite3")
    original = reference(tmp_path, result["review"]["workflow_path"])
    run_id = result["run_id"]
    frozen = InputSnapshot.create(
        snapshot_id="historical-inputs",
        process=original,
        created_at="2026-09-30T12:00:00Z",
        bindings=(),
    )
    receipt = StartReceipt(
        principal_id="test-user",
        process=original,
        request_id="historical-start",
        payload_digest=canonical_digest(frozen.bindings),
        input_snapshot_id=frozen.snapshot_id,
        input_digest=frozen.digest,
        run_id=run_id,
        run_log_path=result["run_log_path"],
        created_at="2026-09-30T12:00:00Z",
    )
    app.inputs.reserve_start(frozen, receipt)
    source = tmp_path / original.source_path
    source.write_bytes(source.read_bytes() + b"\n")
    recorded = tmp_path / result["run_log_path"]
    before = recorded.read_bytes()
    calls_before = list(calls)
    scoped = scope(run_bound=run_bound, run_id=run_id if run_bound else None)
    view = await app.get_snapshot(scoped, original, run_id=run_id)
    assert view.context.process == original and view.context.run_id == run_id
    assert view.outputs and view.interactions[0].state == "stale"
    assert all(not item.enabled for item in view.actions)
    assert view.interactions[0].decision is None
    assert recorded.read_bytes() == before and calls == calls_before
    forged = original.model_copy(update={"source_digest": "0" * 64})
    with pytest.raises(ProcessInterfaceError) as failure:
        await app.get_snapshot(scoped, forged, run_id=run_id)
    assert failure.value.reason.code == "SCOPE_DENIED"


@pytest.mark.asyncio
async def test_wrong_run_review_pointer_cannot_expose_another_review(tmp_path):
    result, service, _, _ = await run_review(tmp_path)
    app = application(service, tmp_path, database="state.sqlite3")
    process = reference(tmp_path, result["review"]["workflow_path"])
    path = tmp_path / result["run_log_path"]
    record = json.loads(path.read_bytes())
    record["run_id"] = record["result"]["run_id"] = "another-run"
    record["events"] = []
    record["result"]["results"] = []
    record["partial_results"] = {}
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ProcessInterfaceError) as error:
        await app.get_snapshot(scope(), process, run_id="another-run")
    assert error.value.reason.code == "SCOPE_DENIED"


@pytest.mark.asyncio
@pytest.mark.parametrize("exact_failure", [True, False])
async def test_failure_navigation_uses_exact_diagnostic_not_completed_producer(
    tmp_path, exact_failure
):
    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    path = tmp_path / case.result["run_log_path"]
    record = json.loads(path.read_bytes())
    record.update(status="failed", code="WORKFLOW_NOT_READY", error="File unavailable")
    record["events"].append({"kind": "step_completed", "task_id": "package"})
    if exact_failure:
        record["events"].append(
            {
                "kind": "step_diagnostic",
                "task_id": "after",
                "message": "File unavailable",
            }
        )
    path.write_text(json.dumps(record), encoding="utf-8")
    original = path.read_bytes()
    calls = list(case.calls)
    view = await app.get_snapshot(
        scope(),
        reference(tmp_path, case.checkpoint.workflow_id),
        run_id=case.result["run_id"],
    )
    reason = view.diagnostics[0]
    assert reason.step_id == ("after" if exact_failure else None)
    assert reason.navigation.kind == ("block" if exact_failure else "run")
    assert case.calls == calls and path.read_bytes() == original
