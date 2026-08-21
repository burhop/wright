from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import UTC, datetime, timedelta

from core.rivet_mcp import RunManifestDraft
from data_vault import WorkflowRunRepository, upgrade_database
from workspace_service.rivet_evidence import (
    build_run_evidence,
    compare_run_manifest,
    project_output_summary,
    project_result_value,
    run_material_projection,
    run_observation_projection,
)
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from data_vault.workflow_runs import WorkflowRunEventRecord, WorkflowRunRecord
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[3]


def test_result_projection_redacts_bounds_and_preserves_success() -> None:
    projected = project_result_value(
        {
            "message": "created",
            "authorization": "Bearer must-not-export",
            "nested": {"api_key": "must-not-export", "value": "x" * 9000},
        },
        name="result",
        origin="final_output",
        maximum_bytes=1024,
    )

    assert projected["complete"] is False
    assert projected["truncation_reason"] == "size_limit"
    assert projected["digest"]
    assert projected["original_bytes"] > projected["retained_bytes"]
    assert projected["redaction_count"] == 2
    assert "must-not-export" not in json.dumps(projected)


def test_output_summary_retains_named_null_and_structured_results() -> None:
    summary, truncated = project_output_summary(
        {"empty": None, "dimensions": {"width": 10, "height": 20}},
        duration_ms=42,
    )

    assert truncated is False
    assert summary["durationMs"] == 42
    assert [item["name"] for item in summary["results"]] == [
        "dimensions",
        "empty",
    ]
    assert summary["outputs"]["empty"] is None
    assert summary["results"][1]["kind"] == "null"


def _manifest() -> dict:
    started = datetime(2026, 8, 13, tzinfo=UTC)
    draft = RunManifestDraft(
        run_id="run-1",
        generation=1,
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest="a" * 64,
        graph_id="Main",
        review_digest="b" * 64,
        binding_set_digest="c" * 64,
        policy_snapshot_digest="d" * 64,
        authority_id="authority-1",
        authority_digest="e" * 64,
        started_at=started,
        trace_id="trace-1",
        runtime_identity={
            "protocol_version": 2,
            "rivet_version": "2.8.9",
            "package_version": "2.1.9",
            "runner_sha256": "f" * 64,
            "source_revision": "fixture",
        },
        authority_expires_at=started + timedelta(minutes=5),
        bindings=(
            {
                "node_id": "node-1",
                "qualified_tool_name": "alpha__inspect",
                "server_revision": "alpha-v1",
                "schema_digest": "1" * 64,
                "validation_evidence_id": "validation-1",
                "binding_digest": "2" * 64,
            },
        ),
    )
    draft.approval_ids.append("approval-1")
    manifest = draft.finalize(
        terminal_state="failed",
        completed_at=started + timedelta(seconds=4),
        reason_code="RIVET_CALL_APPROVAL_DENIED",
    )
    return {**manifest.digest_material(), "manifest_digest": manifest.manifest_digest}


def test_evidence_orders_correlations_and_proves_denial_before_child() -> None:
    manifest = _manifest()
    evidence = build_run_evidence(
        manifest=manifest,
        child_calls=(),
        approvals=(
            {
                "approval_id": "approval-1",
                "run_id": "run-1",
                "authority_id": "must-not-export",
                "session_id": "gateway-session",
                "node_id": "node-1",
                "binding_digest": "2" * 64,
                "server_id": "alpha",
                "qualified_tool_name": "alpha__inspect",
                "request_id": "request-1",
                "argument_digest": "3" * 64,
                "argument_summary": {"authorization": "Bearer must-not-export"},
                "required_gates": ["engineering.write"],
                "state": "denied",
                "created_at": "2026-08-13T00:00:02Z",
                "expires_at": "2026-08-13T00:05:00Z",
            },
        ),
        events=(
            {
                "sequence": 1,
                "occurred_at": 1786579201,
                "kind": "started",
                "payload": {},
            },
            {
                "sequence": 2,
                "occurred_at": 1786579203,
                "kind": "failed",
                "payload": {"code": "RIVET_CALL_APPROVAL_DENIED"},
            },
        ),
        current={
            "workflow_digest": "a" * 64,
            "review_digest": "b" * 64,
            "binding_set_digest": "c" * 64,
            "policy_snapshot_digest": "d" * 64,
            "runner_sha256": "f" * 64,
        },
    )

    kinds = [item["kind"] for item in evidence["timeline"]]
    assert {"binding", "started", "approval", "failed"}.issubset(kinds)
    assert [item["occurred_at"] for item in evidence["timeline"]] == sorted(
        item["occurred_at"] for item in evidence["timeline"]
    )
    assert evidence["accounting"]["denied_before_child_count"] == 1
    assert evidence["accounting"]["child_call_count"] == 0
    assert evidence["accounting"]["complete"] is True
    assert evidence["reproducibility"]["reproducible"] is True
    encoded = json.dumps(evidence)
    assert "must-not-export" not in encoded
    assert "gateway-session" not in encoded
    assert "[redacted]" in encoded.lower()


def test_reproducibility_reports_exact_stale_differences_and_recovery() -> None:
    report = compare_run_manifest(
        _manifest(),
        {
            "workflow_digest": "9" * 64,
            "review_digest": "8" * 64,
            "binding_set_digest": "7" * 64,
            "policy_snapshot_digest": "6" * 64,
            "runner_sha256": "5" * 64,
            "stale_reasons": ["validation_evidence_changed"],
        },
    )

    assert report["reproducible"] is False
    assert {item["code"] for item in report["differences"]} == {
        "workflow_changed",
        "review_changed",
        "binding_set_changed",
        "policy_snapshot_changed",
        "runner_artifact_changed",
        "validation_evidence_changed",
    }
    assert all(item["recovery_action"] for item in report["differences"])


def test_run_and_ordered_events_are_restored_after_process_restart(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', ?, 1, 1)""",
            (str(tmp_path),),
        )
    repository = WorkflowRunRepository(str(database))
    repository.create(
        WorkflowRunRecord(
            run_id="restart-run",
            workspace_id="workspace-1",
            session_id="session-1",
            workflow_id="workflow-1",
            revision=1,
            digest="a" * 64,
            graph="Main",
            state="running",
            generation=1,
            started_at=1,
            completed_at=None,
            reason_code=None,
            output_summary=None,
            output_truncated=False,
        )
    )
    repository.transition(
        "restart-run", "failed", completed_at=3, reason_code="runner_restarted"
    )
    repository.append_event(WorkflowRunEventRecord("restart-run", 1, 1, "started", {}))
    repository.append_event(
        WorkflowRunEventRecord(
            "restart-run", 2, 3, "failed", {"code": "runner_restarted"}
        )
    )
    restarted = WorkspaceWorkflowRunner(
        supervisor=object(),  # type: ignore[arg-type]
        settings=RunnerSettings(enabled=True),
        node_path="node",
        run_repository=repository,
    )

    assert restarted.get("restart-run").reason == "runner_restarted"
    events = restarted.events("restart-run")
    assert [event.sequence for event in events] == [1, 2]
    assert events[-1].occurred_at == 3


def test_provider_neutral_v2_contracts_are_valid_and_v1_resources_are_unchanged() -> (
    None
):
    contracts = (
        ROOT
        / "packages"
        / "workspace_service"
        / "src"
        / "workspace_service"
        / "_rivet"
        / "contracts"
    )
    archived = ROOT / "specs" / "069-rivet-mcp-gateway" / "contracts"
    for name in ("capability-binding.schema.json", "run-manifest.schema.json"):
        assert (contracts / name).read_bytes() == (archived / name).read_bytes()
    for name in ("capability-binding-v2.schema.json", "run-manifest-v2.schema.json"):
        Draft202012Validator.check_schema(
            json.loads((contracts / name).read_text(encoding="utf-8"))
        )


def test_capability_v2_schema_rejects_kind_evidence_mismatch() -> None:
    path = (
        ROOT
        / "packages"
        / "workspace_service"
        / "src"
        / "workspace_service"
        / "_rivet"
        / "contracts"
        / "capability-binding-v2.schema.json"
    )
    schema = json.loads(path.read_text(encoding="utf-8"))
    provider = {
        "schema_version": "1.0",
        "provider_kind": "engineering_model",
        "provider_id": "model-1",
        "capability_id": "screen",
        "resource_class": "small",
        "evidence": {
            "server_id": "server-1",
            "server_revision": "1",
            "tool_name": "inspect",
            "validation_evidence_id": "validation-1",
            "workspace_grant_digest": "a" * 64,
        },
    }
    provider_schema = schema["$defs"]["provider"]
    errors = list(
        Draft202012Validator(schema)
        .evolve(schema=provider_schema)
        .iter_errors(provider)
    )
    assert errors


def test_provider_material_is_compared_while_observation_is_non_material() -> None:
    manifest = _manifest()
    provider = {
        "schema_version": "1.0",
        "provider_kind": "mcp",
        "provider_id": "fixture-cad",
        "capability_id": "inspect_context",
        "resource_class": "small",
        "evidence": {
            "server_id": "fixture-cad",
            "server_revision": "fixture-v1",
            "tool_name": "inspect_context",
            "validation_evidence_id": "validation-fixture-cad",
            "workspace_grant_digest": "4" * 64,
        },
    }
    manifest["schema_version"] = 2
    manifest["bindings"][0]["provider"] = provider
    first_material = run_material_projection(manifest)
    first_observation = run_observation_projection(manifest)
    changed_observation = dict(manifest)
    changed_observation.update(
        {
            "run_id": "another-run",
            "trace_id": "another-trace",
            "started_at": "2026-08-13T00:10:00Z",
            "completed_at": "2026-08-13T00:10:01Z",
        }
    )
    assert run_material_projection(changed_observation) == first_material
    assert run_observation_projection(changed_observation) != first_observation

    report = compare_run_manifest(
        manifest,
        {"provider_evidence_digests": ["9" * 64]},
    )
    assert report["reproducible"] is False
    assert report["differences"][0]["code"] == "provider_evidence_changed"
