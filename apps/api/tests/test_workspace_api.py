import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from api.main import app
from agent_adapters import BaseAgentEngine, AgentSessionInfo, AgentChatRequest, AgentChatStartResponse, AgentStreamEvent
from typing import AsyncIterator

# Mock Agent Engine to return a temporary workspace path
class MockAgentEngine(BaseAgentEngine):
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path

    async def check_health(self) -> dict:
        return {"state": "connected", "latencyMs": 1.0}

    async def create_session(self, workspace: str | None = None) -> AgentSessionInfo:
        return AgentSessionInfo(
            session_id="mock-session",
            title="Mock Session",
            created_at=1000,
            updated_at=1000,
            message_count=0
        )

    async def list_sessions(self) -> list[AgentSessionInfo]:
        return []

    async def delete_session(self, session_id: str) -> bool:
        return True

    async def start_chat(self, request: AgentChatRequest) -> AgentChatStartResponse:
        return AgentChatStartResponse(stream_id="stream-1", session_id=request.session_id)

    async def stream_response(self, stream_id: str) -> AsyncIterator[AgentStreamEvent]:
        yield AgentStreamEvent(type="token", data={"text": "hello"})

    async def get_session_workspace(self, session_id: str) -> str | None:
        return self.workspace_path

@pytest.fixture
def workspace_setup():
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create designs folder
        designs_dir = os.path.join(temp_dir, "designs")
        os.makedirs(designs_dir, exist_ok=True)
        
        # Create a sample stl file
        stl_path = os.path.join(designs_dir, "bracket.stl")
        with open(stl_path, "wb") as f:
            f.write(b"solid mesh data here")
            
        # Create a sample scad file
        scad_path = os.path.join(temp_dir, "model.scad")
        with open(scad_path, "w") as f:
            f.write("cube([10, 20, 30]);")
            
        yield temp_dir

@pytest.fixture
def client(workspace_setup) -> TestClient:
    mock_engine = MockAgentEngine(workspace_setup)
    app.state.agent_engine = mock_engine
    with TestClient(app) as c:
        yield c

def test_list_workspace_files(client):
    response = client.get("/api/workspace/files", params={"session_id": "test-session"})
    assert response.status_code == 200
    data = response.json()
    assert "workspace" in data
    root = data["workspace"]
    assert root["type"] == "directory"
    
    # Check children
    children = root["children"]
    assert len(children) >= 2
    
    names = [c["name"] for c in children]
    assert "designs" in names
    assert "model.scad" in names
    
    # Find designs folder and check child file
    designs_node = next(c for c in children if c["name"] == "designs")
    assert designs_node["type"] == "directory"
    assert len(designs_node["children"]) == 1
    assert designs_node["children"][0]["name"] == "bracket.stl"
    assert designs_node["children"][0]["path"] == "/designs/bracket.stl"

def test_get_file_content_success(client):
    # Fetch .scad file content
    response = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/model.scad"}
    )
    assert response.status_code == 200
    assert response.text == "cube([10, 20, 30]);"
    assert "text/plain" in response.headers["content-type"]

    # Fetch .stl file content (binary stream)
    response_stl = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/designs/bracket.stl"}
    )
    assert response_stl.status_code == 200
    assert response_stl.content == b"solid mesh data here"
    assert "application/octet-stream" in response_stl.headers["content-type"]

def test_get_file_content_not_found(client):
    response = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/missing.stl"}
    )
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]

def test_get_file_content_traversal_blocked(client):
    # Attempt directory traversal out of workspace root
    response = client.get(
        "/api/workspace/files/content",
        params={"session_id": "test-session", "path": "/../../etc/passwd"}
    )
    assert response.status_code == 400
    assert "Access denied" in response.json()["detail"]
