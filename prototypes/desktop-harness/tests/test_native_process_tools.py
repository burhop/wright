import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from mcp.server.fastmcp import FastMCP


@pytest.fixture
def panel(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from native_process_tools import register_native_process_tools

    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value={"accepted": True})
    )
    server = FastMCP("panel-process-test")
    register_native_process_tools(server, client)
    return server, client


def scope(operation, **extra):
    return {
        "workspace_id": "workspace",
        "session_id": "session",
        "path": "workflows/example.wflow",
        "expected_storage_digest": "a" * 64,
        "operation": operation,
        **extra,
    }


def run(server, tool, request):
    return asyncio.run(server.call_tool(tool, {"request": request}))[1]


def test_readonly_and_update_ports_are_distinct_and_ui_only(panel):
    server, _ = panel
    tools = {item.name: item for item in asyncio.run(server.list_tools())}
    assert tools["wright_process_ui_read"].annotations.readOnlyHint is True
    assert tools["wright_process_ui_update"].annotations.readOnlyHint is False
    assert all(tool.meta["ui"]["visibility"] == ["app"] for tool in tools.values())


def test_snapshot_preserves_exact_source_run_and_page(panel):
    server, client = panel
    run(
        server,
        "wright_process_ui_read",
        scope("snapshot", run_id="saved-run", page="saved-cursor"),
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    assert client.call.call_args.args == (
        "GET",
        "/api/workspace/process-interfaces/runs/saved-run",
    )
    query = client.call.call_args.kwargs["params"]
    assert (
        query["expected_storage_digest"] == "a" * 64 and query["page"] == "saved-cursor"
    )


def test_declared_response_accepts_scalar_without_creating_approval(panel):
    server, client = panel
    run(
        server,
        "wright_process_ui_update",
        scope(
            "respond",
            checkpoint_id="checkpoint",
            subject_digest="b" * 64,
            value="selected",
            request_id="same-request",
        ),
    )
    body = client.call.call_args.kwargs["json"]
    assert body["value"] == "selected" and body["auto"] is False
    assert body["request_id"] == "same-request" and body["subject_digest"] == "b" * 64
    assert "decision" not in body


@pytest.mark.parametrize(
    "extra", [{"auto": True}, {"url": "http://outside"}, {"decision": "approved"}]
)
def test_response_cannot_expand_its_authority(panel, extra):
    server, client = panel
    with pytest.raises(Exception):
        run(
            server,
            "wright_process_ui_update",
            scope(
                "respond",
                checkpoint_id="checkpoint",
                subject_digest="b" * 64,
                value="selected",
                request_id="same-request",
                **extra,
            ),
        )
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


def test_read_port_cannot_start_or_accept_path_injection(panel):
    server, client = panel
    with pytest.raises(Exception):
        run(
            server,
            "wright_process_ui_read",
            scope(
                "start",
                input_snapshot_id="inputs",
                expected_input_digest="a" * 64,
                request_id="start",
            ),
        )
    with pytest.raises(Exception):
        run(server, "wright_process_ui_read", scope("snapshot", run_id="../other-run"))
    client.scope.assert_not_awaited()
    client.call.assert_not_awaited()


@pytest.mark.parametrize("status,uncertain", [(403, False), (409, False), (500, True)])
def test_owner_rejection_is_distinct_from_uncertain_effect_without_retry(
    panel, status, uncertain
):
    from native_source_tools import WrightRequestRejected

    server, client = panel
    client.call.side_effect = WrightRequestRejected(status, "private diagnostics")
    result = run(
        server,
        "wright_process_ui_update",
        scope(
            "start",
            input_snapshot_id="inputs",
            expected_input_digest="a" * 64,
            request_id="stable-start",
        ),
    )
    assert (result["reason"]["code"] == "OUTCOME_UNKNOWN") is uncertain
    assert "private" not in str(result)
    assert client.call.await_count == 1


def test_scope_denial_prevents_start(panel):
    from native_source_tools import WrightRequestRejected

    server, client = panel
    client.scope.side_effect = WrightRequestRejected(403, "private diagnostics")
    result = run(
        server,
        "wright_process_ui_update",
        scope(
            "start",
            input_snapshot_id="inputs",
            expected_input_digest="a" * 64,
            request_id="stable-start",
        ),
    )
    assert result["reason"]["code"] == "SCOPE_DENIED"
    client.call.assert_not_awaited()


def test_chat_wait_read_first_authorizes_exact_run_and_does_not_answer(panel):
    server, client = panel
    client.call.side_effect = [
        {"state": "running"},
        [{"request": {"run_id": "saved-run"}}, {"request": {"run_id": "other-run"}}],
    ]
    result = run(
        server, "wright_process_ui_read", scope("reasoning", run_id="saved-run")
    )
    assert result["document"] == [{"request": {"run_id": "saved-run"}}]
    assert client.call.call_args_list[0].args == (
        "GET",
        "/api/workspace/process-interfaces/runs/saved-run",
    )
    assert all(call.args[0] == "GET" for call in client.call.call_args_list)


@pytest.mark.parametrize("changed", [False, True])
def test_text_reader_requires_owner_headers_and_actual_recorded_hash(panel, changed):
    import base64
    import hashlib
    import httpx

    server, client = panel
    body = b"Recorded digital result\n"
    digest = hashlib.sha256(body).hexdigest()

    def respond(request):
        return httpx.Response(
            200,
            content=b"changed" if changed else body,
            headers={
                "content-type": "text/markdown",
                "content-length": str(len(body)),
                "x-wright-artifact-sha256": digest,
                "x-content-type-options": "nosniff",
            },
            request=request,
        )

    client.http = httpx.AsyncClient(
        base_url="http://private", transport=httpx.MockTransport(respond)
    )
    request = scope(
        "representation",
        run_id="saved-run",
        reference={"artifact_ref": "result.md", "sha256": digest},
    )
    result = run(server, "wright_process_ui_read", request)
    if changed:
        assert result["ok"] is False and result["reason"]["code"] == "SUBJECT_STALE"
    else:
        assert base64.b64decode(result["document"]["bytes_base64"]) == body
        assert result["document"]["sha256"] == digest


def test_native_reader_reports_unsupported_preview_before_reading_file(panel):
    server, client = panel
    result = run(
        server,
        "wright_process_ui_read",
        scope(
            "representation",
            run_id="saved-run",
            reference={"artifact_ref": "result.pdf", "sha256": "b" * 64},
            preview="pdf-page",
            page=1,
        ),
    )
    assert result["reason"]["code"] == "CAPABILITY_UNAVAILABLE"
    client.call.assert_not_awaited()
