"""Pure, versioned process presentation contracts; execution stays in its owner."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from jsonschema import Draft202012Validator, FormatChecker
from pydantic import (
    AfterValidator,
    Field,
    JsonValue,
    StrictBool,
    field_validator,
    model_validator,
)

from .process_validation import (
    Contract,
    Digest,
    Identifier,
    ResultIdentifier,
    Text,
    canonical_digest,
    canonical_json,
    relative_locator,
)

INTERACTION_VERSION = "wright.process-interaction/1"
INPUT_VERSION = "wright.process-input-snapshot/1"
INLINE_BYTES = 65_536
PAGE_ITEMS = 256
MAX_JSON_DEPTH = 24


def checked_json(value: JsonValue) -> JsonValue:
    if len(canonical_json(value).encode("utf-8")) > INLINE_BYTES:
        raise ValueError("Inline JSON exceeds 64 KiB; use an artifact reference")

    def depth(item, level=0):
        if level > MAX_JSON_DEPTH:
            raise ValueError("JSON nesting exceeds the supported bound")
        if isinstance(item, dict):
            for child in item.values():
                depth(child, level + 1)
        elif isinstance(item, list):
            for child in item:
                depth(child, level + 1)

    depth(value)
    return value


def checked_timestamp(value: str) -> str:
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Timestamp must be an ISO8601 UTC instant") from exc
    if moment.tzinfo is None or moment.utcoffset() != timezone.utc.utcoffset(moment):
        raise ValueError("Timestamp must be an ISO8601 UTC instant")
    return value


Timestamp = Annotated[str, AfterValidator(checked_timestamp)]
Locator = Annotated[Identifier, AfterValidator(relative_locator)]
InlineJSON = Annotated[JsonValue, AfterValidator(checked_json)]
Operation = Literal[
    "start", "respond", "review", "action", "cancel", "attach", "read", "navigate"
]
ProcessCapability = Literal[
    "process.read",
    "process.inputs",
    "process.start",
    "process.respond",
    "process.review",
    "process.action",
    "process.cancel",
    "process.results",
    "process.navigate",
]
RunState = Literal[
    "preparing",
    "ready",
    "running",
    "waiting_human",
    "waiting_external",
    "reconciliation_required",
    "completed",
    "failed",
    "cancelled",
    "cancellation_requested",
]
DependencyKind = Literal[
    "supplied",
    "explicit_default",
    "upstream_produced",
    "declared_human_response",
    "unresolved",
]


def checked_value_schema(schema: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """Bounded JSON Schema subset with local, acyclic definitions only.

    Unsupported keywords fail explicitly. Arbitrary regular expressions and
    remote references are outside v1; validation cannot execute producer code.
    """
    checked_json(schema)
    allowed = {
        "$schema",
        "$defs",
        "$ref",
        "type",
        "title",
        "description",
        "default",
        "enum",
        "const",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "minItems",
        "maxItems",
        "uniqueItems",
        "minProperties",
        "maxProperties",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minLength",
        "maxLength",
        "format",
    }
    if (
        "$schema" in schema
        and schema["$schema"] != "https://json-schema.org/draft/2020-12/schema"
    ):
        raise ValueError("Unsupported value-schema dialect")

    visits = 0

    def walk(node, stack=(), level=0):
        nonlocal visits
        visits += 1
        if visits > 4096:
            raise ValueError("Value-schema expansion exceeds the supported bound")
        if level > MAX_JSON_DEPTH:
            raise ValueError("Value-schema nesting exceeds the supported bound")
        if isinstance(node, bool):
            return
        if not isinstance(node, dict):
            raise ValueError("A value-schema node must be an object or boolean")
        if unknown := set(node) - allowed:
            raise ValueError(
                f"Unsupported value-schema keywords: {', '.join(sorted(unknown))}"
            )
        if node.get("format") not in {None, "date-time", "date", "time", "uuid"}:
            raise ValueError("Unsupported value-schema format")
        if "$ref" in node:
            ref = node["$ref"]
            if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
                raise ValueError("Value-schema references must name a local definition")
            name = ref[len("#/$defs/") :].replace("~1", "/").replace("~0", "~")
            definitions = schema.get("$defs", {})
            if not isinstance(definitions, dict) or name not in definitions:
                raise ValueError("Value-schema reference does not resolve")
            if ref in stack:
                raise ValueError("Recursive value-schema references are unsupported")
            walk(definitions[name], (*stack, ref), level + 1)
        for key in ("properties", "$defs"):
            entries = node.get(key, {})
            if not isinstance(entries, dict) or len(entries) > PAGE_ITEMS:
                raise ValueError("Value-schema entries must be a bounded object")
            for child in entries.values():
                walk(child, stack, level + 1)
        for key in ("items", "additionalProperties"):
            if key in node:
                walk(node[key], stack, level + 1)

    walk(schema)
    Draft202012Validator.check_schema(schema)
    return schema


def validate_response(schema: dict[str, JsonValue], value: JsonValue) -> None:
    checked_value_schema(schema)
    checked_json(value)
    error = next(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(value),
        None,
    )
    if error is not None:
        location = "/".join(str(part) for part in error.absolute_path) or "root"
        raise ValueError(
            f"Response does not match declared {error.validator} at {location}"
        )


def unique_ids(items, field: str) -> None:
    values = [getattr(item, field) for item in items]
    if len(set(values)) != len(values):
        raise ValueError(f"{field} identities must be unique")


class ProcessRef(Contract):
    workspace_id: Identifier
    source_path: Locator
    source_digest: Digest
    semantic_digest: Digest | None = None
    source_contract: Identifier = "canonical-source"


class ArtifactRef(Contract):
    artifact_ref: Locator
    sha256: Digest
    media_type: Identifier | None = None
    result_id: ResultIdentifier | None = None
    representation_id: Identifier | None = None


class CapabilityRef(Contract):
    binding_id: Identifier
    schema_digest: Digest
    resource_digest: Digest | None = None


class ValueBinding(Contract):
    kind: Literal["value"] = "value"
    input_id: Identifier
    value: InlineJSON
    provenance: Literal["supplied", "explicit_default"] = "supplied"


class FileBinding(Contract):
    kind: Literal["file"] = "file"
    input_id: Identifier
    reference: ArtifactRef
    provenance: Literal["supplied", "explicit_default"] = "supplied"


class OptionBinding(Contract):
    kind: Literal["option"] = "option"
    input_id: Identifier
    option_id: Identifier
    capability: CapabilityRef
    value: InlineJSON
    observed_at: Timestamp
    stale_after: Timestamp | None = None
    provenance: Literal["supplied", "explicit_default"] = "supplied"


InputBinding = Annotated[
    ValueBinding | FileBinding | OptionBinding, Field(discriminator="kind")
]


class InputSnapshotContent(Contract):
    schema_version: Literal["wright.process-input-snapshot/1"] = INPUT_VERSION
    snapshot_id: Identifier
    process: ProcessRef
    created_at: Timestamp
    bindings: tuple[InputBinding, ...] = Field(default=(), max_length=PAGE_ITEMS)

    @model_validator(mode="after")
    def unique_bindings(self):
        unique_ids(self.bindings, "input_id")
        return self


class InputSnapshot(InputSnapshotContent):
    digest: Digest

    @classmethod
    def create(cls, **values) -> InputSnapshot:
        content = InputSnapshotContent.model_validate(values)
        return cls(**content.model_dump(), digest=canonical_digest(content))

    @model_validator(mode="after")
    def verify_digest(self):
        if self.digest != canonical_digest(self.model_dump(exclude={"digest"})):
            raise ValueError("Input snapshot digest does not match immutable content")
        return self


class StartReceipt(Contract):
    """Allocated identity before dispatch; live run state stays in the recorder."""

    principal_id: Identifier
    process: ProcessRef
    request_id: Identifier
    payload_digest: Digest
    input_snapshot_id: Identifier
    input_digest: Digest
    run_id: Identifier
    run_log_path: Locator | None = None
    initial_outcome: Literal["accepted"] = "accepted"
    created_at: Timestamp


class InteractionResponseContent(Contract):
    response_id: Identifier
    workspace_id: Identifier
    run_id: Identifier
    checkpoint_id: Identifier
    subject_digest: Digest
    schema_digest: Digest
    input_digest: Digest
    value: InlineJSON
    actor: Identifier
    reason: Text
    request_id: Identifier
    created_at: Timestamp
    integration_test: StrictBool = False


class InteractionResponse(InteractionResponseContent):
    digest: Digest

    @classmethod
    def create(cls, **values) -> InteractionResponse:
        content = InteractionResponseContent.model_validate(values)
        return cls(**content.model_dump(), digest=canonical_digest(content))

    @model_validator(mode="after")
    def verify_digest(self):
        if self.digest != canonical_digest(self.model_dump(exclude={"digest"})):
            raise ValueError("Response digest does not match immutable content")
        return self


class NavigationTarget(Contract):
    kind: Literal["process", "block", "run", "result", "assessment", "evidence"]
    block_id: Identifier | None = None
    run_id: Identifier | None = None
    result_id: ResultIdentifier | None = None
    assessment_id: Identifier | None = None
    artifact_ref: Locator | None = None

    @model_validator(mode="after")
    def exact_destination(self):
        required = {
            "block": "block_id",
            "run": "run_id",
            "result": "result_id",
            "assessment": "assessment_id",
            "evidence": "artifact_ref",
        }.get(self.kind)
        if required and not getattr(self, required):
            raise ValueError(f"{self.kind} navigation requires {required}")
        return self


class NavigationResolution(Contract):
    """Exact host intent resolved against accepted source and recorded subjects."""

    process: ProcessRef
    target: NavigationTarget
    representation: ArtifactRef | None = None


class Reason(Contract):
    code: Identifier
    message: Text
    correction: Text
    binding_id: Identifier | None = None
    step_id: Identifier | None = None
    navigation: NavigationTarget | None = None
    technical_details_ref: Locator | None = None


class InputDependency(Contract):
    binding_id: Identifier
    classification: DependencyKind
    producer_step: Identifier | None = None
    producer_port: Identifier | None = None
    interaction_step: Identifier | None = None
    reasons: tuple[Reason, ...] = ()

    @model_validator(mode="after")
    def declared_source(self):
        if self.classification == "upstream_produced" and not (
            self.producer_step and self.producer_port
        ):
            raise ValueError("Produced dependency requires the declared step and port")
        if (
            self.classification == "declared_human_response"
            and not self.interaction_step
        ):
            raise ValueError("Human response dependency requires its declared step")
        if self.classification == "unresolved" and not self.reasons:
            raise ValueError("Unresolved dependency requires a correction reason")
        return self


class InputOption(Contract):
    option_id: Identifier
    title: Text
    value: InlineJSON


class InputDefinition(Contract):
    input_id: Identifier
    block_id: Identifier
    port_id: Identifier
    title: Text
    value_schema: dict[str, JsonValue]
    binding_kind: Literal["value", "file", "option"] = "value"
    required: StrictBool = True
    unit: Identifier | None = None
    frame: Identifier | None = None
    default: InputBinding | None = None
    current_value: InputBinding | None = None
    option_source: CapabilityRef | None = None
    available_options: tuple[InputOption, ...] = Field(
        default=(), max_length=PAGE_ITEMS
    )
    options_observed_at: Timestamp | None = None
    options_stale_after: Timestamp | None = None
    dependencies: tuple[InputDependency, ...] = Field(default=(), max_length=PAGE_ITEMS)

    _schema = field_validator("value_schema")(checked_value_schema)

    @model_validator(mode="after")
    def exact_input(self):
        unique_ids(self.available_options, "option_id")
        if any(
            value and value.input_id != self.input_id
            for value in (self.default, self.current_value)
        ):
            raise ValueError("Input value must match its exact input identity")
        for value in (self.default, self.current_value):
            if isinstance(value, (ValueBinding, OptionBinding)):
                validate_response(self.value_schema, value.value)
        return self


class Readiness(Contract):
    state: Literal["ready", "blocked", "unsupported"]
    assessment_id: Identifier
    process: ProcessRef
    input_digest: Digest | None = None
    assessed_at: Timestamp
    expires_at: Timestamp | None = None
    dependencies: tuple[InputDependency, ...] = Field(default=(), max_length=PAGE_ITEMS)
    reasons: tuple[Reason, ...] = ()

    @model_validator(mode="after")
    def no_unresolved_ready(self):
        unique_ids(self.dependencies, "binding_id")
        if self.state == "ready" and (
            self.reasons
            or any(x.classification == "unresolved" for x in self.dependencies)
        ):
            raise ValueError("Unresolved prerequisites cannot be ready")
        if self.state != "ready" and not self.reasons:
            raise ValueError("Unavailable readiness requires a correction reason")
        return self


class AssessmentRef(Contract):
    assessment_id: Identifier
    subject_digest: Digest
    outcome: Literal[
        "pass", "fail", "blocked", "inconclusive", "error", "not_applicable"
    ]
    currentness: Literal["current", "stale", "unresolved"]


class OutputRef(Contract):
    result_id: ResultIdentifier
    step_id: Identifier
    port_id: Identifier
    role: Identifier
    title: Text
    producer_attempt: Identifier | None = None
    revision_id: Identifier | None = None
    representations: tuple[ArtifactRef, ...] = Field(default=(), max_length=PAGE_ITEMS)
    assessments: tuple[AssessmentRef, ...] = Field(default=(), max_length=PAGE_ITEMS)
    supported_viewers: tuple[Identifier, ...] = ()


class ReviewDecision(Contract):
    """Recorded exact decision evidence; it is not dispatch authority."""

    decision: Literal["approved", "changes_requested"]
    actor: Identifier
    reason: str = Field(default="", max_length=2000, strict=True)
    request_id: Identifier | None = None
    integration_test: StrictBool = False


class ApprovedActionReceipt(Contract):
    """One consumed action request; acceptance and observed completion are distinct."""

    request_id: Identifier
    principal_id: Identifier | None = None
    submission: Literal["authorized", "accepted", "rejected", "unknown"]
    delivery_completed: StrictBool = False
    observed_outcome: (
        Literal["completed", "failed", "cancelled", "unknown", "input_required"] | None
    ) = None
    provider_reference: str | None = Field(
        default=None, min_length=1, max_length=160, strict=True
    )
    cancellation_requested: StrictBool = False
    cancellation_outcome: (
        Literal["completed", "failed", "cancelled", "unknown", "input_required"] | None
    ) = None


class PendingInteraction(Contract):
    checkpoint_id: Identifier
    step_id: Identifier
    kind: Literal["input", "review", "action"]
    subject_digest: Digest
    instructions: Text
    response_schema: dict[str, JsonValue] | None = None
    decisions: tuple[Identifier, ...] = ()
    evidence: tuple[ArtifactRef, ...] = Field(default=(), max_length=PAGE_ITEMS)
    state: Literal["waiting", "responded", "consumed", "stale", "cancelled"] = "waiting"
    decision: ReviewDecision | None = None
    action_receipt: ApprovedActionReceipt | None = None

    @field_validator("response_schema")
    @classmethod
    def response_shape(cls, value):
        return checked_value_schema(value) if value is not None else None

    @model_validator(mode="after")
    def declared_response(self):
        if self.kind != "action" and self.action_receipt is not None:
            raise ValueError(
                "Only an action checkpoint can carry a consumed action receipt"
            )
        if self.kind == "input" and self.decision is not None:
            raise ValueError("Input answers are not review decisions")
        if self.kind == "input" and (self.response_schema is None or self.decisions):
            raise ValueError(
                "Input checkpoint requires only its declared response schema"
            )
        if self.kind != "input" and (
            not self.decisions or self.response_schema is not None
        ):
            raise ValueError("Review/action checkpoint requires its declared decisions")
        return self


class Action(Contract):
    action_id: Identifier
    operation: Operation
    title: Text
    enabled: StrictBool
    subject_digest: Digest | None = None
    reasons: tuple[Reason, ...] = ()
    checkpoint_id: Identifier | None = None
    idempotency_required: StrictBool = True

    @model_validator(mode="after")
    def exact_permission(self):
        if not self.enabled and not self.reasons:
            raise ValueError("Disabled action requires an actionable reason")
        if (
            self.enabled
            and self.operation not in {"read", "navigate", "attach"}
            and not self.subject_digest
        ):
            raise ValueError("Enabled mutation requires an exact subject digest")
        return self


class Observation(Contract):
    observation_id: Identifier
    provider_binding: Identifier
    state: RunState
    observed_at: Timestamp
    stale_after: Timestamp | None = None
    operation_id: Identifier | None = None
    activity: Text | None = None
    progress_percent: Annotated[float, Field(ge=0, le=100)] | None = None
    estimated_remaining_seconds: Annotated[float, Field(ge=0)] | None = None
    metrics: dict[str, InlineJSON] = Field(default_factory=dict, max_length=32)
    limitations: tuple[Text, ...] = ()


class InteractionContext(Contract):
    process: ProcessRef
    run_id: Identifier | None = None
    input_snapshot_id: Identifier | None = None
    input_digest: Digest | None = None
    cursor: Annotated[int, Field(strict=True, ge=0)] = 0
    generated_at: Timestamp

    @model_validator(mode="after")
    def paired_inputs(self):
        if (self.input_snapshot_id is None) != (self.input_digest is None):
            raise ValueError(
                "Input snapshot identity and digest must be supplied together"
            )
        return self


class InteractionSnapshot(Contract):
    schema_version: Literal["wright.process-interaction/1"] = INTERACTION_VERSION
    context: InteractionContext
    state: RunState
    inputs: tuple[InputDefinition, ...] = Field(default=(), max_length=PAGE_ITEMS)
    readiness: Readiness | None = None
    outputs: tuple[OutputRef, ...] = Field(default=(), max_length=PAGE_ITEMS)
    interactions: tuple[PendingInteraction, ...] = Field(
        default=(), max_length=PAGE_ITEMS
    )
    actions: tuple[Action, ...] = Field(default=(), max_length=PAGE_ITEMS)
    observations: tuple[Observation, ...] = Field(default=(), max_length=PAGE_ITEMS)
    diagnostics: tuple[Reason, ...] = Field(default=(), max_length=PAGE_ITEMS)
    navigation: tuple[NavigationTarget, ...] = Field(default=(), max_length=PAGE_ITEMS)
    next_page: Identifier | None = None

    @model_validator(mode="after")
    def consistent_identity(self):
        for items, field in (
            (self.inputs, "input_id"),
            (self.interactions, "checkpoint_id"),
            (self.actions, "action_id"),
        ):
            unique_ids(items, field)
        if (
            self.readiness is not None
            and self.readiness.process != self.context.process
        ):
            raise ValueError("Readiness belongs to another accepted process")
        if (
            self.readiness is not None
            and self.readiness.input_digest != self.context.input_digest
        ):
            raise ValueError("Readiness belongs to another input snapshot")
        return self


class ProcessRunEvent(Contract):
    """Recorder progress metadata; engineering payloads have their own readers."""

    sequence: Annotated[int, Field(strict=True, ge=1)]
    kind: Annotated[str, Field(max_length=256)] | None = None
    at: Annotated[str, Field(max_length=256)] | None = None
    task_id: Annotated[str, Field(max_length=256)] | None = None
    task_title: Annotated[str, Field(max_length=256)] | None = None
    step_id: Annotated[str, Field(max_length=256)] | None = None
    execution_kind: Annotated[str, Field(max_length=256)] | None = None


class ProcessRunEventPage(Contract):
    run_id: Identifier
    state: RunState
    events: tuple[ProcessRunEvent, ...] = Field(default=(), max_length=PAGE_ITEMS)
    cursor: Annotated[str, Field(min_length=1, max_length=256)]
    has_more: StrictBool
    following: StrictBool

    @model_validator(mode="after")
    def bounded_page(self):
        checked_json(self.model_dump(mode="json"))
        return self


class ProcessCancellationReceipt(Contract):
    request_id: Identifier
    run_id: Identifier
    state: Literal["cancellation_requested"] = "cancellation_requested"
