"""Resolve authoring defaults; accepted source owns subsequent execution policy."""

from __future__ import annotations

import json
from collections.abc import Callable

from core.workflow_instructions import (
    WorkflowInstructionSet,
    WorkflowInstructionOverride,
)
from data_vault.workflow_instruction_repository import (
    WorkflowInstructionRepository,
    WorkflowInstructionDefaultsConflict,
    stored_defaults_revision,
)


class WorkflowInstructionSettings:
    def __init__(
        self,
        db_path: str,
        *,
        default_loader: Callable[[], WorkflowInstructionSet] | None = None,
    ):
        self.repository = WorkflowInstructionRepository(db_path)
        self.default_loader = default_loader

    def _packaged(self) -> WorkflowInstructionSet:
        if self.default_loader is not None:
            return self.default_loader()
        from agent_adapters.workflow_instructions import (
            load_default_workflow_instructions,
        )

        return load_default_workflow_instructions()

    def read(self) -> dict:
        stored = self.repository.read()
        instructions = (
            WorkflowInstructionSet.model_validate_json(stored)
            if stored is not None
            else self._packaged()
        )
        return {
            "instructions": instructions.model_dump(mode="json"),
            "digest": instructions.digest,
            "origin": "global" if stored is not None else "packaged",
            "revision": stored_defaults_revision(stored, instructions.digest),
        }

    def replace(self, instructions: dict, *, expected_revision: str) -> dict:
        validated = WorkflowInstructionSet.model_validate(instructions)
        stored = self.repository.read()
        current_digest = (
            WorkflowInstructionSet.model_validate_json(stored).digest
            if stored is not None
            else self._packaged().digest
        )
        if stored_defaults_revision(stored, current_digest) != expected_revision:
            raise WorkflowInstructionDefaultsConflict(
                "Instruction defaults changed. Reload before saving your edit."
            )
        value = json.dumps(
            validated.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )
        self.repository.replace(value, expected_value=stored)
        return self.read()

    def propose_action_intent_upgrade(self, instructions: dict | None = None) -> dict:
        """Read-only migration proposal, preserving customer instructions/policy.

        The defaults revision supports the existing CAS save. A workflow-specific
        collection instead remains subject to its source owner's revision/CAS.
        No accepted source, defaults, checkpoints or approvals are rewritten.
        """
        from agent_adapters.workflow_instructions import (
            embedded_asset,
            load_default_workflow_instructions,
            workflow_action_intent_instructions,
            WORKFLOW_HELPER_CONTRACTS,
            validate_workflow_helper_instructions,
        )

        current_defaults = self.read()
        current = WorkflowInstructionSet.model_validate(
            instructions
            if instructions is not None
            else current_defaults["instructions"]
        )
        proposed = current.model_dump(mode="json")
        changes = []
        if current.action_intent_contract is None:
            helper = next(
                (
                    item
                    for item in current.assets
                    if item.id == "protocol.action-intent"
                ),
                None,
            )
            if helper is None:
                packaged = load_default_workflow_instructions()
                helper = embedded_asset(packaged, "protocol.action-intent")
                proposed["assets"].append(helper.model_dump(mode="json"))
                changes.append(
                    {
                        "path": "assets.protocol.action-intent",
                        "before": None,
                        "after": helper.model_dump(mode="json"),
                    }
                )
            proposed["action_intent_contract"] = "wright.workflow-action-intent/1"
            changes.append(
                {
                    "path": "action_intent_contract",
                    "before": None,
                    "after": "wright.workflow-action-intent/1",
                }
            )
        packaged = None
        for identity in WORKFLOW_HELPER_CONTRACTS:
            if not any(item["id"] == identity for item in proposed["assets"]):
                packaged = packaged or load_default_workflow_instructions()
                helper = embedded_asset(packaged, identity)
                proposed["assets"].append(helper.model_dump(mode="json"))
                changes.append(
                    {
                        "path": "assets." + identity,
                        "before": None,
                        "after": helper.model_dump(mode="json"),
                    }
                )
        validated = WorkflowInstructionSet.model_validate(proposed)
        workflow_action_intent_instructions(validated)
        for identity in WORKFLOW_HELPER_CONTRACTS:
            validate_workflow_helper_instructions(validated, identity)
        return {
            "scope": "workflow" if instructions is not None else "defaults",
            "current_revision": current_defaults["revision"]
            if instructions is None
            else None,
            "current_digest": current.digest,
            "proposed_digest": validated.digest,
            "instructions": validated.model_dump(mode="json"),
            "changes": changes,
            "available": bool(changes),
        }

    def for_workspace(self, workspace_prompt: str | None = None) -> dict:
        result = self.read()
        instructions = WorkflowInstructionSet.model_validate(result["instructions"])
        if workspace_prompt and workspace_prompt.strip():
            layer = WorkflowInstructionOverride(
                origin="workspace-context", text=workspace_prompt
            )
            instructions = WorkflowInstructionSet.model_validate(
                {
                    **instructions.model_dump(mode="json"),
                    "layers": [
                        *(
                            entry.model_dump(mode="json")
                            for entry in instructions.layers
                        ),
                        layer.model_dump(mode="json"),
                    ],
                }
            )
            result.update(
                instructions=instructions.model_dump(mode="json"),
                digest=instructions.digest,
            )
        return result


def materialize_new_workflow_instructions(
    source: str, instructions: WorkflowInstructionSet
) -> str:
    """Snapshot defaults in a new draft; never rewrite an existing legacy source."""
    from .workflow_source_execution import _parse

    blocks = _parse(source)
    workflows = [block for block in blocks if block["kind"] == "workflow"]
    if len(workflows) != 1:
        raise ValueError("A new workflow requires one workflow header")
    embedded = workflows[0]["fields"].get("instructions")
    if embedded is not None:
        WorkflowInstructionSet.model_validate(embedded)
        return source
    lines = source.splitlines(keepends=True)
    header = f"workflow {workflows[0]['id']}"
    position = next(index for index, line in enumerate(lines) if line.strip() == header)
    newline = "\r\n" if lines[position].endswith("\r\n") else "\n"
    lines.insert(
        position + 1,
        "  instructions: "
        + json.dumps(instructions.model_dump(mode="json"), separators=(",", ":"))
        + newline,
    )
    return "".join(lines)
