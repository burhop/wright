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


@pytest.mark.parametrize("media", ["text/markdown", "image/png", "image/jpeg"])
@pytest.mark.parametrize("changed", [False, True])
def test_reader_requires_owner_headers_and_actual_recorded_hash(panel, changed, media):
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
                "content-type": media,
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
        assert result["document"]["media_type"] == media


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


@pytest.mark.parametrize("media,size", [("image/svg+xml", 5), ("image/png", 1048577)])
def test_image_transport_keeps_active_content_and_size_limits(panel, media, size):
    import httpx

    server, client = panel
    client.http = httpx.AsyncClient(
        base_url="http://private",
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                content=b"bytes",
                headers={
                    "content-type": media,
                    "content-length": str(size),
                    "x-wright-artifact-sha256": "b" * 64,
                    "x-content-type-options": "nosniff",
                },
                request=request,
            )
        ),
    )
    result = run(
        server,
        "wright_process_ui_read",
        scope(
            "representation",
            run_id="saved-run",
            reference={"artifact_ref": "result.image", "sha256": "b" * 64},
        ),
    )
    assert result["ok"] is False
    assert result["reason"]["code"] == "CAPABILITY_UNAVAILABLE"


def test_review_decision_uses_existing_exact_subject_owner(panel):
    server, client = panel
    run(
        server,
        "wright_process_ui_update",
        scope(
            "decide",
            checkpoint_id="review",
            subject_digest="b" * 64,
            decision="changes_requested",
            reason="Inspect the missing evidence",
            request_id="review-request",
        ),
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    assert client.call.call_args.args == (
        "POST",
        "/api/workspace/process-interfaces/interactions/review/decision",
    )
    body = client.call.call_args.kwargs["json"]
    assert body["decision"] == "changes_requested"
    assert body["subject_digest"] == "b" * 64
    assert body["expected_storage_digest"] == "a" * 64
    assert body["request_id"] == "review-request"
    assert "auto" not in body and "actor" not in body


@pytest.mark.parametrize(
    "extra", [{"auto": True}, {"actor": "engineer"}, {"action": "dispatch"}]
)
def test_review_cannot_supply_authority_or_dispatch(panel, extra):
    server, client = panel
    with pytest.raises(Exception):
        run(
            server,
            "wright_process_ui_update",
            scope(
                "decide",
                checkpoint_id="review",
                subject_digest="b" * 64,
                decision="approved",
                reason="Private test fixture only",
                request_id="review-request",
                **extra,
            ),
        )
    client.call.assert_not_awaited()


def test_continuation_delegates_once_to_exact_action_owner(panel):
    server, client = panel
    run(
        server,
        "wright_process_ui_update",
        scope(
            "continue",
            action_id="continue-checkpoint",
            subject_digest="b" * 64,
            request_id="same-continuation",
        ),
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    client.call.assert_awaited_once_with(
        "POST",
        "/api/workspace/process-interfaces/actions/continue-checkpoint",
        json={
            "session_id": "session",
            "path": "workflows/example.wflow",
            "expected_storage_digest": "a" * 64,
            "subject_digest": "b" * 64,
            "request_id": "same-continuation",
        },
    )


@pytest.mark.parametrize("action", ["dispatch", "continue-", "continue-../other"])
def test_continuation_rejects_non_declared_or_path_injected_action(panel, action):
    server, client = panel
    with pytest.raises(Exception):
        run(
            server,
            "wright_process_ui_update",
            scope(
                "continue",
                action_id=action,
                subject_digest="b" * 64,
                request_id="same-continuation",
            ),
        )
    client.call.assert_not_awaited()


def test_upload_delegates_exact_bytes_and_declared_scope_to_existing_owner(panel):
    import base64

    server, client = panel
    content = b"time,error_mm\n0,0.25\n1,0.5\n"
    run(
        server,
        "wright_process_ui_update",
        scope(
            "upload",
            input_id="measurements",
            filename="tracking.csv",
            bytes_base64=base64.b64encode(content).decode(),
        ),
    )
    client.scope.assert_awaited_once_with("workspace", "session")
    assert client.call.call_args.args == (
        "POST",
        "/api/workspace/process-interfaces/inputs/upload",
    )
    assert client.call.call_args.kwargs == {
        "data": {
            "session_id": "session",
            "path": "workflows/example.wflow",
            "expected_storage_digest": "a" * 64,
            "input_id": "measurements",
        },
        "files": {"file": ("tracking.csv", content, "application/octet-stream")},
    }


@pytest.mark.parametrize("encoded", ["", "!!!!", "YQ==garbage", "☃☃☃☃"])
def test_upload_malformed_encoding_never_reaches_owner(panel, encoded):
    server, client = panel
    with pytest.raises(Exception):
        run(
            server,
            "wright_process_ui_update",
            scope(
                "upload",
                input_id="measurements",
                filename="tracking.csv",
                bytes_base64=encoded,
            ),
        )
    client.call.assert_not_awaited()


def test_upload_lost_owner_acknowledgement_is_uncertain_and_not_retried(panel):
    from native_source_tools import WrightRequestRejected

    server, client = panel
    client.call.side_effect = WrightRequestRejected(503, "owner acknowledgement lost")
    reply = run(
        server,
        "wright_process_ui_update",
        scope(
            "upload",
            input_id="measurements",
            filename="tracking.csv",
            bytes_base64="YQ==",
        ),
    )
    assert reply["reason"]["code"] == "OUTCOME_UNKNOWN"
    client.call.assert_awaited_once()


def test_upload_cannot_use_readonly_port_or_expand_to_arbitrary_url(panel):
    server, client = panel
    request = scope(
        "upload", input_id="measurements", filename="data.csv", bytes_base64="YQ=="
    )
    with pytest.raises(Exception):
        run(server, "wright_process_ui_read", request)
    with pytest.raises(Exception):
        run(
            server,
            "wright_process_ui_update",
            {**request, "url": "https://example.com/file"},
        )
    client.call.assert_not_awaited()


def test_upload_scope_denial_does_not_send_file_bytes_to_owner(panel):
    from native_source_tools import WrightRequestRejected

    server, client = panel
    client.scope.side_effect = WrightRequestRejected(403, "foreign workspace")
    reply = run(
        server,
        "wright_process_ui_update",
        scope(
            "upload",
            input_id="measurements",
            filename="data.csv",
            bytes_base64="YQ==",
        ),
    )
    assert reply["reason"]["code"] == "SCOPE_DENIED"
    client.call.assert_not_awaited()


def test_upload_decoded_size_cannot_exceed_existing_owner_limit(panel):
    import base64

    server, client = panel
    # 32 MiB + 1 shares the same encoded length as the allowed maximum.
    # The decoded bound must still reject it, before any owner write.
    encoded = base64.b64encode(b"x" * 33_554_433).decode()
    with pytest.raises(Exception):
        run(
            server,
            "wright_process_ui_update",
            scope(
                "upload",
                input_id="measurements",
                filename="data.csv",
                bytes_base64=encoded,
            ),
        )
    client.call.assert_not_awaited()
