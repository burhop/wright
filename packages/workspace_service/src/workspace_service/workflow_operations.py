"""Revision-checked workflow operations over Wright-owned workspace boundaries."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime, timedelta
from collections.abc import Mapping
from dataclasses import dataclass, replace

from core.rivet_mcp import (
    CapabilityBinding,
    PendingRivetCallApproval,
    WorkflowBindingSet,
    canonical_digest,
)
from core.workflow_runs import WorkflowRun, WorkflowRunEvent
from data_vault import (
    RivetMcpRepository,
    WorkflowReview,
    WorkflowReviewRepository,
)

from .rivet_capabilities import (
    RivetCapabilityService,
    RivetDiscoverySnapshot,
)
from .rivet_evidence import build_run_evidence
from .rivet_approvals import RivetApprovalService
from .rivet_settings import RivetMcpGatewaySettings
from .rivet_validation import (
    RivetMcpNodeRequirement,
    ValidationIssue,
    extract_rivet_mcp_requirements,
    validate_rivet_project,
)
from .workflow_runner import WorkspaceWorkflowRunner
from .workflows import WorkspaceWorkflowStore


class WorkflowOperationsError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class WorkflowOperationsSettings:
    enabled: bool = False
    history_limit: int = 100

    @classmethod
    def from_env(
        cls, env: Mapping[str, str] | None = None
    ) -> "WorkflowOperationsSettings":
        source = env or os.environ
        return cls(
            enabled=source.get("WRIGHT_RIVET_WORKFLOW_OPERATIONS_ENABLED", "0")
            .strip()
            .lower()
            in {"1", "true", "yes"},
            history_limit=max(
                1, int(source.get("WRIGHT_RIVET_WORKFLOW_HISTORY_LIMIT", "100"))
            ),
        )


@dataclass(frozen=True, slots=True)
class WorkflowOperationRecord:
    workflow_id: str
    slug: str
    revision: int
    digest: str
    review: WorkflowReview | None
    stale_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkflowMcpCapabilityRecord:
    workflow_id: str
    slug: str
    revision: int
    digest: str
    graph_id: str
    requirements: tuple[RivetMcpNodeRequirement, ...]
    issues: tuple[ValidationIssue, ...]
    snapshot: RivetDiscoverySnapshot


@dataclass(frozen=True, slots=True)
class WorkflowMcpNodePreview:
    requirement: RivetMcpNodeRequirement
    selected_tool: str | None
    binding: CapabilityBinding | None
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WorkflowMcpBindingPreview:
    workflow_id: str
    slug: str
    revision: int
    digest: str
    graph_id: str
    snapshot_digest: str
    policy_snapshot_digest: str
    nodes: tuple[WorkflowMcpNodePreview, ...]
    binding_set: WorkflowBindingSet | None
    expires_at: datetime


class WorkspaceWorkflowOperations:
    """Runs exact saved workflow revisions within the current workspace scope."""

    def __init__(
        self,
        reviews: WorkflowReviewRepository,
        runner: WorkspaceWorkflowRunner,
        *,
        settings: WorkflowOperationsSettings | None = None,
    ) -> None:
        self._reviews = reviews
        self._runner = runner
        self._settings = settings or WorkflowOperationsSettings.from_env()
        self._mcp_capabilities: RivetCapabilityService | None = None
        self._mcp_repository: RivetMcpRepository | None = None
        self._mcp_approvals: RivetApprovalService | None = None
        self._mcp_settings = RivetMcpGatewaySettings()

    def configure_mcp(
        self,
        *,
        capabilities: RivetCapabilityService,
        repository: RivetMcpRepository,
        settings: RivetMcpGatewaySettings,
        approvals: RivetApprovalService | None = None,
    ) -> None:
        self._mcp_capabilities = capabilities
        self._mcp_repository = repository
        self._mcp_settings = settings
        self._mcp_approvals = approvals

    def _mcp_enabled(self) -> tuple[RivetCapabilityService, RivetMcpRepository]:
        if (
            not self._mcp_settings.enabled
            or self._mcp_capabilities is None
            or self._mcp_repository is None
        ):
            raise WorkflowOperationsError(
                "RIVET_MCP_GATEWAY_DISABLED",
                "Rivet MCP workspace capabilities are disabled",
            )
        return self._mcp_capabilities, self._mcp_repository

    def discover_mcp_capabilities(
        self, *, workspace_id: str, session_id: str
    ) -> RivetDiscoverySnapshot:
        """Return the current workspace catalog without requiring a saved graph."""
        capabilities, _repository = self._mcp_enabled()
        return capabilities.discover(
            session_id=session_id,
            workspace_id=workspace_id,
        )

    @staticmethod
    def _selected_graph(document, graph: str | None) -> str:
        validation = validate_rivet_project(
            document.project,
            workflow_id=document.workflow_id,
            revision=document.revision,
            digest=document.digest,
            selected_graph=graph,
        )
        if validation.main_graph is None:
            raise WorkflowOperationsError(
                "RIVET_GRAPH_NOT_FOUND", "The selected Rivet graph was not found"
            )
        return validation.main_graph.id

    async def mcp_capabilities(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        slug: str,
        graph: str | None = None,
    ) -> WorkflowMcpCapabilityRecord:
        self._enabled()
        document = WorkspaceWorkflowStore(workspace_dir).read(slug)
        graph_id = self._selected_graph(document, graph)
        requirements = extract_rivet_mcp_requirements(
            document.project, selected_graph=graph_id
        )
        snapshot = self.discover_mcp_capabilities(
            session_id=session_id,
            workspace_id=workspace_id,
        )
        return WorkflowMcpCapabilityRecord(
            document.workflow_id,
            document.slug,
            document.revision,
            document.digest,
            graph_id,
            requirements.nodes,
            requirements.errors,
            snapshot,
        )

    async def preview_mcp_bindings(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        slug: str,
        expected_revision: int,
        expected_digest: str,
        graph: str | None,
        selections: Mapping[str, str],
        units_policy: Mapping[str, Mapping[str, object]] | None = None,
        material_defaults: Mapping[str, Mapping[str, object]] | None = None,
    ) -> WorkflowMcpBindingPreview:
        record = await self.mcp_capabilities(
            workspace_id=workspace_id,
            session_id=session_id,
            workspace_dir=workspace_dir,
            slug=slug,
            graph=graph,
        )
        if record.revision != expected_revision or record.digest != expected_digest:
            raise WorkflowOperationsError(
                "RIVET_WORKFLOW_REVISION_CONFLICT", "Workflow contents changed"
            )
        if record.issues:
            raise WorkflowOperationsError(
                record.issues[0].code, record.issues[0].message
            )
        capabilities, repository = self._mcp_enabled()
        node_previews: list[WorkflowMcpNodePreview] = []
        bindings: list[CapabilityBinding] = []
        tool_requirements = tuple(
            item for item in record.requirements if item.node_type == "mcpToolCall"
        )
        unknown_selections = sorted(
            set(selections) - {item.node_id for item in tool_requirements}
        )
        if unknown_selections:
            raise WorkflowOperationsError(
                "RIVET_BINDING_EXTRA", "A proposed binding does not match an MCP node"
            )
        now = datetime.now(UTC)
        for requirement in tool_requirements:
            selected = selections.get(requirement.node_id)
            candidates = (
                [
                    item
                    for item in record.snapshot.tools
                    if item.qualified_tool_name == selected
                ]
                if selected
                else [
                    item
                    for item in record.snapshot.tools
                    if item.qualified_tool_name == requirement.static_tool_name
                    or item.tool_name == requirement.static_tool_name
                ]
            )
            blockers: tuple[str, ...] = ()
            binding: CapabilityBinding | None = None
            if len(candidates) == 0:
                blockers = ("binding_missing",)
            elif len(candidates) > 1:
                blockers = ("binding_ambiguous",)
            elif not candidates[0].binding_eligible:
                blockers = candidates[0].blocking_reasons
            else:
                selected = candidates[0].qualified_tool_name
                binding = capabilities.bind(
                    snapshot=record.snapshot,
                    requirement=requirement,
                    qualified_tool_name=selected,
                    workflow_id=record.workflow_id,
                    workflow_revision=record.revision,
                    workflow_digest=record.digest,
                    units_policy=dict(
                        (units_policy or {}).get(requirement.node_id) or {}
                    ),
                    material_defaults=dict(
                        (material_defaults or {}).get(requirement.node_id) or {}
                    ),
                    created_at=now,
                )
                bindings.append(binding)
            node_previews.append(
                WorkflowMcpNodePreview(requirement, selected, binding, blockers)
            )
        binding_set: WorkflowBindingSet | None = None
        if len(bindings) == len(tool_requirements):
            temporary = WorkflowBindingSet.build(
                binding_set_id="pending-binding-set",
                workspace_id=workspace_id,
                workflow_id=record.workflow_id,
                workflow_revision=record.revision,
                workflow_digest=record.digest,
                graph_id=record.graph_id,
                bindings=bindings,
                discovery_snapshot_digest=record.snapshot.snapshot_digest,
                policy_snapshot_digest=record.snapshot.policy_snapshot_digest,
                created_at=now,
            )
            binding_set = replace(
                temporary,
                binding_set_id=f"binding-set-{temporary.binding_set_digest[:32]}",
            )
            repository.save_binding_set(binding_set)
        return WorkflowMcpBindingPreview(
            record.workflow_id,
            record.slug,
            record.revision,
            record.digest,
            record.graph_id,
            record.snapshot.snapshot_digest,
            record.snapshot.policy_snapshot_digest,
            tuple(node_previews),
            binding_set,
            now + timedelta(minutes=5),
        )

    def _enabled(self) -> None:
        if not self._settings.enabled:
            raise WorkflowOperationsError(
                "RIVET_OPERATIONS_DISABLED", "Rivet workflow operations are disabled"
            )

    async def review(
        self,
        *,
        workspace_id: str,
        workspace_dir: str,
        slug: str,
        state: str,
        reviewer: str,
        session_id: str | None = None,
        expected_digest: str | None = None,
        graph: str | None = None,
        binding_set_digest: str | None = None,
    ) -> WorkflowOperationRecord:
        self._enabled()
        if not reviewer.strip():
            raise WorkflowOperationsError(
                "RIVET_REVIEWER_REQUIRED", "A reviewer is required"
            )
        document = WorkspaceWorkflowStore(workspace_dir).read(slug)
        unscoped_requirements = extract_rivet_mcp_requirements(document.project)
        has_mcp_node = bool(unscoped_requirements.nodes)
        requirement_result = (
            extract_rivet_mcp_requirements(
                document.project,
                selected_graph=self._selected_graph(document, graph),
            )
            if has_mcp_node
            else unscoped_requirements
        )
        tool_requirements = tuple(
            item for item in requirement_result.nodes if item.node_type == "mcpToolCall"
        )
        now = int(time.time())
        if requirement_result.nodes:
            if requirement_result.errors:
                raise WorkflowOperationsError(
                    requirement_result.errors[0].code,
                    requirement_result.errors[0].message,
                )
            capabilities, repository = self._mcp_enabled()
            if expected_digest != document.digest or not binding_set_digest:
                raise WorkflowOperationsError(
                    "RIVET_REVIEW_STALE",
                    "The exact workflow and binding preview must be reviewed",
                )
            binding_set = repository.get_binding_set_by_digest(binding_set_digest)
            graph_id = self._selected_graph(document, graph)
            if (
                binding_set is None
                or binding_set.workspace_id != workspace_id
                or binding_set.workflow_id != document.workflow_id
                or binding_set.workflow_revision != document.revision
                or binding_set.workflow_digest != document.digest
                or binding_set.graph_id != graph_id
                or {item.node_id for item in binding_set.bindings}
                != {item.node_id for item in tool_requirements}
            ):
                raise WorkflowOperationsError(
                    "RIVET_REVIEW_STALE", "The binding preview is stale"
                )
            if not session_id:
                raise WorkflowOperationsError(
                    "RIVET_REVIEW_STALE", "The review session is unavailable"
                )
            current = capabilities.discover(
                session_id=session_id, workspace_id=workspace_id
            )
            stale = tuple(
                reason
                for binding in binding_set.bindings
                for reason in capabilities.stale_reasons(binding, current)
            )
            if (
                stale
                or current.policy_snapshot_digest != binding_set.policy_snapshot_digest
            ):
                raise WorkflowOperationsError(
                    "RIVET_REVIEW_STALE",
                    "The current workspace capability scope changed",
                )
            review_digest = canonical_digest(
                {
                    "workspace_id": workspace_id,
                    "workflow_id": document.workflow_id,
                    "revision": document.revision,
                    "workflow_digest": document.digest,
                    "graph_id": graph_id,
                    "binding_set_digest": binding_set.binding_set_digest,
                    "policy_snapshot_digest": binding_set.policy_snapshot_digest,
                    "state": state,
                    "reviewer": reviewer.strip(),
                    "updated_at": now,
                }
            )
            review = WorkflowReview(
                workspace_id=workspace_id,
                workflow_id=document.workflow_id,
                revision=document.revision,
                state=state,
                reviewer=reviewer.strip(),
                updated_at=now,
                workflow_digest=document.digest,
                graph_id=graph_id,
                binding_set_id=binding_set.binding_set_id,
                binding_set_digest=binding_set.binding_set_digest,
                policy_snapshot_digest=binding_set.policy_snapshot_digest,
                review_digest=review_digest,
            )
        else:
            review = WorkflowReview(
                workspace_id,
                document.workflow_id,
                document.revision,
                state,
                reviewer.strip(),
                now,
            )
        self._reviews.set(review)
        return WorkflowOperationRecord(
            document.workflow_id,
            document.slug,
            document.revision,
            document.digest,
            review,
        )

    async def detail(
        self,
        *,
        workspace_id: str,
        workspace_dir: str,
        slug: str,
        session_id: str | None = None,
    ) -> WorkflowOperationRecord:
        self._enabled()
        document = WorkspaceWorkflowStore(workspace_dir).read(slug)
        review = self._reviews.get(workspace_id, document.workflow_id)
        return WorkflowOperationRecord(
            document.workflow_id,
            document.slug,
            document.revision,
            document.digest,
            review,
            self._stale_review_reasons(
                workspace_id=workspace_id,
                session_id=session_id,
                document=document,
                review=review,
            ),
        )

    async def list(
        self,
        *,
        workspace_id: str,
        workspace_dir: str,
        session_id: str | None = None,
    ) -> tuple[WorkflowOperationRecord, ...]:
        self._enabled()
        store = WorkspaceWorkflowStore(workspace_dir)
        records: list[WorkflowOperationRecord] = []
        for slug in store.list_slugs():
            document = store.read(slug)
            review = self._reviews.get(workspace_id, document.workflow_id)
            records.append(
                WorkflowOperationRecord(
                    document.workflow_id,
                    document.slug,
                    document.revision,
                    document.digest,
                    review,
                    self._stale_review_reasons(
                        workspace_id=workspace_id,
                        session_id=session_id,
                        document=document,
                        review=review,
                    ),
                )
            )
        return tuple(records)

    def _stale_review_reasons(
        self,
        *,
        workspace_id: str,
        session_id: str | None,
        document,
        review: WorkflowReview | None,
    ) -> tuple[str, ...]:
        if review is None or review.binding_set_digest is None:
            return ()
        if (
            review.workflow_digest != document.digest
            or review.revision != document.revision
        ):
            return ("workflow_changed",)
        if (
            not self._mcp_settings.enabled
            or self._mcp_capabilities is None
            or self._mcp_repository is None
            or not session_id
        ):
            return ("mcp_gateway_unavailable",)
        binding_set = self._mcp_repository.get_binding_set_by_digest(
            review.binding_set_digest
        )
        if binding_set is None or binding_set.workspace_id != workspace_id:
            return ("binding_set_unavailable",)
        current = self._mcp_capabilities.discover(
            session_id=session_id, workspace_id=workspace_id
        )
        reasons = [
            reason
            for binding in binding_set.bindings
            for reason in self._mcp_capabilities.stale_reasons(binding, current)
        ]
        if current.policy_snapshot_digest != binding_set.policy_snapshot_digest:
            reasons.append("policy_snapshot_changed")
        return tuple(dict.fromkeys(reasons))

    async def start(
        self,
        *,
        workspace_id: str,
        session_id: str,
        workspace_dir: str,
        slug: str,
        expected_generation: int | None = None,
        expected_revision: int | None = None,
        expected_digest: str | None = None,
        expected_review_digest: str | None = None,
        binding_set_digest: str | None = None,
        graph: str | None = None,
        inputs: Mapping[str, object] | None = None,
        context: Mapping[str, object] | None = None,
        timeout_seconds: float | None = None,
        progress_callback=None,
    ) -> WorkflowRun:
        self._enabled()
        # Retained for API compatibility with older clients. Workflow-level
        # approval is no longer part of the run contract.
        _ = expected_review_digest
        document = WorkspaceWorkflowStore(workspace_dir).read(slug)
        if expected_revision is not None and document.revision != expected_revision:
            raise WorkflowOperationsError(
                "RIVET_WORKFLOW_REVISION_CONFLICT", "Workflow revision changed"
            )
        if expected_digest is not None and document.digest != expected_digest:
            raise WorkflowOperationsError(
                "RIVET_WORKFLOW_REVISION_CONFLICT", "Workflow contents changed"
            )
        requirements = extract_rivet_mcp_requirements(document.project)
        has_mcp_node = bool(requirements.nodes)
        run_authorization_digest: str | None = None
        resolved_binding_set_digest: str | None = None
        if has_mcp_node:
            if requirements.errors:
                raise WorkflowOperationsError(
                    requirements.errors[0].code,
                    requirements.errors[0].message,
                )
            capabilities, repository = self._mcp_enabled()
            graph_id = self._selected_graph(document, graph)
            binding_set = (
                repository.get_binding_set_by_digest(binding_set_digest)
                if binding_set_digest
                else None
            )
            if binding_set is None and binding_set_digest:
                raise WorkflowOperationsError(
                    "RIVET_BINDING_MISSING",
                    "The selected MCP tool connection is unavailable",
                )
            if binding_set is None:
                preview = await self.preview_mcp_bindings(
                    workspace_id=workspace_id,
                    session_id=session_id,
                    workspace_dir=workspace_dir,
                    slug=slug,
                    expected_revision=document.revision,
                    expected_digest=document.digest,
                    graph=graph_id,
                    selections={},
                )
                binding_set = preview.binding_set
                if binding_set is None:
                    blockers = sorted(
                        {blocker for node in preview.nodes for blocker in node.blockers}
                    )
                    detail = ", ".join(blockers) if blockers else "binding_missing"
                    raise WorkflowOperationsError(
                        "RIVET_BINDING_MISSING",
                        "Configure one static workspace tool for each MCP node: "
                        + detail,
                    )
            if (
                binding_set.workspace_id != workspace_id
                or binding_set.workflow_id != document.workflow_id
                or binding_set.workflow_revision != document.revision
                or binding_set.workflow_digest != document.digest
                or binding_set.graph_id != graph_id
            ):
                raise WorkflowOperationsError(
                    "RIVET_BINDING_STALE", "The selected MCP tool connection is stale"
                )
            current = capabilities.discover(
                session_id=session_id, workspace_id=workspace_id
            )
            stale = tuple(
                dict.fromkeys(
                    [
                        reason
                        for binding in binding_set.bindings
                        for reason in capabilities.stale_reasons(binding, current)
                    ]
                    + (
                        ["policy_snapshot_changed"]
                        if current.policy_snapshot_digest
                        != binding_set.policy_snapshot_digest
                        else []
                    )
                )
            )
            if stale:
                raise WorkflowOperationsError(
                    "RIVET_BINDING_STALE",
                    "The current MCP tool connection changed: " + ", ".join(stale),
                )
            resolved_binding_set_digest = binding_set.binding_set_digest
            run_authorization_digest = canonical_digest(
                {
                    "kind": "workspace-run",
                    "workspace_id": workspace_id,
                    "workflow_id": document.workflow_id,
                    "workflow_revision": document.revision,
                    "workflow_digest": document.digest,
                    "graph_id": graph_id,
                    "binding_set_digest": binding_set.binding_set_digest,
                    "policy_snapshot_digest": binding_set.policy_snapshot_digest,
                }
            )
        return await self._runner.start(
            workspace_id=workspace_id,
            session_id=session_id,
            workspace_dir=workspace_dir,
            slug=slug,
            expected_generation=expected_generation,
            expected_revision=expected_revision,
            expected_digest=expected_digest,
            expected_review_digest=run_authorization_digest,
            binding_set_digest=resolved_binding_set_digest,
            graph=graph,
            inputs=inputs,
            context=context,
            timeout_seconds=timeout_seconds,
            progress_callback=progress_callback,
        )

    def history(
        self,
        *,
        workspace_id: str,
        session_id: str,
        run_id: str,
        after_sequence: int = 0,
    ) -> tuple[WorkflowRunEvent, ...]:
        self._enabled()
        run = self._runner.get(run_id)
        if run.workspace_id != workspace_id or run.session_id != session_id:
            raise WorkflowOperationsError(
                "RIVET_RUN_NOT_FOUND", "Workflow run was not found"
            )
        return self._runner.events(run_id, after_sequence=after_sequence)[
            -self._settings.history_limit :
        ]

    def run(self, *, workspace_id: str, session_id: str, run_id: str) -> WorkflowRun:
        self._enabled()
        run = self._runner.get(run_id)
        if run.workspace_id != workspace_id or run.session_id != session_id:
            raise WorkflowOperationsError(
                "RIVET_RUN_NOT_FOUND", "Workflow run was not found"
            )
        return run

    async def cancel(
        self, *, workspace_id: str, session_id: str, run_id: str, generation: int
    ) -> WorkflowRun:
        self._enabled()
        run = self._runner.get(run_id)
        if run.workspace_id != workspace_id or run.session_id != session_id:
            raise WorkflowOperationsError(
                "RIVET_RUN_NOT_FOUND", "Workflow run was not found"
            )
        return await self._runner.cancel(run_id, generation=generation)

    def call_approvals(
        self, *, workspace_id: str, session_id: str, run_id: str
    ) -> tuple[PendingRivetCallApproval, ...]:
        self.run(workspace_id=workspace_id, session_id=session_id, run_id=run_id)
        if self._mcp_approvals is None:
            return ()
        return self._mcp_approvals.list_for_run(run_id)

    def decide_call_approval(
        self,
        *,
        workspace_id: str,
        session_id: str,
        run_id: str,
        approval_id: str,
        expected_digest: str,
        actor: str,
        approved: bool,
        reason: str | None = None,
    ) -> PendingRivetCallApproval:
        self.run(workspace_id=workspace_id, session_id=session_id, run_id=run_id)
        if self._mcp_approvals is None:
            raise WorkflowOperationsError(
                "RIVET_CALL_APPROVAL_NOT_FOUND", "Call approval was not found"
            )
        approval = self._mcp_approvals.get(approval_id)
        if approval.run_id != run_id:
            raise WorkflowOperationsError(
                "RIVET_CALL_APPROVAL_NOT_FOUND", "Call approval was not found"
            )
        return self._mcp_approvals.decide(
            approval_id,
            expected_digest=expected_digest,
            actor=actor,
            approved=approved,
            reason=reason,
        )

    def run_manifest(
        self, *, workspace_id: str, session_id: str, run_id: str
    ) -> dict | None:
        self.run(workspace_id=workspace_id, session_id=session_id, run_id=run_id)
        return self._runner.manifest(run_id)

    def run_evidence(self, *, workspace_id: str, session_id: str, run_id: str) -> dict:
        self.run(workspace_id=workspace_id, session_id=session_id, run_id=run_id)
        if self._mcp_repository is None:
            raise WorkflowOperationsError(
                "RIVET_MCP_EVIDENCE_UNAVAILABLE", "Run evidence is unavailable"
            )
        manifest = self._runner.manifest(run_id)
        if manifest is None:
            raise WorkflowOperationsError(
                "RIVET_MCP_EVIDENCE_UNAVAILABLE", "Run evidence is unavailable"
            )
        child_calls, approvals = self._mcp_repository.run_evidence_documents(run_id)
        current: dict[str, object] = {
            "workflow_digest": manifest.get("workflow_digest"),
            "review_digest": manifest.get("review_digest"),
            "binding_set_digest": manifest.get("binding_set_digest"),
            "policy_snapshot_digest": manifest.get("policy_snapshot_digest"),
        }
        runtime = self._runner.runtime_identity()
        if runtime is not None:
            current["runner_sha256"] = runtime["runner_sha256"]
        events = tuple(
            {
                "sequence": event.sequence,
                "kind": event.kind,
                "payload": dict(event.payload),
                "occurred_at": event.occurred_at,
            }
            for event in self._runner.events(run_id)
        )
        return build_run_evidence(
            manifest=manifest,
            child_calls=child_calls,
            approvals=approvals,
            events=events,
            current=current,
        )
