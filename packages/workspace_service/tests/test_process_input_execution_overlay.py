"""Frozen inputs reach the existing source runtime without accepted-source edits."""

import pytest

from core.process_interactions import ValueBinding
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.inputs import prepare_inputs
from workspace_service.process_interfaces import inputs as input_owner
from workspace_service.workflow_source_execution import (
    prepare_prompt_workflow,
    execute_prompt_workflow,
)
from packages.workspace_service.tests.test_process_input_readiness import (
    application,
    process,
    source,
)


@pytest.mark.asyncio
async def test_existing_preparation_and_execution_use_overlay_and_same_run(tmp_path):
    text = source(default="Source default")
    app = application(tmp_path, text)
    prepared = await prepare_inputs(
        service=app,
        workspace_dir=str(tmp_path),
        process=process(text),
        source=text,
        bindings=(
            ValueBinding(input_id="brief", value="Frozen requirements for this run"),
        ),
    )
    plan, values = await prepare_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        workspace_id="workspace",
        path=process(text).source_path,
        expected_digest=process(text).source_digest,
        input_snapshot=prepared.snapshot,
    )
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Result from the ordinary source executor"

    result = await execute_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        plan=plan,
        input_values=values,
        response_generator=generate,
        run_id="retained-run",
    )
    assert result["run_id"] == "retained-run"
    assert "Frozen requirements for this run" in calls[0]
    assert "Source default" not in calls[0]
    assert (
        tmp_path / "first.txt"
    ).read_text() == "Result from the ordinary source executor"


@pytest.mark.asyncio
async def test_optional_omission_executes_without_a_synthetic_value(tmp_path):
    text = source(
        metadata={"version": 1, "value_schema": {"type": "string"}, "required": False},
        required=False,
    )
    app = application(tmp_path, text)
    prepared = await prepare_inputs(
        service=app, workspace_dir=str(tmp_path), process=process(text), source=text
    )
    plan, values = await prepare_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        workspace_id="workspace",
        path=process(text).source_path,
        expected_digest=process(text).source_digest,
        input_snapshot=prepared.snapshot,
    )
    assert not values

    async def generate(prompt, fmt):
        assert prompt == "Prepare a result"
        return "Result"

    result = await execute_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        plan=plan,
        input_values=values,
        response_generator=generate,
    )
    assert (tmp_path / "first.txt").read_text() == "Result"
    assert result["run_id"]


@pytest.mark.asyncio
async def test_wrong_workspace_snapshot_rejects_before_tool_preflight(tmp_path):
    text = source(default="Explicit default")
    app = application(tmp_path, text)
    prepared = await prepare_inputs(
        service=app, workspace_dir=str(tmp_path), process=process(text), source=text
    )
    with pytest.raises(ProcessInterfaceError) as error:
        await prepare_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            workspace_id="other",
            path=process(text).source_path,
            expected_digest=process(text).source_digest,
            input_snapshot=prepared.snapshot,
        )
    assert error.value.reason.code == "SCOPE_DENIED"


@pytest.mark.asyncio
async def test_source_metadata_defaults_are_not_ignored_by_legacy_request(tmp_path):
    text = source(
        metadata={
            "version": 1,
            "value_schema": {"type": "integer", "minimum": 1},
            "default": 3,
        }
    )
    app = application(tmp_path, text)
    _, values = await prepare_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        workspace_id="workspace",
        path=process(text).source_path,
        expected_digest=process(text).source_digest,
    )
    assert values == {"brief": 3}


@pytest.mark.asyncio
async def test_only_later_required_choice_blocks_before_first_generation(tmp_path):
    text = source(later=True, late_root=True, required=False)
    app = application(tmp_path, text)
    prepared = await prepare_inputs(
        service=app, workspace_dir=str(tmp_path), process=process(text), source=text
    )
    assert input_owner.input_readiness(prepared).state == "blocked"
    assert prepared.plan.steps[0].references == ()
    with pytest.raises(ProcessInterfaceError) as error:
        await prepare_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            workspace_id="workspace",
            path=process(text).source_path,
            expected_digest=process(text).source_digest,
            input_snapshot=prepared.snapshot,
        )
    assert error.value.reason.code == "INPUT_REQUIRED"
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_boolean_input_keeps_type_and_renders_canonical_json_for_llm(tmp_path):
    text = source(
        metadata={"version": 1, "value_schema": {"type": "boolean"}, "default": False}
    )
    app = application(tmp_path, text)
    prepared = await prepare_inputs(
        service=app, workspace_dir=str(tmp_path), process=process(text), source=text
    )
    plan, values = await prepare_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        workspace_id="workspace",
        path=process(text).source_path,
        expected_digest=process(text).source_digest,
        input_snapshot=prepared.snapshot,
    )
    assert values["brief"] is False
    prompts = []

    async def generate(prompt, fmt):
        prompts.append(prompt)
        return "Result"

    await execute_prompt_workflow(
        service=app,
        workspace_dir=str(tmp_path),
        plan=plan,
        input_values=values,
        response_generator=generate,
    )
    assert "false" in prompts[0]
    assert "False" not in prompts[0]


@pytest.mark.asyncio
async def test_changed_snapshot_digest_has_a_safe_boundary_error(tmp_path):
    text = source(default="Default")
    app = application(tmp_path, text)
    prepared = await prepare_inputs(
        service=app, workspace_dir=str(tmp_path), process=process(text), source=text
    )
    invalid = prepared.snapshot.model_copy(update={"digest": "0" * 64})
    with pytest.raises(ProcessInterfaceError) as error:
        await prepare_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            workspace_id="workspace",
            path=process(text).source_path,
            expected_digest=process(text).source_digest,
            input_snapshot=invalid,
        )
    assert error.value.reason.code == "RESPONSE_INVALID"
