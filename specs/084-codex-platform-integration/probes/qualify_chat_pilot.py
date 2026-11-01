"""Bounded real-runtime chat/gateway proof against a credential-free local provider.

Use Wright's Python, --sdk-python pointing at the pinned isolated SDK environment,
and a fresh absolute --output outside Wright's protected application directory.
This qualifies the local protocol path, not authenticated model entitlement or MCP
stdio interoperability. Original configurations/campaigns are never used.
"""

import argparse
import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
from types import SimpleNamespace


def sse(item, number):
    return [
        {
            "type": "response.created",
            "response": {
                "id": f"response-{number}",
                "status": "in_progress",
                "output": [],
            },
        },
        {"type": "response.output_item.done", "output_index": 0, "item": item},
        {
            "type": "response.completed",
            "response": {
                "id": f"response-{number}",
                "status": "completed",
                "output": [item],
            },
        },
    ]


async def qualify(output, sdk_python):
    db = output / "state.db"
    os.environ.update(
        DATABASE_PATH=str(db),
        WRIGHT_SECRETS_PATH=str(output / "secrets.json"),
        WRIGHT_AUTH_MODE="compat",
        WRIGHT_API_MCP_AUTOSTART="0",
    )
    from api.database.migrate import run_migrations
    from api.composition import build_api_gateway_service
    from api.config import McpTransportSettings
    from api.services.codex_chat_gateway import prepare_codex_chat_gateway
    from agent_adapters.base import AgentChatRequest
    from agent_adapters.codex import CodexAdapter
    from agent_adapters.codex_transport import CodexRuntimeSettings
    from core.agent_platform import AgentPlatformConflict
    from data_vault.agent_platform_repository import AgentPlatformRepository
    from data_vault.state_store import connect_state_db
    from tool_registry import McpEngine
    from workspace_service import WorkspaceService
    from workspace_service.adapters.runtime import create_workspace
    from workspace_service.chat_invocation_evidence import ChatInvocationRecorder

    run_migrations()
    workspace = output / "workspace"
    workspace.mkdir()
    engine = McpEngine(str(db))
    gateway = build_api_gateway_service(
        str(db), engine, McpTransportSettings.from_env()
    )
    service = WorkspaceService(str(db))
    captured = []
    mode = {"value": "gateway"}
    received = threading.Event()
    release = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            size = int(self.headers["Content-Length"])
            if size > 2_097_152 or len(captured) >= 8:
                self.send_error(400)
                return
            body = json.loads(self.rfile.read(size))
            captured.append(body)
            number = len(captured)
            last = body.get("input", [])[-1] if body.get("input") else {}
            needs_tool = (
                mode["value"] in {"gateway", "denied"}
                and last.get("type") != "function_call_output"
            )
            if needs_tool:
                item = {
                    "type": "function_call",
                    "id": f"tool-{number}",
                    "call_id": f"fixture-call-{number}",
                    "name": "wright__workspace_status",
                    "arguments": "{}"
                    if mode["value"] == "gateway"
                    else '{"workspace_id":"another"}',
                }
            else:
                item = {
                    "type": "message",
                    "id": f"message-{number}",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Local chat fixture complete.",
                            "annotations": [],
                        }
                    ],
                }
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            try:
                for index, event in enumerate(sse(item, number)):
                    self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
                    self.wfile.flush()
                    if mode["value"] == "cancel" and index == 0:
                        received.set()
                        release.wait(timeout=10)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = output / "runtime"
    home = root / "home"
    home.mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    (home / "config.toml").write_text(
        'model_provider="qualification"\n[model_providers.qualification]\nname="local chat fixture"\nwire_api="responses"\n'
        f'base_url="http://127.0.0.1:{server.server_port}/v1"\nrequires_openai_auth=false\nrequest_max_retries=0\nstream_max_retries=0\n'
    )
    settings = CodexRuntimeSettings(root, python=sdk_python, gateway_enabled=True)
    adapter = CodexAdapter(
        str(db),
        settings,
        repository=AgentPlatformRepository(str(db)),
        model="gpt-6.1-sol",
        auth_method="fixture",
    )
    restarted = None
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway_service=gateway)),
        state=SimpleNamespace(principal_id="local-admin"),
    )
    scope = SimpleNamespace(workspace_id="chat-pilot", workspace_dir=str(workspace))

    async def chat(agent, session, attempt):
        handler, cleanup = await prepare_codex_chat_gateway(
            request, agent, scope, session.session_id
        )
        recorder = ChatInvocationRecorder(
            service,
            workspace_id=scope.workspace_id,
            workspace_dir=scope.workspace_dir,
            session_id=session.session_id,
            request_id=attempt,
        )
        try:
            return [
                event
                async for event in agent.stream_chat(
                    AgentChatRequest(
                        session.session_id,
                        "Local fixture input.",
                        trace_id=attempt,
                        invocation_observer=recorder.observe,
                        gateway_handler=handler,
                    )
                )
            ]
        finally:
            await cleanup()

    try:
        session = await adapter.create_session(str(workspace))
        create_workspace(
            str(db),
            scope.workspace_id,
            session.session_id,
            str(workspace),
            workspace_name="Codex local pilot",
            agent_id="codex",
        )
        first = await chat(adapter, session, "gateway-success")
        assert first[-1].data["status"] == "completed", first
        assert any(
            event.type == "token" and "complete" in event.data["content"]
            for event in first
        )
        tool_outputs = [
            item
            for body in captured
            for item in body.get("input", [])
            if item.get("type") == "function_call_output"
        ]
        assert any(
            "chat-pilot" in str(item.get("output"))
            and session.session_id in str(item.get("output"))
            for item in tool_outputs
        ), tool_outputs
        saved = adapter.repository.get_session(session.session_id)
        assert saved.gateway_binding_digest
        await adapter.close()
        restarted = CodexAdapter(
            str(db),
            settings,
            repository=AgentPlatformRepository(str(db)),
            model="gpt-6.1-sol",
            auth_method="fixture",
        )
        assert [row.session_id for row in await restarted.list_sessions()] == [
            session.session_id
        ]
        history = await restarted.get_chat_history(session.session_id)
        assert [message.role for message in history] == ["user", "assistant"]
        mode["value"] = "denied"
        denied = await chat(restarted, session, "gateway-denial")
        assert denied[-1].data["status"] == "completed", denied
        denied_outputs = [
            item
            for body in captured
            for item in body.get("input", [])
            if item.get("type") == "function_call_output"
            and item.get("call_id") == "fixture-call-3"
        ]
        assert denied_outputs and all(
            item.get("output") == [] for item in denied_outputs
        ), denied_outputs
        request.state.principal_id = "different-principal"
        try:
            await prepare_codex_chat_gateway(
                request, restarted, scope, session.session_id
            )
        except AgentPlatformConflict:
            pass
        else:
            raise AssertionError("Gateway principal drift was accepted")
        request.state.principal_id = "local-admin"
        foreign_scope = SimpleNamespace(
            workspace_id="another", workspace_dir=str(workspace)
        )
        try:
            await prepare_codex_chat_gateway(
                request, restarted, foreign_scope, session.session_id
            )
        except ValueError:
            pass
        else:
            raise AssertionError("Foreign gateway scope was accepted")
        mode["value"] = "cancel"
        task = asyncio.create_task(chat(restarted, session, "cancellation"))
        assert await asyncio.to_thread(received.wait, 5)
        assert await restarted.cancel_chat(session.session_id)
        cancelled = await asyncio.wait_for(task, 10)
        assert cancelled[-1].data["status"] == "interrupted", cancelled
        assert (
            restarted.repository.get_turn(session.session_id, "cancellation").status
            == "interrupted"
        )
        assert not (await restarted.get_invocation_capabilities()).available
        with connect_state_db(str(db), read_only=True) as connection:
            calls = connection.execute(
                "SELECT target_name,workspace_id,principal_id,outcome FROM gateway_audit_events WHERE operation='tool.call'"
            ).fetchall()
            assert [tuple(row) for row in calls] == [
                ("workspace_status", "chat-pilot", "local-admin", "started"),
                ("workspace_status", "chat-pilot", "local-admin", "succeeded"),
            ], [dict(row) for row in calls]
            tables = [
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%audit%'"
                )
            ]
        report = {
            "schema": "wright.codex-chat-pilot-qualification/1",
            "result": "PASSED_LOCAL_CHAT_GATEWAY_PILOT",
            "sdk_version": "0.162.1",
            "runtime_version": "0.162.1",
            "model": "gpt-6.1-sol",
            "reasoning_effort": "high",
            "live_openai_request": False,
            "credentials_present": False,
            "gateway_transport": "app-server dynamic-tool callback to existing Wright GatewayService",
            "native_mcp_stdio_qualified": False,
            "no_tools_qualified": False,
            "native_tool_exception": "wright.codex-native-chat-tools-exception/1",
            "history_after_restart": [message.role for message in history],
            "persisted_cancellation": "interrupted",
            "gateway_binding_frozen": bool(saved.gateway_binding_digest),
            "gateway_principal_drift_denied": True,
            "gateway_foreign_scope_denied": True,
            "gateway_malformed_arguments_denied": True,
            "gateway_audited_tool_calls": sum(
                row["outcome"] == "succeeded" for row in calls
            ),
            "audit_tables": tables,
            "provider_request_count": len(captured),
            "process_ui_authoring_available": False,
            "workflow_tasks_available": False,
        }
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        release.set()
        (output / "fixture-provider-requests.json").write_text(
            json.dumps(captured, indent=2) + "\n"
        )
        await adapter.close()
        if restarted:
            await restarted.close()
        await gateway.shutdown()
        await service.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sdk-python", type=Path, required=True)
    args = parser.parse_args()
    if os.name == "nt":
        raise SystemExit("Native Windows cleanup remains unqualified")
    output = args.output.absolute()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    asyncio.run(qualify(output, args.sdk_python.absolute()))


if __name__ == "__main__":
    main()
