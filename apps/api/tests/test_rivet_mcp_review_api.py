from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from api.routers import workspace as workspace_router
from api.schemas.workspace import (
    RivetMcpBindingPreviewRequest,
    RivetMcpBindingSelectionRequest,
    WorkflowReviewRequest,
)
from core.rivet_mcp import CapabilityBinding, ProviderEvidence, WorkflowBindingSet
from data_vault import WorkflowReview
from workspace_service.rivet_capabilities import (
    RivetCapabilityProjection,
    RivetDiscoverySnapshot,
)
from workspace_service.rivet_validation import RivetMcpNodeRequirement
from workspace_service.workflow_operations import (
    WorkflowOperationRecord,
    WorkflowOperationsError,
    WorkflowMcpBindingPreview,
    WorkflowMcpCapabilityRecord,
    WorkflowMcpNodePreview,
)


def _provider(server_id: str = "alpha") -> ProviderEvidence:
    return ProviderEvidence(
        provider_kind="mcp",
        provider_id=server_id,
        capability_id=f"{server_id}__inspect",
        resource_class="small",
        evidence={
            "server_id": server_id,
            "server_revision": f"{server_id}-v1",
            "tool_name": "inspect",
            "validation_evidence_id": f"validation-{server_id[0]}",
            "workspace_grant_digest": "b" * 64,
        },
    )


def _projection() -> RivetCapabilityProjection:
    return RivetCapabilityProjection(
        workspace_id="workspace-a",
        qualified_tool_name="alpha__inspect",
        server_id="alpha",
        tool_name="inspect",
        title="Inspect",
        description="Inspect geometry",
        server_revision="alpha-v1",
        capability_digest="a" * 64,
        validation_evidence_id="validation-a",
        workspace_grant_digest="b" * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        schema_digest="c" * 64,
        annotations={"readOnlyHint": True},
        required_approvals=(),
        compatibility="compatible",
        binding_eligible=True,
        blocking_reasons=(),
        provider=_provider(),
    )


def _binding() -> CapabilityBinding:
    return CapabilityBinding.build(
        binding_id="binding-a",
        workspace_id="workspace-a",
        workflow_id="workflow-a",
        workflow_revision=2,
        workflow_digest="d" * 64,
        graph_id="graph-a",
        node_id="node-a",
        node_handle="wright:abcdefghijklmnop",
        requirement_id=None,
        qualified_tool_name="alpha__inspect",
        server_id="alpha",
        server_revision="alpha-v1",
        capability_digest="a" * 64,
        validation_evidence_id="validation-a",
        workspace_grant_digest="b" * 64,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
        risk={
            "data_classes": [],
            "effect_classes": [],
            "required_approvals": [],
            "idempotency": "idempotent",
            "annotations_untrusted": True,
        },
        units_policy={"length": "mm"},
        material_defaults={},
        argument_constraints={"type": "object"},
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )


def _preview() -> WorkflowMcpBindingPreview:
    binding = _binding()
    binding_set = WorkflowBindingSet.build(
        binding_set_id="binding-set-a",
        workspace_id="workspace-a",
        workflow_id="workflow-a",
        workflow_revision=2,
        workflow_digest="d" * 64,
        graph_id="graph-a",
        bindings=(binding,),
        discovery_snapshot_digest="e" * 64,
        policy_snapshot_digest="f" * 64,
        created_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    requirement = RivetMcpNodeRequirement(
        "graph-a", "node-a", "mcpToolCall", "alpha__inspect"
    )
    return WorkflowMcpBindingPreview(
        "workflow-a",
        "flow",
        2,
        "d" * 64,
        "graph-a",
        "e" * 64,
        "f" * 64,
        (WorkflowMcpNodePreview(requirement, "alpha__inspect", binding, ()),),
        binding_set,
        datetime(2099, 1, 1, tzinfo=UTC),
    )


def _service(operations):
    async def resolve(*_args):
        return "C:/workspace-a"

    return SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session_id: (
                {"workspace_id": "workspace-a"} if session_id == "session-a" else None
            )
        ),
        resolve_workspace_dir=resolve,
        workflow_operations=operations,
    )


@pytest.mark.asyncio
async def test_capability_and_binding_preview_contracts_are_exact_and_safe(monkeypatch):
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)
    snapshot = RivetDiscoverySnapshot(
        "workspace-a", "internal-session", (_projection(),), "e" * 64, "f" * 64
    )
    requirement = RivetMcpNodeRequirement(
        "graph-a", "node-a", "mcpToolCall", "alpha__inspect"
    )

    class Operations:
        async def mcp_capabilities(self, **kwargs):
            assert kwargs["workspace_id"] == "workspace-a"
            return WorkflowMcpCapabilityRecord(
                "workflow-a",
                "flow",
                2,
                "d" * 64,
                "graph-a",
                (requirement,),
                (),
                snapshot,
            )

        async def preview_mcp_bindings(self, **kwargs):
            assert kwargs["selections"] == {"node-a": "alpha__inspect"}
            assert "serverUrl" not in kwargs
            return _preview()

    service = _service(Operations())
    capabilities = await workspace_router.workflow_mcp_capabilities_endpoint(
        "flow", "session-a", "Main", 0, 100, object(), service
    )
    assert capabilities.capabilities[0].qualified_tool_name == "alpha__inspect"
    assert capabilities.capabilities[0].validation_evidence_id == "validation-a"
    assert "token" not in capabilities.model_dump_json().lower()
    preview = await workspace_router.workflow_mcp_binding_preview_endpoint(
        "flow",
        RivetMcpBindingPreviewRequest(
            session_id="session-a",
            expected_revision=2,
            expected_digest="d" * 64,
            graph="Main",
            selections=[
                RivetMcpBindingSelectionRequest(
                    node_id="node-a",
                    qualified_tool_name="alpha__inspect",
                    units_policy={"length": "mm"},
                )
            ],
        ),
        object(),
        service,
    )
    assert preview.ready
    assert preview.binding_set_digest == _preview().binding_set.binding_set_digest
    assert preview.bindings[0].node_handle == "wright:abcdefghijklmnop"


@pytest.mark.asyncio
async def test_review_v2_exact_digest_stale_and_cross_workspace_contract(monkeypatch):
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)
    preview = _preview()
    review = WorkflowReview(
        "workspace-a",
        "workflow-a",
        2,
        "approved",
        "engineer",
        1,
        workflow_digest="d" * 64,
        graph_id="graph-a",
        binding_set_id=preview.binding_set.binding_set_id,
        binding_set_digest=preview.binding_set.binding_set_digest,
        policy_snapshot_digest="f" * 64,
        review_digest="9" * 64,
    )

    class Operations:
        async def review(self, **kwargs):
            assert kwargs["workspace_id"] == "workspace-a"
            assert (
                kwargs["binding_set_digest"] == preview.binding_set.binding_set_digest
            )
            return WorkflowOperationRecord("workflow-a", "flow", 2, "d" * 64, review)

    response = await workspace_router.review_workflow_endpoint(
        "flow",
        WorkflowReviewRequest(
            session_id="session-a",
            state="approved",
            reviewer="engineer",
            expected_digest="d" * 64,
            graph="Main",
            binding_set_digest=preview.binding_set.binding_set_digest,
        ),
        object(),
        _service(Operations()),
    )
    assert response.review_digest == "9" * 64
    assert response.binding_set_digest == preview.binding_set.binding_set_digest

    class Stale:
        async def review(self, **_kwargs):
            raise WorkflowOperationsError("RIVET_REVIEW_STALE", "Preview changed")

    with pytest.raises(HTTPException) as stale:
        await workspace_router.review_workflow_endpoint(
            "flow",
            WorkflowReviewRequest(
                session_id="session-a",
                state="approved",
                reviewer="engineer",
                expected_digest="d" * 64,
                graph="Main",
                binding_set_digest=preview.binding_set.binding_set_digest,
            ),
            object(),
            _service(Stale()),
        )
    assert stale.value.status_code == 409
    assert stale.value.detail["code"] == "RIVET_REVIEW_STALE"

    with pytest.raises(HTTPException) as cross_workspace:
        await workspace_router.review_workflow_endpoint(
            "flow",
            WorkflowReviewRequest(
                session_id="session-b", state="approved", reviewer="engineer"
            ),
            object(),
            _service(Operations()),
        )
    assert cross_workspace.value.status_code == 404


@pytest.mark.asyncio
async def test_legacy_non_mcp_review_response_remains_compatible(monkeypatch):
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)
    legacy = WorkflowReview("workspace-a", "legacy", 1, "approved", "engineer", 1)

    class Operations:
        async def review(self, **_kwargs):
            return WorkflowOperationRecord("legacy", "legacy-flow", 1, "1" * 64, legacy)

    response = await workspace_router.review_workflow_endpoint(
        "legacy-flow",
        WorkflowReviewRequest(
            session_id="session-a", state="approved", reviewer="engineer"
        ),
        object(),
        _service(Operations()),
    )
    assert response.review_state == "approved"
    assert response.binding_set_digest is None
    assert response.review_digest is None


@pytest.mark.asyncio
async def test_two_workspace_discovery_and_review_scope_never_crosses_or_starts_child(
    monkeypatch,
):
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)
    child_receipts = 0
    requirement = RivetMcpNodeRequirement("graph-a", "node-a", "mcpToolCall", "inspect")

    class Operations:
        async def mcp_capabilities(self, **kwargs):
            workspace_id = kwargs["workspace_id"]
            projection = _projection()
            projection = replace(
                projection,
                workspace_id=workspace_id,
                qualified_tool_name=(
                    "alpha__inspect"
                    if workspace_id == "workspace-a"
                    else "beta__inspect"
                ),
                server_id="alpha" if workspace_id == "workspace-a" else "beta",
                provider=_provider(
                    "alpha" if workspace_id == "workspace-a" else "beta"
                ),
            )
            snapshot = RivetDiscoverySnapshot(
                workspace_id,
                f"internal-{workspace_id}",
                (projection,),
                "e" * 64,
                "f" * 64,
            )
            return WorkflowMcpCapabilityRecord(
                "workflow-a",
                "flow",
                2,
                "d" * 64,
                "graph-a",
                (requirement,),
                (),
                snapshot,
            )

        async def review(self, **kwargs):
            if kwargs["workspace_id"] != "workspace-a":
                raise WorkflowOperationsError(
                    "RIVET_REVIEW_STALE", "Binding belongs to another workspace"
                )
            raise AssertionError("not called in workspace A")

    async def resolve(*_args):
        return "C:/workspace"

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session_id: {
                "workspace_id": (
                    "workspace-a" if session_id == "session-a" else "workspace-b"
                )
            }
        ),
        resolve_workspace_dir=resolve,
        workflow_operations=Operations(),
    )
    workspace_a = await workspace_router.workflow_mcp_capabilities_endpoint(
        "flow", "session-a", None, 0, 100, object(), service
    )
    workspace_b = await workspace_router.workflow_mcp_capabilities_endpoint(
        "flow", "session-b", None, 0, 100, object(), service
    )
    assert [item.qualified_tool_name for item in workspace_a.capabilities] == [
        "alpha__inspect"
    ]
    assert [item.qualified_tool_name for item in workspace_b.capabilities] == [
        "beta__inspect"
    ]
    with pytest.raises(HTTPException) as crossed:
        await workspace_router.review_workflow_endpoint(
            "flow",
            WorkflowReviewRequest(
                session_id="session-b",
                state="approved",
                reviewer="engineer",
                expected_digest="d" * 64,
                graph="graph-a",
                binding_set_digest="8" * 64,
            ),
            object(),
            service,
        )
    assert crossed.value.status_code == 409
    assert child_receipts == 0
