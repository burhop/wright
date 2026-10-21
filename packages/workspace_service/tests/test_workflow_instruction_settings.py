from __future__ import annotations

import asyncio
import json
import sqlite3
from types import SimpleNamespace

import pytest

from core.workflow_instructions import WorkflowInstructionSet, instruction_text_digest
from data_vault.workflow_instruction_repository import (
    WorkflowInstructionDefaultsConflict,
)
from workspace_service.workflow_instruction_settings import (
    WorkflowInstructionSettings,
    materialize_new_workflow_instructions,
)
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    source,
    task,
    service,
)


def profile(body="Saved instructions A"):
    return WorkflowInstructionSet.model_validate(
        {
            "profile_id": "test-defaults",
            "profile_version": "v1",
            "assets": [
                {
                    "id": "task-instructions",
                    "role": "workflow-task",
                    "version": "v1",
                    "body": body,
                    "body_digest": instruction_text_digest(body),
                    "origin": "test-defaults",
                }
            ],
            "bindings": [{"role": "workflow-task", "asset_ids": ["task-instructions"]}],
            "policy": {"assumption_policy": "document_reasonable"},
        }
    )


@pytest.fixture
def settings(tmp_path):
    database = tmp_path / "settings.sqlite"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE system_settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
    return WorkflowInstructionSettings(str(database), default_loader=profile)


def test_global_defaults_cas_and_workspace_role_scoping(settings):
    packaged = settings.read()
    assert packaged["origin"] == "packaged"
    saved = settings.replace(
        profile("Instructions B").model_dump(mode="json"),
        expected_revision=packaged["revision"],
    )
    assert saved["origin"] == "global"
    with pytest.raises(WorkflowInstructionDefaultsConflict):
        settings.replace(
            packaged["instructions"], expected_revision=packaged["revision"]
        )
    scoped = settings.for_workspace("Use the supplied material requirements.")
    retained = WorkflowInstructionSet.model_validate(scoped["instructions"])
    assert retained.resolve("workflow-task").text.endswith(
        "Use the supplied material requirements."
    )
    assert "process-ui-author" not in retained.layers[-1].roles
    assert settings.read() == saved


def test_invalid_stored_defaults_fail_closed_instead_of_using_packaged(settings):
    with sqlite3.connect(settings.repository.db_path) as connection:
        connection.execute(
            "INSERT INTO system_settings VALUES (?, ?)",
            ("workflow_instruction_defaults_v1", "{}"),
        )
    with pytest.raises(ValueError):
        settings.read()


def test_source_embeds_complete_snapshot_and_does_not_replace_saved_a_with_b():
    original = source(task())
    snapshot = materialize_new_workflow_instructions(original, profile())
    assert (
        materialize_new_workflow_instructions(snapshot, profile("Instructions B"))
        == snapshot
    )
    plan = compile_prompt_workflow(snapshot)
    assert plan.instruction_set == profile().model_dump(mode="json")
    assert plan.steps[0].instruction_set == plan.instruction_set
    assert compile_prompt_workflow(original).instruction_set is None


def test_invalid_digest_and_absent_role_are_readiness_failures():
    serialized = profile().model_dump(mode="json")
    serialized["assets"][0]["body"] = "tampered"
    workflow_source = source(task()).replace(
        '  name: "Test workflow"',
        '  name: "Test workflow"\n  instructions: ' + json.dumps(serialized),
    )
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(workflow_source)
    serialized = profile().model_dump(mode="json")
    serialized["assets"][0]["role"] = "mcp-task"
    serialized["bindings"][0]["role"] = "mcp-task"
    with pytest.raises(WorkflowSourceExecutionError, match="workflow-task role"):
        compile_prompt_workflow(
            source(task()).replace(
                '  name: "Test workflow"',
                '  name: "Test workflow"\n  instructions: ' + json.dumps(serialized),
            )
        )


def test_action_upgrade_is_read_only_and_preserves_custom_policy_bodies_and_history(
    settings,
):
    initial = settings.read()
    raw = profile("Customer-specific design instructions.").model_dump(mode="json")
    raw["policy"] = {
        "assumption_policy": "require_specified",
        "protected_requirements": ["wall-thickness"],
    }
    stored = settings.replace(raw, expected_revision=initial["revision"])
    historical_source = materialize_new_workflow_instructions(
        source(task()), WorkflowInstructionSet.model_validate(raw)
    )
    historical_digest = WorkflowInstructionSet.model_validate(
        compile_prompt_workflow(historical_source).instruction_set
    ).digest
    proposal = settings.propose_action_intent_upgrade()
    assert settings.read() == stored
    assert proposal["scope"] == "defaults"
    assert proposal["current_revision"] == stored["revision"]
    assert proposal["current_digest"] == stored["digest"]
    assert proposal["available"] is True
    upgraded = proposal["instructions"]
    assert upgraded["action_intent_contract"] == "wright.workflow-action-intent/1"
    for key in ("policy", "layers", "bindings", "profile_id", "profile_version"):
        assert upgraded[key] == stored["instructions"][key]
    assert (
        upgraded["assets"][: len(stored["instructions"]["assets"])]
        == stored["instructions"]["assets"]
    )
    assert {
        item["id"]
        for item in upgraded["assets"][len(stored["instructions"]["assets"]) :]
    } == {
        "protocol.action-intent",
        "validation.design-check",
        "validation.design-revision",
        "context.expected-files",
        "context.task-workspace",
        "context.mcp-input-completion",
    }
    assert {item["path"] for item in proposal["changes"]} == {
        "action_intent_contract",
        "assets.protocol.action-intent",
        "assets.validation.design-check",
        "assets.validation.design-revision",
        "assets.context.expected-files",
        "assets.context.task-workspace",
        "assets.context.mcp-input-completion",
    }
    applied = settings.replace(upgraded, expected_revision=proposal["current_revision"])
    assert applied["digest"] == proposal["proposed_digest"] != historical_digest
    assert (
        materialize_new_workflow_instructions(
            historical_source, WorkflowInstructionSet.model_validate(upgraded)
        )
        == historical_source
    )
    assert (
        WorkflowInstructionSet.model_validate(
            compile_prompt_workflow(historical_source).instruction_set
        ).digest
        == historical_digest
    )
    assert settings.propose_action_intent_upgrade()["available"] is False


def test_workflow_specific_upgrade_uses_exact_collection_not_global_defaults(settings):
    before = settings.read()
    custom = profile(
        "Exact workflow instructions, different from current defaults."
    ).model_dump(mode="json")
    proposal = settings.propose_action_intent_upgrade(custom)
    assert proposal["scope"] == "workflow" and proposal["current_revision"] is None
    assert proposal["instructions"]["assets"][0] == custom["assets"][0]
    assert settings.read() == before
    assert (
        proposal["current_digest"]
        == WorkflowInstructionSet.model_validate(custom).digest
    )


def test_existing_custom_action_protocol_is_retained_or_incompatible_dependency_rejected(
    settings,
):
    proposed = settings.propose_action_intent_upgrade()["instructions"]
    helper = next(
        item for item in proposed["assets"] if item["id"] == "protocol.action-intent"
    )
    helper["body"] = "Custom model-facing declaration guidance."
    helper["body_digest"] = instruction_text_digest(helper["body"])
    proposed.pop("action_intent_contract")
    upgraded = settings.propose_action_intent_upgrade(proposed)
    assert upgraded["instructions"]["assets"] == proposed["assets"]
    assert len(upgraded["changes"]) == 1
    helper["role"] = "chat"
    with pytest.raises(ValueError, match="action-intent"):
        settings.propose_action_intent_upgrade(proposed)


def test_step_override_requires_portable_collection_and_retains_explicit_policy():
    override = {
        "origin": "step-author",
        "text": "Use centimeters.",
        "assumption_policy": "require_specified",
    }
    original = source(task(instruction_override=override))
    with pytest.raises(
        WorkflowSourceExecutionError, match="embedded workflow instruction"
    ):
        compile_prompt_workflow(original)
    plan = compile_prompt_workflow(
        materialize_new_workflow_instructions(original, profile())
    )
    assert (
        plan.steps[0].instruction_override["assumption_policy"] == "require_specified"
    )


def test_new_source_application_materializes_but_updates_preserve_legacy(settings):
    stored = []

    class Executor:
        async def run_to_completion(self, name, operation):
            return operation()

    class Store:
        def create(self, path, text, **kwargs):
            stored.append(text)
            return SimpleNamespace(source=text)

        def update(self, path, *, source, **kwargs):
            stored.append(source)
            return SimpleNamespace(source=source)

    application = WorkspaceWorkflowSourceUseCases(
        Executor(), lambda _: Store(), instruction_defaults=lambda _: settings.read()
    )
    original = source(task())
    created = asyncio.run(
        application.create("isolated", "workflows/test.workflow.wflow", original)
    )
    assert compile_prompt_workflow(created.source).instruction_set
    updated = asyncio.run(
        application.update(
            "isolated",
            "workflows/legacy.workflow.wflow",
            source=original,
            expected_storage_revision=1,
            expected_storage_digest="a" * 64,
            semantic_change_validated=True,
        )
    )
    assert updated.source == original


def test_saved_instruction_delivery_and_actual_invocations_retained(tmp_path):
    plan = compile_prompt_workflow(
        materialize_new_workflow_instructions(source(task(fmt="text")), profile())
    )
    events = []

    class Result(str):
        pass

    async def generate(
        prompt, fmt, *, instruction_set, instruction_override, invocation_observer
    ):
        assert instruction_set == profile().model_dump(mode="json")
        assert instruction_override is None
        generated = Result("Finished result")
        generated.wright_instructions = (
            profile().resolve("workflow-task").model_dump(mode="json")
        )
        generated.wright_invocations = [
            {"messages": [{"role": "system", "content": "Saved instructions A"}]}
        ]
        await invocation_observer(generated.wright_invocations[0])
        generated.wright_assumptions = [
            {
                "parameter": "length",
                "value": "10",
                "units": "mm",
                "rationale": "Illustrative dimension was unspecified",
                "affected_outputs": ["report_response"],
            }
        ]
        return generated

    async def emit(event):
        events.append(event)

    asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            on_event=emit,
        )
    )
    assert (
        next(event for event in events if event["kind"] == "model_invocation")[
            "invocation"
        ]["messages"][0]["content"]
        == "Saved instructions A"
    )
    assert (
        next(event for event in events if event["kind"] == "assumptions_recorded")[
            "assumptions"
        ][0]["units"]
        == "mm"
    )
