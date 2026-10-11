"""Declared questions are source barriers; an AI question cannot create one."""

import asyncio
import copy
from pathlib import Path

import pytest

from core.process_interactions import validate_response
from workspace_service.process_interfaces.inputs import prepare_inputs
from workspace_service.workflow_source_execution import (
    WorkflowSourceExecutionError,
    _parse,
    compile_prompt_workflow,
    prepare_prompt_workflow,
    validate_workspace_authoring_shape,
)
from workspace_service.workflow_sources import WorkspaceWorkflowSourceStore
from workspace_service.workflow_human_input import validate_human_input_rework
from packages.workspace_service.tests.test_process_input_readiness import (
    application,
    process,
    source as input_source,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section, port


DECLARATION = {
    "version": 1,
    "kind": "input",
    "instructions": "Choose the comparison to carry forward after reviewing the output.",
    "response_schema": {
        "type": "object",
        "properties": {"selection": {"type": "string", "enum": ["a", "b"]}},
        "required": ["selection"],
        "additionalProperties": False,
    },
    "output_port": "choice_response",
}


def human_source():
    text = input_source(
        metadata={
            "version": 1,
            "value_schema": {"type": "string", "minLength": 1},
            "required": True,
            "default": "Compare a and b.",
        }
    )
    text += section(
        "task",
        "choice",
        name="Select comparison",
        purpose="Declared input",
        step_type="work",
        group=None,
        performed_by="engineer",
        inputs=[port("choice_evidence", True)],
        outputs=[{**port("choice_response", True), "kind": "structured_result"}],
        instructions="Review the comparison before selecting.",
        tool=None,
        reusable_step=None,
        settings={
            "authoring_template": "human-input",
            "human_interaction": DECLARATION,
        },
    )
    text += section(
        "task",
        "second",
        name="Use selection",
        purpose="Use declared response",
        step_type="work",
        group=None,
        performed_by="ai_assisted",
        inputs=[{**port("second_input", True), "kind": "structured_result"}],
        outputs=[port("second_output")],
        prompt="Use the supplied selection.",
        tool=None,
        reusable_step=None,
        settings={"output_format": "text", "output_filename": "second.txt"},
    )
    for key, src, dst in (
        ("evidence", "first.first_out", "choice.choice_evidence"),
        ("response", "choice.choice_response", "second.second_input"),
    ):
        text += section(
            "connection",
            key,
            type="item",
            **{"from": src, "to": dst},
            label="Declared dependency",
            when=None,
        )
    return text


def test_shared_browser_and_source_fixture_matches_the_compiled_declaration():
    root = Path(__file__).resolve().parents[3]
    fixture = (
        root
        / "specs/083-process-working-interfaces/fixtures/declared-human-input.workflow.wflow"
    )
    assert fixture.read_text(encoding="utf-8") == human_source()


def test_actual_inspector_saved_source_compiles_with_edited_declarations(tmp_path):
    """Captured from served inspector edits; no manual source normalization."""
    root = Path(__file__).resolve().parents[3]
    text = (
        root
        / "specs/083-process-working-interfaces/fixtures/inspector-edited-human-input.workflow.wflow"
    ).read_text(encoding="utf-8")
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    saved = store.create("workflows/inspector.workflow.wflow", text)
    loaded = store.read(saved.path)
    assert loaded.source == text
    plan = compile_prompt_workflow(loaded.source)
    human = next(step for step in plan.steps if step.id == "choice")
    assert (
        human.human_interaction["instructions"]
        == "Review both measured comparison outputs before selecting."
    )
    assert human.human_interaction["response_schema"]["properties"]["selection"][
        "enum"
    ] == ["a", "b", "c"]
    assert human.human_interaction["output_port"] == "choice_response"
    assert human.references == (("choice_evidence", "first.first_out"),)
    assert not human.prompt and not human.human_review and human.external_action is None
    prepared = asyncio.run(
        prepare_inputs(
            service=application(tmp_path, text),
            workspace_dir=str(tmp_path),
            process=process(text),
            source=loaded.source,
        )
    )
    assert prepared.values == {"brief": "Compare a and b after editing."}
    assert not prepared.reasons
    dependency = next(
        item
        for item in prepared.dependencies
        if item.binding_id == "second.second_input"
    )
    assert dependency.classification == "declared_human_response"
    assert dependency.interaction_step == "choice"
    validate_response(human.human_interaction["response_schema"], {"selection": "c"})


def changed_source(change):
    blocks = _parse(human_source())
    change(blocks)
    return "".join(section(b["kind"], b["id"], **b["fields"]) for b in blocks)


def change_choice(mutator):
    return changed_source(
        lambda blocks: mutator(next(b["fields"] for b in blocks if b["id"] == "choice"))
    )


def test_declared_input_round_trips_existing_source_storage_and_compiler(tmp_path):
    source = human_source()
    validate_workspace_authoring_shape(source)
    store = WorkspaceWorkflowSourceStore(str(tmp_path))
    saved = store.create("workflows/human-input.workflow.wflow", source)
    loaded = store.read(saved.path)
    assert loaded.source == source
    plan = compile_prompt_workflow(loaded.source)
    assert [step.id for step in plan.steps] == ["first", "choice", "second"]
    step = plan.steps[1]
    assert step.human_interaction == DECLARATION
    assert step.output_ports == (("choice_response", "structured_result"),)
    assert step.references == (("choice_evidence", "first.first_out"),)
    assert not step.prompt and not step.save and not step.tool_name
    assert not step.human_review and step.external_action is None
    # Re-serialization uses the existing JSON-valued grammar, with no new parser.
    normalized = "".join(
        section(b["kind"], b["id"], **b["fields"]) for b in _parse(source)
    )
    assert compile_prompt_workflow(normalized).steps[1] == step


@pytest.mark.parametrize(
    "key,value",
    [
        ("version", 4),
        ("version", True),
        ("kind", "approval"),
        ("instructions", "  "),
        ("instructions", "x" * 8001),
        ("output_port", "missing"),
        ("response_schema", {"type": "string"}),
        ("response_schema", {"type": "object", "$ref": "https://example.com/schema"}),
        (
            "response_schema",
            {"type": "object", "patternProperties": {".*": {"type": "string"}}},
        ),
        (
            "response_schema",
            {"type": "object", "$defs": {"loop": {"$ref": "#/$defs/loop"}}},
        ),
        ("unknown_field", "no implicit instruction channel"),
    ],
)
def test_rejects_unsupported_declarations(key, value):
    text = change_choice(
        lambda fields: fields["settings"]["human_interaction"].update({key: value})
    )
    with pytest.raises(WorkflowSourceExecutionError) as caught:
        compile_prompt_workflow(text)
    assert caught.value.code == "WORKFLOW_NOT_READY"
    assert caught.value.correction


@pytest.mark.parametrize(
    "key,value",
    [
        ("performed_by", "ai_assisted"),
        ("step_type", "review"),
        ("tool", "ask_user"),
        ("reusable_step", "another_runner"),
        ("prompt", "Please choose something"),
        ("outputs", []),
        ("outputs", [port("choice_response")]),
        (
            "outputs",
            [
                {
                    **port("choice_response"),
                    "kind": "structured_result",
                    "quantity": "many",
                }
            ],
        ),
    ],
)
def test_rejects_implicit_prompts_execution_bindings_and_ambiguous_outputs(key, value):
    text = change_choice(lambda fields: fields.update({key: value}))
    with pytest.raises(WorkflowSourceExecutionError):
        compile_prompt_workflow(text)


def test_declaration_on_unattended_template_is_not_a_checkpoint():
    text = change_choice(
        lambda fields: fields["settings"].update(authoring_template="ai-prompt")
    )
    with pytest.raises(WorkflowSourceExecutionError, match="human-input template"):
        compile_prompt_workflow(text)


def test_a_preparation_input_cannot_masquerade_as_a_runtime_barrier():
    def mutate(blocks):
        next(b["fields"] for b in blocks if b["id"] == "brief")["settings"][
            "human_interaction"
        ] = DECLARATION

    with pytest.raises(WorkflowSourceExecutionError, match="must be a task barrier"):
        compile_prompt_workflow(changed_source(mutate))


def test_order_only_input_has_no_connected_evidence():
    def mutate(blocks):
        next(b["fields"] for b in blocks if b["id"] == "evidence").update(
            type="order",
            **{"from": "first", "to": "choice"},
        )

    with pytest.raises(
        WorkflowSourceExecutionError, match="connected upstream evidence"
    ):
        compile_prompt_workflow(changed_source(mutate))


def test_a_declared_input_cannot_hide_an_extra_tool_binding():
    text = change_choice(
        lambda fields: fields["settings"].update(mcp_server="unexpected")
    )
    with pytest.raises(WorkflowSourceExecutionError) as caught:
        compile_prompt_workflow(text)
    assert "remove AI prompts, tools" in caught.value.correction


def test_every_required_evidence_port_must_have_a_producer():
    text = change_choice(
        lambda fields: fields["inputs"].append(port("missing_evidence", True))
    )
    with pytest.raises(
        WorkflowSourceExecutionError, match="connected upstream evidence"
    ):
        compile_prompt_workflow(text)


def test_multiple_response_outputs_are_not_a_supported_barrier():
    text = change_choice(
        lambda fields: fields["outputs"].append(
            {**port("ambiguous_response"), "kind": "structured_result"},
        )
    )
    with pytest.raises(WorkflowSourceExecutionError, match="one structured response"):
        compile_prompt_workflow(text)


def test_conditional_human_response_does_not_extend_the_supported_graph():
    text = changed_source(
        lambda blocks: next(
            b["fields"] for b in blocks if b["id"] == "response"
        ).update(when="selected")
    )
    with pytest.raises(WorkflowSourceExecutionError, match="conditional or control"):
        compile_prompt_workflow(text)


def test_automatic_corrections_cannot_replay_a_declared_answer():
    plan = compile_prompt_workflow(human_source())
    with pytest.raises(WorkflowSourceExecutionError, match="cannot replay"):
        validate_human_input_rework(plan.steps, {"second": "first"})
    # The ordinary rework validator retains authority over all other conditions.
    validate_human_input_rework(plan.steps, {"second": "second"})


def test_schema_checks_response_without_inventing_default():
    schema = copy.deepcopy(DECLARATION["response_schema"])
    validate_response(schema, {"selection": "a"})
    for invalid in ({}, {"selection": "c"}, {"selection": "a", "extra": True}):
        with pytest.raises(ValueError):
            validate_response(schema, invalid)
    assert "default" not in schema


def test_readiness_distinguishes_planned_human_response_from_ordinary_production(
    tmp_path,
):
    text = human_source()
    prepared = asyncio.run(
        prepare_inputs(
            service=application(tmp_path, text),
            workspace_dir=str(tmp_path),
            process=process(text),
            source=text,
        )
    )
    dependencies = {item.binding_id: item for item in prepared.dependencies}
    assert dependencies["choice.choice_evidence"].classification == "upstream_produced"
    response = dependencies["second.second_input"]
    assert response.classification == "declared_human_response"
    assert response.interaction_step == "choice"
    assert response.producer_port == "choice_response"
    assert not prepared.reasons
    assert {binding.input_id for binding in prepared.snapshot.bindings} == {"brief"}


def test_unavailable_continuation_blocks_before_any_execution_or_tool_qualification(
    tmp_path,
):
    text = human_source()
    app = application(tmp_path, text)

    def forbidden_tools():
        raise AssertionError(
            "No tool qualification before a missing runtime capability"
        )

    with pytest.raises(WorkflowSourceExecutionError) as caught:
        asyncio.run(
            prepare_prompt_workflow(
                service=app,
                workspace_dir=str(tmp_path),
                path=process(text).source_path,
                expected_digest=process(text).source_digest,
                tool_runtime=forbidden_tools,
            )
        )
    assert caught.value.code == "WORKFLOW_HUMAN_INPUT_UNAVAILABLE"
