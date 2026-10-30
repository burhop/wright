"""Source-run export reuses retained receipts and the canonical recorder."""

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError as SchemaValidationError, validate
from referencing import Registry, Resource

from core.process_interactions import InputSnapshot, ProcessRef, StartReceipt
from core.process_validation import canonical_digest
from data_vault import upgrade_database
from data_vault.process_input_repository import ProcessInputRepository
from workspace_service.adapters.runtime import create_workspace
from workspace_service.support_diagnostic_service import (
    SupportDiagnosticError,
    SupportDiagnosticService,
)


@pytest.fixture
def recorded(tmp_path):
    database = tmp_path / "state.db"
    upgrade_database(database)
    root = tmp_path / "workspace"
    (root / "workflows").mkdir(parents=True)
    create_workspace(str(database), "ws-1", "session-1", str(root), "Private fixture")
    source = "workflows/private-part.workflow.wflow"
    (root / source).write_text("# private customer instructions\n")
    process = ProcessRef(
        workspace_id="ws-1",
        source_path=source,
        source_digest=hashlib.sha256((root / source).read_bytes()).hexdigest(),
    )
    inputs = InputSnapshot.create(
        snapshot_id="inputs-1",
        process=process,
        created_at="2026-10-23T12:00:00Z",
    )
    receipt = StartReceipt(
        process=process,
        principal_id="engineer-1",
        request_id="request-1",
        payload_digest="a" * 64,
        input_snapshot_id=inputs.snapshot_id,
        input_digest=inputs.digest,
        run_id="source-run-1",
        run_log_path="runs/private-part/retained.json",
        created_at=inputs.created_at,
    )
    ProcessInputRepository(database).reserve_start(inputs, receipt)
    record = {
        "workflow_path": source,
        "run_id": receipt.run_id,
        "source_digest": process.source_digest,
        "status": "failed",
        "started_at": inputs.created_at,
        "execution_ended_at": "2026-10-23T12:00:05Z",
        "error": "Bearer SECRET_TOKEN /home/customer/private.step",
        "events": [
            {
                "kind": "step_started",
                "at": "2026-10-23T12:00:01Z",
                "task_id": "create_mesh",
            },
            {
                "kind": "step_completed",
                "at": "2026-10-23T12:00:03Z",
                "task_id": "create_mesh",
            },
            {
                "kind": "step_started",
                "at": "2026-10-23T12:00:04Z",
                "task_id": "check_mesh",
            },
            {
                "kind": "step_diagnostic",
                "at": "2026-10-23T12:00:05Z",
                "task_id": "check_mesh",
                "code": "TASK_FAILED",
                "message": "private model response",
                "prompt": "private engineering prompt",
                "tool_result": "private geometry",
            },
        ],
    }
    path = root / receipt.run_log_path
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record))
    service = SupportDiagnosticService(
        database,
        clock=lambda: datetime(2026, 10, 23, 12, 1, tzinfo=UTC),
    )
    return service, record, path, receipt


def preview(service, **scope):
    return service.preview(
        principal_id="engineer-1",
        workspace_id="ws-1",
        scope=scope or {"source_run_id": "source-run-1"},
    )


def export(service, result):
    return service.export(
        principal_id="engineer-1",
        workspace_id="ws-1",
        snapshot_digest=result.snapshot.snapshot_digest,
        confirmation_token=result.confirmation_token,
    )


def test_exact_source_evidence_and_recorded_timing_export_without_private_values(
    recorded, caplog
):
    service, record, path, receipt = recorded
    original = path.read_bytes()
    with caplog.at_level("INFO"):
        result = preview(service)
        exported = export(service, result)
    run = result.snapshot.source_run
    assert run.run_id == receipt.run_id
    assert run.source_digest == f"sha256:{receipt.process.source_digest}"
    assert run.record_digest == f"sha256:{canonical_digest(record)}"
    assert run.recorded_status == "failed"
    assert run.events[1].elapsed_ms == 2000
    assert run.events[1].start_sequence == 1
    assert run.events[3].reason == "TASK_FAILED"
    assert run.events[3].step_id == "check_mesh"
    assert result.snapshot.failures[0].reason == "SOURCE_RUN_FAILED"
    assert result.snapshot.failures[0].cleanup == "unknown"
    assert path.read_bytes() == original
    assert exported.content == result.snapshot.export_bytes()
    schema = (
        Path(__file__).resolve().parents[3]
        / "specs/073-program-hardening/contracts/support-diagnostic-snapshot.schema.json"
    )
    inventory_schema = json.loads(
        (schema.parent / "state-inventory.schema.json").read_text()
    )
    registry = Registry().with_resource(
        inventory_schema["$id"], Resource.from_contents(inventory_schema)
    )
    validate(
        json.loads(exported.content), json.loads(schema.read_text()), registry=registry
    )
    surfaces = exported.content.decode() + caplog.text
    for private in (
        "private-part",
        "/home/customer",
        "SECRET_TOKEN",
        "private geometry",
        "private engineering prompt",
        "private model response",
        receipt.principal_id,
        result.confirmation_token,
    ):
        assert private not in surfaces
    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_EXPORT_DENIED"):
        export(service, result)


@pytest.mark.parametrize(
    "other_scope", [{"scenario_run_id": "scenario-1"}, {"session_id": "session-1"}]
)
def test_source_scope_cannot_claim_scenario_or_session_identity(recorded, other_scope):
    with pytest.raises(SupportDiagnosticError, match="INVALID_DIAGNOSTIC_SCOPE"):
        preview(recorded[0], source_run_id="source-run-1", **other_scope)


def test_run_from_another_workspace_is_denied(recorded, tmp_path):
    service, _, _, _ = recorded
    other = tmp_path / "other"
    other.mkdir()
    create_workspace(
        str(service.database_path), "ws-2", "session-2", str(other), "Other"
    )
    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_SCOPE_FORBIDDEN"):
        service.preview(
            principal_id="engineer-1",
            workspace_id="ws-2",
            scope={"source_run_id": "source-run-1"},
        )


@pytest.mark.parametrize(
    "mutation", ["missing", "wrong-run", "wrong-source", "invalid-json", "symlink"]
)
def test_missing_or_unverifiable_record_never_becomes_healthy_preview(
    recorded, tmp_path, mutation
):
    service, record, path, _ = recorded
    if mutation == "missing":
        path.unlink()
    elif mutation == "invalid-json":
        path.write_text("{")
    elif mutation == "symlink":
        outside = tmp_path / "outside.json"
        outside.write_text(path.read_text())
        path.unlink()
        path.symlink_to(outside)
    else:
        record["run_id" if mutation == "wrong-run" else "source_digest"] = "f" * 64
        path.write_text(json.dumps(record))
    with pytest.raises(
        SupportDiagnosticError, match="DIAGNOSTIC_SOURCE_EVIDENCE_UNAVAILABLE"
    ):
        preview(service)


@pytest.mark.parametrize("mutation", ["event-content", "deleted"])
def test_same_count_event_change_or_missing_evidence_invalidates_grant(
    recorded, mutation
):
    service, record, path, _ = recorded
    result = preview(service)
    if mutation == "deleted":
        path.unlink()
    else:
        record["events"][-1]["message"] = "changed private diagnostic"
        path.write_text(json.dumps(record))
    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_PREVIEW_STALE"):
        export(service, result)


def test_timing_export_is_bounded_and_reports_omitted_untrusted_metadata(recorded):
    service, record, path, _ = recorded
    record["events"] = [
        {"kind": "step_started", "task_id": "check_mesh", "at": "2026-10-23T12:00:01Z"}
        for _ in range(105)
    ] + [
        {
            "kind": "step_diagnostic",
            "task_id": "/home/private/step",
            "at": "not a date",
            "code": "SECRET_VALUE",
        }
    ]
    path.write_text(json.dumps(record))
    run = preview(service).snapshot.source_run
    assert run.event_count == 106
    assert len(run.events) == 100
    assert run.events_truncated and run.metadata_omitted
    assert run.events[0].sequence == 7
    assert run.events[-1].step_id is None and run.events[-1].at is None
    assert run.events[-1].reason == "SOURCE_STEP_DIAGNOSTIC"
    assert "SECRET_VALUE" not in run.model_dump_json()


def test_repeated_steps_keep_distinct_observed_attempt_timings(recorded):
    service, record, path, _ = recorded
    record["events"] += [
        {
            "kind": "step_started",
            "task_id": "create_mesh",
            "at": "2026-10-23T12:01:01Z",
        },
        {
            "kind": "step_completed",
            "task_id": "create_mesh",
            "at": "2026-10-23T12:01:06Z",
        },
    ]
    path.write_text(json.dumps(record))
    run = preview(service).snapshot.source_run
    assert [
        (event.start_sequence, event.elapsed_ms)
        for event in run.events
        if event.elapsed_ms is not None
    ] == [(1, 2000), (5, 5000)]


@pytest.mark.parametrize("kind", ["run_started", "run_resumed", "run_completed"])
def test_whole_run_empty_task_sentinel_does_not_claim_metadata_omission(recorded, kind):
    service, record, path, _ = recorded
    record["events"] = [{"kind": kind, "task_id": "", "at": "2026-10-23T12:00:00Z"}]
    path.write_text(json.dumps(record))
    run = preview(service).snapshot.source_run
    assert run.events[0].step_id is None
    assert not run.metadata_omitted


@pytest.mark.parametrize(
    ("field", "invalid"),
    [
        ("run_id", "/home/customer/run"),
        ("run_id", "r" * 129),
        ("source_digest", "a" * 64),
        ("source_digest", "sha256:" + "A" * 64),
        ("record_digest", "private record"),
        ("record_digest", "sha256:" + "a" * 63),
        ("reason", "private failure /home/customer/part"),
        ("reason", "task_failed"),
    ],
)
def test_published_source_schema_rejects_unsafe_identity_digest_and_reason(
    recorded, field, invalid
):
    run = preview(recorded[0]).snapshot.source_run.model_dump(
        mode="json", exclude_none=True
    )
    if field == "reason":
        run["events"][-1]["reason"] = invalid
    else:
        run[field] = invalid
    contract = (
        Path(__file__).resolve().parents[3]
        / "specs/073-program-hardening/contracts/support-diagnostic-snapshot.schema.json"
    )
    schema = json.loads(contract.read_text())
    with pytest.raises(SchemaValidationError):
        validate(run, {"$ref": "#/$defs/SourceRunDiagnostic", "$defs": schema["$defs"]})
