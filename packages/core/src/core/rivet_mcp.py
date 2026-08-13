"""Neutral values for reviewed Rivet-to-MCP execution.

This module contains no gateway, process, API, or persistence behavior. It owns the
canonical identities shared by those adapters and rejects secret-bearing evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Mapping, Sequence


_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_QUALIFIED_TOOL = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}__[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
)
_NODE_HANDLE = re.compile(r"^wright:[A-Za-z0-9_-]{16,128}$")
_SECRET_KEYS = re.compile(
    r"(?i)(?:^|[_-])(token|secret|password|passwd|api[_-]?key|authorization|credential)(?:$|[_-])"
)
_URL_CREDENTIAL = re.compile(r"(?i)^[a-z][a-z0-9+.-]*://[^/\s]*@")


def _canonical(value: Any) -> Any:
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC).isoformat(timespec="microseconds")
        return normalized.replace("+00:00", "Z")
    if isinstance(value, StrEnum):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_canonical(item) for item in value)
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def reject_secret_material(value: Any, *, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            name = str(key)
            if _SECRET_KEYS.search(name):
                raise ValueError(f"secret-like field is not permitted at {path}.{name}")
            reject_secret_material(item, path=f"{path}.{name}")
    elif isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            reject_secret_material(item, path=f"{path}[{index}]")
    elif isinstance(value, str) and _URL_CREDENTIAL.search(value):
        raise ValueError(f"secret-bearing URL is not permitted at {path}")


def _require_text(value: str, label: str, *, maximum: int = 512) -> None:
    if not value or not value.strip() or len(value) > maximum:
        raise ValueError(f"{label} is invalid")


def _require_digest(value: str, label: str) -> None:
    if not _DIGEST.fullmatch(value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    artifact_id: str
    media_type: str
    sha256: str
    bytes: int
    label: str

    def __post_init__(self) -> None:
        _require_text(self.artifact_id, "Artifact identity")
        _require_text(self.media_type, "Artifact media type")
        _require_text(self.label, "Artifact label")
        _require_digest(self.sha256, "Artifact digest")
        if self.bytes < 0:
            raise ValueError("Artifact size is invalid")

    def canonical(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "media_type": self.media_type,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "label": self.label,
        }


@dataclass(frozen=True, slots=True)
class ProviderEvidence:
    """Closed, provider-neutral identity for a reviewed gateway capability."""

    provider_kind: str
    provider_id: str
    capability_id: str
    resource_class: str
    evidence: Mapping[str, Any]
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError("Provider evidence schema version is unsupported")
        if self.provider_kind not in {"mcp", "engineering_model"}:
            raise ValueError("Provider kind is invalid")
        if self.resource_class not in {"small", "medium", "large", "external"}:
            raise ValueError("Provider resource class is invalid")
        _require_text(self.provider_id, "Provider identity", maximum=128)
        _require_text(self.capability_id, "Provider capability identity", maximum=128)
        material = dict(self.evidence)
        required = (
            {
                "server_id",
                "server_revision",
                "tool_name",
                "validation_evidence_id",
                "workspace_grant_digest",
            }
            if self.provider_kind == "mcp"
            else {
                "model_id",
                "package_revision",
                "manifest_digest",
                "variant_id",
                "artifact_set_digest",
                "installation_id",
                "installation_digest",
                "adapter_id",
                "adapter_version",
                "runtime_version",
                "test_evidence_id",
                "test_material_digest",
                "workspace_binding_digest",
                "task_id",
                "input_schema_digest",
                "output_schema_digest",
                "threshold",
                "resource_digest",
            }
        )
        if set(material) != required:
            raise ValueError("Provider evidence fields are invalid")
        digest_fields = (
            {"workspace_grant_digest"}
            if self.provider_kind == "mcp"
            else {
                "manifest_digest",
                "artifact_set_digest",
                "installation_digest",
                "test_material_digest",
                "workspace_binding_digest",
                "input_schema_digest",
                "output_schema_digest",
                "resource_digest",
            }
        )
        for name in digest_fields:
            _require_digest(str(material[name]), name.replace("_", " ").title())
        if self.provider_kind == "engineering_model":
            try:
                revision = int(material["package_revision"])
            except (TypeError, ValueError) as error:
                raise ValueError("Model provider evidence is invalid") from error
            threshold_value = material["threshold"]
            try:
                threshold = None if threshold_value is None else float(threshold_value)
            except (TypeError, ValueError) as error:
                raise ValueError("Model provider evidence is invalid") from error
            if revision < 1 or (threshold is not None and not 0 < threshold < 1):
                raise ValueError("Model provider evidence is invalid")
        reject_secret_material(self.canonical())

    @property
    def provider_evidence_digest(self) -> str:
        return canonical_digest(self.canonical())

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "provider_kind": self.provider_kind,
            "provider_id": self.provider_id,
            "capability_id": self.capability_id,
            "resource_class": self.resource_class,
            "evidence": dict(self.evidence),
        }

    @classmethod
    def parse(cls, value: Mapping[str, Any]) -> "ProviderEvidence":
        return cls(
            schema_version=str(value.get("schema_version") or ""),
            provider_kind=str(value.get("provider_kind") or ""),
            provider_id=str(value.get("provider_id") or ""),
            capability_id=str(value.get("capability_id") or ""),
            resource_class=str(value.get("resource_class") or ""),
            evidence=dict(value.get("evidence") or {}),
        )


@dataclass(frozen=True, slots=True)
class CapabilityBinding:
    binding_id: str
    workspace_id: str
    workflow_id: str
    workflow_revision: int
    workflow_digest: str
    graph_id: str
    node_id: str
    node_handle: str
    requirement_id: str | None
    qualified_tool_name: str
    server_id: str
    server_revision: str
    capability_digest: str
    validation_evidence_id: str
    workspace_grant_digest: str
    input_schema: Mapping[str, Any]
    output_schema: Mapping[str, Any] | None
    schema_digest: str
    risk: Mapping[str, Any]
    units_policy: Mapping[str, Any]
    material_defaults: Mapping[str, Any]
    argument_constraints: Mapping[str, Any]
    binding_digest: str
    created_at: datetime
    provider: ProviderEvidence | None = None

    @classmethod
    def build(
        cls,
        *,
        binding_id: str,
        workspace_id: str,
        workflow_id: str,
        workflow_revision: int,
        workflow_digest: str,
        graph_id: str,
        node_id: str,
        node_handle: str,
        requirement_id: str | None,
        qualified_tool_name: str,
        server_id: str,
        server_revision: str,
        capability_digest: str,
        validation_evidence_id: str,
        workspace_grant_digest: str,
        input_schema: Mapping[str, Any],
        output_schema: Mapping[str, Any] | None,
        risk: Mapping[str, Any],
        units_policy: Mapping[str, Any],
        material_defaults: Mapping[str, Any],
        argument_constraints: Mapping[str, Any],
        created_at: datetime,
        provider: ProviderEvidence | Mapping[str, Any] | None = None,
    ) -> "CapabilityBinding":
        provider_value = (
            ProviderEvidence.parse(provider)
            if isinstance(provider, Mapping)
            else provider
        )
        schema_digest = canonical_digest(
            {"input": input_schema, "output": output_schema}
        )
        material = {
            "workspace_id": workspace_id,
            "workflow_id": workflow_id,
            "workflow_revision": workflow_revision,
            "workflow_digest": workflow_digest,
            "graph_id": graph_id,
            "node_id": node_id,
            "node_handle": node_handle,
            "requirement_id": requirement_id,
            "qualified_tool_name": qualified_tool_name,
            "server_id": server_id,
            "server_revision": server_revision,
            "capability_digest": capability_digest,
            "validation_evidence_id": validation_evidence_id,
            "workspace_grant_digest": workspace_grant_digest,
            "input_schema": input_schema,
            "output_schema": output_schema,
            "schema_digest": schema_digest,
            "risk": risk,
            "units_policy": units_policy,
            "material_defaults": material_defaults,
            "argument_constraints": argument_constraints,
        }
        if provider_value is not None:
            material["provider"] = provider_value.canonical()
        reject_secret_material(material)
        return cls(
            binding_id=binding_id,
            schema_digest=schema_digest,
            binding_digest=canonical_digest(material),
            created_at=created_at,
            provider=provider_value,
            **{
                key: value
                for key, value in material.items()
                if key not in {"schema_digest", "provider"}
            },
        )

    def __post_init__(self) -> None:
        for label, value in (
            ("Binding identity", self.binding_id),
            ("Workspace identity", self.workspace_id),
            ("Workflow identity", self.workflow_id),
            ("Graph identity", self.graph_id),
            ("Node identity", self.node_id),
            ("Server identity", self.server_id),
            ("Server revision", self.server_revision),
            ("Validation evidence identity", self.validation_evidence_id),
        ):
            _require_text(value, label)
        if self.workflow_revision < 1:
            raise ValueError("Workflow revision is invalid")
        if not _NODE_HANDLE.fullmatch(self.node_handle):
            raise ValueError("Node handle is invalid")
        if not _QUALIFIED_TOOL.fullmatch(self.qualified_tool_name):
            raise ValueError("Qualified tool name is invalid")
        for label, value in (
            ("Workflow digest", self.workflow_digest),
            ("Capability digest", self.capability_digest),
            ("Workspace grant digest", self.workspace_grant_digest),
            ("Schema digest", self.schema_digest),
            ("Binding digest", self.binding_digest),
        ):
            _require_digest(value, label)
        reject_secret_material(self.digest_material())

    def digest_material(self) -> dict[str, Any]:
        material = {
            "workspace_id": self.workspace_id,
            "workflow_id": self.workflow_id,
            "workflow_revision": self.workflow_revision,
            "workflow_digest": self.workflow_digest,
            "graph_id": self.graph_id,
            "node_id": self.node_id,
            "node_handle": self.node_handle,
            "requirement_id": self.requirement_id,
            "qualified_tool_name": self.qualified_tool_name,
            "server_id": self.server_id,
            "server_revision": self.server_revision,
            "capability_digest": self.capability_digest,
            "validation_evidence_id": self.validation_evidence_id,
            "workspace_grant_digest": self.workspace_grant_digest,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "schema_digest": self.schema_digest,
            "risk": self.risk,
            "units_policy": self.units_policy,
            "material_defaults": self.material_defaults,
            "argument_constraints": self.argument_constraints,
        }
        if self.provider is not None:
            material["provider"] = self.provider.canonical()
        return material

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": 2 if self.provider is not None else 1,
            "binding_id": self.binding_id,
            **self.digest_material(),
            "binding_digest": self.binding_digest,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class WorkflowBindingSet:
    binding_set_id: str
    workspace_id: str
    workflow_id: str
    workflow_revision: int
    workflow_digest: str
    graph_id: str
    bindings: tuple[CapabilityBinding, ...]
    discovery_snapshot_digest: str
    policy_snapshot_digest: str
    binding_set_digest: str
    created_at: datetime

    @classmethod
    def build(
        cls,
        *,
        binding_set_id: str,
        workspace_id: str,
        workflow_id: str,
        workflow_revision: int,
        workflow_digest: str,
        graph_id: str,
        bindings: Sequence[CapabilityBinding],
        discovery_snapshot_digest: str,
        policy_snapshot_digest: str,
        created_at: datetime,
    ) -> "WorkflowBindingSet":
        ordered = tuple(sorted(bindings, key=lambda item: item.node_id))
        nodes = [item.node_id for item in ordered]
        handles = [item.node_handle for item in ordered]
        if len(nodes) != len(set(nodes)):
            raise ValueError("A binding set cannot contain a duplicate node")
        if len(handles) != len(set(handles)):
            raise ValueError("A binding set cannot contain a duplicate node handle")
        for item in ordered:
            identity = (
                item.workspace_id,
                item.workflow_id,
                item.workflow_revision,
                item.workflow_digest,
                item.graph_id,
            )
            if identity != (
                workspace_id,
                workflow_id,
                workflow_revision,
                workflow_digest,
                graph_id,
            ):
                raise ValueError("Binding identity differs from its binding set")
        material = {
            "workspace_id": workspace_id,
            "workflow_id": workflow_id,
            "workflow_revision": workflow_revision,
            "workflow_digest": workflow_digest,
            "graph_id": graph_id,
            "binding_digests": [item.binding_digest for item in ordered],
            "discovery_snapshot_digest": discovery_snapshot_digest,
            "policy_snapshot_digest": policy_snapshot_digest,
        }
        return cls(
            binding_set_id=binding_set_id,
            bindings=ordered,
            binding_set_digest=canonical_digest(material),
            created_at=created_at,
            workspace_id=workspace_id,
            workflow_id=workflow_id,
            workflow_revision=workflow_revision,
            workflow_digest=workflow_digest,
            graph_id=graph_id,
            discovery_snapshot_digest=discovery_snapshot_digest,
            policy_snapshot_digest=policy_snapshot_digest,
        )


class ApprovalState(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"
    CONSUMED = "consumed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class PendingRivetCallApproval:
    approval_id: str
    run_id: str
    authority_id: str
    node_id: str
    binding_digest: str
    session_id: str
    server_id: str
    qualified_tool_name: str
    request_id: str
    argument_digest: str
    argument_summary: Mapping[str, Any]
    required_gates: tuple[str, ...]
    state: ApprovalState
    requested_by: str
    created_at: datetime
    expires_at: datetime
    approval_digest: str
    decided_by: str | None = None
    decision_reason: str | None = None
    decided_at: datetime | None = None
    consumed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class RivetChildCallRecord:
    call_id: str
    request_id: str
    run_id: str
    authority_id: str
    node_id: str
    binding_digest: str
    qualified_tool_name: str
    server_revision: str
    schema_digest: str
    validation_evidence_id: str
    argument_digest: str
    trace_id: str
    state: str
    child_received: bool
    started_at: datetime
    completed_at: datetime | None = None
    reason_code: str | None = None
    artifacts: tuple[ArtifactReference, ...] = ()
    redaction_count: int = 0


@dataclass(frozen=True, slots=True)
class RunManifest:
    run_id: str
    generation: int
    workspace_id: str
    session_id: str
    workflow_id: str
    workflow_revision: int
    workflow_digest: str
    graph_id: str
    review_digest: str
    binding_set_digest: str
    policy_snapshot_digest: str
    authority_id: str
    authority_digest: str
    started_at: datetime
    completed_at: datetime
    terminal_state: str
    reason_code: str | None
    trace_id: str
    artifacts: tuple[ArtifactReference, ...]
    child_call_ids: tuple[str, ...]
    approval_ids: tuple[str, ...]
    redaction_count: int
    event_truncated: bool
    output_truncated: bool
    cancellation_acknowledged: bool | None
    residue_possible: bool
    recovery_code: str | None
    manifest_digest: str
    runtime_identity: Mapping[str, Any] = field(default_factory=dict)
    authority_expires_at: datetime | None = None
    bindings: tuple[Mapping[str, Any], ...] = ()
    schema_version: int = 1
    child_calls: tuple[Mapping[str, Any], ...] = ()

    def digest_material(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "generation": self.generation,
            "workspace_id": self.workspace_id,
            "session_id": self.session_id,
            "workflow": {
                "workflow_id": self.workflow_id,
                "revision": self.workflow_revision,
                "digest": self.workflow_digest,
                "graph_id": self.graph_id,
            },
            "runtime": {
                "protocol_version": int(
                    self.runtime_identity.get("protocol_version", 2)
                ),
                "rivet_version": str(
                    self.runtime_identity.get("rivet_version", "unknown")
                ),
                "package_version": str(
                    self.runtime_identity.get("package_version", "unknown")
                ),
                "runner_sha256": str(
                    self.runtime_identity.get("runner_sha256", "0" * 64)
                ),
                "source_revision": str(
                    self.runtime_identity.get("source_revision", "unknown")
                ),
            },
            "review_digest": self.review_digest,
            "binding_set_digest": self.binding_set_digest,
            "policy_snapshot_digest": self.policy_snapshot_digest,
            "authority": {
                "authority_id": self.authority_id,
                "authority_digest": self.authority_digest,
                "issued_at": self.started_at,
                "expires_at": self.authority_expires_at or self.started_at,
                "revoked_at": self.completed_at,
            },
            "bindings": [dict(item) for item in self.bindings],
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "terminal_state": self.terminal_state,
            "reason_code": self.reason_code,
            "recovery_code": self.recovery_code,
            "trace_id": self.trace_id,
            "artifacts": [item.canonical() for item in self.artifacts],
            "child_call_ids": self.child_call_ids,
            **(
                {"child_calls": [dict(item) for item in self.child_calls]}
                if self.schema_version == 2
                else {}
            ),
            "approval_ids": self.approval_ids,
            "redaction_count": self.redaction_count,
            "event_truncated": self.event_truncated,
            "output_truncated": self.output_truncated,
            "cancellation": (
                {
                    "authority_revoked": True,
                    "child_acknowledged": bool(self.cancellation_acknowledged),
                    "residue_state": ("possible" if self.residue_possible else "none"),
                    "recovery_code": self.recovery_code,
                }
                if self.cancellation_acknowledged is not None
                or self.residue_possible
                or self.terminal_state == "cancelled"
                else None
            ),
        }


@dataclass(slots=True)
class RunManifestDraft:
    run_id: str
    generation: int
    workspace_id: str
    session_id: str
    workflow_id: str
    workflow_revision: int
    workflow_digest: str
    graph_id: str
    review_digest: str
    binding_set_digest: str
    policy_snapshot_digest: str
    authority_id: str
    authority_digest: str
    started_at: datetime
    trace_id: str
    child_call_ids: list[str] = field(default_factory=list)
    approval_ids: list[str] = field(default_factory=list)
    redaction_count: int = 0
    event_truncated: bool = False
    output_truncated: bool = False
    cancellation_acknowledged: bool | None = None
    residue_possible: bool = False
    recovery_code: str | None = None
    runtime_identity: Mapping[str, Any] = field(default_factory=dict)
    authority_expires_at: datetime | None = None
    bindings: tuple[Mapping[str, Any], ...] = ()
    schema_version: int = 1
    child_calls: tuple[Mapping[str, Any], ...] = ()
    _finalized: bool = field(default=False, init=False, repr=False)

    def finalize(
        self,
        *,
        terminal_state: str,
        completed_at: datetime,
        reason_code: str | None,
        artifacts: Sequence[ArtifactReference] = (),
    ) -> RunManifest:
        if self._finalized:
            raise ValueError("Run manifest draft is already finalized")
        if self.schema_version not in {1, 2}:
            raise ValueError("Run manifest schema version is invalid")
        if self.schema_version == 2 and any(
            not isinstance(item.get("provider"), Mapping) for item in self.bindings
        ):
            raise ValueError("Run manifest version 2 requires provider evidence")
        if terminal_state not in {"cancelled", "succeeded", "failed"}:
            raise ValueError("Run manifest terminal state is invalid")
        if (
            len(self.child_call_ids) > 1000
            or len(self.approval_ids) > 1000
            or len(self.bindings) > 100
            or len(artifacts) > 1000
        ):
            self.event_truncated = True
        manifest = RunManifest(
            run_id=self.run_id,
            generation=self.generation,
            workspace_id=self.workspace_id,
            session_id=self.session_id,
            workflow_id=self.workflow_id,
            workflow_revision=self.workflow_revision,
            workflow_digest=self.workflow_digest,
            graph_id=self.graph_id,
            review_digest=self.review_digest,
            binding_set_digest=self.binding_set_digest,
            policy_snapshot_digest=self.policy_snapshot_digest,
            authority_id=self.authority_id,
            authority_digest=self.authority_digest,
            started_at=self.started_at,
            completed_at=completed_at,
            terminal_state=terminal_state,
            reason_code=reason_code,
            trace_id=self.trace_id,
            artifacts=tuple(artifacts[:1000]),
            child_call_ids=tuple(self.child_call_ids[:1000]),
            approval_ids=tuple(self.approval_ids[:1000]),
            redaction_count=self.redaction_count,
            event_truncated=self.event_truncated,
            output_truncated=self.output_truncated,
            cancellation_acknowledged=self.cancellation_acknowledged,
            residue_possible=self.residue_possible,
            recovery_code=self.recovery_code,
            manifest_digest="",
            runtime_identity=dict(self.runtime_identity),
            authority_expires_at=self.authority_expires_at,
            bindings=tuple(dict(item) for item in self.bindings[:100]),
            schema_version=self.schema_version,
            child_calls=tuple(dict(item) for item in self.child_calls[:1000]),
        )
        material = manifest.digest_material()
        reject_secret_material(material)
        self._finalized = True
        return replace(manifest, manifest_digest=canonical_digest(material))


__all__ = [
    "ApprovalState",
    "ArtifactReference",
    "CapabilityBinding",
    "PendingRivetCallApproval",
    "ProviderEvidence",
    "RivetChildCallRecord",
    "RunManifest",
    "RunManifestDraft",
    "WorkflowBindingSet",
    "canonical_digest",
    "canonical_json",
    "reject_secret_material",
]
