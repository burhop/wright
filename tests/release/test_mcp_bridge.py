from email.message import Message
from io import BytesIO
import json
from urllib.error import URLError

import pytest

from wright_engineering import mcp_bridge


class _Response:
    def __init__(
        self,
        payload: bytes,
        *,
        session: str | None = None,
        content_type: str = "application/json",
    ) -> None:
        self._payload = payload
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        if session:
            self.headers["Mcp-Session-Id"] = session

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return self._payload


def test_stdio_bridge_forwards_binding_and_reuses_transport_session(
    monkeypatch,
) -> None:
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        message = json.loads(request.data)
        payload = json.dumps(
            {"jsonrpc": "2.0", "id": message["id"], "result": {}}
        ).encode()
        return _Response(payload, session="transport-1")

    monkeypatch.setenv("WRIGHT_API_TOKEN", "secret")
    monkeypatch.setattr(mcp_bridge, "urlopen", fake_urlopen)
    source = BytesIO(
        b'{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25"}}\n{"jsonrpc":"2.0","id":2,"method":"ping"}\n'
    )
    sink = BytesIO()
    assert (
        mcp_bridge.serve_stdio(
            workspace=mcp_bridge.Path("workspace-path"),
            workspace_id="workspace-id",
            stdin=source,
            stdout=sink,
        )
        == 0
    )
    assert sink.getvalue().count(b"\n") == 2
    assert requests[0][0].headers["X-wright-workspace-id"] == "workspace-id"
    assert requests[0][0].headers["Authorization"] == "Bearer secret"
    assert requests[1][0].headers["Mcp-session-id"] == "transport-1"


def test_stdio_bridge_requires_token(monkeypatch) -> None:
    monkeypatch.delenv("WRIGHT_API_TOKEN", raising=False)
    with pytest.raises(mcp_bridge.McpBridgeError, match="required bearer token"):
        mcp_bridge.serve_stdio(
            workspace=mcp_bridge.Path("workspace-id"), stdin=BytesIO(), stdout=BytesIO()
        )


def test_event_stream_response_extracts_last_data_event() -> None:
    assert (
        mcp_bridge._response_payload(
            "text/event-stream", b'event: message\ndata: {"id":1}\n\n'
        )
        == b'{"id":1}'
    )


def test_empty_response_and_invalid_input_fail_without_leaking_details(
    monkeypatch,
) -> None:
    assert mcp_bridge._response_payload("application/json", b"") is None
    monkeypatch.setenv("WRIGHT_API_TOKEN", "test-secret-value")
    with pytest.raises(mcp_bridge.McpBridgeError, match="invalid JSON"):
        mcp_bridge.serve_stdio(
            workspace=mcp_bridge.Path("workspace"),
            stdin=BytesIO(b"not-json\n"),
            stdout=BytesIO(),
        )


def test_transport_failure_is_bounded(monkeypatch) -> None:
    monkeypatch.setenv("WRIGHT_API_TOKEN", "test-secret-value")

    def unavailable(*_args, **_kwargs):
        raise URLError("sensitive upstream detail")

    monkeypatch.setattr(mcp_bridge, "urlopen", unavailable)
    with pytest.raises(mcp_bridge.McpBridgeError, match="URLError") as captured:
        mcp_bridge.serve_stdio(
            workspace=mcp_bridge.Path("workspace"),
            stdin=BytesIO(b'{"jsonrpc":"2.0","id":1,"method":"ping"}\n'),
            stdout=BytesIO(),
        )
    assert "sensitive upstream detail" not in str(captured.value)
