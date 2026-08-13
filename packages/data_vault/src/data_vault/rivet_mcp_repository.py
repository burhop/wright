"""SQLite persistence for reviewed Rivet MCP bindings and run evidence."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from core.rivet_mcp import (
    CapabilityBinding,
    PendingRivetCallApproval,
    RivetChildCallRecord,
    RunManifest,
    RunManifestDraft,
    WorkflowBindingSet,
    canonical_digest,
    canonical_json,
)

from .state_store import connect_state_db


def _epoch(value: datetime) -> int:
    return int(value.astimezone(UTC).timestamp())


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _json(value: Any) -> str:
    return canonical_json(value)


def _binding_document(binding: CapabilityBinding) -> dict[str, Any]:
    return json.loads(_json(binding.canonical()))


def _binding_from_document(value: dict[str, Any]) -> CapabilityBinding:
    document = dict(value)
    document.pop("schema_version", None)
    document["created_at"] = _datetime(str(document["created_at"]))
    return CapabilityBinding(**document)


def _draft_document(draft: RunManifestDraft) -> dict[str, Any]:
    return {
        "run_id": draft.run_id,
        "generation": draft.generation,
        "workspace_id": draft.workspace_id,
        "session_id": draft.session_id,
        "workflow_id": draft.workflow_id,
        "workflow_revision": draft.workflow_revision,
        "workflow_digest": draft.workflow_digest,
        "graph_id": draft.graph_id,
        "review_digest": draft.review_digest,
        "binding_set_digest": draft.binding_set_digest,
        "policy_snapshot_digest": draft.policy_snapshot_digest,
        "authority_id": draft.authority_id,
        "authority_digest": draft.authority_digest,
        "started_at": draft.started_at,
        "trace_id": draft.trace_id,
        "child_call_ids": tuple(draft.child_call_ids),
        "approval_ids": tuple(draft.approval_ids),
        "redaction_count": draft.redaction_count,
        "event_truncated": draft.event_truncated,
        "output_truncated": draft.output_truncated,
        "cancellation_acknowledged": draft.cancellation_acknowledged,
        "residue_possible": draft.residue_possible,
        "recovery_code": draft.recovery_code,
        "runtime_identity": dict(draft.runtime_identity),
        "authority_expires_at": draft.authority_expires_at,
        "bindings": tuple(dict(item) for item in draft.bindings),
    }


def _manifest_document(manifest: RunManifest) -> dict[str, Any]:
    return {**manifest.digest_material(), "manifest_digest": manifest.manifest_digest}


class RivetMcpRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def save_binding_set(self, binding_set: WorkflowBindingSet) -> None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            existing = connection.execute(
                "SELECT binding_set_digest FROM workspace_workflow_binding_sets WHERE binding_set_id=?",
                (binding_set.binding_set_id,),
            ).fetchone()
            if existing is not None:
                if existing[0] != binding_set.binding_set_digest:
                    raise ValueError("Binding set identity is immutable")
                return
            connection.execute(
                """INSERT INTO workspace_workflow_binding_sets
                (binding_set_id, workspace_id, workflow_id, workflow_revision,
                 workflow_digest, graph_id, discovery_snapshot_digest,
                 policy_snapshot_digest, binding_set_digest, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    binding_set.binding_set_id,
                    binding_set.workspace_id,
                    binding_set.workflow_id,
                    binding_set.workflow_revision,
                    binding_set.workflow_digest,
                    binding_set.graph_id,
                    binding_set.discovery_snapshot_digest,
                    binding_set.policy_snapshot_digest,
                    binding_set.binding_set_digest,
                    _epoch(binding_set.created_at),
                ),
            )
            for binding in binding_set.bindings:
                connection.execute(
                    """INSERT INTO workspace_workflow_capability_bindings
                    (binding_id, binding_set_id, node_id, node_handle,
                     qualified_tool_name, binding_digest, binding_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        binding.binding_id,
                        binding_set.binding_set_id,
                        binding.node_id,
                        binding.node_handle,
                        binding.qualified_tool_name,
                        binding.binding_digest,
                        _json(binding.canonical()),
                        _epoch(binding.created_at),
                    ),
                )

    def get_binding_set(self, binding_set_id: str) -> WorkflowBindingSet | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                "SELECT * FROM workspace_workflow_binding_sets WHERE binding_set_id=?",
                (binding_set_id,),
            ).fetchone()
            if row is None:
                return None
            binding_rows = connection.execute(
                """SELECT binding_json FROM workspace_workflow_capability_bindings
                WHERE binding_set_id=? ORDER BY node_id""",
                (binding_set_id,),
            ).fetchall()
        bindings = tuple(
            _binding_from_document(json.loads(item[0])) for item in binding_rows
        )
        return WorkflowBindingSet(
            binding_set_id=str(row["binding_set_id"]),
            workspace_id=str(row["workspace_id"]),
            workflow_id=str(row["workflow_id"]),
            workflow_revision=int(row["workflow_revision"]),
            workflow_digest=str(row["workflow_digest"]),
            graph_id=str(row["graph_id"]),
            bindings=bindings,
            discovery_snapshot_digest=str(row["discovery_snapshot_digest"]),
            policy_snapshot_digest=str(row["policy_snapshot_digest"]),
            binding_set_digest=str(row["binding_set_digest"]),
            created_at=datetime.fromtimestamp(int(row["created_at"]), tz=UTC),
        )

    def get_binding_set_by_digest(
        self, binding_set_digest: str
    ) -> WorkflowBindingSet | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                """SELECT binding_set_id FROM workspace_workflow_binding_sets
                WHERE binding_set_digest=?""",
                (binding_set_digest,),
            ).fetchone()
        return self.get_binding_set(str(row[0])) if row is not None else None

    def get_binding_by_digest(self, binding_digest: str) -> CapabilityBinding | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                """SELECT binding_json FROM workspace_workflow_capability_bindings
                WHERE binding_digest=?""",
                (binding_digest,),
            ).fetchone()
        return _binding_from_document(json.loads(row[0])) if row is not None else None

    def create_manifest_draft(self, manifest_id: str, draft: RunManifestDraft) -> None:
        document = _draft_document(draft)
        identity_digest = canonical_digest(document)
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            existing = connection.execute(
                """SELECT run_id, identity_digest
                FROM workspace_workflow_run_manifests WHERE manifest_id=?""",
                (manifest_id,),
            ).fetchone()
            if existing is not None:
                if (
                    str(existing["run_id"]) != draft.run_id
                    or str(existing["identity_digest"]) != identity_digest
                ):
                    raise ValueError("Run manifest draft identity is immutable")
                return
            connection.execute(
                """INSERT INTO workspace_workflow_run_manifests
                (manifest_id, run_id, state, identity_digest, draft_json,
                 created_at) VALUES (?, ?, 'prepared', ?, ?, ?)""",
                (
                    manifest_id,
                    draft.run_id,
                    identity_digest,
                    _json(document),
                    _epoch(draft.started_at),
                ),
            )
            connection.execute(
                """UPDATE workspace_workflow_runs SET manifest_id=?,
                review_digest=?, binding_set_digest=?, authority_digest=?, trace_id=?
                WHERE run_id=?""",
                (
                    manifest_id,
                    draft.review_digest,
                    draft.binding_set_digest,
                    draft.authority_digest,
                    draft.trace_id,
                    draft.run_id,
                ),
            )

    def set_manifest_state(self, manifest_id: str, state: str) -> None:
        if state not in {"running", "cancelling"}:
            raise ValueError("Manifest draft state is invalid")
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            result = connection.execute(
                """UPDATE workspace_workflow_run_manifests SET state=?
                WHERE manifest_id=? AND state!='finalized'""",
                (state, manifest_id),
            )
            if result.rowcount != 1:
                raise ValueError("Run manifest draft is unavailable")

    def set_manifest_cancellation(
        self, manifest_id: str, draft: RunManifestDraft
    ) -> None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            result = connection.execute(
                """UPDATE workspace_workflow_run_manifests
                SET state='cancelling', draft_json=?
                WHERE manifest_id=? AND state!='finalized'""",
                (_json(_draft_document(draft)), manifest_id),
            )
            if result.rowcount != 1:
                raise ValueError("Run manifest draft is unavailable")

    def finalize_manifest(self, manifest_id: str, manifest: RunManifest) -> None:
        document = _manifest_document(manifest)
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            result = connection.execute(
                """UPDATE workspace_workflow_run_manifests SET
                    state='finalized', manifest_json=?, manifest_digest=?,
                    finalized_at=?, terminal_state=?, reason_code=?
                WHERE manifest_id=? AND run_id=? AND state!='finalized'""",
                (
                    _json(document),
                    manifest.manifest_digest,
                    _epoch(manifest.completed_at),
                    manifest.terminal_state,
                    manifest.reason_code,
                    manifest_id,
                    manifest.run_id,
                ),
            )
            if result.rowcount != 1:
                raise ValueError("Run manifest is already finalized or unavailable")

    def get_manifest_document(self, run_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                """SELECT manifest_json FROM workspace_workflow_run_manifests
                WHERE run_id=? AND state='finalized'""",
                (run_id,),
            ).fetchone()
        return json.loads(row[0]) if row is not None and row[0] else None

    def run_evidence_documents(
        self, run_id: str
    ) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
        """Return bounded, already-sanitized child and approval evidence for a run."""

        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            child_rows = connection.execute(
                """SELECT call_json FROM workspace_workflow_child_calls
                WHERE run_id=? ORDER BY created_at, call_id LIMIT 2000""",
                (run_id,),
            ).fetchall()
            approval_rows = connection.execute(
                """SELECT approval_json FROM workspace_workflow_call_approvals
                WHERE run_id=? ORDER BY created_at, approval_id LIMIT 2000""",
                (run_id,),
            ).fetchall()
        return (
            tuple(json.loads(row[0]) for row in child_rows),
            tuple(json.loads(row[0]) for row in approval_rows),
        )

    def orphaned_manifest_ids(self) -> tuple[str, ...]:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            rows = connection.execute(
                """SELECT manifest_id FROM workspace_workflow_run_manifests
                WHERE state!='finalized' ORDER BY created_at"""
            ).fetchall()
        return tuple(str(row[0]) for row in rows)

    def orphaned_manifest_drafts(self) -> tuple[tuple[str, dict[str, Any]], ...]:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            rows = connection.execute(
                """SELECT manifest_id, draft_json
                FROM workspace_workflow_run_manifests
                WHERE state!='finalized' ORDER BY created_at"""
            ).fetchall()
        return tuple((str(row[0]), json.loads(row[1])) for row in rows)

    def finalize_orphaned_manifests(
        self, *, reason_code: str = "runner_restarted"
    ) -> int:
        """Truthfully terminalize persisted drafts without recreating authority."""

        finalized = 0
        for manifest_id, document in self.orphaned_manifest_drafts():
            draft = RunManifestDraft(
                run_id=str(document["run_id"]),
                generation=int(document["generation"]),
                workspace_id=str(document["workspace_id"]),
                session_id=str(document["session_id"]),
                workflow_id=str(document["workflow_id"]),
                workflow_revision=int(document["workflow_revision"]),
                workflow_digest=str(document["workflow_digest"]),
                graph_id=str(document["graph_id"]),
                review_digest=str(document["review_digest"]),
                binding_set_digest=str(document["binding_set_digest"]),
                policy_snapshot_digest=str(document["policy_snapshot_digest"]),
                authority_id=str(document["authority_id"]),
                authority_digest=str(document["authority_digest"]),
                started_at=_datetime(str(document["started_at"])),
                trace_id=str(document["trace_id"]),
                child_call_ids=list(document.get("child_call_ids") or ()),
                approval_ids=list(document.get("approval_ids") or ()),
                redaction_count=int(document.get("redaction_count") or 0),
                event_truncated=bool(document.get("event_truncated")),
                output_truncated=bool(document.get("output_truncated")),
                cancellation_acknowledged=document.get("cancellation_acknowledged"),
                residue_possible=bool(document.get("residue_possible")),
                recovery_code=(
                    str(document["recovery_code"])
                    if document.get("recovery_code")
                    else None
                ),
                runtime_identity=dict(document.get("runtime_identity") or {}),
                authority_expires_at=(
                    _datetime(str(document["authority_expires_at"]))
                    if document.get("authority_expires_at")
                    else None
                ),
                bindings=tuple(dict(item) for item in document.get("bindings") or ()),
            )
            manifest = draft.finalize(
                terminal_state="failed",
                completed_at=datetime.now(UTC),
                reason_code=reason_code,
            )
            self.finalize_manifest(manifest_id, manifest)
            with connect_state_db(self.db_path, ensure_parent=True) as connection:
                connection.execute(
                    """UPDATE workspace_workflow_runs
                    SET state='failed', completed_at=?, reason_code=?
                    WHERE run_id=? AND state IN ('queued', 'running', 'cancelling')""",
                    (_epoch(manifest.completed_at), reason_code, draft.run_id),
                )
            finalized += 1
        return finalized

    def append_child_call(self, record: RivetChildCallRecord) -> None:
        document = asdict(record)
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            connection.execute(
                """INSERT INTO workspace_workflow_child_calls
                (call_id, run_id, request_id, node_id, binding_digest, state,
                 child_received, call_json, created_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.call_id,
                    record.run_id,
                    record.request_id,
                    record.node_id,
                    record.binding_digest,
                    record.state,
                    int(record.child_received),
                    _json(document),
                    _epoch(record.started_at),
                    _epoch(record.completed_at) if record.completed_at else None,
                ),
            )

    def save_approval(self, approval: PendingRivetCallApproval) -> None:
        document = asdict(approval)
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            connection.execute(
                """INSERT INTO workspace_workflow_call_approvals
                (approval_id, run_id, request_id, argument_digest,
                 approval_digest, state, approval_json, created_at, expires_at,
                 decided_at, consumed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(approval_id) DO UPDATE SET
                    state=excluded.state, approval_json=excluded.approval_json,
                    decided_at=excluded.decided_at, consumed_at=excluded.consumed_at""",
                (
                    approval.approval_id,
                    approval.run_id,
                    approval.request_id,
                    approval.argument_digest,
                    approval.approval_digest,
                    str(approval.state),
                    _json(document),
                    _epoch(approval.created_at),
                    _epoch(approval.expires_at),
                    _epoch(approval.decided_at) if approval.decided_at else None,
                    _epoch(approval.consumed_at) if approval.consumed_at else None,
                ),
            )

    def approval_document(self, approval_id: str) -> dict[str, Any] | None:
        with connect_state_db(self.db_path, ensure_parent=True) as connection:
            row = connection.execute(
                "SELECT approval_json FROM workspace_workflow_call_approvals WHERE approval_id=?",
                (approval_id,),
            ).fetchone()
        return json.loads(row[0]) if row is not None else None


__all__ = ["RivetMcpRepository"]
