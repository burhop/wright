import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent_adapters import HermesAdapter, AgentChatRequest


@pytest.mark.asyncio
async def test_hermes_adapter_check_health_success():
    adapter = HermesAdapter("http://127.0.0.1:8788")

    mock_response = MagicMock()
    mock_response.status_code = 200

    # We patch httpx.AsyncClient.get to return a mock response
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await adapter.check_health()

        assert result["state"] == "connected"
        assert result["latencyMs"] > 0
        mock_get.assert_called_once_with("http://127.0.0.1:8788/health", timeout=5.0)


@pytest.mark.asyncio
async def test_hermes_adapter_check_health_failure():
    adapter = HermesAdapter("http://127.0.0.1:8788")

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Connection refused")
        result = await adapter.check_health()

        assert result["state"] == "disconnected"
        assert result["latencyMs"] == 0.0


@pytest.mark.asyncio
async def test_hermes_adapter_create_session():
    adapter = HermesAdapter("http://127.0.0.1:8788")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "session": {
            "session_id": "test_session_123",
            "title": "Test Title",
            "created_at": 1780423855.15,
            "updated_at": 1780423855.15,
            "message_count": 5,
        }
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        session_info = await adapter.create_session("/home/workspace")

        assert session_info.session_id == "test_session_123"
        assert session_info.title == "Test Title"
        assert session_info.created_at == 1780423855150
        assert session_info.updated_at == 1780423855150
        assert session_info.message_count == 5

        mock_post.assert_called_once_with(
            "http://127.0.0.1:8788/api/session/new",
            json={"workspace": "/home/workspace"},
            headers=adapter.headers,
            timeout=10.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_list_sessions():
    adapter = HermesAdapter("http://127.0.0.1:8788")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sessions": [
            {
                "session_id": "session1",
                "title": "Title 1",
                "created_at": 1780423800.0,
                "updated_at": 1780423810.0,
                "message_count": 2,
            }
        ]
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        sessions = await adapter.list_sessions()

        assert len(sessions) == 1
        assert sessions[0].session_id == "session1"
        assert sessions[0].title == "Title 1"
        assert sessions[0].created_at == 1780423800000
        assert sessions[0].message_count == 2

        mock_get.assert_called_once_with(
            "http://127.0.0.1:8788/api/sessions?all_profiles=0",
            headers=adapter.headers,
            timeout=10.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_delete_session():
    adapter = HermesAdapter("http://127.0.0.1:8788")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"ok": True}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await adapter.delete_session("session1")

        assert result is True
        mock_post.assert_called_once_with(
            "http://127.0.0.1:8788/api/session/delete",
            json={"session_id": "session1"},
            headers=adapter.headers,
            timeout=10.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_start_chat():
    adapter = HermesAdapter("http://127.0.0.1:8788")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "stream_id": "stream123",
        "session_id": "session123",
    }

    req = AgentChatRequest(session_id="session123", message="Hello")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await adapter.start_chat(req)

        assert res.stream_id == "stream123"
        assert res.session_id == "session123"

        mock_post.assert_called_once_with(
            "http://127.0.0.1:8788/api/chat/start",
            json={"session_id": "session123", "message": "Hello", "profile": "wright"},
            headers=adapter.headers,
            timeout=10.0,
        )


@pytest.mark.asyncio
async def test_hermes_adapter_stream_response():
    adapter = HermesAdapter("http://127.0.0.1:8788")

    # Mock EventSource and its events
    mock_sse_1 = MagicMock()
    mock_sse_1.event = "token"
    mock_sse_1.data = '{"text": "Hello"}'

    mock_sse_2 = MagicMock()
    mock_sse_2.event = "stream_end"
    mock_sse_2.data = '{"session_id": "session123"}'

    async def mock_aiter_sse():
        yield mock_sse_1
        yield mock_sse_2

    mock_event_source = MagicMock()
    mock_event_source.aiter_sse = mock_aiter_sse

    # We patch aconnect_sse context manager
    class MockAconnectSse:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return mock_event_source

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    with patch("agent_adapters.hermes.aconnect_sse", new=MockAconnectSse):
        events = []
        async for event in adapter.stream_response("stream123"):
            events.append(event)

        assert len(events) == 2
        assert events[0].type == "token"
        assert events[0].data == {"text": "Hello"}
        assert events[1].type == "stream_end"
        assert events[1].data == {"session_id": "session123"}


@pytest.mark.asyncio
async def test_hermes_adapter_get_chat_history():
    adapter = HermesAdapter("http://127.0.0.1:8788")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "session": {
            "session_id": "session123",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": 1780423800.0,
                    "trace_id": "trace1",
                },
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "Hi there!"}],
                    "timestamp": 1780423805000,
                    "trace_id": "trace2",
                },
            ],
        }
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
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

        mock_get.assert_called_once_with(
            "http://127.0.0.1:8788/api/session?session_id=session123&messages=1",
            headers=adapter.headers,
            timeout=10.0,
        )
