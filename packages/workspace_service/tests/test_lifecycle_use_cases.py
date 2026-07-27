from __future__ import annotations

from workspace_service.use_cases.context import WorkspaceContextUseCases
from workspace_service.use_cases.lifecycle import WorkspaceLifecycleUseCases
from workspace_service.use_cases.tools import WorkspaceToolUseCases

from .fakes import RecordingRepository


def test_lifecycle_context_and_tools_use_only_injected_repository():
    repository = RecordingRepository()
    repository.add("ws-a", "session-a", "/work/a")
    lifecycle = WorkspaceLifecycleUseCases(repository)
    context = WorkspaceContextUseCases(repository)
    tools = WorkspaceToolUseCases(
        repository,
        lambda: ["cad", "solver"],
        lambda session_id: repository.enabled_tools(
            repository.get_by_session(session_id)["workspace_id"]
        ),
        lambda: [],
    )

    assert lifecycle.get_by_session("session-a")["workspace_id"] == "ws-a"
    context.save("ws-a", {"units": "metric"})
    assert context.load("ws-a")["context_data"] == {"units": "metric"}
    assert tools.list_by_workspace("ws-a").enabled_tools == ["cad", "solver"]
    tools.set_by_session("session-a", "cad", False)
    assert repository.tools["ws-a"] == ["solver"]
