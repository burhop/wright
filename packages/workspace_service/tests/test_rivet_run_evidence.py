from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

from core.rivet_mcp import RunManifestDraft
from data_vault import WorkflowRunRepository, upgrade_database
from workspace_service.rivet_evidence import (
    build_run_evidence,
    compare_run_manifest,
)
from workspace_service.workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from data_vault.workflow_runs import WorkflowRunEventRecord, WorkflowRunRecord


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
