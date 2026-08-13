from __future__ import annotations

from datetime import UTC, datetime

import pytest

from core.rivet_mcp import (
    ArtifactReference,
    CapabilityBinding,
    RunManifestDraft,
    WorkflowBindingSet,
    canonical_digest,
)


HEX = "a" * 64


def binding(**changes) -> CapabilityBinding:
    values = {
        "binding_id": "binding-1",
        "workspace_id": "workspace-1",
        "workflow_id": "workflow-1",
        "workflow_revision": 1,
        "workflow_digest": HEX,
        "graph_id": "Main",
        "node_id": "node-1",
        "node_handle": "wright:abcdefghijklmnop",
        "requirement_id": "cad.inspect",
        "qualified_tool_name": "alpha__inspect",
        "server_id": "alpha",
        "server_revision": "1.0",
        "capability_digest": HEX,
        "validation_evidence_id": "validation-1",
        "workspace_grant_digest": HEX,
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
        "risk": {
            "data_classes": [],
            "effect_classes": [],
            "required_approvals": [],
            "idempotency": "idempotent",
            "annotations_untrusted": True,
        },
        "units_policy": {},
        "material_defaults": {},
        "argument_constraints": {"type": "object"},
        "created_at": datetime(2026, 8, 13, tzinfo=UTC),
    }
    values.update(changes)
    return CapabilityBinding.build(**values)


def test_capability_binding_digest_is_canonical_and_material():
    first = binding(input_schema={"required": [], "type": "object"})
    same = binding(input_schema={"type": "object", "required": []})
    changed = binding(server_revision="2.0")
    assert first.binding_digest == same.binding_digest
    assert first.binding_digest != changed.binding_digest
    assert first.schema_digest == same.schema_digest


def test_binding_set_is_sorted_and_rejects_duplicate_nodes_or_handles():
    one = binding()
    two = binding(
        binding_id="binding-2",
        node_id="node-2",
        node_handle="wright:qrstuvwxyzabcdef",
        qualified_tool_name="beta__inspect",
    )
    result = WorkflowBindingSet.build(
        binding_set_id="set-1",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest=HEX,
        graph_id="Main",
        bindings=(two, one),
        discovery_snapshot_digest=HEX,
        policy_snapshot_digest=HEX,
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    assert [item.node_id for item in result.bindings] == ["node-1", "node-2"]
    with pytest.raises(ValueError, match="node"):
        WorkflowBindingSet.build(
            binding_set_id="bad",
            workspace_id="workspace-1",
            workflow_id="workflow-1",
            workflow_revision=1,
            workflow_digest=HEX,
            graph_id="Main",
            bindings=(one, one),
            discovery_snapshot_digest=HEX,
            policy_snapshot_digest=HEX,
            created_at=datetime.now(UTC),
        )


def test_secret_like_fields_are_rejected_from_review_records():
    with pytest.raises(ValueError, match="secret"):
        binding(material_defaults={"api_key": "do-not-store"})


def test_manifest_finalizes_once_and_contains_no_raw_authority():
    draft = RunManifestDraft(
        run_id="run-1",
        generation=1,
        workspace_id="workspace-1",
        session_id="session-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest=HEX,
        graph_id="Main",
        review_digest=HEX,
        binding_set_digest=HEX,
        policy_snapshot_digest=HEX,
        authority_id="authority-1",
        authority_digest=HEX,
        started_at=datetime(2026, 8, 13, tzinfo=UTC),
        trace_id="trace-1",
    )
    manifest = draft.finalize(
        terminal_state="succeeded",
        completed_at=datetime(2026, 8, 13, 0, 0, 1, tzinfo=UTC),
        reason_code=None,
        artifacts=(ArtifactReference("file-1", "text/plain", HEX, 4, "result"),),
    )
    assert manifest.terminal_state == "succeeded"
    assert manifest.manifest_digest == canonical_digest(manifest.digest_material())
    with pytest.raises(ValueError, match="finalized"):
        draft.finalize(
            terminal_state="failed",
            completed_at=datetime.now(UTC),
            reason_code="late",
        )
