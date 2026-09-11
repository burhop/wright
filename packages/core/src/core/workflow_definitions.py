"""Production canonical workflow-definition and command boundaries.

This module deliberately promotes only the approved semantic contract. Layout,
proposal UI state, renderer-vendor state, and run facts remain separate records.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass
from typing import Annotated, Any, Literal, Mapping, Union

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    model_validator,
)

from .rivet_mcp import reject_secret_material
from .workflow_drafts import WorkflowDraft, WorkflowLayout, canonical_json_bytes


WORKFLOW_DEFINITION_KIND = "workflow-ir"
WORKFLOW_DEFINITION_VERSION = "2.0.0"
RECOVERY_WORKFLOW_DEFINITION_VERSION = "2.0.0-recovery.1"
WORKFLOW_COMMAND_KIND = "workflow-command-batch"
WORKFLOW_COMMAND_VERSION = "1.0.0"

Identifier = Annotated[
    str,
    StringConstraints(
        min_length=3,
        max_length=160,
        pattern=r"^[a-z0-9][a-z0-9._-]*$",
    ),
]
BoundedText = Annotated[str, StringConstraints(min_length=1, max_length=1000)]
SemanticSha256 = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
SchemaSha256 = Annotated[str, StringConstraints(pattern=r"^sha256:[a-f0-9]{64}$")]


def _unique(value: tuple[str, ...]) -> tuple[str, ...]:
    if len(value) != len(set(value)):
        raise ValueError("WFR-IDENTITY-REPEATED: identity list contains duplicates")
    return value


IdentifierTuple = Annotated[
    tuple[Identifier, ...], Field(max_length=4000), AfterValidator(_unique)
]


class _ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class WorkflowDefinitionMetadata(_ClosedModel):
    title: BoundedText
    purpose: BoundedText
    engineering_domain: Identifier
    authorship: Literal["human", "human_with_ai_proposal"]


class WorkflowPhase(_ClosedModel):
    id: Identifier
    name: BoundedText
    purpose: BoundedText
    order: Annotated[int, Field(ge=0)]
    block_ids: IdentifierTuple


class WorkflowDefinitionBlock(_ClosedModel):
    id: Identifier
    kind: Literal["work", "decision", "approval", "component"]
    title: BoundedText
    purpose: BoundedText
    phase_id: Identifier | None
    execution_kind: Literal["deterministic", "ai_capable", "human"]
    instructions: Annotated[str, StringConstraints(max_length=4000)]
    configuration: Annotated[dict[str, str | int | float | bool], Field(max_length=128)]
    input_port_ids: IdentifierTuple
    output_port_ids: IdentifierTuple
    binding_id: Identifier | None
    component_ref: WorkflowComponentReference | None


class WorkflowComponentReference(_ClosedModel):
    component_id: Identifier
    version_range: Annotated[str, StringConstraints(min_length=1, max_length=80)]


WorkflowDefinitionBlock.model_rebuild()


class WorkflowDefinitionPort(_ClosedModel):
    id: Identifier
    owner_block_id: Identifier
    direction: Literal["input", "output"]
    name: BoundedText
    type_id: Identifier
    required: bool
    cardinality: Literal["one", "optional", "many"]
    artifact_contract_id: Identifier | None
    description: Annotated[str, StringConstraints(max_length=1000)]


class WorkflowDefinitionRelationship(_ClosedModel):
    id: Identifier
    kind: Literal["data", "control", "decision", "feedback"]
    source_id: Identifier
    target_id: Identifier
    label: Annotated[str, StringConstraints(max_length=500)]
    condition: Annotated[str | None, StringConstraints(max_length=1000)]


class WorkflowArtifactContract(_ClosedModel):
    id: Identifier
    name: BoundedText
    type_id: Identifier
    media_type: Annotated[str, StringConstraints(min_length=1, max_length=160)]
    description: BoundedText
    producer_block_id: Identifier | None
    required_for_block_ids: IdentifierTuple
    preview_policy: Literal["inline", "metadata", "none"]
    allowed_actions: Annotated[
        tuple[Literal["inspect", "preview", "open", "download", "replace"], ...],
        Field(max_length=5),
        AfterValidator(_unique),
    ]


class WorkflowBindingMap(_ClosedModel):
    semantic_source: Identifier
    implementation_target: Annotated[
        str, StringConstraints(min_length=1, max_length=240)
    ]


class WorkflowBinding(_ClosedModel):
    id: Identifier
    kind: Literal["internal", "mcp_tool", "human"]
    provider_id: Annotated[str | None, StringConstraints(max_length=160)]
    server_id: Annotated[str | None, StringConstraints(max_length=160)]
    tool_id: Annotated[str | None, StringConstraints(max_length=160)]
    schema_digest: SchemaSha256 | None
    argument_map: Annotated[tuple[WorkflowBindingMap, ...], Field(max_length=4000)]
    result_map: Annotated[tuple[WorkflowBindingMap, ...], Field(max_length=4000)]
    approval_policy: Literal["none", "review_before_run", "explicit_external_write"]
    capability_name: BoundedText


class WorkflowComponentInternalAddress(_ClosedModel):
    semantic_id: Identifier
    concept_kind: Literal[
        "block", "port", "relationship", "artifact_contract", "binding", "component"
    ]
    relative_path: Annotated[
        str,
        StringConstraints(
            min_length=3,
            max_length=320,
            pattern=r"^[a-z0-9][a-z0-9._/-]*$",
        ),
    ]


class WorkflowComponent(_ClosedModel):
    id: Identifier
    version: Annotated[str, StringConstraints(min_length=1, max_length=80)]
    title: BoundedText
    input_port_ids: IdentifierTuple
    output_port_ids: IdentifierTuple
    internal_definition_digest: SchemaSha256
    internal_addresses: Annotated[
        tuple[WorkflowComponentInternalAddress, ...],
        Field(min_length=1, max_length=4000),
    ]


class WorkflowDefinition(_ClosedModel):
    document_kind: Literal["workflow-ir"]
    schema_version: Literal["2.0.0"]
    workflow_id: Identifier
    revision: Annotated[int, Field(ge=1)]
    parent_revision: Annotated[int | None, Field(ge=1)]
    semantic_sha256: SemanticSha256 | None = None
    metadata: WorkflowDefinitionMetadata
    phases: Annotated[tuple[WorkflowPhase, ...], Field(max_length=64)]
    blocks: Annotated[
        tuple[WorkflowDefinitionBlock, ...], Field(min_length=1, max_length=1000)
    ]
    ports: Annotated[tuple[WorkflowDefinitionPort, ...], Field(max_length=4000)]
    relationships: Annotated[
        tuple[WorkflowDefinitionRelationship, ...], Field(max_length=4000)
    ]
    artifact_contracts: Annotated[
        tuple[WorkflowArtifactContract, ...], Field(max_length=2000)
    ]
    bindings: Annotated[tuple[WorkflowBinding, ...], Field(max_length=1000)]
    components: Annotated[tuple[WorkflowComponent, ...], Field(max_length=256)]

    @model_validator(mode="after")
    def validate_definition(self) -> "WorkflowDefinition":
        _validate_definition(self)
        if self.semantic_sha256 is not None and (
            canonical_definition_sha256(self) != self.semantic_sha256
        ):
            raise ValueError(
                "WFR-DEFINITION-DIGEST-MISMATCH: semantic_sha256 does not match canonical definition bytes"
            )
        return self


@dataclass(frozen=True, slots=True)
class WorkflowDiagnostic:
    code: str
    explanation: str
    correction: str
    semantic_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkflowDecodeResult:
    definition: WorkflowDefinition | None
    diagnostics: tuple[WorkflowDiagnostic, ...]
    original: bytes


class SetBlockTitle(_ClosedModel):
    kind: Literal["set_block_title"]
    block_id: Identifier
    title: BoundedText


class SetBlockConfiguration(_ClosedModel):
    kind: Literal["set_block_configuration"]
    block_id: Identifier
    key: Identifier
    value: str | int | float | bool


class SetPortContract(_ClosedModel):
    kind: Literal["set_port_contract"]
    port_id: Identifier
    required: bool
    cardinality: Literal["one", "optional", "many"]


class SetBindingTool(_ClosedModel):
    kind: Literal["set_binding_tool"]
    binding_id: Identifier
    tool_id: Identifier | None


class SetRelationshipCondition(_ClosedModel):
    kind: Literal["set_relationship_condition"]
    relationship_id: Identifier
    condition: Annotated[str | None, StringConstraints(max_length=1000)]


class ConnectRelationship(_ClosedModel):
    kind: Literal["connect"]
    relationship: WorkflowDefinitionRelationship


class DisconnectRelationship(_ClosedModel):
    kind: Literal["disconnect"]
    relationship_id: Identifier


WorkflowCommand = Annotated[
    Union[
        SetBlockTitle,
        SetBlockConfiguration,
        SetPortContract,
        SetBindingTool,
        SetRelationshipCondition,
        ConnectRelationship,
        DisconnectRelationship,
    ],
    Field(discriminator="kind"),
]


class WorkflowCommandBatch(_ClosedModel):
    document_kind: Literal["workflow-command-batch"]
    schema_version: Literal["1.0.0"]
    base_revision: Annotated[int, Field(ge=1)]
    origin: Literal["graph", "form", "text", "ai_proposal"]
    commands: Annotated[
        tuple[WorkflowCommand, ...], Field(min_length=1, max_length=1000)
    ]


@dataclass(frozen=True, slots=True)
class WorkflowApplyResult:
    ok: bool
    candidate: WorkflowDefinition | None
    diagnostics: tuple[WorkflowDiagnostic, ...]
    semantic_diff: tuple[dict[str, Any], ...]


class WorkflowProjectionPort(_ClosedModel):
    semantic_id: Identifier
    direction: Literal["input", "output"]
    name: str
    type_id: Identifier
    required: bool
    cardinality: Literal["one", "optional", "many"]
    artifact_contract_id: Identifier | None


class WorkflowProjectionNode(_ClosedModel):
    semantic_id: Identifier
    title: str
    kind: Literal["work", "decision", "approval", "component"]
    phase_id: Identifier | None
    input_ports: tuple[WorkflowProjectionPort, ...]
    output_ports: tuple[WorkflowProjectionPort, ...]


class WorkflowProjectionEdge(_ClosedModel):
    semantic_id: Identifier
    kind: Literal["data", "control", "decision", "feedback"]
    source_id: Identifier
    target_id: Identifier
    label: str
    condition: str | None


class WorkflowDefinitionProjection(_ClosedModel):
    workflow_id: Identifier
    revision: int
    semantic_sha256: SemanticSha256
    nodes: tuple[WorkflowProjectionNode, ...]
    edges: tuple[WorkflowProjectionEdge, ...]


@dataclass(frozen=True, slots=True)
class WorkflowDraftPromotion:
    definition: WorkflowDefinition
    legacy_layout: WorkflowLayout
    source_envelope: bytes
    source_envelope_sha256: str
    target_definition_sha256: str


@dataclass(frozen=True, slots=True)
class WorkflowRecoveryPromotion:
    definition: WorkflowDefinition
    source_envelope: bytes
    source_envelope_sha256: str
    source_definition_sha256: str
    target_definition_sha256: str


def canonical_definition_bytes(
    definition: WorkflowDefinition | Mapping[str, Any],
) -> bytes:
    value = (
        definition.model_dump(mode="json")
        if isinstance(definition, WorkflowDefinition)
        else copy.deepcopy(dict(definition))
    )
    value.pop("semantic_sha256", None)
    for collection in (
        "blocks",
        "ports",
        "relationships",
        "artifact_contracts",
        "bindings",
        "components",
    ):
        rows = value.get(collection)
        if isinstance(rows, list):
            value[collection] = sorted(rows, key=lambda row: str(row["id"]))
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_definition_sha256(
    definition: WorkflowDefinition | Mapping[str, Any],
) -> str:
    return hashlib.sha256(canonical_definition_bytes(definition)).hexdigest()


def definition_envelope_bytes(definition: WorkflowDefinition) -> bytes:
    return json.dumps(
        definition.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _all_finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, Mapping):
        return all(_all_finite(item) for item in value.values())
    if isinstance(value, (tuple, list)):
        return all(_all_finite(item) for item in value)
    return True


def _validate_definition(definition: WorkflowDefinition) -> None:
    reject_secret_material(definition.model_dump(mode="python"))
    collections: dict[str, tuple[Any, ...]] = {
        "phases": definition.phases,
        "blocks": definition.blocks,
        "ports": definition.ports,
        "relationships": definition.relationships,
        "artifact_contracts": definition.artifact_contracts,
        "bindings": definition.bindings,
        "components": definition.components,
    }
    owners: dict[str, str] = {}
    for collection, rows in collections.items():
        for row in rows:
            if row.id in owners:
                raise ValueError(
                    f"WFR-IDENTITY-DUPLICATE: {row.id} appears in {owners[row.id]} and {collection}"
                )
            owners[row.id] = collection
    phases = {item.id: item for item in definition.phases}
    blocks = {item.id: item for item in definition.blocks}
    ports = {item.id: item for item in definition.ports}
    artifacts = {item.id: item for item in definition.artifact_contracts}
    bindings = {item.id: item for item in definition.bindings}
    components = {item.id: item for item in definition.components}
    if sorted(item.order for item in definition.phases) != list(
        range(len(definition.phases))
    ):
        raise ValueError("WFR-PHASE-ORDER: phases must use contiguous unique order")
    for phase in definition.phases:
        for block_id in phase.block_ids:
            if block_id not in blocks or blocks[block_id].phase_id != phase.id:
                raise ValueError(
                    f"WFR-PHASE-BLOCK-RECIPROCITY: {phase.id} and {block_id} disagree"
                )
    for block in definition.blocks:
        if block.phase_id is not None and (
            block.phase_id not in phases
            or block.id not in phases[block.phase_id].block_ids
        ):
            raise ValueError(
                f"WFR-BLOCK-PHASE-RECIPROCITY: {block.id} has invalid phase"
            )
        for direction, port_ids in (
            ("input", block.input_port_ids),
            ("output", block.output_port_ids),
        ):
            for port_id in port_ids:
                port = ports.get(port_id)
                if (
                    port is None
                    or port.owner_block_id != block.id
                    or port.direction != direction
                ):
                    raise ValueError(
                        f"WFR-BLOCK-PORT-RECIPROCITY: {block.id} and {port_id} disagree"
                    )
        if block.binding_id is not None and block.binding_id not in bindings:
            raise ValueError(f"WFR-BLOCK-BINDING: {block.binding_id} does not exist")
        if block.component_ref is not None and (
            block.component_ref.component_id not in components
        ):
            raise ValueError(
                f"WFR-BLOCK-COMPONENT: {block.component_ref.component_id} does not exist"
            )
    for port in definition.ports:
        owner = blocks.get(port.owner_block_id)
        expected = (
            owner.input_port_ids
            if owner is not None and port.direction == "input"
            else owner.output_port_ids
            if owner is not None
            else ()
        )
        if owner is None or port.id not in expected:
            raise ValueError(f"WFR-PORT-BLOCK-RECIPROCITY: {port.id} has invalid owner")
        if port.artifact_contract_id is not None and (
            port.artifact_contract_id not in artifacts
        ):
            raise ValueError(
                f"WFR-PORT-ARTIFACT: {port.artifact_contract_id} does not exist"
            )
    incoming: dict[str, int] = {}
    endpoints: set[tuple[str, str]] = set()
    forward: dict[str, set[str]] = {identity: set() for identity in blocks}
    for relationship in definition.relationships:
        endpoint = (relationship.source_id, relationship.target_id)
        if endpoint in endpoints:
            raise ValueError(
                f"WFR-RELATIONSHIP-ENDPOINT-DUPLICATE: {relationship.id} repeats endpoints"
            )
        endpoints.add(endpoint)
        if relationship.kind == "data":
            source = ports.get(relationship.source_id)
            target = ports.get(relationship.target_id)
            if (
                source is None
                or target is None
                or source.direction != "output"
                or target.direction != "input"
            ):
                raise ValueError(
                    f"WFR-RELATIONSHIP-DIRECTION: {relationship.id} must connect output to input"
                )
            if source.type_id != target.type_id:
                raise ValueError(
                    f"WFR-RELATIONSHIP-TYPE: {relationship.id} connects incompatible types"
                )
            incoming[target.id] = incoming.get(target.id, 0) + 1
            if target.cardinality != "many" and incoming[target.id] > 1:
                raise ValueError(
                    f"WFR-RELATIONSHIP-CARDINALITY: {target.id} accepts only one source"
                )
            forward[source.owner_block_id].add(target.owner_block_id)
        else:
            if (
                relationship.source_id not in blocks
                or relationship.target_id not in blocks
            ):
                raise ValueError(
                    f"WFR-RELATIONSHIP-ENDPOINT: {relationship.id} must reference blocks"
                )
            if relationship.kind != "feedback":
                forward[relationship.source_id].add(relationship.target_id)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(block_id: str) -> None:
        if block_id in visiting:
            raise ValueError(
                "WFR-RELATIONSHIP-CYCLE: only feedback may create a back edge"
            )
        if block_id in visited:
            return
        visiting.add(block_id)
        for target_id in forward[block_id]:
            visit(target_id)
        visiting.remove(block_id)
        visited.add(block_id)

    for block_id in blocks:
        visit(block_id)
    for artifact in definition.artifact_contracts:
        if (
            artifact.producer_block_id is not None
            and artifact.producer_block_id not in blocks
        ):
            raise ValueError(
                f"WFR-ARTIFACT-PRODUCER: {artifact.producer_block_id} does not exist"
            )
        if any(block_id not in blocks for block_id in artifact.required_for_block_ids):
            raise ValueError(
                f"WFR-ARTIFACT-CONSUMER: {artifact.id} has an unknown consumer"
            )
    semantic_sources = set(owners)
    for binding in definition.bindings:
        if binding.kind == "mcp_tool" and (
            binding.provider_id is None
            or binding.server_id is None
            or binding.tool_id is None
            or binding.schema_digest is None
        ):
            raise ValueError(
                f"WFR-BINDING-IDENTITY: {binding.id} lacks exact MCP identity"
            )
        for entry in (*binding.argument_map, *binding.result_map):
            if entry.semantic_source not in semantic_sources:
                raise ValueError(
                    f"WFR-BINDING-MAP-SOURCE: {entry.semantic_source} does not exist"
                )
    roots = {
        "block": "blocks/",
        "port": "ports/",
        "relationship": "relationships/",
        "artifact_contract": "artifact-contracts/",
        "binding": "bindings/",
        "component": "components/",
    }
    for component in definition.components:
        semantic_ids: set[str] = set()
        paths: set[str] = set()
        for address in component.internal_addresses:
            if not address.semantic_id.startswith(f"{component.id}."):
                raise ValueError(
                    f"WFR-COMPONENT-ADDRESS-SCOPE: {address.semantic_id} is outside {component.id}"
                )
            parts = address.relative_path.split("/")
            if not address.relative_path.startswith(roots[address.concept_kind]) or any(
                part in {".", ".."} for part in parts
            ):
                raise ValueError(
                    f"WFR-COMPONENT-ADDRESS-PATH: {address.relative_path} is invalid"
                )
            if address.semantic_id in semantic_ids or address.relative_path in paths:
                raise ValueError(
                    f"WFR-COMPONENT-ADDRESS-DUPLICATE: {component.id} repeats an address"
                )
            semantic_ids.add(address.semantic_id)
            paths.add(address.relative_path)
    if not _all_finite(definition.model_dump(mode="python")):
        raise ValueError(
            "WFR-NUMBER-NONFINITE: definition contains a non-finite number"
        )


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key}")
        result[key] = value
    return result


def decode_workflow_definition(original: bytes) -> WorkflowDecodeResult:
    try:
        value = json.loads(
            original,
            object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite number {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return WorkflowDecodeResult(
            None,
            (
                WorkflowDiagnostic(
                    "WFR-DEFINITION-DECODE",
                    "The workflow definition is not strict UTF-8 JSON.",
                    "Restore the original supported definition bytes.",
                ),
            ),
            original,
        )
    if (
        not isinstance(value, dict)
        or value.get("document_kind") != WORKFLOW_DEFINITION_KIND
    ):
        code = "WFR-DEFINITION-KIND-UNSUPPORTED"
    elif value.get("schema_version") != WORKFLOW_DEFINITION_VERSION:
        code = "WFR-DEFINITION-VERSION-UNSUPPORTED"
    else:
        try:
            return WorkflowDecodeResult(
                WorkflowDefinition.model_validate(value), (), original
            )
        except ValidationError as error:
            return WorkflowDecodeResult(
                None, _diagnostics_from_validation(error), original
            )
    return WorkflowDecodeResult(
        None,
        (
            WorkflowDiagnostic(
                code,
                "The definition kind or version is not supported by this reader.",
                "Open it with an explicitly compatible reader; do not rewrite it.",
            ),
        ),
        original,
    )


def promote_recovery_workflow_definition(original: bytes) -> WorkflowRecoveryPromotion:
    """Promote the exact approved recovery wire into the stable v2 boundary."""

    try:
        value = json.loads(
            original,
            object_pairs_hook=_strict_object,
            parse_constant=lambda item: (_ for _ in ()).throw(
                ValueError(f"non-finite number {item}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError("Recovery workflow definition is not strict JSON") from error
    if (
        not isinstance(value, dict)
        or value.get("document_kind") != WORKFLOW_DEFINITION_KIND
    ):
        raise ValueError("Recovery workflow definition kind is unsupported")
    if value.get("schema_version") != RECOVERY_WORKFLOW_DEFINITION_VERSION:
        raise ValueError("Recovery workflow definition version is unsupported")
    source_definition_sha256 = canonical_definition_sha256(value)
    declared_source_digest = value.get("semantic_sha256")
    if (
        declared_source_digest is not None
        and declared_source_digest != source_definition_sha256
    ):
        raise ValueError(
            "Recovery workflow definition digest does not match its content"
        )
    value["schema_version"] = WORKFLOW_DEFINITION_VERSION
    value["semantic_sha256"] = None
    value["semantic_sha256"] = canonical_definition_sha256(value)
    definition = WorkflowDefinition.model_validate(value)
    return WorkflowRecoveryPromotion(
        definition=definition,
        source_envelope=original,
        source_envelope_sha256=hashlib.sha256(original).hexdigest(),
        source_definition_sha256=source_definition_sha256,
        target_definition_sha256=definition.semantic_sha256,
    )


def rollback_recovery_workflow_definition(
    promotion: WorkflowRecoveryPromotion, definition: WorkflowDefinition
) -> bytes:
    """Return exact recovery bytes only while the promoted target is unchanged."""

    if canonical_definition_sha256(definition) != promotion.target_definition_sha256:
        raise ValueError(
            "Workflow promotion target digest changed; exact recovery rollback is unavailable"
        )
    if hashlib.sha256(promotion.source_envelope).hexdigest() != (
        promotion.source_envelope_sha256
    ):
        raise ValueError("Workflow promotion source envelope digest changed")
    return promotion.source_envelope


def _diagnostics_from_validation(
    error: ValidationError,
) -> tuple[WorkflowDiagnostic, ...]:
    diagnostics: list[WorkflowDiagnostic] = []
    for item in error.errors(include_url=False):
        message = str(item["msg"])
        marker = message.find("WFR-")
        code = (
            message[marker:].split(":", 1)[0]
            if marker >= 0
            else "WFR-DEFINITION-INVALID"
        )
        diagnostics.append(
            WorkflowDiagnostic(
                code,
                message,
                "Correct the complete candidate and retry the atomic batch.",
            )
        )
    return tuple(diagnostics)


def _entity(payload: dict[str, Any], collection: str, identity: str) -> dict[str, Any]:
    for row in payload[collection]:
        if row["id"] == identity:
            return row
    raise KeyError(identity)


def apply_workflow_commands(
    current: WorkflowDefinition, batch: WorkflowCommandBatch
) -> WorkflowApplyResult:
    if batch.base_revision != current.revision:
        return WorkflowApplyResult(
            False,
            None,
            (
                WorkflowDiagnostic(
                    "WFR-COMMAND-STALE-BASE",
                    "The command base revision is no longer current.",
                    "Regenerate the command batch from the current revision.",
                ),
            ),
            (),
        )
    payload = copy.deepcopy(current.model_dump(mode="json"))
    payload["semantic_sha256"] = None
    try:
        for command in batch.commands:
            if isinstance(command, SetBlockTitle):
                _entity(payload, "blocks", command.block_id)["title"] = command.title
            elif isinstance(command, SetBlockConfiguration):
                _entity(payload, "blocks", command.block_id)["configuration"][
                    command.key
                ] = command.value
            elif isinstance(command, SetPortContract):
                port = _entity(payload, "ports", command.port_id)
                port["required"] = command.required
                port["cardinality"] = command.cardinality
            elif isinstance(command, SetBindingTool):
                _entity(payload, "bindings", command.binding_id)["tool_id"] = (
                    command.tool_id
                )
            elif isinstance(command, SetRelationshipCondition):
                _entity(payload, "relationships", command.relationship_id)[
                    "condition"
                ] = command.condition
            elif isinstance(command, ConnectRelationship):
                payload["relationships"].append(
                    command.relationship.model_dump(mode="json")
                )
            elif isinstance(command, DisconnectRelationship):
                before = len(payload["relationships"])
                payload["relationships"] = [
                    row
                    for row in payload["relationships"]
                    if row["id"] != command.relationship_id
                ]
                if len(payload["relationships"]) == before:
                    raise KeyError(command.relationship_id)
        candidate = WorkflowDefinition.model_validate(payload)
    except KeyError as error:
        return WorkflowApplyResult(
            False,
            None,
            (
                WorkflowDiagnostic(
                    "WFR-COMMAND-TARGET-MISSING",
                    f"Command target {error.args[0]} does not exist.",
                    "Regenerate the command from the current definition.",
                ),
            ),
            (),
        )
    except ValidationError as error:
        return WorkflowApplyResult(False, None, _diagnostics_from_validation(error), ())
    return WorkflowApplyResult(
        True,
        candidate,
        (),
        _semantic_diff(
            current.model_dump(mode="json"), candidate.model_dump(mode="json")
        ),
    )


def accept_workflow_candidate(
    current: WorkflowDefinition, candidate: WorkflowDefinition
) -> WorkflowDefinition:
    if (
        candidate.workflow_id != current.workflow_id
        or candidate.revision != current.revision
    ):
        raise ValueError("WFR-COMMAND-STALE-BASE: candidate subject is not current")
    payload = candidate.model_dump(mode="json")
    payload["revision"] = current.revision + 1
    payload["parent_revision"] = current.revision
    payload["semantic_sha256"] = None
    digest = canonical_definition_sha256(payload)
    payload["semantic_sha256"] = digest
    return WorkflowDefinition.model_validate(payload)


def _semantic_diff(
    before: Any, after: Any, path: str = ""
) -> tuple[dict[str, Any], ...]:
    changes: list[dict[str, Any]] = []
    if type(before) is not type(after):
        changes.append(
            {"kind": "changed", "path": path or "/", "before": before, "after": after}
        )
    elif isinstance(before, dict):
        for key in sorted(set(before) | set(after)):
            child = f"{path}/{key}"
            if key not in before:
                changes.append({"kind": "added", "path": child, "after": after[key]})
            elif key not in after:
                changes.append(
                    {"kind": "removed", "path": child, "before": before[key]}
                )
            else:
                changes.extend(_semantic_diff(before[key], after[key], child))
    elif isinstance(before, list):
        if before != after:
            changes.append(
                {
                    "kind": "changed",
                    "path": path or "/",
                    "before": before,
                    "after": after,
                }
            )
    elif before != after:
        changes.append(
            {"kind": "changed", "path": path or "/", "before": before, "after": after}
        )
    return tuple(changes)


def project_workflow_definition(
    definition: WorkflowDefinition,
) -> WorkflowDefinitionProjection:
    ports = {item.id: item for item in definition.ports}
    nodes = tuple(
        WorkflowProjectionNode(
            semantic_id=block.id,
            title=block.title,
            kind=block.kind,
            phase_id=block.phase_id,
            input_ports=tuple(
                WorkflowProjectionPort(
                    semantic_id=ports[identity].id,
                    direction=ports[identity].direction,
                    name=ports[identity].name,
                    type_id=ports[identity].type_id,
                    required=ports[identity].required,
                    cardinality=ports[identity].cardinality,
                    artifact_contract_id=ports[identity].artifact_contract_id,
                )
                for identity in block.input_port_ids
            ),
            output_ports=tuple(
                WorkflowProjectionPort(
                    semantic_id=ports[identity].id,
                    direction=ports[identity].direction,
                    name=ports[identity].name,
                    type_id=ports[identity].type_id,
                    required=ports[identity].required,
                    cardinality=ports[identity].cardinality,
                    artifact_contract_id=ports[identity].artifact_contract_id,
                )
                for identity in block.output_port_ids
            ),
        )
        for block in sorted(definition.blocks, key=lambda item: item.id)
    )
    edges = tuple(
        WorkflowProjectionEdge(
            semantic_id=item.id,
            kind=item.kind,
            source_id=item.source_id,
            target_id=item.target_id,
            label=item.label,
            condition=item.condition,
        )
        for item in sorted(definition.relationships, key=lambda item: item.id)
    )
    return WorkflowDefinitionProjection(
        workflow_id=definition.workflow_id,
        revision=definition.revision,
        semantic_sha256=definition.semantic_sha256
        or canonical_definition_sha256(definition),
        nodes=nodes,
        edges=edges,
    )


def promote_workflow_draft(draft: WorkflowDraft) -> WorkflowDraftPromotion:
    semantic = draft.semantic
    artifact_by_producer_type = {
        (item.produced_by_block_id, item.artifact_type_id): item.id
        for item in semantic.intended_artifacts
    }
    blocks_by_port = {port.id: port.owner_block_id for port in semantic.ports}
    incoming_source = {
        item.target_port_id: item.source_port_id for item in semantic.connections
    }
    ports_by_id = {item.id: item for item in semantic.ports}

    def artifact_for_port(port: Any) -> str | None:
        producer = port.owner_block_id
        if port.direction == "input" and port.id in incoming_source:
            producer = blocks_by_port[incoming_source[port.id]]
        return artifact_by_producer_type.get((producer, port.value_type_id))

    required_for: dict[str, set[str]] = {
        item.id: set() for item in semantic.intended_artifacts
    }
    for port in semantic.ports:
        artifact_id = artifact_for_port(port)
        if artifact_id is not None and port.direction == "input":
            required_for[artifact_id].add(port.owner_block_id)
    relationships: list[dict[str, Any]] = [
        {
            "id": item.id,
            "kind": "data",
            "source_id": item.source_port_id,
            "target_id": item.target_port_id,
            "label": ports_by_id[item.source_port_id].name,
            "condition": None,
        }
        for item in semantic.connections
    ]
    gate_owner = {item.id: item.owner_block_id for item in semantic.gates}
    relationships.extend(
        {
            "id": item.id,
            "kind": "decision",
            "source_id": item.owner_block_id,
            "target_id": item.proceed_target_block_id,
            "label": "Proceed",
            "condition": item.condition,
        }
        for item in semantic.gates
    )
    relationships.extend(
        {
            "id": item.id,
            "kind": "feedback",
            "source_id": gate_owner[item.from_gate_id],
            "target_id": item.to_block_id,
            "label": item.reason,
            "condition": item.reason,
        }
        for item in semantic.feedback_paths
    )
    payload: dict[str, Any] = {
        "document_kind": WORKFLOW_DEFINITION_KIND,
        "schema_version": WORKFLOW_DEFINITION_VERSION,
        "workflow_id": draft.draft_id,
        "revision": draft.revision,
        "parent_revision": draft.revision - 1 if draft.revision > 1 else None,
        "semantic_sha256": None,
        "metadata": {
            "title": semantic.title,
            "purpose": semantic.purpose,
            "engineering_domain": "legacy.workflow-draft",
            "authorship": "human",
        },
        "phases": [item.model_dump(mode="json") for item in semantic.phases],
        "blocks": [
            {
                "id": item.id,
                "kind": "decision" if item.role == "review" else "work",
                "title": item.title,
                "purpose": item.purpose,
                "phase_id": item.phase_id,
                "execution_kind": "human"
                if item.role in {"input", "review"}
                else "deterministic",
                "instructions": item.purpose,
                "configuration": {},
                "input_port_ids": list(item.input_port_ids),
                "output_port_ids": list(item.output_port_ids),
                "binding_id": None,
                "component_ref": None,
            }
            for item in semantic.blocks
        ],
        "ports": [
            {
                "id": item.id,
                "owner_block_id": item.owner_block_id,
                "direction": item.direction,
                "name": item.name,
                "type_id": item.value_type_id,
                "required": item.required,
                "cardinality": item.cardinality,
                "artifact_contract_id": artifact_for_port(item),
                "description": item.name,
            }
            for item in semantic.ports
        ],
        "relationships": relationships,
        "artifact_contracts": [
            {
                "id": item.id,
                "name": item.title,
                "type_id": item.artifact_type_id,
                "media_type": "application/octet-stream",
                "description": item.description,
                "producer_block_id": item.produced_by_block_id,
                "required_for_block_ids": sorted(required_for[item.id]),
                "preview_policy": "metadata",
                "allowed_actions": ["inspect"],
            }
            for item in semantic.intended_artifacts
        ],
        "bindings": [],
        "components": [],
    }
    payload["semantic_sha256"] = canonical_definition_sha256(payload)
    definition = WorkflowDefinition.model_validate(payload)
    source_envelope = canonical_json_bytes(draft)
    return WorkflowDraftPromotion(
        definition=definition,
        legacy_layout=draft.layout,
        source_envelope=source_envelope,
        source_envelope_sha256=hashlib.sha256(source_envelope).hexdigest(),
        target_definition_sha256=definition.semantic_sha256,
    )


def rollback_workflow_draft(
    promotion: WorkflowDraftPromotion, definition: WorkflowDefinition
) -> WorkflowDraft:
    if canonical_definition_sha256(definition) != promotion.target_definition_sha256:
        raise ValueError(
            "Workflow promotion target digest changed; exact legacy rollback is unavailable"
        )
    if hashlib.sha256(promotion.source_envelope).hexdigest() != (
        promotion.source_envelope_sha256
    ):
        raise ValueError("Workflow promotion source envelope digest changed")
    return WorkflowDraft.model_validate_json(promotion.source_envelope)


__all__ = [
    "WORKFLOW_COMMAND_KIND",
    "WORKFLOW_COMMAND_VERSION",
    "WORKFLOW_DEFINITION_KIND",
    "WORKFLOW_DEFINITION_VERSION",
    "RECOVERY_WORKFLOW_DEFINITION_VERSION",
    "WorkflowApplyResult",
    "WorkflowCommandBatch",
    "WorkflowDecodeResult",
    "WorkflowDefinition",
    "WorkflowDefinitionProjection",
    "WorkflowDiagnostic",
    "WorkflowDraftPromotion",
    "WorkflowRecoveryPromotion",
    "accept_workflow_candidate",
    "apply_workflow_commands",
    "canonical_definition_bytes",
    "canonical_definition_sha256",
    "decode_workflow_definition",
    "definition_envelope_bytes",
    "project_workflow_definition",
    "promote_recovery_workflow_definition",
    "promote_workflow_draft",
    "rollback_recovery_workflow_definition",
    "rollback_workflow_draft",
]
