import copy

import pytest
from pydantic import ValidationError

from core.workflow_instructions import (
    WorkflowAssumption,
    WorkflowInstructionAsset,
    WorkflowInstructionOverride,
    WorkflowInstructionSet,
    instruction_text_digest,
)
from core.workflow_step_outcomes import UnattendedStepOutcome
from core.process_validation import canonical_digest


def test_absent_action_contract_preserves_legacy_serialization_and_digest():
    saved = WorkflowInstructionSet.model_validate(definition())
    original = {
        "schema_version": "wright.workflow-instructions/1",
        "profile_id": "wright-defaults",
        "profile_version": "1",
        "assets": [
            WorkflowInstructionAsset.model_validate(asset()).model_dump(mode="json")
        ],
        "bindings": [{"role": "workflow-task", "asset_ids": ["task"]}],
        "policy": {
            "assumption_policy": "require_specified",
            "protected_requirements": [],
        },
        "layers": [],
    }
    assert saved.model_dump(mode="json") == original
    assert saved.digest == canonical_digest(original)
    assert (
        WorkflowInstructionSet.model_validate(
            {**original, "action_intent_contract": None}
        ).digest
        == saved.digest
    )
    modern = WorkflowInstructionSet.model_validate(
        {**original, "action_intent_contract": "wright.workflow-action-intent/1"}
    )
    assert modern.digest != saved.digest
    assert (
        WorkflowInstructionSet.model_validate_json(modern.model_dump_json()).digest
        == modern.digest
    )
    with pytest.raises(ValidationError):
        WorkflowInstructionSet.model_validate(
            {**original, "action_intent_contract": "wright.workflow-action-intent/999"}
        )


def test_legacy_outcome_serialization_omits_absent_assumptions():
    original = {
        "version": "wright.unattended-step/1",
        "status": "completed",
        "response": "A result",
        "reason": None,
    }
    assert (
        UnattendedStepOutcome.model_validate(original).model_dump(mode="json")
        == original
    )


def asset(
    identity="task", role="workflow-task", body="Use supplied evidence.", **extra
):
    return {
        "id": identity,
        "role": role,
        "version": "1",
        "body": body,
        "body_digest": instruction_text_digest(body),
        "origin": "wright-defaults/1",
        **extra,
    }


def definition(**extra):
    return {
        "profile_id": "wright-defaults",
        "profile_version": "1",
        "assets": [asset()],
        "bindings": [{"role": "workflow-task", "asset_ids": ["task"]}],
        **extra,
    }


def test_saved_text_is_self_contained_and_survives_other_defaults():
    saved = WorkflowInstructionSet.model_validate(definition())
    exported = saved.model_dump_json()
    changed_defaults = WorkflowInstructionSet.model_validate(
        definition(assets=[asset(body="Use a different default.")])
    )
    imported = WorkflowInstructionSet.model_validate_json(exported)
    assert imported.digest == saved.digest != changed_defaults.digest
    assert imported.resolve("workflow-task").text == "Use supplied evidence."


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d["assets"][0].update(body="Changed without updating digest"),
        lambda d: d["bindings"][0].update(asset_ids=["missing"]),
        lambda d: d["assets"].append(copy.deepcopy(d["assets"][0])),
        lambda d: d["bindings"].append(copy.deepcopy(d["bindings"][0])),
        lambda d: d["assets"][0].update(role="process-ui-author"),
        lambda d: d.update(schema_version="wright.workflow-instructions/999"),
    ],
)
def test_tampered_missing_or_cross_role_dependencies_fail_closed(change):
    raw = definition()
    change(raw)
    with pytest.raises(ValidationError):
        WorkflowInstructionSet.model_validate(raw)


def test_append_replace_and_policy_overrides_have_explicit_order_and_origins():
    saved = WorkflowInstructionSet.model_validate(
        definition(
            layers=[
                {"origin": "workspace-profile", "text": "Workspace guidance."},
                {
                    "origin": "workflow",
                    "mode": "replace",
                    "text": "Workflow guidance.",
                    "assumption_policy": "document_reasonable",
                },
            ]
        )
    )
    resolved = saved.resolve(
        "workflow-task",
        step_override=WorkflowInstructionOverride(
            origin="step",
            text="Step guidance.",
            assumption_policy="require_specified",
        ),
    )
    assert resolved.text == "Workflow guidance.\n\nStep guidance."
    assert resolved.assumption_policy == "require_specified"
    assert resolved.origins == (
        "wright-defaults/1",
        "workspace-profile",
        "workflow",
        "step",
    )
    assert resolved.text_digest == instruction_text_digest(resolved.text)
    assert resolved.instruction_set_digest == saved.digest
    assert saved.resolve("workflow-task").assumption_policy == "document_reasonable"


def test_templates_substitute_data_once_without_evaluating_inserted_expressions():
    template = WorkflowInstructionAsset.model_validate(
        asset(
            body="Format: {{output_format}}. Workspace: {{workspace}}.",
            variables=["output_format", "workspace"],
        )
    )
    assert template.render(
        {"output_format": "json", "workspace": "{{output_format}}"}
    ) == ("Format: json. Workspace: {{output_format}}.")
    for variables in (
        {"output_format": "json"},
        {"output_format": "json", "workspace": "x", "extra": "y"},
    ):
        with pytest.raises(ValueError):
            template.render(variables)


@pytest.mark.parametrize(
    "body,variables",
    [
        ("Use {{undeclared}}.", []),
        ("Use evidence.", ["unused"]),
        ("Use {{format}}.", ["format", "format"]),
        ("Use evidence.", ["expression.name"]),
    ],
)
def test_invalid_template_variable_contract_is_rejected(body, variables):
    with pytest.raises(ValidationError):
        WorkflowInstructionAsset.model_validate(asset(body=body, variables=variables))


def test_role_resolution_cannot_inherit_unbound_chat_instructions():
    saved = WorkflowInstructionSet.model_validate(
        definition(
            assets=[
                asset(),
                asset("chat", "chat", "Broad workspace chat guidance."),
            ]
        )
    )
    assert "chat" not in saved.resolve("workflow-task").text
    with pytest.raises(ValueError, match="do not declare"):
        saved.resolve("process-ui-author")


def test_workspace_task_layers_do_not_leak_into_the_confined_ui_author_role():
    saved = WorkflowInstructionSet.model_validate(
        definition(
            assets=[
                asset(),
                asset("ui", "process-ui-author", "Compose a scoped interface."),
            ],
            bindings=[
                {"role": "workflow-task", "asset_ids": ["task"]},
                {"role": "process-ui-author", "asset_ids": ["ui"]},
            ],
            layers=[
                {"origin": "workspace", "text": "Task-specific engineering guidance."}
            ],
        )
    )
    assert "Task-specific" in saved.resolve("workflow-task").text
    assert saved.resolve("process-ui-author").text == "Compose a scoped interface."
    assert saved.resolve("process-ui-author").origins == ("wright-defaults/1",)


def test_utf8_size_is_bounded_in_addition_to_character_count():
    body = "界" * 50000
    with pytest.raises(ValidationError, match="128 KiB"):
        WorkflowInstructionAsset.model_validate(asset(body=body))
    saved = WorkflowInstructionSet.model_validate(
        definition(assets=[asset(body="a" * 100000)])
    )
    with pytest.raises(ValueError, match="128 KiB"):
        saved.resolve(
            "workflow-task",
            step_override=WorkflowInstructionOverride(
                origin="step",
                text="b" * 100000,
            ),
        )


def test_blank_replacement_and_unsupported_policy_are_rejected():
    with pytest.raises(ValidationError):
        WorkflowInstructionOverride(origin="workflow", mode="replace", text=" ")
    with pytest.raises(ValidationError):
        WorkflowInstructionOverride(
            origin="workflow", assumption_policy="ask_whenever_unsure"
        )


def test_assumption_evidence_requires_value_rationale_and_affected_outputs():
    choice = WorkflowAssumption(
        parameter="bend-radius",
        value="3.175",
        units="mm",
        rationale="Unspecified design choice permitted by the saved policy.",
        affected_outputs=("cad-model", "cad-image"),
    )
    assert choice.model_dump()["units"] == "mm"
    with pytest.raises(ValidationError):
        WorkflowAssumption(
            parameter="bend-radius", value=" ", rationale="because", affected_outputs=()
        )
