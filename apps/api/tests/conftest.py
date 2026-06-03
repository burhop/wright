"""
Shared test fixtures for Wright API tests.

Provides:
  - Temporary SQLite database for test isolation
  - mock_agent_engine fixture for simulating HermesAdapter
  - httpx TestClient fixture with traced request support
  - ErrorResponse assertion helper
"""
import os
import tempfile
import time
import uuid

import pytest

# Create a temporary SQLite database for the test session
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix="-test.db")
os.close(temp_db_fd)

# Set the environment variables before importing any application code
os.environ["DATABASE_PATH"] = temp_db_path


@pytest.fixture(autouse=True)
def set_testing_env(monkeypatch):
    monkeypatch.setenv("WRIGHT_TESTING", "1")


@pytest.fixture(scope="session", autouse=True)
def run_api_migrations():
    from api.database.migrate import run_migrations
    run_migrations()

    yield

    # Cleanup temp database
    if os.path.exists(temp_db_path):
        try:
            os.unlink(temp_db_path)
        except Exception:
            pass


# ── Mock Agent Engine ─────────────────────────────────────────────────────
class _MockSession:
    def __init__(self, session_id: str, workspace: str = "/tmp/test-workspace"):
        self.session_id = session_id
        self.title = "Test Session"
        self.created_at = int(time.time())
        self.workspace = workspace


class MockAgentEngine:
    """A fake BaseAgentEngine that can be used in tests without a live agent backend."""

    def __init__(self):
        self._sessions: dict[str, _MockSession] = {}
        self._active_chat: dict[str, str] = {}
        self._chat_responses: dict[str, list[str]] = {}

    async def create_session(self, workspace: str = "/tmp/test-workspace") -> _MockSession:
        sid = str(uuid.uuid4())
        session = _MockSession(sid, workspace)
        self._sessions[sid] = session
        return session

    async def list_sessions(self) -> list[_MockSession]:
        return list(self._sessions.values())

    async def delete_session(self, session_id: str) -> dict:
        if session_id not in self._sessions:
            raise Exception(f"Session {session_id} not found")
        del self._sessions[session_id]
        return {"success": True}

    async def get_session_workspace(self, session_id: str) -> str | None:
        session = self._sessions.get(session_id)
        return session.workspace if session else None

    async def start_chat(self, request) -> dict:
        stream_id = str(uuid.uuid4())
        self._chat_responses[stream_id] = ["Hello!", "How can I help?"]
        return {"stream_id": stream_id, "trace_id": "test-trace-id"}

    async def stream_response(self, stream_id: str):
        responses = self._chat_responses.get(stream_id, [])
        for chunk in responses:
            yield {"type": "message", "data": chunk}
        yield {"type": "done"}

    async def check_health(self) -> dict:
        return {"state": "connected", "latencyMs": 1.0}

    async def save_context(self, session_id: str, workspace_id: str) -> bool:
        return True

    async def load_context(self, session_id: str, workspace_id: str) -> dict | None:
        return None

    async def get_chat_history(self, session_id: str) -> list:
        return []

    def set_fail_create_session(self, should_fail: bool = True):
        """Test helper to make create_session raise errors."""
        if should_fail:
            self._original_create = self.create_session
            async def failing_create(*args, **kwargs):
                raise Exception("Agent backend unavailable")
            self.create_session = failing_create
        elif hasattr(self, '_original_create'):
            self.create_session = self._original_create


@pytest.fixture
def mock_agent_engine():
    """Provide a MockAgentEngine instance for tests."""
    return MockAgentEngine()


@pytest.fixture
def client(mock_agent_engine):
    """Provide a TestClient with the mock agent engine injected."""
    from httpx import ASGITransport, AsyncClient
    from api.main import app

    app.state.agent_engine = mock_agent_engine
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://testserver")


@pytest.fixture
def sync_client(mock_agent_engine):
    """Provide a synchronous TestClient for non-async tests."""
    from fastapi.testclient import TestClient
    from api.main import app

    app.state.agent_engine = mock_agent_engine
    return TestClient(app)


# ── Error Response Helper ─────────────────────────────────────────────────
def assert_error_response(response, expected_status: int, expected_error_code: str | None = None):
    """Assert an API response matches the ErrorResponse contract.

    Verifies:
      - Status code matches expected
      - Body contains error_code, message, trace_id fields
      - error_code matches expected value if provided
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert "error_code" in data, f"Missing error_code in response: {data}"
    assert "message" in data, f"Missing message in response: {data}"
    assert "trace_id" in data, f"Missing trace_id in response: {data}"
    if expected_error_code:
        assert data["error_code"] == expected_error_code, (
            f"Expected error_code={expected_error_code}, got {data['error_code']}"
        )
    return data
