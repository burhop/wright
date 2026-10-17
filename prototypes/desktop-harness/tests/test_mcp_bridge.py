import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
import pytest


@pytest.fixture
def bridge(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    import mcp_bridge

    return mcp_bridge


def test_pinned_sdk_preserves_unattended_json_as_text(bridge):
    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"accepted": True})
    )
    server = bridge.server(client)
    step_json = json.dumps(
        {
            "version": "wright.unattended-step/1",
            "status": "completed",
            "response": "Result",
            "reason": None,
        }
    )
    asyncio.run(
        server.call_tool(
            "wright_reasoning_answer",
            {
                "workspace_id": "workspace",
                "session_id": "session",
                "request_id": "request",
                "request_digest": "a" * 64,
                "binding_digest": "b" * 64,
                "response_id": "response",
                "reply": step_json,
            },
        )
    )
    payload = client.call.call_args.kwargs["json"]
    assert payload["response"]["reply"] == step_json
    assert isinstance(payload["response"]["reply"], str)


def test_html_success_cannot_be_accepted_as_api_evidence(bridge):
    client = bridge.WrightDesktopClient.__new__(bridge.WrightDesktopClient)
    client.http = SimpleNamespace(
        request=AsyncMock(
            return_value=httpx.Response(
                200,
                headers={"content-type": "text/html"},
                text="<html>Frontend fallback</html>",
            )
        )
    )
    with pytest.raises(RuntimeError, match="non-JSON"):
        asyncio.run(client.call("POST", "/api/workspace/workflow-sources", json={}))
    assert client.http.request.await_count == 1


def test_pinned_sdk_preserves_typed_action_and_original_arguments(bridge):
    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"accepted": True})
    )
    decision = {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {
                "id": "inspection-proposal",
                "type": "function",
                "function": {
                    "name": "tool_0",
                    "arguments": '{"relativePath":"inputs/requirements.md"}',
                },
            }
        ],
    }
    asyncio.run(
        bridge.server(client).call_tool(
            "wright_reasoning_action",
            {
                "workspace_id": "workspace",
                "session_id": "session",
                "request_id": "request",
                "request_digest": "a" * 64,
                "binding_digest": "b" * 64,
                "response_id": "response",
                "decision": decision,
            },
        )
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    assert client.call.await_count == 1
    assert client.call.call_args.kwargs["json"]["response"]["reply"] == decision


@pytest.mark.parametrize(
    "decision",
    [
        {"role": "assistant", "content": None, "tool_calls": []},
        {"role": "assistant", "content": "result", "extra_authority": True},
        {"role": "assistant", "tool_calls": [{"id": "one"}, {"id": "two"}]},
    ],
)
def test_invalid_action_never_reaches_wright_api(bridge, decision):
    from mcp.server.fastmcp.exceptions import ToolError

    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock())
    with pytest.raises(ToolError):
        asyncio.run(
            bridge.server(client).call_tool(
                "wright_reasoning_action",
                {
                    "workspace_id": "workspace",
                    "session_id": "session",
                    "request_id": "request",
                    "request_digest": "a" * 64,
                    "binding_digest": "b" * 64,
                    "response_id": "response",
                    "decision": decision,
                },
            )
        )
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


def test_workspace_panel_has_scoped_read_only_metadata_and_versioned_resource(bridge):
    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock())

    async def inspect():
        server = bridge.server(client)
        tool = next(
            t for t in await server.list_tools() if t.name == "wright_workspace_panel"
        )
        assert tool.annotations.readOnlyHint is True
        assert tool.outputSchema["type"] == "object"
        assert tool.meta["ui"]["resourceUri"] == bridge.WORKSPACE_PANEL_URI
        assert tool.meta["openai/ui"]["entrypoints"] == [{"type": "thread"}]
        resource = (await server.read_resource(bridge.WORKSPACE_PANEL_URI))[0]
        assert resource.mime_type == "text/html;profile=mcp-app"
        assert resource.meta["ui"]["csp"] == {
            "connectDomains": [],
            "resourceDomains": [],
        }
        assert resource.content == bridge.WORKSPACE_PANEL_HTML
        assert "fetch(" not in resource.content

    asyncio.run(inspect())
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


def test_workspace_panel_reads_only_exact_workspace_and_connection(bridge):
    workspace = {"workspace_id": "workspace", "workspace_name": "Lab"}
    client = SimpleNamespace(
        scope=AsyncMock(return_value=workspace),
        call=AsyncMock(return_value={"connected": True}),
    )
    result = asyncio.run(
        bridge.server(client).call_tool(
            "wright_workspace_panel",
            {"workspace_id": "workspace", "session_id": "session"},
        )
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with("GET", "/api/desktop/connection")
    assert result[1] == {"connection": {"connected": True}, "workspace": workspace}


@pytest.mark.parametrize(
    "arguments", [{"workspace_id": "workspace"}, {"session_id": "session"}]
)
def test_incomplete_panel_scope_never_reads_api(bridge, arguments):
    from mcp.server.fastmcp.exceptions import ToolError

    client = SimpleNamespace(scope=AsyncMock(), call=AsyncMock())
    with pytest.raises(ToolError, match="together"):
        asyncio.run(
            bridge.server(client).call_tool("wright_workspace_panel", arguments)
        )
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


def test_denied_workspace_panel_does_not_read_connection_or_another_workspace(bridge):
    from mcp.server.fastmcp.exceptions import ToolError

    client = SimpleNamespace(
        scope=AsyncMock(side_effect=ValueError("Scope denied")), call=AsyncMock()
    )
    with pytest.raises(ToolError, match="Scope denied"):
        asyncio.run(
            bridge.server(client).call_tool(
                "wright_workspace_panel",
                {"workspace_id": "other", "session_id": "session"},
            )
        )
    client.call.assert_not_awaited()


def test_native_editor_is_opt_in_and_uses_same_source_owner(bridge):
    client = SimpleNamespace(
        scope=AsyncMock(
            return_value={"workspace_id": "workspace", "session_id": "session"}
        ),
        call=AsyncMock(return_value={"source": "accepted"}),
    )
    plain = bridge.server(client)
    assert "wright_workflow_save" not in {
        item.name for item in asyncio.run(plain.list_tools())
    }
    native = bridge.server(client, native_editor=True)
    tools = {item.name: item for item in asyncio.run(native.list_tools())}
    assert tools["wright_workflow_save"].meta["ui"]["visibility"] == ["app"]
    uri = tools["wright_workflow_open"].meta["ui"]["resourceUri"]
    import hashlib

    assert (
        hashlib.sha256(
            Path(bridge.__file__).with_name("native-editor.html").read_bytes()
        ).hexdigest()
        in uri
    )
    _, document = asyncio.run(
        native.call_tool(
            "wright_workflow_open",
            {
                "workspace_id": "workspace",
                "session_id": "session",
                "path": "workflows/test.workflow.wflow",
            },
        )
    )
    assert document["document"] == {"source": "accepted"}
    client.scope.assert_awaited_once_with("workspace", "session")
    assert client.call.call_args.args == ("GET", "/api/workspace/workflow-sources")


def test_frozen_editor_configuration_must_match_on_connection(bridge, tmp_path):
    import hashlib

    (tmp_path / "preview.json").write_text(
        json.dumps({"api_url": "http://127.0.0.1:8122"})
    )
    (tmp_path / "desktop-binding.json").write_text("{}")
    files = {
        "transport": hashlib.sha256(Path(bridge.__file__).read_bytes()).hexdigest(),
        "native_editor": "0" * 64,
    }
    (tmp_path / "desktop-versions.json").write_text(
        json.dumps(
            {"mcp_sdk": bridge.version("mcp"), "native_editor": True, "files": files}
        )
    )
    with pytest.raises(ValueError, match="capability differs"):
        bridge.WrightDesktopClient(tmp_path)
    with pytest.raises(ValueError, match="bytes changed"):
        bridge.WrightDesktopClient(tmp_path, native_editor=True)


def test_sdk_version_drift_is_denied_before_connecting(bridge, tmp_path):
    (tmp_path / "preview.json").write_text(
        json.dumps({"api_url": "http://127.0.0.1:8122"})
    )
    (tmp_path / "desktop-binding.json").write_text("{}")
    (tmp_path / "desktop-versions.json").write_text(
        json.dumps({"mcp_sdk": "untested", "files": {}})
    )
    with pytest.raises(ValueError, match="SDK version differs"):
        bridge.WrightDesktopClient(tmp_path, native_editor=True)


def test_working_view_requires_opt_in_and_reuses_immutable_editor_resource(bridge):
    client = SimpleNamespace(
        scope=AsyncMock(
            return_value={"workspace_id": "workspace", "session_id": "session"}
        ),
        call=AsyncMock(return_value={"context": {"run_id": "saved-run"}}),
    )
    with pytest.raises(ValueError, match="requires the native editor"):
        bridge.server(client, native_working_view=True)
    editor = bridge.server(client, native_editor=True)
    assert "wright_process_view" not in {
        t.name for t in asyncio.run(editor.list_tools())
    }
    native = bridge.server(client, native_editor=True, native_working_view=True)
    tools = {t.name: t for t in asyncio.run(native.list_tools())}
    assert len(tools) == 49
    for name in ("wright_editor_drafts_read", "wright_editor_draft_save"):
        assert tools[name].meta["ui"]["visibility"] == ["app"]
    assert {
        "wright_connection_preview",
        "wright_connection_command_preview",
        "wright_recorded_run_read",
        "wright_connection_import_plan",
        "wright_workflow_export",
        "wright_workflow_transfer_assets",
        "wright_workflow_import_inspect",
        "wright_workflow_import",
    } <= tools.keys()
    assert tools["wright_workflow_history"].annotations.readOnlyHint is True
    view = tools["wright_process_view"]
    assert view.annotations.readOnlyHint is True
    assert (
        view.meta["ui"]["resourceUri"]
        == tools["wright_workflow_open"].meta["ui"]["resourceUri"]
    )
    assert tools["wright_process_ui_update"].meta["ui"]["visibility"] == ["app"]
    _, result = asyncio.run(
        native.call_tool(
            "wright_process_view",
            {
                "request": {
                    "operation": "snapshot",
                    "workspace_id": "workspace",
                    "session_id": "session",
                    "path": "workflows/test.wflow",
                    "expected_storage_digest": "a" * 64,
                    "run_id": "saved-run",
                }
            },
        )
    )
    assert (
        result["working_view_enabled"] is True
        and result["snapshot"]["context"]["run_id"] == "saved-run"
    )
    assert client.call.await_count == 1
    assert client.call.call_args.args == (
        "GET",
        "/api/workspace/process-interfaces/runs/saved-run",
    )


def test_working_view_configuration_drift_fails_before_connecting(bridge, tmp_path):
    import hashlib

    (tmp_path / "preview.json").write_text(
        json.dumps({"api_url": "http://127.0.0.1:8122"})
    )
    (tmp_path / "desktop-binding.json").write_text("{}")
    files = {
        "transport": hashlib.sha256(Path(bridge.__file__).read_bytes()).hexdigest()
    }
    (tmp_path / "desktop-versions.json").write_text(
        json.dumps(
            {
                "mcp_sdk": bridge.version("mcp"),
                "native_editor": True,
                "native_working_view": True,
                "files": files,
            }
        )
    )
    with pytest.raises(ValueError, match="working view differs"):
        bridge.WrightDesktopClient(tmp_path, native_editor=True)
    files["native_process_tools"] = "0" * 64
    (tmp_path / "desktop-versions.json").write_text(
        json.dumps(
            {
                "mcp_sdk": bridge.version("mcp"),
                "native_editor": True,
                "native_working_view": True,
                "files": files,
            }
        )
    )
    with pytest.raises(ValueError, match="bytes changed"):
        bridge.WrightDesktopClient(
            tmp_path, native_editor=True, native_working_view=True
        )


def test_panel_creation_uses_source_owner_and_rejects_scope_before_write(bridge):
    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"path": "workflows/new.wflow"})
    )
    server = bridge.server(client)
    tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}
    assert tools["wright_workflow_create"].meta["ui"]["visibility"] == ["model", "app"]
    args = {
        "workspace_id": "workspace",
        "session_id": "session",
        "path": "workflows/new.wflow",
        "source": "source",
    }
    asyncio.run(server.call_tool("wright_workflow_create", args))
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with(
        "POST",
        "/api/workspace/workflow-sources",
        json={
            "session_id": "session",
            "path": "workflows/new.wflow",
            "source": "source",
        },
    )
    client.call.reset_mock()
    client.scope.side_effect = PermissionError("wrong workspace")
    with pytest.raises(Exception, match="wrong workspace"):
        asyncio.run(server.call_tool("wright_workflow_create", args))
    client.call.assert_not_awaited()


def test_templates_use_existing_owner_and_scope_before_creation(bridge):
    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"templates": []})
    )
    server = bridge.server(client)
    tools = {t.name: t for t in asyncio.run(server.list_tools())}
    assert tools["wright_workflow_templates"].annotations.readOnlyHint
    assert tools["wright_workflow_template_create"].meta["ui"]["visibility"] == [
        "model",
        "app",
    ]
    args = {
        "workspace_id": "workspace",
        "session_id": "session",
        "template_id": "robot-tracking-diagnosis",
        "template_version": "1.0.0",
        "expected_source_digest": "a" * 64,
        "workflow_path": "workflows/robot.workflow.wflow",
        "request_id": "copy-1",
    }
    asyncio.run(server.call_tool("wright_workflow_template_create", args))
    client.call.assert_awaited_once_with(
        "POST",
        "/api/workspace/workflow-source-templates/robot-tracking-diagnosis/instances",
        json={
            k: v for k, v in args.items() if k not in {"workspace_id", "template_id"}
        },
    )
    client.call.reset_mock()
    client.scope.side_effect = PermissionError("wrong scope")
    with pytest.raises(Exception, match="wrong scope"):
        asyncio.run(server.call_tool("wright_workflow_template_create", args))
    client.call.assert_not_awaited()


@pytest.mark.parametrize(
    "path,extra,accepted",
    [
        ("/api/workspace/process-interfaces/inputs/upload", {}, True),
        ("/api/workspace/process-interfaces/inputs/upload", {"grant": True}, False),
        ("/api/desktop/workspaces", {}, False),
    ],
)
@pytest.mark.parametrize("envelope", ["detail", "details"])
def test_only_valid_public_process_reason_reaches_panel(
    bridge, path, extra, accepted, envelope
):
    from native_source_tools import WrightRequestRejected

    public = {
        "code": "READINESS_UNSUPPORTED",
        "message": "Mesh step needs a tool binding.",
        "correction": "Configure that step before preparing inputs.",
        **extra,
    }
    client = bridge.WrightDesktopClient.__new__(bridge.WrightDesktopClient)
    client.http = SimpleNamespace(
        request=AsyncMock(
            return_value=httpx.Response(
                422,
                headers={"content-type": "application/json"},
                json={envelope: {"reason": public, "diagnostic": "PRIVATE RAW DATA"}},
            )
        )
    )
    with pytest.raises(WrightRequestRejected) as caught:
        asyncio.run(client.call("POST", path, json={}))
    if accepted:
        assert caught.value.reason.code == public["code"]
        assert caught.value.reason.message == public["message"]
        assert "PRIVATE" not in str(caught.value.reason)
    else:
        assert caught.value.reason is None
    assert client.http.request.await_count == 1
