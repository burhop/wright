import asyncio
import json
from types import SimpleNamespace

import pytest
from starlette.requests import Request

from agent_adapters import AgentChatRequest, AgentStreamEvent
from api.routers.agent import (
    ChatRequest,
    ChatStreamJob,
    _restart_hermes_gateway_process,
    chat,
)
from fastapi import HTTPException


class _SlowEngine:
    async def stream_chat(self, request):
        await asyncio.sleep(0.03)
        yield AgentStreamEvent(
            type="progress",
            data={
                "server": "geometry",
                "tool": "geometry__create",
                "title": "Create geometry",
                "status": "running",
            },
        )
        yield AgentStreamEvent(type="stream_end", data={})


class _CompletedThenSlowEngine:
    async def stream_chat(self, request):
        yield AgentStreamEvent(
            type="progress",
            data={
                "server": "geometry",
                "tool": "geometry__create",
                "title": "Create geometry",
                "status": "completed",
            },
        )
        await asyncio.sleep(0.03)
        yield AgentStreamEvent(type="stream_end", data={})


class _FailingEngine:
    async def stream_chat(self, request):
        if False:
            yield
        raise RuntimeError("sentinel C:\\private\\agent-token.txt")


class _DisconnectedLlmEngine:
    async def check_llm_backend_health(self):
        return {
            "state": "disconnected",
            "error": "Codex auth expired",
        }

    async def stream_chat(self, request):
        if False:
            yield
        raise AssertionError("chat should not start with disconnected LLM")


class _AttachFailureJob:
    stream_id = "attach-failure-stream"
    started_at_ms = 0

    async def stream_from(self, index=0):
        if False:
            yield
        raise RuntimeError("sentinel C:\\private\\attach-token.txt")


class _AttachFailureRegistry:
    async def start(self, request, engine):
        return _AttachFailureJob()


def test_restart_hermes_gateway_uses_supported_cli(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "api.routers.agent.shutil.which",
        lambda name: "hermes.exe" if name == "hermes" else None,
    )
    monkeypatch.setattr("api.routers.agent.Path.is_file", lambda _path: False)

    def run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("api.routers.agent.subprocess.run", run)

    _restart_hermes_gateway_process()

    assert captured["command"] == ["hermes.exe", "gateway", "restart"]
    assert captured["kwargs"]["timeout"] == 30


def test_restart_hermes_gateway_finds_official_windows_install(monkeypatch):
    captured = {}
    executable = (
        "C:\\Users\\tester\\AppData\\Local\\hermes\\hermes-agent"
        "\\venv\\Scripts\\hermes.exe"
    )
    monkeypatch.setattr("api.routers.agent.shutil.which", lambda _name: None)
    monkeypatch.setattr(
        "api.routers.agent.official_hermes_cli_path", lambda: executable
    )
    monkeypatch.setattr("api.routers.agent.Path.is_file", lambda _path: False)

    def run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("api.routers.agent.subprocess.run", run)

    _restart_hermes_gateway_process()

    assert captured["command"] == [executable, "gateway", "restart"]
    assert captured["kwargs"]["timeout"] == 30


def test_restart_hermes_gateway_prefers_supervisor_in_appliance(monkeypatch):
    captured = {}

    def which(name):
        return {
            "supervisorctl": "/usr/bin/supervisorctl",
            "hermes": "/opt/hermes/bin/hermes",
        }.get(name)

    monkeypatch.setattr("api.routers.agent.shutil.which", which)
    monkeypatch.setattr("api.routers.agent.Path.is_file", lambda _path: True)

    def run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout="started", stderr="")

    monkeypatch.setattr("api.routers.agent.subprocess.run", run)

    _restart_hermes_gateway_process()

    assert captured["command"] == [
        "/usr/bin/supervisorctl",
        "-c",
        "/etc/supervisor/conf.d/wright.conf",
        "restart",
        "hermes-gateway",
    ]
    assert captured["kwargs"]["timeout"] == 30


def test_restart_hermes_gateway_failure_includes_diagnostics(monkeypatch):
    monkeypatch.setattr(
        "api.routers.agent.shutil.which",
        lambda name: "hermes.exe" if name == "hermes" else None,
    )
    monkeypatch.setattr("api.routers.agent.Path.is_file", lambda _path: False)

    def run(_command, **_kwargs):
        return SimpleNamespace(
            returncode=19,
            stdout="",
            stderr="gateway lock could not be acquired",
        )

    monkeypatch.setattr("api.routers.agent.subprocess.run", run)

    with pytest.raises(RuntimeError) as error:
        _restart_hermes_gateway_process()

    assert "Hermes gateway restart failed after workspace rebinding (exit 19)" in str(
        error.value
    )
    assert "gateway lock could not be acquired" in str(error.value)


@pytest.mark.asyncio
async def test_chat_stream_emits_planning_and_elapsed_heartbeat_progress():
    request = AgentChatRequest(session_id="session-1", message="Create a part")
    job = ChatStreamJob("session-1", request, _SlowEngine(), heartbeat_seconds=0.01)
    job.start()

    events = [event async for event in job.stream_from()]
    progress = [data for event_type, data in events if event_type == "progress"]

    assert progress[0]["title"] == "Planning request"
    assert any(item.get("heartbeat") for item in progress)
    assert any(item.get("tool") == "geometry__create" for item in progress)


@pytest.mark.asyncio
async def test_completed_tool_heartbeat_does_not_claim_the_turn_is_finishing():
    request = AgentChatRequest(session_id="session-1", message="Create a part")
    job = ChatStreamJob(
        "session-1", request, _CompletedThenSlowEngine(), heartbeat_seconds=0.01
    )
    job.start()

    events = [event async for event in job.stream_from()]
    progress = [data for event_type, data in events if event_type == "progress"]

    assert any(item.get("title") == "Create geometry" for item in progress)
    assert all("Solid Edge" not in item.get("message", "") for item in progress)
    heartbeats = [item for item in progress if item.get("heartbeat")]
    assert all(item["title"] == "Working on request" for item in heartbeats)


@pytest.mark.asyncio
async def test_chat_job_failure_emits_generic_trace_bearing_error():
    request = AgentChatRequest(
        session_id="session-1",
        message="Create a part",
        trace_id="trace-job-123",
    )
    job = ChatStreamJob("session-1", request, _FailingEngine())
    job.start()

    events = [event async for event in job.stream_from()]
    errors = [data for event_type, data in events if event_type == "error"]

    assert errors == [
        {
            "message": "Agent response stream failed.",
            "trace_id": "trace-job-123",
        }
    ]
    assert "sentinel" not in json.dumps(events)


@pytest.mark.asyncio
async def test_chat_attach_failure_emits_generic_trace_bearing_error(monkeypatch):
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/agent/chat",
            "headers": [],
            "app": SimpleNamespace(state=SimpleNamespace()),
        }
    )

    async def no_mcp_activation(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "api.routers.agent.ensure_workspace_mcp_servers_active",
        no_mcp_activation,
    )
    monkeypatch.setattr(
        "api.routers.agent.get_chat_stream_registry",
        lambda request: _AttachFailureRegistry(),
    )

    response = await chat(
        ChatRequest(session_id="session-1", message="Create a part"),
        request,
        _FailingEngine(),
    )
    chunks = [chunk async for chunk in response.body_iterator]
    body = "".join(chunks)

    assert "Agent response stream failed." in body
    assert '"trace_id"' in body
    assert "sentinel" not in body


@pytest.mark.asyncio
async def test_chat_preflight_reports_disconnected_llm(monkeypatch):
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/agent/chat",
            "headers": [],
            "app": SimpleNamespace(state=SimpleNamespace()),
        }
    )

    async def no_mcp_activation(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "api.routers.agent.ensure_workspace_mcp_servers_active",
        no_mcp_activation,
    )

    with pytest.raises(HTTPException) as error:
        await chat(
            ChatRequest(session_id="session-1", message="Create a part"),
            request,
            _DisconnectedLlmEngine(),
        )

    assert error.value.status_code == 503
    assert error.value.detail == "LLM backend is not ready: Codex auth expired"


@pytest.mark.asyncio
async def test_no_tools_chat_skips_mcp_activation_and_forwards_thinking(monkeypatch):
    class FailingSyncManager:
        def sync_workspace_tools(self, _session_id):
            raise AssertionError("no-tools turn must not sync workspace tools")

    class CaptureRegistry:
        request = None

        async def start(self, request, _engine):
            self.request = request
            return _AttachFailureJob()

    capture_registry = CaptureRegistry()
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/agent/chat",
            "headers": [],
            "app": SimpleNamespace(
                state=SimpleNamespace(agent_sync_manager=FailingSyncManager())
            ),
        }
    )

    async def ready(_engine):
        return None

    async def unexpected_mcp_activation(*_args, **_kwargs):
        raise AssertionError("no-tools turn must not activate MCP servers")

    def unexpected_rivet_binding(*_args, **_kwargs):
        raise AssertionError("no-tools turn must not mirror a Rivet binding")

    monkeypatch.setattr("api.routers.agent.ensure_llm_backend_ready", ready)
    monkeypatch.setattr(
        "api.routers.agent.ensure_workspace_mcp_servers_active",
        unexpected_mcp_activation,
    )
    monkeypatch.setattr(
        "api.routers.agent._mirror_active_rivet_workflow_to_gateway_binding",
        unexpected_rivet_binding,
    )
    monkeypatch.setattr(
        "api.routers.agent.get_chat_stream_registry",
        lambda _request: capture_registry,
    )

    await chat(
        ChatRequest(
            session_id="session-1",
            message="Create a concise design brief.",
            thinking_level="high",
            tool_policy="none",
            provider="openai-codex",
            model="gpt-test",
            require_model_lock=True,
        ),
        request,
        _FailingEngine(),
    )

    assert capture_registry.request is not None
    assert capture_registry.request.thinking_level == "high"
    assert capture_registry.request.tool_policy == "none"
    assert capture_registry.request.model_provider == "openai-codex"
    assert capture_registry.request.model == "gpt-test"
    assert capture_registry.request.require_model_lock is True
