"""Workspace-scoped Rivet MCP discovery, exact binding, and stale comparison."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Mapping, Protocol, Sequence

from core.rivet_mcp import (
    CapabilityBinding,
    ProviderEvidence,
    canonical_digest,
    canonical_json,
)
from tool_registry.gateway_models import GatewayTool

from .rivet_validation import RivetMcpNodeRequirement


class GatewayDiscoveryPort(Protocol):
    def list_tools(self, session_id: str) -> Sequence[GatewayTool]: ...


@dataclass(frozen=True, slots=True)
class RivetCapabilityProjection:
    workspace_id: str
    qualified_tool_name: str
    server_id: str
    tool_name: str
    title: str
    description: str
    server_revision: str
    capability_digest: str
    validation_evidence_id: str
    workspace_grant_digest: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any] | None
    schema_digest: str
    annotations: Mapping[str, Any]
    required_approvals: tuple[str, ...]
    compatibility: str
    binding_eligible: bool
    blocking_reasons: tuple[str, ...]
    provider: ProviderEvidence

    def digest_material(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "qualified_tool_name": self.qualified_tool_name,
            "server_id": self.server_id,
            "tool_name": self.tool_name,
            "server_revision": self.server_revision,
            "capability_digest": self.capability_digest,
            "validation_evidence_id": self.validation_evidence_id,
            "workspace_grant_digest": self.workspace_grant_digest,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "schema_digest": self.schema_digest,
            "annotations": self.annotations,
            "required_approvals": self.required_approvals,
            "compatibility": self.compatibility,
            "binding_eligible": self.binding_eligible,
            "blocking_reasons": self.blocking_reasons,
            "provider": self.provider.canonical(),
        }


@dataclass(frozen=True, slots=True)
class RivetDiscoverySnapshot:
    workspace_id: str
    session_id: str
    tools: tuple[RivetCapabilityProjection, ...]
    snapshot_digest: str
    policy_snapshot_digest: str


class RivetCapabilityService:
    _SAFE_ANNOTATIONS = {
        "readOnlyHint",
        "destructiveHint",
        "idempotentHint",
        "openWorldHint",
    }

    def __init__(
        self,
        gateway: GatewayDiscoveryPort,
        *,
        session_resolver: Callable[[str, str], str] | None = None,
        maximum_schema_bytes: int = 64 * 1024,
    ) -> None:
        self._gateway = gateway
        self._session_resolver = session_resolver or (
            lambda session_id, workspace_id: session_id
        )
        self._maximum_schema_bytes = maximum_schema_bytes

    def discover(self, *, session_id: str, workspace_id: str) -> RivetDiscoverySnapshot:
        resolved_session_id = self._session_resolver(session_id, workspace_id)
        projections = tuple(
            sorted(
                (
                    self._project(workspace_id, tool)
                    for tool in self._gateway.list_tools(resolved_session_id)
                ),
                key=lambda item: item.qualified_tool_name,
            )
        )
        snapshot_digest = canonical_digest(
            {
                "workspace_id": workspace_id,
                "tools": [item.digest_material() for item in projections],
            }
        )
        policy_snapshot_digest = canonical_digest(
            {
                "workspace_id": workspace_id,
                "tools": [
                    {
                        "qualified_tool_name": item.qualified_tool_name,
                        "annotations": item.annotations,
                        "required_approvals": item.required_approvals,
                        "compatibility": item.compatibility,
                    }
                    for item in projections
                ],
            }
        )
        return RivetDiscoverySnapshot(
            workspace_id,
            resolved_session_id,
            projections,
            snapshot_digest,
            policy_snapshot_digest,
        )

    def _project(
        self, workspace_id: str, tool: GatewayTool
    ) -> RivetCapabilityProjection:
        input_valid = isinstance(tool.input_schema, Mapping)
        output_valid = tool.output_schema is None or isinstance(
            tool.output_schema, Mapping
        )
        raw_input_schema = dict(tool.input_schema) if input_valid else {}
        raw_output_schema = (
            dict(tool.output_schema)
            if tool.output_schema is not None and output_valid
            else None
        )
        input_too_large = (
            len(canonical_json(raw_input_schema).encode("utf-8"))
            > self._maximum_schema_bytes
        )
        output_too_large = bool(
            raw_output_schema
            and len(canonical_json(raw_output_schema).encode("utf-8"))
            > self._maximum_schema_bytes
        )
        input_schema = (
            {
                "type": "object",
                "description": "Schema omitted because it exceeds Wright's review limit.",
                "additionalProperties": False,
            }
            if input_too_large
            else raw_input_schema
        )
        output_schema = None if output_too_large else raw_output_schema
        annotations = {
            key: tool.annotations[key]
            for key in sorted(self._SAFE_ANNOTATIONS)
            if key in tool.annotations and isinstance(tool.annotations[key], bool)
        }
        schema_digest = canonical_digest(
            {"input": raw_input_schema, "output": raw_output_schema}
        )
        server_revision = str(
            tool.provenance.get("server_revision")
            or tool.provenance.get("source_revision")
            or "unknown"
        )
        capability_digest = str(
            tool.provenance.get("capability_digest")
            or canonical_digest(
                {
                    "server_id": tool.server_id,
                    "tool": tool.tool_name,
                    "server_revision": server_revision,
                }
            )
        )
        validation_evidence_id = str(
            tool.provenance.get("validation_evidence_id")
            or f"gateway-current:{capability_digest[:32]}"
        )
        workspace_grant_digest = canonical_digest(
            {
                "workspace_id": workspace_id,
                "server_id": tool.server_id,
                "qualified_tool_name": tool.name,
            }
        )
        blockers: list[str] = []
        provider_value = tool.provenance.get("provider")
        try:
            if isinstance(provider_value, Mapping):
                provider = ProviderEvidence.parse(provider_value)
                if tool.provenance.get("provider_evidence_digest") not in {
                    None,
                    provider.provider_evidence_digest,
                }:
                    raise ValueError("Provider evidence digest changed")
            else:
                provider = ProviderEvidence(
                    provider_kind="mcp",
                    provider_id=tool.server_id,
                    capability_id=tool.tool_name,
                    resource_class="small",
                    evidence={
                        "server_id": tool.server_id,
                        "server_revision": server_revision,
                        "tool_name": tool.tool_name,
                        "validation_evidence_id": validation_evidence_id,
                        "workspace_grant_digest": workspace_grant_digest,
                    },
                )
        except (TypeError, ValueError):
            provider = ProviderEvidence(
                provider_kind="mcp",
                provider_id="invalid-provider",
                capability_id="invalid-capability",
                resource_class="small",
                evidence={
                    "server_id": "invalid-provider",
                    "server_revision": "invalid",
                    "tool_name": "invalid-capability",
                    "validation_evidence_id": "invalid",
                    "workspace_grant_digest": workspace_grant_digest,
                },
            )
            blockers.append("provider_evidence_invalid")
        if "__" not in tool.name:
            blockers.append("tool_namespace_invalid")
        if not input_valid:
            blockers.append("input_schema_invalid")
        if not output_valid:
            blockers.append("output_schema_invalid")
        if server_revision == "unknown":
            blockers.append("server_revision_unknown")
        if input_too_large:
            blockers.append("input_schema_too_large")
        if output_too_large:
            blockers.append("output_schema_too_large")
        return RivetCapabilityProjection(
            workspace_id=workspace_id,
            qualified_tool_name=tool.name,
            server_id=tool.server_id,
            tool_name=tool.tool_name,
            title=(tool.title or tool.name)[:256],
            description=tool.description[:2048],
            server_revision=server_revision,
            capability_digest=capability_digest,
            validation_evidence_id=validation_evidence_id,
            workspace_grant_digest=workspace_grant_digest,
            input_schema=input_schema,
            output_schema=output_schema,
            schema_digest=schema_digest,
            annotations=annotations,
            required_approvals=tuple(sorted(tool.required_approvals)),
            compatibility="compatible" if not blockers else "blocked",
            binding_eligible=not blockers,
            blocking_reasons=tuple(blockers),
            provider=provider,
        )

    def bind(
        self,
        *,
        snapshot: RivetDiscoverySnapshot,
        requirement: RivetMcpNodeRequirement,
        qualified_tool_name: str,
        workflow_id: str,
        workflow_revision: int,
        workflow_digest: str,
        units_policy: Mapping[str, Any],
        material_defaults: Mapping[str, Any],
        created_at: datetime,
    ) -> CapabilityBinding:
        matches = [
            item
            for item in snapshot.tools
            if item.qualified_tool_name == qualified_tool_name
        ]
        if len(matches) != 1:
            raise ValueError("Capability binding is missing or ambiguous")
        capability = matches[0]
        if not capability.binding_eligible:
            raise ValueError(
                "Capability binding is blocked: "
                + ", ".join(capability.blocking_reasons)
            )
        identity = canonical_digest(
            {
                "workspace_id": snapshot.workspace_id,
                "workflow_id": workflow_id,
                "workflow_revision": workflow_revision,
                "workflow_digest": workflow_digest,
                "graph_id": requirement.graph_id,
                "node_id": requirement.node_id,
                "qualified_tool_name": qualified_tool_name,
                "schema_digest": capability.schema_digest,
                "server_revision": capability.server_revision,
            }
        )
        annotations = capability.annotations
        risk = {
            "data_classes": [],
            "effect_classes": (
                ["application_mutation"]
                if annotations.get("destructiveHint") is True
                else []
            ),
            "required_approvals": list(capability.required_approvals),
            "idempotency": (
                "idempotent" if annotations.get("idempotentHint") is True else "unknown"
            ),
            "annotations_untrusted": True,
        }
        return CapabilityBinding.build(
            binding_id=f"binding-{identity[:32]}",
            workspace_id=snapshot.workspace_id,
            workflow_id=workflow_id,
            workflow_revision=workflow_revision,
            workflow_digest=workflow_digest,
            graph_id=requirement.graph_id,
            node_id=requirement.node_id,
            node_handle=f"wright:{identity[:32]}",
            requirement_id=None,
            qualified_tool_name=capability.qualified_tool_name,
            server_id=capability.server_id,
            server_revision=capability.server_revision,
            capability_digest=capability.capability_digest,
            validation_evidence_id=capability.validation_evidence_id,
            workspace_grant_digest=capability.workspace_grant_digest,
            input_schema=capability.input_schema,
            output_schema=capability.output_schema,
            risk=risk,
            units_policy=units_policy,
            material_defaults=material_defaults,
            argument_constraints=capability.input_schema,
            created_at=created_at,
            provider=capability.provider,
        )

    def stale_reasons(
        self, binding: CapabilityBinding, current: RivetDiscoverySnapshot
    ) -> tuple[str, ...]:
        candidate = next(
            (
                item
                for item in current.tools
                if item.qualified_tool_name == binding.qualified_tool_name
            ),
            None,
        )
        if candidate is None:
            return ("workspace_grant_removed",)
        reasons: list[str] = []
        comparisons = (
            (candidate.server_id, binding.server_id, "server_changed"),
            (
                candidate.server_revision,
                binding.server_revision,
                "server_revision_changed",
            ),
            (candidate.schema_digest, binding.schema_digest, "tool_schema_changed"),
            (
                candidate.validation_evidence_id,
                binding.validation_evidence_id,
                "validation_evidence_changed",
            ),
            (
                candidate.workspace_grant_digest,
                binding.workspace_grant_digest,
                "workspace_grant_changed",
            ),
            (
                candidate.provider.provider_evidence_digest,
                (
                    binding.provider.provider_evidence_digest
                    if binding.provider is not None
                    else ""
                ),
                "provider_evidence_changed",
            ),
        )
        for actual, expected, code in comparisons:
            if actual != expected:
                reasons.append(code)
        if not candidate.binding_eligible:
            reasons.extend(candidate.blocking_reasons)
        return tuple(reasons)


__all__ = [
    "RivetCapabilityProjection",
    "RivetCapabilityService",
    "RivetDiscoverySnapshot",
]
