"""Portable AI instruction identities and policy; no execution authority.

Definitions contain their instruction text. A profile name is provenance, never
an instruction lookup performed while resuming a run. Runtime permissions and
engineering validation remain the responsibility of their existing owners.
"""

from __future__ import annotations

import hashlib
import re
from typing import Annotated, Literal

from pydantic import (
    Field,
    StrictStr,
    field_validator,
    model_serializer,
    model_validator,
)

from .process_validation import Contract, Digest, Identifier, canonical_digest

INSTRUCTIONS_VERSION = "wright.workflow-instructions/1"
ACTION_INTENT_VERSION = "wright.workflow-action-intent/1"
InstructionRole = Literal[
    "workflow-task",
    "image-generation",
    "mcp-task",
    "recovery",
    "protocol",
    "validation",
    "chat",
    "process-ui-author",
    "resource-context",
]
AssumptionPolicy = Literal["document_reasonable", "require_specified"]
InstructionText = Annotated[StrictStr, Field(max_length=131072)]
_VARIABLE = re.compile(r"\{\{([a-z][a-z0-9_]*)\}\}")
_VARIABLE_NAME = re.compile(r"[a-z][a-z0-9_]*\Z")


def instruction_text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def checked_instruction_text(text: str, *, empty: bool = False) -> str:
    if (not empty and not text.strip()) or "\x00" in text:
        raise ValueError("Instructions require meaningful text without NUL characters")
    if len(text.encode("utf-8")) > 131072:
        raise ValueError("Instructions exceed the 128 KiB UTF-8 limit")
    return text


class WorkflowInstructionAsset(Contract):
    """An embedded template with a checked body digest and declared variables."""

    schema_version: Literal["wright.instruction-asset/1"] = "wright.instruction-asset/1"
    id: Identifier
    role: InstructionRole
    version: Identifier
    body: InstructionText
    body_digest: Digest
    origin: Identifier
    variables: tuple[Identifier, ...] = Field(default=(), max_length=64)
    execution_contract: Literal["wright.workflow-instructions/1"] = INSTRUCTIONS_VERSION

    @field_validator("body")
    @classmethod
    def bounded_body(cls, value):
        return checked_instruction_text(value)

    @model_validator(mode="after")
    def checked_identity(self):
        if instruction_text_digest(self.body) != self.body_digest:
            raise ValueError("Instruction body does not match its saved digest")
        if len(set(self.variables)) != len(self.variables) or any(
            not _VARIABLE_NAME.fullmatch(name) for name in self.variables
        ):
            raise ValueError("Instruction variables must be unique stable names")
        if set(_VARIABLE.findall(self.body)) != set(self.variables):
            raise ValueError("Template placeholders must match the declared variables")
        return self

    def render(self, values: dict[str, str]) -> str:
        """Substitute declared data only; do not evaluate format expressions/code."""
        if set(values) != set(self.variables):
            raise ValueError(
                "Rendered instructions require exactly their declared variables"
            )
        for value in values.values():
            if not isinstance(value, str):
                raise ValueError("Instruction variable values must be text")
            checked_instruction_text(value, empty=True)
        rendered = _VARIABLE.sub(lambda match: values[match[1]], self.body)
        return checked_instruction_text(rendered)


class WorkflowBehaviorPolicy(Contract):
    """A declaration of delegated choices; never permission to change constraints."""

    assumption_policy: AssumptionPolicy = "require_specified"
    protected_requirements: tuple[Identifier, ...] = Field(default=(), max_length=256)

    @field_validator("protected_requirements")
    @classmethod
    def unique_requirements(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Protected requirements must be unique")
        return value


class WorkflowInstructionBinding(Contract):
    role: InstructionRole
    asset_ids: tuple[Identifier, ...] = Field(min_length=1, max_length=64)

    @field_validator("asset_ids")
    @classmethod
    def unique_assets(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("A role cannot contain a duplicate instruction asset")
        return value


class WorkflowInstructionOverride(Contract):
    """Explicit layer semantics; no inference from the wording of instructions."""

    origin: Identifier
    roles: tuple[InstructionRole, ...] = (
        "workflow-task",
        "image-generation",
        "mcp-task",
    )
    mode: Literal["append", "replace"] = "append"
    text: InstructionText = ""
    assumption_policy: AssumptionPolicy | None = None

    @field_validator("text")
    @classmethod
    def bounded_override(cls, value):
        return checked_instruction_text(value, empty=True)

    @model_validator(mode="after")
    def meaningful_replace(self):
        if self.mode == "replace" and not self.text.strip():
            raise ValueError("Replacement instructions require meaningful text")
        if not self.roles or len(set(self.roles)) != len(self.roles):
            raise ValueError(
                "An instruction layer requires unique declared role scopes"
            )
        return self


class WorkflowInstructionSet(Contract):
    """The portable instruction dependency collection frozen with saved source."""

    schema_version: Literal["wright.workflow-instructions/1"] = INSTRUCTIONS_VERSION
    profile_id: Identifier
    profile_version: Identifier
    action_intent_contract: Literal["wright.workflow-action-intent/1"] | None = None
    assets: tuple[WorkflowInstructionAsset, ...] = Field(min_length=1, max_length=128)
    bindings: tuple[WorkflowInstructionBinding, ...] = Field(
        min_length=1, max_length=16
    )
    policy: WorkflowBehaviorPolicy = Field(default_factory=WorkflowBehaviorPolicy)
    layers: tuple[WorkflowInstructionOverride, ...] = Field(default=(), max_length=16)

    @model_serializer(mode="wrap")
    def preserve_legacy_identity(self, handler):
        """Optional contracts do not alter previously accepted source digests."""
        serialized = handler(self)
        if self.action_intent_contract is None:
            serialized.pop("action_intent_contract", None)
        return serialized

    @model_validator(mode="after")
    def complete_dependencies(self):
        assets = {asset.id: asset for asset in self.assets}
        if len(assets) != len(self.assets):
            raise ValueError("Instruction asset identities must be unique")
        if len({binding.role for binding in self.bindings}) != len(self.bindings):
            raise ValueError("Instruction roles must have one ordered binding")
        for binding in self.bindings:
            if any(identity not in assets for identity in binding.asset_ids):
                raise ValueError("A saved role references a missing instruction body")
            if any(
                assets[identity].role != binding.role for identity in binding.asset_ids
            ):
                raise ValueError("An instruction binding cannot cross role scopes")
        if sum(len(asset.body.encode("utf-8")) for asset in self.assets) > 524288:
            raise ValueError(
                "Saved instruction bodies exceed the 512 KiB collection bound"
            )
        return self

    @property
    def digest(self) -> str:
        return canonical_digest(self)

    def resolve(
        self,
        role: InstructionRole,
        *,
        variables: dict[str, str] | None = None,
        step_override: WorkflowInstructionOverride | None = None,
    ) -> ResolvedWorkflowInstructions:
        binding = next((item for item in self.bindings if item.role == role), None)
        if binding is None:
            raise ValueError(f"Saved instructions do not declare the {role} role")
        assets = {asset.id: asset for asset in self.assets}
        selected = [assets[identity] for identity in binding.asset_ids]
        required = {name for asset in selected for name in asset.variables}
        supplied = variables or {}
        if set(supplied) != required:
            raise ValueError(
                "Effective instructions require exactly the role's variables"
            )
        text = "\n\n".join(
            asset.render({name: supplied[name] for name in asset.variables})
            for asset in selected
        )
        policy = self.policy.assumption_policy
        origins = [asset.origin for asset in selected]
        for layer in (*self.layers, *((step_override,) if step_override else ())):
            if role not in layer.roles:
                continue
            if layer.text.strip():
                text = (
                    layer.text
                    if layer.mode == "replace"
                    else text + "\n\n" + layer.text
                )
            if layer.assumption_policy is not None:
                policy = layer.assumption_policy
            origins.append(layer.origin)
        return ResolvedWorkflowInstructions(
            role=role,
            instruction_set_digest=self.digest,
            asset_ids=binding.asset_ids,
            text=checked_instruction_text(text),
            text_digest=instruction_text_digest(text),
            assumption_policy=policy,
            origins=tuple(origins),
        )


class ResolvedWorkflowInstructions(Contract):
    role: InstructionRole
    instruction_set_digest: Digest
    asset_ids: tuple[Identifier, ...]
    text: InstructionText
    text_digest: Digest
    assumption_policy: AssumptionPolicy
    origins: tuple[Identifier, ...]

    @model_validator(mode="after")
    def exact_submission(self):
        checked_instruction_text(self.text)
        if instruction_text_digest(self.text) != self.text_digest:
            raise ValueError(
                "Effective instruction digest does not match submitted text"
            )
        return self


class WorkflowAssumption(Contract):
    """A model's declared choice, distinct from a supplied requirement or measurement."""

    parameter: Identifier
    value: Annotated[StrictStr, Field(min_length=1, max_length=4096)]
    units: Annotated[StrictStr, Field(max_length=128)] = ""
    rationale: Annotated[StrictStr, Field(min_length=1, max_length=8192)]
    affected_outputs: tuple[Identifier, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def meaningful_choice(self):
        if not self.value.strip() or not self.rationale.strip():
            raise ValueError("Assumptions require a chosen value and rationale")
        if len(set(self.affected_outputs)) != len(self.affected_outputs):
            raise ValueError("Affected outputs must be unique")
        return self
