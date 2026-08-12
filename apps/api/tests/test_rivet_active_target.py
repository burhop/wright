import pytest

from tool_registry.gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewaySessionContext,
)
from workspace_service.adapters.runtime import set_active_rivet_workflow


def _session() -> GatewaySessionContext:
    return GatewaySessionContext(
        session_id="gateway-session",
        principal_id="local-user",
        workspace_id="workspace-1",
        workspace_path="D:/workspace",
        transport="stdio",
        binding_session_id="chat-session",
    )


def test_rivet_tool_defaults_to_currently_displayed_workflow(
    tmp_path, monkeypatch
) -> None:
    from api import composition

    database = str(tmp_path / "wright.db")
    monkeypatch.setattr(composition, "DATABASE_PATH", database)
    set_active_rivet_workflow(database, "chat-session", "untitled-workflow-2")

    assert (
        composition._resolve_rivet_tool_slug(_session(), {}, require_displayed=True)
        == "untitled-workflow-2"
    )


def test_rivet_tool_rejects_an_offscreen_workflow_target(tmp_path, monkeypatch) -> None:
    from api import composition

    database = str(tmp_path / "wright.db")
    monkeypatch.setattr(composition, "DATABASE_PATH", database)
    set_active_rivet_workflow(database, "chat-session", "untitled-workflow-2")

    with pytest.raises(GatewayError) as exc_info:
        composition._resolve_rivet_tool_slug(
            _session(), {"slug": "rivet"}, require_displayed=True
        )

    assert exc_info.value.code == GatewayErrorCode.INVALID_INPUT
    assert "untitled-workflow-2" in str(exc_info.value)


def test_rivet_mutation_requires_a_displayed_workflow(tmp_path, monkeypatch) -> None:
    from api import composition

    monkeypatch.setattr(composition, "DATABASE_PATH", str(tmp_path / "wright.db"))

    with pytest.raises(GatewayError) as exc_info:
        composition._resolve_rivet_tool_slug(
            _session(), {"slug": "rivet"}, require_displayed=True
        )

    assert exc_info.value.code == GatewayErrorCode.INVALID_INPUT
    assert "currently displayed" in str(exc_info.value)


def test_rivet_management_schemas_do_not_require_model_selected_slug() -> None:
    from api.composition import _rivet_gateway_tools

    specs = {spec.name: spec for spec, _handler in _rivet_gateway_tools()}

    assert specs["wright__rivet_inspect_graph"].input_schema["required"] == []
    assert specs["wright__rivet_add_node"].input_schema["required"] == [
        "expected_revision"
    ]
    assert specs["wright__rivet_save_revision"].input_schema["required"] == [
        "expected_revision",
        "project",
    ]
