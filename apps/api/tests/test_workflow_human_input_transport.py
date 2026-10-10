"""The diagram's compatibility transport observes the existing input supervisor."""

import json
from types import SimpleNamespace

import pytest
from starlette.requests import Request

from api.routers import workspace as router
from api.schemas.workspace import WorkflowSourceRunRequest
from core.process_interactions import ProcessRef
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.executor import BoundedExecutor
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.service import ProcessScope
from workspace_service.use_cases.files import WorkspaceFileUseCases
from workspace_service.workflow_sources import WorkspaceWorkflowSourceUseCases
from apps.api.tests.process_interface_fixtures import bind_process_interfaces
from packages.workspace_service.tests.test_process_human_input_source import (
    human_source,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("stream", [False, True])
async def test_compatibility_run_wait_preserves_checkpoint_and_resumes_same_run(
    tmp_path, monkeypatch, stream
):
    executor = BoundedExecutor(max_workers=1)
    service = SimpleNamespace(
        files=WorkspaceFileUseCases(
            str(tmp_path / "state.db"), executor, LocalWorkspaceFiles
        ),
        workflow_sources=WorkspaceWorkflowSourceUseCases(executor),
        lifecycle=SimpleNamespace(
            get_by_session=lambda _: {
                "workspace_id": "workspace",
                "local_path": str(tmp_path),
            }
        ),
        ensure_workspace_path_safe=lambda value: value,
    )
    bind_process_interfaces(service, tmp_path, "workspace")
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Synthetic input-transport test output"

    monkeypatch.setattr(router, "generate_workflow_response", generate)
    path = "workflows/input-transport.workflow.wflow"
    saved = await service.workflow_sources.create(str(tmp_path), path, human_source())
    reference = ProcessRef(
        workspace_id="workspace", source_path=path, source_digest=saved.storage_digest
    )
    scope = ProcessScope(
        "local-control-plane",
        "workspace",
        frozenset({"process.read", "process.respond"}),
    )
    try:
        response = await router.run_workflow_source_endpoint(
            WorkflowSourceRunRequest(
                session_id="session",
                path=path,
                expected_storage_digest=saved.storage_digest,
            ),
            Request(
                {
                    "type": "http",
                    "headers": [(b"accept", b"application/x-ndjson")] if stream else [],
                }
            ),
            service,
        )
        if stream:
            chunks = [chunk async for chunk in response.body_iterator]
            events = [json.loads(line) for line in "".join(chunks).splitlines()]
            assert not any(event["kind"] == "failed" for event in events)
            assert any(event["kind"] == "input_requested" for event in events)
            assert events[-1]["kind"] == "waiting_human"
            result = events[-1]["result"]
        else:
            result = response.model_dump()
        assert result["status"] == "waiting_human"
        checkpoint = result["input_checkpoint"]
        assert checkpoint["run_id"] == result["run_id"]
        assert checkpoint["action_kind"] == "human_input"
        assert checkpoint["subject"]["declaration"]["response_schema"]["required"] == [
            "selection"
        ]
        assert checkpoint["subject"]["definition_digest"] == saved.storage_digest
        assert len(calls) == 1

        with pytest.raises(ProcessInterfaceError):
            await service.process_interfaces.runs.respond(
                scope,
                reference,
                checkpoint["checkpoint_id"],
                "invalid-answer",
                expected_subject_digest=checkpoint["subject_digest"],
                value={"selection": "invalid"},
                response_generator=generate,
            )
        pending = await service.process_interfaces.runs.wait(
            scope, reference, result["run_id"]
        )
        assert pending["status"] == "waiting_human"
        assert (
            pending["input_checkpoint"]["checkpoint_id"] == checkpoint["checkpoint_id"]
        )
        assert len(calls) == 1

        answer = await service.process_interfaces.runs.respond(
            scope,
            reference,
            checkpoint["checkpoint_id"],
            "valid-answer",
            expected_subject_digest=checkpoint["subject_digest"],
            value={"selection": "b"},
            response_generator=generate,
        )
        assert answer.run_id == result["run_id"]
        completed = await service.process_interfaces.runs.wait(
            scope, reference, result["run_id"]
        )
        assert completed["status"] == "completed"
        assert len(calls) == 2
        assert [step["task_id"] for step in completed["steps"]] == [
            "first",
            "choice",
            "second",
        ]
        assert "input_checkpoint" not in completed
        repeated = await service.process_interfaces.runs.respond(
            scope,
            reference,
            checkpoint["checkpoint_id"],
            "valid-answer",
            expected_subject_digest=checkpoint["subject_digest"],
            value={"selection": "b"},
            response_generator=generate,
        )
        assert repeated == answer
        assert len(calls) == 2
    finally:
        await service.process_interfaces.close()
        await executor.close()
