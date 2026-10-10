"""Inspectable shipped defaults and resolution of embedded workflow resources.

Loading defaults is for authoring or an explicitly labelled legacy invocation.
An accepted instruction set is resolved entirely from its embedded assets.
This catalog covers workflow requests, recovery and bridge helpers, CAD/resource
context, validation feedback and general chat. Accepted source owns its snapshot.
"""

from __future__ import annotations

from importlib.resources import files
from copy import deepcopy
import hashlib
import json

from core.process_validation import canonical_digest, canonical_json
from core.redaction import redact_mapping

from core.workflow_instructions import (
    ResolvedWorkflowInstructions,
    WorkflowInstructionAsset,
    WorkflowInstructionOverride,
    WorkflowInstructionSet,
    WorkflowAssumption,
    instruction_text_digest,
)


def load_default_workflow_instructions() -> WorkflowInstructionSet:
    root = files(__package__)
    manifest = json.loads(root.joinpath("manifest.json").read_text(encoding="utf-8"))
    assets = []
    for item in manifest.pop("assets"):
        body = root.joinpath(item.pop("file")).read_text(encoding="utf-8").strip()
        assets.append(
            WorkflowInstructionAsset(
                **item,
                body=body,
                body_digest=instruction_text_digest(body),
                version=manifest["profile_version"],
                origin=manifest["profile_id"],
            )
        )
    return WorkflowInstructionSet.model_validate({**manifest, "assets": assets})


def embedded_instruction_set(value=None) -> WorkflowInstructionSet:
    if value is not None:
        return WorkflowInstructionSet.model_validate(value)
    # Older callers have no captured instructions. Name the dependency instead
    # of implying their historical definitions contained this resource snapshot.
    defaults = load_default_workflow_instructions()
    return defaults.model_copy(
        update={
            "profile_id": "wright.legacy-unattended-compatibility",
            "action_intent_contract": None,
            "policy": defaults.policy.model_copy(
                update={"assumption_policy": "require_specified"}
            ),
        }
    )


def embedded_asset(instructions: WorkflowInstructionSet, identity: str):
    asset = next((item for item in instructions.assets if item.id == identity), None)
    if asset is None:
        raise ValueError(
            f"Saved workflow instructions are missing {identity}; explicitly update their instruction assets before running."
        )
    return asset


def workflow_action_intent_instructions(instruction_set) -> str | None:
    """Return the saved model-facing action protocol, never current defaults.

    Absent metadata explicitly identifies legacy calls; their eligibility is
    checked by readiness against actual operation effects and saved policy.
    """
    instructions = embedded_instruction_set(instruction_set)
    if instructions.action_intent_contract is None:
        return None
    asset = embedded_asset(instructions, "protocol.action-intent")
    if asset.role != "resource-context" or asset.variables:
        raise ValueError(
            "Saved action-intent instructions must be constant resource context"
        )
    return asset.body


WORKFLOW_HELPER_CONTRACTS = {
    "validation.design-check": ("validation", ()),
    "validation.design-revision": ("validation", ("feedback",)),
    "context.expected-files": ("resource-context", ("files",)),
    "context.task-workspace": ("resource-context", ("workspace_dir",)),
}


def validate_workflow_helper_instructions(instruction_set, identity):
    """Qualify a saved runner helper without consulting current packaged text."""
    role, variables = WORKFLOW_HELPER_CONTRACTS[identity]
    asset = embedded_asset(embedded_instruction_set(instruction_set), identity)
    if asset.role != role or set(asset.variables) != set(variables):
        raise ValueError(
            f"Saved {identity} has an incompatible role or variable contract"
        )
    return asset


def workflow_helper_instructions(instruction_set, identity, *, variables=None):
    return validate_workflow_helper_instructions(instruction_set, identity).render(
        variables or {}
    )


def workflow_design_revision_feedback(feedback, *, instruction_set=None):
    """Bound model guidance and exact prior evidence without changing authority."""
    rendered = workflow_helper_instructions(
        instruction_set,
        "validation.design-revision",
        variables={"feedback": canonical_json(feedback)},
    )
    if len(rendered.encode("utf-8")) > 16 * 1024:
        raise ValueError(
            "Design revision feedback exceeds the 16 KiB inline budget; inspect the complete design check before a new run"
        )
    return rendered


def resolve_workflow_instructions(
    role, *, instruction_set=None, instruction_override=None, variables=None
):
    instructions = embedded_instruction_set(instruction_set)
    override = (
        WorkflowInstructionOverride.model_validate(instruction_override)
        if instruction_override
        else None
    )
    resolved = instructions.resolve(role, variables=variables, step_override=override)
    policy = embedded_asset(
        instructions, "policy." + resolved.assumption_policy.replace("_", "-")
    )
    text = policy.body + "\n\n" + resolved.text
    return ResolvedWorkflowInstructions(
        **{
            **resolved.model_dump(),
            "text": text,
            "text_digest": instruction_text_digest(text),
            "asset_ids": (policy.id, *resolved.asset_ids),
            "origins": (policy.origin, *resolved.origins),
        },
    )


def workflow_response_instructions(
    output_format, *, instruction_set=None, instruction_override=None
):
    instructions = embedded_instruction_set(instruction_set)
    format_asset = embedded_asset(instructions, f"format.{output_format}")
    resolved = resolve_workflow_instructions(
        "workflow-task",
        instruction_set=instructions,
        instruction_override=instruction_override,
        variables={"output_format_instructions": format_asset.body},
    )
    return resolved.model_copy(
        update={
            "asset_ids": (*resolved.asset_ids, format_asset.id),
            "origins": (*resolved.origins, format_asset.origin),
        }
    )


def validate_workflow_assumptions(records, policy):
    if not isinstance(records, (list, tuple)) or len(records) > 64:
        raise ValueError(
            "Workflow assumptions require a bounded array of declared choices"
        )
    parsed = tuple(WorkflowAssumption.model_validate(item) for item in records)
    if parsed and policy != "document_reasonable":
        raise ValueError(
            "This saved policy requires specified values and cannot accept invented assumptions"
        )
    return [item.model_dump(mode="json") for item in parsed]


def validate_workflow_instruction_dependencies(
    instruction_set, role, instruction_override=None
):
    """Check portable primary dependencies without consulting shipped defaults.

    Editable bodies retain the runtime's declared substitution interface. Helper
    policy and document-format resources cannot introduce runtime variables.
    Provider bridge/chat resources are not covered by this primary contract.
    """
    instructions = embedded_instruction_set(instruction_set)
    variables = {
        "workflow-task": {"output_format_instructions": "checked format"},
        "image-generation": {},
        "mcp-task": {
            "output_format": "text",
            "max_tool_calls": "1",
            "task_guidance": "",
        },
        "recovery": {"output_format": "text"},
        "protocol": {},
    }
    if role not in variables:
        raise ValueError("No primary workflow dependency contract for this role")
    roles = [role]
    if role == "mcp-task":
        workflow_action_intent_instructions(instructions)
        roles.extend(["recovery", "protocol"])
        for identity, names in {
            "bridge.workflow-translation": ("optional_notice",),
            "bridge.translation-system": (),
            "bridge.translation-repair": ("error",),
            "bridge.transcript-omissions": (),
            "bridge.optional-workflow": (),
            "bridge.required-workflow": (),
            "bridge.observation-reference-guide": (),
            "bridge.tool-content-guide": (),
            "bridge.image-tool-label": ("image_index", "tool_call_id"),
            "bridge.image-reference-label": ("image_index",),
        }.items():
            asset = embedded_asset(instructions, identity)
            if asset.role != "resource-context" or set(asset.variables) != set(names):
                raise ValueError("Embedded bridge assets have incompatible variables")
    for selected in roles:
        resolved = resolve_workflow_instructions(
            selected,
            instruction_set=instructions,
            instruction_override=instruction_override,
            variables=variables[selected],
        )
        policy = embedded_asset(
            instructions, "policy." + resolved.assumption_policy.replace("_", "-")
        )
        if policy.role != "resource-context" or policy.variables:
            raise ValueError("Embedded policy assets must be constant resource context")
    if role == "workflow-task":
        for output_format in ("text", "markdown", "html", "json"):
            asset = embedded_asset(instructions, f"format.{output_format}")
            if asset.role != "resource-context" or asset.variables:
                raise ValueError(
                    "Embedded format assets must be constant resource context"
                )


def invocation_evidence(
    payload, *, operation, instruction_set=None, resolved=None, attempt=1
):
    """Retain actual primary messages; large image content uses exact references.

    The request digest covers original submitted values before redaction. This
    deliberately describes our primary adapter request, not hidden provider or
    bridge-translated system instructions. The latter have separate owners.
    """
    snapshot = deepcopy(payload)
    original_digest = canonical_digest(snapshot)
    for message in snapshot.get("messages", []):
        content = message.get("content")
        if not isinstance(content, list):
            continue
        retained = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                image_url = part.get("image_url", {}).get("url", "")
                retained.append(
                    {
                        "type": "image_reference",
                        "sha256": hashlib.sha256(image_url.encode()).hexdigest(),
                        "encoded_size_bytes": len(image_url.encode()),
                        "media_type": image_url.split(";", 1)[0].removeprefix("data:")
                        if image_url.startswith("data:")
                        else "external-image",
                    }
                )
            else:
                retained.append(part)
        message["content"] = retained
    instructions = embedded_instruction_set(instruction_set)
    evidence = {
        "schema_version": "wright.workflow-invocation/1",
        "operation": operation,
        "request_digest": original_digest,
        "attempt": attempt,
        "messages": snapshot.get("messages", []),
        "tool_schemas": snapshot.get("tools", []),
        "tool_schemas_digest": canonical_digest(payload.get("tools", [])),
        "instruction_set_digest": instructions.digest,
        "profile_id": instructions.profile_id,
        "capture_scope": "primary_adapter_request",
        "resolved_instructions": resolved.model_dump(mode="json")
        if resolved is not None
        else None,
    }
    return redact_mapping(evidence)
