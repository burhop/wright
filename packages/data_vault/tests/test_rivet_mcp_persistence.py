from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from core.rivet_mcp import CapabilityBinding, RunManifestDraft, WorkflowBindingSet
from data_vault import RivetMcpRepository
from data_vault.migrations import MIGRATIONS, upgrade_database


HEX = "c" * 64


def _binding() -> CapabilityBinding:
    return CapabilityBinding.build(
        binding_id="binding-1",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest=HEX,
        graph_id="Main",
        node_id="node-1",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name="alpha__inspect",
        server_id="alpha",
        server_revision="1",
        capability_digest=HEX,
        validation_evidence_id="evidence-1",
        workspace_grant_digest=HEX,
        input_schema={"type": "object"},
        output_schema=None,
        risk={
            "data_classes": [],
            "effect_classes": [],
            "required_approvals": [],
            "idempotency": "idempotent",
            "annotations_untrusted": True,
        },
        units_policy={},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )


def _database(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', 'D:/workspace', 1, 1)"""
        )
        connection.execute(
            """INSERT INTO workspace_workflow_runs
            (run_id, workspace_id, session_id, workflow_id, revision, digest,
             graph, state, generation, started_at, output_truncated)
            VALUES ('run-1', 'workspace-1', 'session-1', 'workflow-1', 1, ?,
                    'Main', 'running', 1, 1, 0)""",
            (HEX,),
        )
        connection.commit()
    return path


def test_migration_14_is_additive_and_preserves_legacy_reviews(tmp_path):
    path = tmp_path / "legacy.db"
    upgrade_database(path, migrations=MIGRATIONS[:13])
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace-1', 'session-1', 'D:/workspace', 1, 1)"""
        )
        connection.execute(
            """INSERT INTO workspace_workflow_reviews
            (workspace_id, workflow_id, revision, state, reviewer, updated_at)
            VALUES ('workspace-1', 'workflow-1', 1, 'approved', 'reviewer', 1)"""
        )
        connection.commit()
    result = upgrade_database(path)
    assert result.applied == ({"version": 14, "name": "rivet_workspace_mcp_gateway"},)
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT state, workflow_digest FROM workspace_workflow_reviews"
        ).fetchone()
        tables = {
            item[0]
            for item in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    assert row == ("approved", None)
    assert {
        "workspace_workflow_binding_sets",
        "workspace_workflow_capability_bindings",
        "workspace_workflow_run_manifests",
        "workspace_workflow_child_calls",
        "workspace_workflow_call_approvals",
    }.issubset(tables)


def test_binding_set_and_manifest_finalize_round_trip(tmp_path):
    path = _database(tmp_path)
    repository = RivetMcpRepository(str(path))
    binding = _binding()
    binding_set = WorkflowBindingSet.build(
        binding_set_id="set-1",
        workspace_id="workspace-1",
        workflow_id="workflow-1",
        workflow_revision=1,
        workflow_digest=HEX,
        graph_id="Main",
        bindings=(binding,),
        discovery_snapshot_digest=HEX,
        policy_snapshot_digest=HEX,
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    repository.save_binding_set(binding_set)
    restored = repository.get_binding_set("set-1")
    assert restored is not None
    assert restored.binding_set_digest == binding_set.binding_set_digest
    assert restored.bindings[0].binding_digest == binding.binding_digest

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
        binding_set_digest=binding_set.binding_set_digest,
        policy_snapshot_digest=HEX,
        authority_id="authority-1",
        authority_digest=HEX,
        started_at=datetime(2026, 8, 13, tzinfo=UTC),
        trace_id="trace-1",
    )
    repository.create_manifest_draft("manifest-1", draft)
    manifest = draft.finalize(
        terminal_state="succeeded",
        completed_at=datetime(2026, 8, 13, 0, 0, 1, tzinfo=UTC),
        reason_code=None,
    )
    repository.finalize_manifest("manifest-1", manifest)
    with pytest.raises(ValueError, match="finalized"):
        repository.finalize_manifest("manifest-1", manifest)
    document = repository.get_manifest_document("run-1")
    assert document is not None
    assert document["terminal_state"] == "succeeded"
    assert document["manifest_digest"] == manifest.manifest_digest
