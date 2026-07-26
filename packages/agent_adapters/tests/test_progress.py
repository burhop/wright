from agent_adapters.progress import GenericProgressProjector


def test_projects_generic_server_tool_and_advertised_title() -> None:
    projector = GenericProgressProjector()

    result = projector.project(
        {
            "server": "geometry",
            "tool": "geometry__create",
            "title": "Create geometry",
            "progress": 1,
            "total": 4,
            "message": "Sketching",
            "correlationId": "request-1",
            "status": "running",
        },
        elapsed_seconds=2.54,
    )

    assert result == {
        "server": "geometry",
        "tool": "geometry__create",
        "title": "Create geometry",
        "progress": 1.0,
        "total": 4.0,
        "message": "Sketching",
        "correlationId": "request-1",
        "status": "running",
        "elapsedSeconds": 2.5,
    }


def test_fallback_heartbeat_monotonicity_and_terminal_replay() -> None:
    projector = GenericProgressProjector()
    first = projector.project(
        {"tool": "server__work", "progress": 3, "status": "running"},
        elapsed_seconds=1,
    )
    decreasing = projector.project(
        {"tool": "server__work", "progress": 2, "status": "running"},
        elapsed_seconds=2,
    )
    heartbeat = projector.heartbeat(elapsed_seconds=3)
    terminal = projector.project(
        {"tool": "server__work", "status": "completed"},
        elapsed_seconds=4,
    )
    replay = projector.project(
        {"tool": "server__work", "status": "failed"},
        elapsed_seconds=5,
    )

    assert first["title"] == "server__work"
    assert first["message"] == "Running server__work."
    assert decreasing["progress"] == 3.0
    assert heartbeat["heartbeat"] is True
    assert heartbeat["title"] == "server__work"
    assert terminal["message"] == "server__work completed."
    assert replay is None
    assert projector.heartbeat(elapsed_seconds=6)["title"] == "Working on request"
