from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from core.rivet_mcp import (
    ArtifactReference,
    RivetChildCallRecord,
    RunManifestDraft,
    canonical_digest,
)
from data_vault import RivetMcpRepository, upgrade_database
from jsonschema import Draft202012Validator, FormatChecker


DIGEST = "a" * 64
ROOT = Path(__file__).resolve().parents[3]


def _repository(tmp_path) -> RivetMcpRepository:
    path = tmp_path / "state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', 'D:/workspace', 1, 1)"""
        )
        for run_id in ("run-1", "run-orphan"):
            connection.execute(
                """INSERT INTO workspace_workflow_runs
                (run_id, workspace_id, session_id, workflow_id, revision, digest,
                 graph, state, generation, started_at, output_truncated)
                VALUES (?, 'workspace-1', 'session-1', 'workflow-1', 1, ?,
                        'Main', 'running', 1, 1, 0)""",
                (run_id, DIGEST),
            )
    return RivetMcpRepository(str(path))


def _draft(run_id: str = "run-1") -> RunManifestDraft:
    started = datetime(2026, 8, 13, tzinfo=UTC)
    return RunManifestDraft(
        run_id=run_id,
        generation=1,
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest=DIGEST,
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
            "source_revision": "fixture-revision",
        },
        authority_expires_at=started + timedelta(minutes=5),
        bindings=(
            {
                "node_id": "node-1",
                "qualified_tool_name": "alpha__inspect",
                "server_revision": "fixture-v1",
                "schema_digest": "1" * 64,
                "validation_evidence_id": "validation-1",
                "binding_digest": "2" * 64,
            },
        ),
    )


def test_manifest_identity_finalization_digest_schema_and_artifact_are_immutable(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)
    draft = _draft()
    repository.create_manifest_draft("manifest-1", draft)
    repository.create_manifest_draft("manifest-1", draft)
    changed = _draft()
    changed.review_digest = "9" * 64
    with pytest.raises(ValueError, match="immutable"):
        repository.create_manifest_draft("manifest-1", changed)

    manifest = draft.finalize(
        terminal_state="succeeded",
        completed_at=draft.started_at + timedelta(seconds=1),
        reason_code=None,
        artifacts=(
            ArtifactReference(
                "result/mesh.vtk", "model/vnd.vtk", "3" * 64, 128, "Mesh"
            ),
        ),
    )
    repository.finalize_manifest("manifest-1", manifest)
    with pytest.raises(ValueError, match="already finalized"):
        repository.finalize_manifest("manifest-1", manifest)
    document = repository.get_manifest_document("run-1")
    assert document is not None
    digest_document = dict(document)
    assert digest_document.pop("manifest_digest") == canonical_digest(digest_document)
    schema = json.loads(
        (
            ROOT / "specs/069-rivet-mcp-gateway/contracts/run-manifest.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(document)
    assert document["artifacts"][0]["artifact_id"] == "result/mesh.vtk"
    assert "token" not in json.dumps(document).lower()


def test_manifest_caps_evidence_and_restart_terminalizes_orphan(tmp_path) -> None:
    repository = _repository(tmp_path)
    draft = _draft("run-orphan")
    draft.child_call_ids.extend(f"call-{index}" for index in range(1002))
    draft.approval_ids.extend(f"approval-{index}" for index in range(1002))
    repository.create_manifest_draft("manifest-orphan", draft)
    assert repository.finalize_orphaned_manifests() == 1
    document = repository.get_manifest_document("run-orphan")
    assert document is not None
    assert document["terminal_state"] == "failed"
    assert document["reason_code"] == "runner_restarted"
    assert document["event_truncated"] is True
    assert len(document["child_call_ids"]) == 1000
    assert len(document["approval_ids"]) == 1000


def test_child_call_documents_preserve_optional_safe_result_and_read_old_records(
    tmp_path,
) -> None:
    repository = _repository(tmp_path)
    started = datetime(2026, 8, 20, tzinfo=UTC)
    repository.append_child_call(
        RivetChildCallRecord(
            call_id="call-new",
            request_id="request-new",
            run_id="run-1",
            authority_id="authority-1",
            node_id="node-1",
            binding_digest="b" * 64,
            qualified_tool_name="cad__inspect",
            server_revision="fixture-v1",
            schema_digest="c" * 64,
            validation_evidence_id="validation-1",
            argument_digest="d" * 64,
            trace_id="trace-child",
            state="succeeded",
            child_received=True,
            started_at=started,
            completed_at=started + timedelta(seconds=1),
            result={"kind": "structured", "value": {"token": "[REDACTED]"}},
            result_complete=True,
            redaction_count=1,
        )
    )
    old_document = {
        "call_id": "call-old",
        "request_id": "request-old",
        "run_id": "run-1",
        "node_id": "node-old",
        "binding_digest": "e" * 64,
        "state": "succeeded",
        "child_received": True,
    }
    with sqlite3.connect(repository.db_path) as connection:
        connection.execute(
            """INSERT INTO workspace_workflow_child_calls
            (call_id, run_id, request_id, node_id, binding_digest, state,
             child_received, call_json, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                "call-old",
                "run-1",
                "request-old",
                "node-old",
                "e" * 64,
                "succeeded",
                1,
                json.dumps(old_document),
                1,
                2,
            ),
        )
    children, _approvals = repository.run_evidence_documents("run-1")
    by_id = {item["call_id"]: item for item in children}
    assert by_id["call-new"]["result"]["value"]["token"] == "[REDACTED]"
    assert by_id["call-new"]["result_complete"] is True
    assert by_id["call-new"]["redaction_count"] == 1
    assert "result" not in by_id["call-old"]
    assert "result_complete" not in by_id["call-old"]
