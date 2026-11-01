"""Interaction views compose real recorder/review/input owners without execution."""

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from core.process_interactions import (
    PAGE_ITEMS,
    InputSnapshot,
    ProcessRef,
    StartReceipt,
    ValueBinding,
)
from core.process_validation import canonical_digest
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.owners import (
    _approval_evidence,
    _approval_instructions,
)
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


def test_action_evidence_is_deduplicated_exact_and_never_truncated():
    artifact = {"path": "outputs/basis.json", "sha256": "a" * 64}
    checkpoint = SimpleNamespace(continuation={"artifact_files": [artifact, artifact]})
    evidence = _approval_evidence(checkpoint)
    assert len(evidence) == 1
    assert evidence[0].artifact_ref == artifact["path"]
    assert evidence[0].sha256 == artifact["sha256"]
    checkpoint.continuation["artifact_files"] = [
        {"path": f"outputs/evidence-{index}.json", "sha256": "a" * 64}
        for index in range(PAGE_ITEMS + 1)
    ]
    with pytest.raises(ProcessInterfaceError) as error:
        _approval_evidence(checkpoint)
    assert error.value.reason.code == "READINESS_UNSUPPORTED"


def test_nested_thermal_evidence_preserves_all_long_paths_and_digests():
    prefix = "thermal/" + "/".join(["recorded-comparison" * 3] * 3)
    artifacts = [
        {"path": f"{prefix}/result-{index}.json", "sha256": f"{index:064x}"}
        for index in range(46)
    ]
    checkpoint = SimpleNamespace(continuation={"artifact_files": artifacts})
    before = json.dumps(checkpoint.continuation, sort_keys=True)
    evidence = _approval_evidence(checkpoint)
    assert len(evidence) == 46
    assert all(len(item.artifact_ref) > 160 for item in evidence)
    assert {(item.artifact_ref, item.sha256) for item in evidence} == {
        (item["path"], item["sha256"]) for item in artifacts
    }
    assert json.dumps(checkpoint.continuation, sort_keys=True) == before


def thermal_review_evidence():
    plot = EngineeringResult(
        "thermal-run:solve:temperature-plot",
        "analysis",
        "Heat-spreader temperature field",
        (
            Representation(
                "workspace_file", "thermal/temperature-map.png", "png", sha256="b" * 64
            ),
        ),
        Provenance(
            "thermal-run", "solve", "temperature-plot", definition_digest="f" * 64
        ),
    )
    table = EngineeringResult(
        "thermal-run:solve:temperatures",
        "file",
        "Temperature table",
        (
            Representation(
                "workspace_file", "thermal/temperatures.csv", "csv", sha256="c" * 64
            ),
        ),
        Provenance("thermal-run", "solve", "temperatures"),
    )
    static = [
        {"path": f"inputs/{name}", "sha256": "a" * 64}
        for name in ("concept.png", "context.md", "loads.json", "requirements.md")
    ]
    return SimpleNamespace(
        run_id="thermal-run",
        subject={"definition_digest": "f" * 64},
        continuation={
            "run_id": "thermal-run",
            "artifact_files": [
                *static,
                {"path": "thermal/temperature-map.png", "sha256": "b" * 64},
                {"path": "thermal/temperatures.csv", "sha256": "c" * 64},
            ],
            "results": [table.to_dict(), plot.to_dict()],
        },
    )


def test_thermal_review_promotes_exact_produced_plot_before_static_concept_without_losing_evidence():
    checkpoint = thermal_review_evidence()
    before = json.dumps(checkpoint.continuation, sort_keys=True)
    original = {
        (item["path"], item["sha256"])
        for item in checkpoint.continuation["artifact_files"]
    }
    # The prior alphabetical presentation placed all four static inputs first.
    assert all(path.startswith("inputs/") for path, _ in sorted(original)[:4])
    evidence = _approval_evidence(checkpoint)
    assert [item.artifact_ref for item in evidence[:2]] == [
        "thermal/temperature-map.png",
        "thermal/temperatures.csv",
    ]
    assert {(item.artifact_ref, item.sha256) for item in evidence} == original
    assert all(
        item.result_id is None and item.representation_id is None for item in evidence
    )
    assert json.dumps(checkpoint.continuation, sort_keys=True) == before


@pytest.mark.parametrize(
    "mismatch",
    ["run", "continuation_run", "definition", "path", "digest", "kind", "missing_hash"],
)
def test_review_does_not_promote_stale_or_mismatched_result_representations(mismatch):
    checkpoint = thermal_review_evidence()
    result = checkpoint.continuation["results"][1]
    representation = result["representations"][0]
    if mismatch == "run":
        result["provenance"]["run_id"] = "previous-run"
    elif mismatch == "continuation_run":
        checkpoint.continuation["run_id"] = "previous-run"
    elif mismatch == "definition":
        result["provenance"]["definition_digest"] = "e" * 64
    elif mismatch == "path":
        representation["location"] = "another/temperature-map.png"
    elif mismatch == "digest":
        representation["sha256"] = "d" * 64
    elif mismatch == "kind":
        representation["kind"] = "value"
    else:
        representation["sha256"] = None
    original = {
        (item["path"], item["sha256"])
        for item in checkpoint.continuation["artifact_files"]
    }
    evidence = _approval_evidence(checkpoint)
    paths = [item.artifact_ref for item in evidence]
    assert paths.index("thermal/temperature-map.png") > paths.index(
        "inputs/concept.png"
    )
    assert {(item.artifact_ref, item.sha256) for item in evidence} == original


def test_review_uses_exact_export_format_and_keeps_other_revisions_unpromoted():
    checkpoint = thermal_review_evidence()
    table, plot = checkpoint.continuation["results"]
    # Named export representations are retained results too; their own provenance
    # and exact path/hash must match, irrespective of their filename suffix.
    plot["representations"][0]["location"] = "thermal/z-field.data"
    plot["representations"][0]["format"] = "PNG"
    table["exports"] = [plot]
    checkpoint.continuation["results"] = [table]
    checkpoint.continuation["artifact_files"] += [
        {"path": "thermal/z-field.data", "sha256": "b" * 64},
        {"path": "thermal/z-field.data", "sha256": "d" * 64},
    ]
    evidence = _approval_evidence(checkpoint)
    assert (evidence[0].artifact_ref, evidence[0].sha256) == (
        "thermal/z-field.data",
        "b" * 64,
    )
    paths = [(item.artifact_ref, item.sha256) for item in evidence]
    assert paths.index(("thermal/z-field.data", "d" * 64)) > paths.index(
        ("inputs/concept.png", "a" * 64)
    )
    assert set(paths) == {
        (item["path"], item["sha256"])
        for item in checkpoint.continuation["artifact_files"]
    }


@pytest.mark.parametrize(
    "saved", [None, {"not": "a result list"}, [{"incomplete": True}]]
)
def test_unusable_optional_result_metadata_keeps_all_exact_review_references(saved):
    checkpoint = thermal_review_evidence()
    checkpoint.continuation["results"] = saved
    evidence = _approval_evidence(checkpoint)
    assert [(item.artifact_ref, item.sha256) for item in evidence] == sorted(
        (item["path"], item["sha256"])
        for item in checkpoint.continuation["artifact_files"]
    )


def test_action_instructions_use_exact_accepted_review_text_not_a_new_revision():
    source = """task review
  instructions: "Inspect the exact socket section."
  settings: {"approval_message":"Confirm the measured D-flat and blind depth."}
end
"""
    resolved = SimpleNamespace(
        process=SimpleNamespace(source_digest="a" * 64),
        document=SimpleNamespace(source=source),
    )
    checkpoint = SimpleNamespace(
        subject={"definition_digest": "a" * 64},
        step_id="review",
        continuation={"step_title": "Original socket review"},
    )
    assert _approval_instructions(checkpoint, resolved) == (
        "Confirm the measured D-flat and blind depth."
    )
    resolved.document.source = source.replace(
        '{"approval_message":"Confirm the measured D-flat and blind depth."}', "{}"
    )
    assert _approval_instructions(checkpoint, resolved) == (
        "Inspect the exact socket section."
    )
    resolved.process.source_digest = "b" * 64
    assert _approval_instructions(checkpoint, resolved) == "Original socket review"


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
    assert view.interactions[0].instructions == "Review the exact package and printer."
    assert {
        (item.artifact_ref, item.sha256) for item in view.interactions[0].evidence
    } == {
        (item["path"], item["sha256"])
        for item in case.checkpoint.continuation["artifact_files"]
    }
    assert view.interactions[0].evidence
    actions = {item.operation: item for item in view.actions}
    assert actions["review"].enabled and not actions["action"].enabled
    assert view.observations[0].progress_percent is None
    local = view.observations[0]
    assert local.provider_binding == "wright-source-run"
    assert datetime.fromisoformat(local.stale_after) == (
        datetime.fromisoformat(local.observed_at) + timedelta(seconds=30)
    )
    assert local.estimated_remaining_seconds is None
    assert view.context.input_snapshot_id is None
    assert case.calls == calls
    assert (tmp_path / case.result["run_log_path"]).read_bytes() == before


@pytest.mark.asyncio
async def test_wide_run_keeps_late_exact_file_readable_without_execution(tmp_path):
    from workspace_service.adapters.filesystem import LocalWorkspaceFiles
    from workspace_service.executor import BoundedExecutor
    from workspace_service.use_cases.files import WorkspaceFileUseCases

    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    process = reference(tmp_path, case.checkpoint.workflow_id)
    run_id = case.result["run_id"]
    path = tmp_path / case.result["run_log_path"]
    record = json.loads(path.read_bytes())
    content = b"requirement,value\nsocket,5.6\n"
    digest = hashlib.sha256(content).hexdigest()
    for index in range(160):
        filename = f"evidence-{index:03d}-" + "a" * 100 + ".csv"
        (tmp_path / filename).write_bytes(content)
        item = EngineeringResult(
            f"{run_id}:producer:evidence-{index}",
            "file",
            filename,
            (
                Representation(
                    "workspace_file",
                    filename,
                    "csv",
                    sha256=digest,
                    size_bytes=len(content),
                ),
            ),
            Provenance(run_id, "producer", f"evidence-{index}"),
        )
        record["partial_results"][item.id] = item.to_dict()
    # Long progress text is still bounded independently from the result inventory.
    record["events"].append(
        {"kind": "step_progress", "task_id": "producer", "message": "x" * 5000}
    )
    path.write_text(json.dumps(record), encoding="utf-8")
    original = path.read_bytes()
    calls = list(case.calls)
    view = await app.get_snapshot(scope(), process, run_id=run_id)
    last = next(output for output in view.outputs if output.result_id == item.id)
    assert last.representations[0].artifact_ref == filename
    reader_scope = scope(capabilities=frozenset({"process.read", "process.results"}))
    executor = BoundedExecutor()
    app.workspace.files = WorkspaceFileUseCases(
        app.db_path, executor, LocalWorkspaceFiles
    )
    try:
        opened = await app.artifacts.read(
            reader_scope, process, last.representations[0], run_id=run_id
        )
        assert opened.content == content
    finally:
        await executor.close()
    assert path.read_bytes() == original
    assert case.calls == calls


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
async def test_checkpoint_evidence_can_be_read_without_review_or_execution(tmp_path):
    from core.process_interactions import ArtifactRef
    from workspace_service.adapters.filesystem import LocalWorkspaceFiles
    from workspace_service.executor import BoundedExecutor
    from workspace_service.use_cases.files import WorkspaceFileUseCases

    case = await setup_case(tmp_path)
    app = application(case.services, tmp_path)
    process = reference(tmp_path, case.checkpoint.workflow_id)
    reader_scope = scope(capabilities=frozenset({"process.read", "process.results"}))
    item = case.checkpoint.continuation["artifact_files"][0]
    evidence = ArtifactRef(artifact_ref=item["path"], sha256=item["sha256"])
    run_file = tmp_path / case.result["run_log_path"]
    before = run_file.read_bytes()
    calls = list(case.calls)
    executor = BoundedExecutor()
    app.workspace.files = WorkspaceFileUseCases(
        app.db_path, executor, LocalWorkspaceFiles
    )
    try:
        artifact = await app.artifacts.read(
            reader_scope, process, evidence, run_id=case.result["run_id"]
        )
        assert artifact.content == (tmp_path / evidence.artifact_ref).read_bytes()
        assert case.calls == calls
        assert run_file.read_bytes() == before
        assert (
            app.workspace.workflow_external_actions.get(
                case.checkpoint.checkpoint_id,
                workspace_id="ws",
                run_id=case.result["run_id"],
            ).actor
            is None
        )
        for forged in (
            evidence.model_copy(update={"artifact_ref": "private.txt"}),
            evidence.model_copy(update={"sha256": "0" * 64}),
            evidence.model_copy(update={"result_id": "invented-result"}),
            evidence.model_copy(
                update={"representation_id": "invented-representation"}
            ),
        ):
            with pytest.raises(ProcessInterfaceError) as denied:
                await app.artifacts.read(
                    reader_scope, process, forged, run_id=case.result["run_id"]
                )
            assert denied.value.reason.code == "SCOPE_DENIED"
        with pytest.raises(ProcessInterfaceError) as wrong_subject:
            app.artifacts._authorize_checkpoint(
                process,
                case.result["run_id"],
                {
                    "approval": {
                        "checkpoint_id": case.checkpoint.checkpoint_id,
                        "subject_digest": "0" * 64,
                    }
                },
                evidence,
            )
        assert wrong_subject.value.reason.code == "SCOPE_DENIED"
        (tmp_path / evidence.artifact_ref).write_bytes(b"changed checkpoint evidence")
        with pytest.raises(ProcessInterfaceError) as stale:
            await app.artifacts.read(
                reader_scope, process, evidence, run_id=case.result["run_id"]
            )
        assert stale.value.reason.code == "SUBJECT_STALE"
    finally:
        await executor.close()


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
