import asyncio
import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from agent_adapters.desktop_reasoning import DesktopWorkflowReasoner
from agent_adapters.workflow_instructions import load_default_workflow_instructions
from core.desktop_reasoning import DesktopHarnessBinding, DesktopReasoningResponse
from data_vault.desktop_reasoning_repository import (
    DesktopHandoffConflict,
    DesktopReasoningRepository,
)
from workspace_service.workflow_instruction_settings import (
    materialize_new_workflow_instructions,
)
from workspace_service.workflow_model_routing import freeze_workflow_model_routing
from workspace_service.workflow_reasoning_dispatch import (
    WorkflowReasoningCallbacks,
    resolve_workflow_reasoning_callbacks,
)
from workspace_service.workflow_source_execution import (
    compile_prompt_workflow,
    execute_prompt_workflow,
    WorkflowSourceExecutionError,
)
from packages.workspace_service.tests.test_workflow_source_execution import (
    task,
    source,
    service,
)


def reasoner(repo, **patch):
    return DesktopWorkflowReasoner(
        repo,
        workspace_id="workspace-1",
        session_id="session-1",
        run_id="run-1",
        binding=DesktopHarnessBinding(connection_id="connection-1", **patch),
        poll_interval=0.005,
    )


async def pending(repo):
    async def wait():
        while True:
            tasks = repo.pending("workspace-1", "session-1")
            if tasks:
                return tasks[0]
            await asyncio.sleep(0.005)

    return await asyncio.wait_for(wait(), 5)


def answer(repo, request, value):
    return repo.submit_response(
        "workspace-1",
        "session-1",
        DesktopReasoningResponse(
            request_id=request.request_id,
            request_digest=request.digest,
            binding_digest=request.binding.digest,
            response_id=str(uuid4()),
            received_at=datetime.now(timezone.utc).isoformat(),
            reply=json.dumps(
                {
                    "version": "wright.unattended-step/1",
                    "status": "completed",
                    "reason": None,
                    "response": value,
                }
            ),
        ),
    )


def test_existing_executor_accepts_scoped_reply_with_saved_instructions_and_frozen_binding(
    tmp_path, monkeypatch
):
    import httpx

    def no_model_service(*args, **kwargs):
        raise AssertionError("This callback must not use an HTTP model service")

    monkeypatch.setattr(httpx, "AsyncClient", no_model_service)
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    accepted = materialize_new_workflow_instructions(
        source(task(fmt="text")), load_default_workflow_instructions()
    )
    plan = compile_prompt_workflow(accepted)
    app = service(tmp_path)
    app.workflow_model_capabilities = desktop.capabilities

    def bind_run(**scope):
        assert scope["workspace_dir"] == str(tmp_path)
        assert scope["run_id"] == "run-1"
        assert scope["execution_context"]["model_routing"][
            "text"
        ] == desktop.resolution().model_dump(mode="json")
        return WorkflowReasoningCallbacks(
            desktop.generate_response, desktop.decide_action
        )

    app.workflow_reasoning_factory = bind_run

    async def forbidden_fallback(*args, **kwargs):
        raise AssertionError("Desktop work must not use a legacy model callback")

    events = []

    async def run():
        frozen, context = await freeze_workflow_model_routing(app, plan, {})

        async def emit(event):
            events.append(event)

        running = asyncio.create_task(
            execute_prompt_workflow(
                service=app,
                workspace_dir=str(tmp_path),
                plan=frozen,
                input_values={},
                response_generator=forbidden_fallback,
                execution_context=context,
                on_event=emit,
                run_id="run-1",
            )
        )
        request = await pending(repo)
        assert request.binding.reported_model is None
        assert (
            request.instruction_set_digest
            == load_default_workflow_instructions().digest
        )
        assert request.payload["messages"][0]["role"] == "system"
        assert request.payload["tools"] == []
        answer(repo, request, "A verified callback test result")
        return await asyncio.wait_for(running, 10)

    result = asyncio.run(run())
    assert result["outputs"][0]["output_path"] == "report.txt"
    assert (tmp_path / "report.txt").read_text() == "A verified callback test result"
    scopes = {
        e["invocation"]["capture_scope"]
        for e in events
        if e["kind"] == "model_invocation"
    }
    assert "desktop_handoff_request" in scopes
    assert "desktop_handoff_response_receipt" in scopes


def test_missing_desktop_dispatch_cannot_use_legacy_callback(tmp_path):
    desktop = reasoner(DesktopReasoningRepository(tmp_path / "wright.sqlite"))
    with pytest.raises(ValueError, match="no bound reasoning callback"):
        resolve_workflow_reasoning_callbacks(
            service(tmp_path),
            workspace_dir=str(tmp_path),
            run_id="run-1",
            execution_context={
                "model_routing": {"text": desktop.resolution().model_dump(mode="json")}
            },
            response=lambda *_: "A silent fallback",
            action=None,
        )


def test_frozen_binding_drift_blocks_before_another_request(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    first = reasoner(repo)
    second = reasoner(repo, requested_model="different-selection")
    plan = compile_prompt_workflow(source(task(fmt="text")))
    app = service(tmp_path)

    async def run():
        app.workflow_model_capabilities = first.capabilities
        _, context = await freeze_workflow_model_routing(app, plan, {})
        app.workflow_model_capabilities = second.capabilities
        with pytest.raises(WorkflowSourceExecutionError) as changed:
            await freeze_workflow_model_routing(app, plan, {}, expected_context=context)
        assert changed.value.code == "WORKFLOW_MODEL_CHANGED"
        with pytest.raises(ValueError, match="frozen desktop binding changed"):
            await second.generate_response(
                "Task",
                "text",
                expected_resolution=first.resolution().model_dump(mode="json"),
            )

    asyncio.run(run())
    assert repo.pending("workspace-1", "session-1") == []


def test_invalid_json_fails_existing_validator_and_writes_no_output(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    plan = compile_prompt_workflow(source(task(fmt="json")))

    async def run():
        running = asyncio.create_task(
            execute_prompt_workflow(
                service=service(tmp_path),
                workspace_dir=str(tmp_path),
                plan=plan,
                input_values={},
                response_generator=desktop.generate_response,
                run_id="run-1",
            )
        )
        request = await pending(repo)
        answer(repo, request, "not a JSON document")
        with pytest.raises(WorkflowSourceExecutionError):
            await running

    asyncio.run(run())
    assert not (tmp_path / "report.json").exists()


def test_cancellation_retains_receipt_and_denies_late_answer(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)

    async def run():
        running = asyncio.create_task(desktop.generate_response("Task", "text"))
        request = await pending(repo)
        running.cancel()
        with pytest.raises(asyncio.CancelledError):
            await running
        assert (
            repo.get_request("workspace-1", "session-1", request.request_id) == request
        )
        with pytest.raises(DesktopHandoffConflict):
            answer(repo, request, "Late response")

    asyncio.run(run())


def test_unqualified_image_capability_is_explicit_and_creates_no_request(tmp_path):
    repo = DesktopReasoningRepository(tmp_path / "wright.sqlite")
    desktop = reasoner(repo)
    with pytest.raises(ValueError, match="not qualified"):
        asyncio.run(
            desktop.generate_response(
                "Task", "text", images=["data:image/png;base64,ignored"]
            )
        )
    assert repo.pending("workspace-1", "session-1") == []
