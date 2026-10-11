"""Runner behavior travels with accepted source, including after a declared wait."""

import asyncio
from dataclasses import asdict, replace
import hashlib
import json
from types import SimpleNamespace

import pytest

from agent_adapters import workflow_instructions as resources
from core.process_interactions import InputSnapshot, ProcessRef
from core.workflow_instructions import WorkflowInstructionSet, instruction_text_digest
from packages.workspace_service.tests.test_process_first_human_input import (
    first_input_source,
)
from packages.workspace_service.tests.test_workflow_artifact_review import section
from packages.workspace_service.tests.test_workflow_design_check import (
    FakeCad,
    plan as design_plan,
    report,
)
from packages.workspace_service.tests.test_workflow_external_action_execution import (
    service as interaction_service,
)
from packages.workspace_service.tests.test_workflow_source_execution import service
from workspace_service.process_interfaces import ProcessInterfaceService
from workspace_service.workflow_instruction_settings import (
    materialize_new_workflow_instructions,
)
from workspace_service.workflow_run_record import (
    record_workflow_run,
    record_workflow_resume,
)
from workspace_service.workflow_source_execution import (
    _parse,
    compile_prompt_workflow,
    execute_prompt_workflow,
)


def captured_profile():
    raw = resources.load_default_workflow_instructions().model_dump(mode="json")
    bodies = {
        "validation.design-check": "SAVED DESIGN CHECK INSTRUCTIONS",
        "validation.design-revision": "SAVED CORRECTION FRAME\n{{feedback}}",
        "context.expected-files": "SAVED EXPECTED FILES: {{files}}",
        "context.task-workspace": "SAVED WORKSPACE: {{workspace_dir}}",
    }
    for asset in raw["assets"]:
        if asset["id"] in bodies:
            asset["body"] = bodies[asset["id"]]
            asset["body_digest"] = instruction_text_digest(asset["body"])
    return WorkflowInstructionSet.model_validate(raw)


@pytest.mark.parametrize("identity", resources.WORKFLOW_HELPER_CONTRACTS)
def test_missing_saved_helper_never_reads_new_packaged_body(monkeypatch, identity):
    raw = captured_profile().model_dump(mode="json")
    raw["assets"] = [item for item in raw["assets"] if item["id"] != identity]
    monkeypatch.setattr(
        resources,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Read defaults for accepted source"),
    )
    with pytest.raises(ValueError, match="missing " + identity):
        resources.validate_workflow_helper_instructions(raw, identity)


@pytest.mark.parametrize("identity", resources.WORKFLOW_HELPER_CONTRACTS)
@pytest.mark.parametrize("change", ["role", "variables"])
def test_saved_helpers_require_their_declared_contract(identity, change):
    raw = captured_profile().model_dump(mode="json")
    asset = next(item for item in raw["assets"] if item["id"] == identity)
    if change == "role":
        asset["role"] = "recovery"
    else:
        asset["variables"] = ["unexpected"]
    with pytest.raises(ValueError):
        resources.validate_workflow_helper_instructions(raw, identity)


def test_design_feedback_preserves_exact_evidence_and_enforces_inline_budget(
    monkeypatch,
):
    saved = captured_profile()
    feedback = report("revise")
    monkeypatch.setattr(
        resources,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Read defaults"),
    )
    actual = resources.workflow_design_revision_feedback(
        feedback, instruction_set=saved
    )
    assert actual.startswith("SAVED CORRECTION FRAME\n")
    assert json.loads(actual.split("\n", 1)[1]) == feedback
    with pytest.raises(ValueError, match="16 KiB"):
        resources.workflow_design_revision_feedback(
            {"corrections": ["x" * 17000]}, instruction_set=saved
        )


def test_saved_custom_check_and_revision_frames_are_used_by_existing_scheduler(
    monkeypatch, tmp_path
):
    saved = captured_profile().model_dump(mode="json")
    original = design_plan()
    plan = replace(
        original,
        instruction_set=saved,
        steps=tuple(replace(step, instruction_set=saved) for step in original.steps),
    )
    prompts, checks = [], iter(["revise", "pass"])
    monkeypatch.setattr("workspace_service.workflow_cad.CadTask", FakeCad)
    monkeypatch.setattr(
        resources,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Read new defaults"),
    )

    async def run_task(step, prompt, *args, **kwargs):
        prompts.append((step.id, prompt))
        return (json.dumps(report(next(checks))) if step.design_check else "Created"), [
            {"status": "succeeded"}
        ]

    async def generate(*args, **kwargs):
        return "Quote handoff"

    result = asyncio.run(
        execute_prompt_workflow(
            service=service(tmp_path),
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=generate,
            tool_runtime=SimpleNamespace(run_task=run_task),
            action_generator=lambda: None,
        )
    )
    assert result["revision_attempts"]
    assert "SAVED DESIGN CHECK INSTRUCTIONS" in prompts[1][1]
    assert "SAVED CORRECTION FRAME" in prompts[2][1]
    assert "SAVED WORKSPACE" in prompts[0][1]
    assert "Never turn absent measurements" not in prompts[1][1]
    assert "preserving satisfied requirements" not in prompts[2][1]


def test_declared_wait_recreation_resumes_same_source_with_saved_workspace_and_file_frames(
    monkeypatch, tmp_path
):
    saved = captured_profile()
    blocks = _parse(first_input_source())
    fields = next(item["fields"] for item in blocks if item["id"] == "report")
    fields["settings"].update(
        authoring_template="mcp-task", mcp_server="docs", expected_files="notes.txt"
    )
    text = materialize_new_workflow_instructions(
        "".join(section(item["kind"], item["id"], **item["fields"]) for item in blocks),
        saved,
    )
    path = tmp_path / "workflows/helper-resume.wflow"
    path.parent.mkdir()
    path.write_text(text, encoding="utf-8")
    app = interaction_service(tmp_path)
    app.db_path = str(tmp_path / "state.db")
    app.process_interfaces = ProcessInterfaceService(app)
    frozen = InputSnapshot.create(
        snapshot_id="helper-inputs",
        process=ProcessRef(
            workspace_id="ws",
            source_path="workflows/helper-resume.wflow",
            source_digest=hashlib.sha256(text.encode()).hexdigest(),
        ),
        created_at="2026-10-08T12:00:00Z",
        bindings=(),
    )
    app.process_interfaces.inputs.put_snapshot(frozen)
    plan = replace(
        compile_prompt_workflow(text),
        definition_digest=frozen.process.source_digest,
        input_snapshot=frozen,
    )
    calls = []

    async def run_task(step, prompt, *args, **kwargs):
        calls.append(prompt)
        assert (
            "SAVED WORKSPACE" in prompt and "SAVED EXPECTED FILES: notes.txt" in prompt
        )
        await app.files.write_generated(
            str(tmp_path), "notes.txt", "Synthetic transport fixture", "indexed"
        )
        return "Synthetic completed report", [{"status": "succeeded"}]

    async def execute(emit, checkpoint=None):
        return await execute_prompt_workflow(
            service=app,
            workspace_dir=str(tmp_path),
            plan=plan,
            input_values={},
            response_generator=None,
            tool_runtime=SimpleNamespace(run_task=run_task),
            action_generator=lambda: None,
            on_event=emit,
            run_id="helper-same-run",
            continuation=checkpoint.continuation if checkpoint else None,
            completed_checkpoint=asdict(checkpoint) if checkpoint else None,
        )

    first = asyncio.run(
        record_workflow_run(
            service=app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            source_path=frozen.process.source_path,
            source_digest=plan.definition_digest,
            execute=execute,
            run_id="helper-same-run",
            required_step_ids=[step.id for step in plan.steps],
        )
    )
    assert first["status"] == "waiting_human" and calls == []
    owner = app.process_interfaces.human_inputs
    checkpoint = owner.get(
        first["input_checkpoint"]["checkpoint_id"],
        workspace_id="ws",
        run_id="helper-same-run",
    )
    _, answer, _ = owner.respond(
        checkpoint.checkpoint_id,
        workspace_id="ws",
        run_id="helper-same-run",
        expected_subject_digest=checkpoint.subject_digest,
        value={"selection": "a"},
        actor="integration_test:helper-resume",
        reason="Synthetic unit-test input, not engineering approval.",
        request_id="helper-answer",
        integration_test=True,
    )
    app = interaction_service(tmp_path)
    app.db_path = str(tmp_path / "state.db")
    app.process_interfaces = ProcessInterfaceService(app)
    monkeypatch.setattr(
        resources,
        "load_default_workflow_instructions",
        lambda: pytest.fail("Read changed defaults while resuming"),
    )
    plan = replace(
        compile_prompt_workflow(path.read_text(encoding="utf-8")),
        definition_digest=frozen.process.source_digest,
        input_snapshot=frozen,
    )
    consumed = app.process_interfaces.human_inputs.consume(
        checkpoint.checkpoint_id,
        workspace_id="ws",
        run_id="helper-same-run",
        response_id=answer.response_id,
    )
    final = asyncio.run(
        record_workflow_resume(
            service=app,
            workspace_dir=str(tmp_path),
            workspace_id="ws",
            checkpoint=consumed,
            execute=lambda emit: execute(emit, consumed),
        )
    )
    assert final["status"] == "completed" and final["run_id"] == first["run_id"]
    assert final["run_log_path"] == first["run_log_path"] and len(calls) == 1
    assert (tmp_path / "notes.txt").read_text() == "Synthetic transport fixture"
