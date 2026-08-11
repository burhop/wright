from api.routers import agent


def test_active_rivet_ui_context_is_mirrored_to_stable_gateway_binding(
    monkeypatch,
) -> None:
    writes: list[tuple[str, str | None]] = []
    monkeypatch.setattr(agent, "get_active_gateway_session", lambda _db: "gateway-1")
    monkeypatch.setattr(
        agent,
        "get_workspace_by_session",
        lambda _db, _session: {"workspace_id": "workspace-1"},
    )
    monkeypatch.setattr(
        agent,
        "set_active_rivet_workflow",
        lambda _db, session_id, slug: writes.append((session_id, slug)),
    )

    agent._mirror_active_rivet_workflow_to_gateway_binding(
        "chat-2", "untitled-workflow-2"
    )

    assert writes == [("gateway-1", "untitled-workflow-2")]


def test_active_rivet_ui_context_is_not_mirrored_across_workspaces(
    monkeypatch,
) -> None:
    writes: list[tuple[str, str | None]] = []
    monkeypatch.setattr(agent, "get_active_gateway_session", lambda _db: "gateway-1")
    monkeypatch.setattr(
        agent,
        "get_workspace_by_session",
        lambda _db, session_id: {
            "workspace_id": "workspace-1" if session_id == "chat-2" else "workspace-2"
        },
    )
    monkeypatch.setattr(
        agent,
        "set_active_rivet_workflow",
        lambda _db, session_id, slug: writes.append((session_id, slug)),
    )

    agent._mirror_active_rivet_workflow_to_gateway_binding(
        "chat-2", "untitled-workflow-2"
    )

    assert writes == []
