import asyncio
import json
from types import SimpleNamespace

import pytest
from starlette.requests import Request

from api.routers import workspace as router
from api.schemas.workspace import WorkflowSourceRunRequest
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases
from workspace_service.workflow_run_record import recent_workflow_runs
from packages.workspace_service.tests.test_workflow_artifact_review import section, port


@pytest.mark.parametrize("checkpoint_times_out", [False, True])
def test_disconnect_drains_real_file_checkpoint_without_recancelling_producer(
    tmp_path, monkeypatch, checkpoint_times_out
):
    if checkpoint_times_out:
        monkeypatch.setattr(
            "workspace_service.workflow_run_record._FINAL_CHECKPOINT_SECONDS", 0.1
        )
    text = section(
        "workflow",
        "disconnect",
        name="Disconnect control",
        purpose="Controlled cancellation",
        discipline="engineering",
        reviewed_ai_suggestions=False,
    )
    for key, fmt in [("first", "text"), ("second", "html")]:
        settings = {
            "output_format": fmt,
            "save_output": True,
            "file_policy": "indexed",
            "output_filename": key + (".txt" if fmt == "text" else ".html"),
        }
        if key == "second":
            settings.update(prompt_source="connection", prompt_input="second_prompt")
        text += section(
            "task",
            key,
            name=key,
            purpose="Controlled task",
            step_type="work",
            group=None,
            tool=None,
            reusable_step=None,
            performed_by="ai_assisted",
            prompt="Write a report",
            inputs=[port(key + "_prompt")],
            outputs=[port(key + "_response")],
            settings=settings,
        )
    text += section(
        "connection",
        "edge",
        type="item",
        **{"from": "first.first_response", "to": "second.second_prompt"},
        label="Prompt",
        when=None,
    )
    path = "workflows/disconnect.workflow.wflow"

    async def scenario():
        executor = BoundedExecutor(max_workers=1)
        svc = SimpleNamespace(
            files=WorkspaceFileUseCases(
                str(tmp_path / "unused.db"), executor, LocalWorkspaceFiles
            ),
            workflow_sources=WorkspaceWorkflowSourceUseCases(executor),
            lifecycle=SimpleNamespace(
                get_by_session=lambda _: {
                    "workspace_id": "controlled",
                    "local_path": str(tmp_path),
                }
            ),
            ensure_workspace_path_safe=lambda value: value,
        )
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def generate(prompt, fmt):
            if fmt == "text":
                return "Completed first task"
            # Saturated real executor: the cancellation checkpoint must wait for
            # capacity, then use the real atomic filesystem publication path.
            await executor._capacity.acquire()
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        monkeypatch.setattr(router, "generate_workflow_response", generate)
        saved = await svc.workflow_sources.create(str(tmp_path), path, text)
        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "headers": [(b"accept", b"application/x-ndjson")],
        }
        response = await router.run_workflow_source_endpoint(
            WorkflowSourceRunRequest(
                session_id="s", path=path, expected_storage_digest=saved.storage_digest
            ),
            Request(scope),
            svc,
        )
        sent = []

        async def receive():
            await started.wait()
            asyncio.get_running_loop().call_later(
                0.25 if checkpoint_times_out else 0.05, executor._capacity.release
            )
            return {"type": "http.disconnect"}

        async def send(message):
            sent.append(message)

        try:
            async with asyncio.timeout(2):
                await response(scope, receive, send)
            assert cancelled.is_set(), "Actual model execution must cancel immediately"
            raw = json.loads(
                next((tmp_path / "runs/disconnect").glob("*.json")).read_text()
            )
            assert raw["status"] == ("running" if checkpoint_times_out else "cancelled")
            if not checkpoint_times_out:
                assert raw["execution_ended_at"] == raw["completed_at"]
                assert raw["completed_at"]
            assert not any(
                event["kind"] == "step_completed" and event.get("task_id") == "second"
                for event in raw["events"]
            )
            assert (tmp_path / "first.txt").read_text() == "Completed first task"
            assert not (tmp_path / "second.html").exists()
            assert recent_workflow_runs(tmp_path, path)[0]["status"] == (
                "interrupted" if checkpoint_times_out else "cancelled"
            )
            assert not any(
                b'"kind": "completed"' in item.get("body", b"") for item in sent
            )
        finally:
            await executor.close()

    asyncio.run(scenario())
