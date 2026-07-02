import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent_adapters import HermesAdapter, AgentChatRequest


@pytest.fixture(autouse=True)
def isolate_host_hermes_config(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(tmp_path / "missing-config.yaml"))
    monkeypatch.setenv("HERMES_ENV_PATH", str(tmp_path / "missing.env"))
    monkeypatch.delenv("LLM_API_URL", raising=False)
    monkeypatch.delenv("LLM_HEALTH_URL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_MODEL", raising=False)


@pytest.mark.asyncio
async def test_hermes_adapter_check_health_success():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"status":"ok"}'

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await adapter.check_health()

        assert result["state"] == "connected"
        assert result["latencyMs"] > 0
        mock_get.assert_called_once_with(
            "http://127.0.0.1:8642/health",
            headers=adapter.headers,
            timeout=2.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_check_health_failure():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Connection refused")
        result = await adapter.check_health()

        assert result["state"] == "disconnected"
        assert result["latencyMs"] == 0.0


@pytest.mark.asyncio
async def test_hermes_adapter_create_session():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "session": {
            "session_id": "test_session_123",
            "title": "Test Title",
            "created_at": 1780423855.15,
            "updated_at": 1780423855.15,
            "message_count": 5,
        }
    }

    with patch.object(
        adapter, "_request_with_fallback", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response
        session_info = await adapter.create_session("/home/workspace")

        assert session_info.session_id == "test_session_123"
        assert session_info.title == "Test Title"
        assert session_info.created_at == 1780423855150
        assert session_info.updated_at == 1780423855150
        assert session_info.message_count == 5

        mock_request.assert_called_once_with(
            "POST",
            "/api/sessions",
            json_body={"workspace": "/home/workspace"},
            timeout=10.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_list_sessions():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "session_id": "session1",
                "title": "Title 1",
                "created_at": 1780423800.0,
                "updated_at": 1780423810.0,
                "message_count": 2,
            }
        ]
    }

    with patch.object(
        adapter, "_request_with_fallback", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response
        sessions = await adapter.list_sessions()

        assert len(sessions) == 1
        assert sessions[0].session_id == "session1"
        assert sessions[0].title == "Title 1"
        assert sessions[0].created_at == 1780423800000
        assert sessions[0].message_count == 2

        mock_request.assert_called_once_with(
            "GET",
            "/api/sessions",
            timeout=10.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_delete_session():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_response = MagicMock()
    mock_response.status_code = 200

    with patch.object(
        adapter, "_request_with_fallback", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response
        result = await adapter.delete_session("session1")

        assert result is True
        mock_request.assert_called_once_with(
            "DELETE",
            "/api/sessions/session1",
            timeout=10.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_stream_chat_success():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_sse_1 = MagicMock()
    mock_sse_1.event = "message"
    mock_sse_1.data = '{"choices": [{"index": 0, "delta": {"content": "Hello"}, "finish_reason": null}]}'

    mock_sse_2 = MagicMock()
    mock_sse_2.event = "hermes.tool.progress"
    mock_sse_2.data = '{"tool": "development", "status": "running"}'

    mock_sse_3 = MagicMock()
    mock_sse_3.event = "message"
    mock_sse_3.data = "[DONE]"

    async def mock_aiter_sse():
        yield mock_sse_1
        yield mock_sse_2
        yield mock_sse_3

    mock_event_source = MagicMock()
    mock_event_source.aiter_sse = mock_aiter_sse
    mock_event_source.response = MagicMock()
    mock_event_source.response.raise_for_status = MagicMock()

    class MockAconnectSse:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return mock_event_source

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    req = AgentChatRequest(session_id="session123", message="Hello")

    with (
        patch("agent_adapters.hermes.aconnect_sse", new=MockAconnectSse),
        patch.object(
            adapter, "get_chat_history", new_callable=AsyncMock
        ) as mock_history,
    ):
        mock_history.return_value = []
        events = []
        async for event in adapter.stream_chat(req):
            events.append(event)

        assert len(events) == 3
        assert events[0].type == "token"
        assert events[0].data == {"text": "Hello"}
        assert events[1].type == "progress"
        assert events[1].data == {"tool": "development", "status": "running"}
        assert events[2].type == "stream_end"
        assert events[2].data == {}


@pytest.mark.asyncio
async def test_hermes_adapter_stream_chat_surfaces_error_chunk():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_sse = MagicMock()
    mock_sse.event = "message"
    mock_sse.data = (
        '{"choices": [{"index": 0, "delta": {}, '
        '"finish_reason": "error"}], '
        '"error": {"message": '
        '"HTTP 404: The model qwen36-35b-moe does not exist."}, '
        '"hermes": {"failed": true}}'
    )

    async def mock_aiter_sse():
        yield mock_sse

    mock_event_source = MagicMock()
    mock_event_source.aiter_sse = mock_aiter_sse
    mock_event_source.response = MagicMock()
    mock_event_source.response.raise_for_status = MagicMock()

    class MockAconnectSse:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return mock_event_source

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    req = AgentChatRequest(session_id="session123", message="Hello")

    with (
        patch("agent_adapters.hermes.aconnect_sse", new=MockAconnectSse),
        patch.object(
            adapter, "get_chat_history", new_callable=AsyncMock
        ) as mock_history,
        patch.object(
            adapter, "get_session_workspace", new_callable=AsyncMock
        ) as mock_workspace,
    ):
        mock_history.return_value = []
        mock_workspace.return_value = None
        events = []
        async for event in adapter.stream_chat(req):
            events.append(event)

        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].data == {
            "message": "HTTP 404: The model qwen36-35b-moe does not exist."
        }


@pytest.mark.asyncio
async def test_hermes_adapter_stream_chat_rejects_empty_done():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_sse = MagicMock()
    mock_sse.event = "message"
    mock_sse.data = "[DONE]"

    async def mock_aiter_sse():
        yield mock_sse

    mock_event_source = MagicMock()
    mock_event_source.aiter_sse = mock_aiter_sse
    mock_event_source.response = MagicMock()
    mock_event_source.response.raise_for_status = MagicMock()

    class MockAconnectSse:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return mock_event_source

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    req = AgentChatRequest(session_id="session123", message="Hello")

    with (
        patch("agent_adapters.hermes.aconnect_sse", new=MockAconnectSse),
        patch.object(
            adapter, "get_chat_history", new_callable=AsyncMock
        ) as mock_history,
        patch.object(
            adapter, "get_session_workspace", new_callable=AsyncMock
        ) as mock_workspace,
    ):
        mock_history.return_value = []
        mock_workspace.return_value = None
        events = []
        async for event in adapter.stream_chat(req):
            events.append(event)

        assert len(events) == 1
        assert events[0].type == "error"
        assert events[0].data == {
            "message": "Hermes ended the chat turn without returning a response."
        }


@pytest.mark.asyncio
async def test_hermes_adapter_get_chat_history():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": 1780423800.0,
                "trace_id": "trace1",
            },
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "Hi there!"}],
                "timestamp": 1780423805.0,
                "trace_id": "trace2",
            },
        ]
    }

    with patch.object(
        adapter, "_request_with_fallback", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response
        history = await adapter.get_chat_history("session123")

        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[0].timestamp == 1780423800000
        assert history[0].trace_id == "trace1"

        assert history[1].role == "assistant"
        assert history[1].content == "Hi there!"
        assert history[1].timestamp == 1780423805000
        assert history[1].trace_id == "trace2"

        mock_request.assert_called_once_with(
            "GET",
            "/api/sessions/session123/messages",
            timeout=10.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_create_session_with_instructions():
    adapter = HermesAdapter("http://127.0.0.1:8642", "test-key")

    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "session": {
            "session_id": "session_123",
            "title": "Untitled",
            "created_at": 1780423855.15,
            "updated_at": 1780423855.15,
            "message_count": 0,
        }
    }

    with patch.object(
        adapter, "_request_with_fallback", new_callable=AsyncMock
    ) as mock_request:
        mock_request.return_value = mock_response
        session_info = await adapter.create_session(
            "/home/workspace", instructions="Please place files in root"
        )

        assert session_info.session_id == "session_123"

        mock_request.assert_called_once_with(
            "POST",
            "/api/sessions",
            json_body={
                "workspace": "/home/workspace",
                "instructions": "Please place files in root",
            },
            timeout=10.0,
        )
