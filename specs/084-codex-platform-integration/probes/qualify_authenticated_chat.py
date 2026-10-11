"""Two bounded ChatGPT turns using an isolated copy of authorized credentials.

No provider substitution, source configuration writes, workflow execution or native
MCP qualification. Credential bytes and account identity never enter the report.
"""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace


async def qualify(output, sdk_python, auth_file):
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
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
    from data_vault.agent_platform_repository import AgentPlatformRepository
    from tool_registry import McpEngine
    from workspace_service import WorkspaceService
    from workspace_service.adapters.runtime import create_workspace
    from workspace_service.chat_invocation_evidence import ChatInvocationRecorder

    source_digest = hashlib.sha256(auth_file.read_bytes()).digest()
    home = output / "runtime" / "home"
    home.mkdir(mode=0o700, parents=True)
    home.parent.chmod(0o700)
    private_auth = home / "auth.json"
    with private_auth.open("xb") as handle:
        os.chmod(private_auth, 0o600)
        handle.write(auth_file.read_bytes())
    run_migrations()
    workspace = output / "workspace"
    workspace.mkdir()
    gateway = build_api_gateway_service(
        str(db), McpEngine(str(db)), McpTransportSettings.from_env()
    )
    service = WorkspaceService(str(db))
    settings = CodexRuntimeSettings(
        home.parent, python=sdk_python, gateway_enabled=True
    )

    def new_adapter():
        return CodexAdapter(
            str(db),
            settings,
            repository=AgentPlatformRepository(str(db)),
            model="gpt-6.1-sol",
            effort="high",
            auth_method="chatgpt",
        )

    adapter = new_adapter()
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(gateway_service=gateway)),
        state=SimpleNamespace(principal_id="local-admin"),
    )
    scope = SimpleNamespace(
        workspace_id="authenticated-chat-pilot", workspace_dir=str(workspace)
    )
    report = {
        "schema": "wright.codex-authenticated-chat-qualification/1",
        "sdk_version": "0.162.1",
        "runtime_version": "0.162.1",
        "model": "gpt-6.1-sol",
        "reasoning_effort": "high",
        "auth_route": "chatgpt",
        "live_openai_request": True,
        "no_tools_qualified": False,
        "process_ui_authoring_available": False,
        "workflow_tasks_available": False,
        "native_mcp_stdio_qualified": False,
        "result": "FAILED",
        "turns": [],
    }
    try:
        async with asyncio.timeout(240):
            health = await adapter.check_health()
            assert health["state"] == "connected", "Authenticated readiness failed"
            session = await adapter.create_session(str(workspace))
            create_workspace(
                str(db),
                scope.workspace_id,
                session.session_id,
                str(workspace),
                workspace_name="Isolated authenticated Codex pilot",
                agent_id="codex",
            )

            async def chat(attempt, message):
                handler, close = await prepare_codex_chat_gateway(
                    request, adapter, scope, session.session_id
                )
                recorder = ChatInvocationRecorder(
                    service,
                    workspace_id=scope.workspace_id,
                    workspace_dir=scope.workspace_dir,
                    session_id=session.session_id,
                    request_id=attempt,
                )
                try:
                    events = [
                        event
                        async for event in adapter.stream_chat(
                            AgentChatRequest(
                                session_id=session.session_id,
                                message=message,
                                trace_id=attempt,
                                invocation_observer=recorder.observe,
                                gateway_handler=handler,
                            )
                        )
                    ]
                finally:
                    await close()
                terminal = (
                    events[-1].data.get("status")
                    if events and events[-1].type == "stream_end"
                    else None
                )
                report["turns"].append(
                    {
                        "attempt": attempt,
                        "terminal": terminal,
                        "token_events": sum(event.type == "token" for event in events),
                        "receipt": adapter.repository.get_turn(
                            session.session_id, attempt
                        ).status,
                    }
                )
                assert terminal == "completed", "Authenticated turn did not complete"
                assert any(event.type == "token" for event in events), (
                    "No assistant response observed"
                )

            await chat(
                "authenticated-first",
                "Reply with exactly 'Wright chat ready'. Do not call any tools.",
            )
            await adapter.close()
            adapter = new_adapter()
            history = await adapter.get_chat_history(session.session_id)
            assert [row.role for row in history] == ["user", "assistant"], (
                "Restart history missing"
            )
            report["history_after_restart"] = [row.role for row in history]
            await chat(
                "authenticated-continuation",
                "Reply with exactly the same phrase you just used. Do not call any tools.",
            )
            report["same_platform_and_thread_continued"] = True
            report["result"] = "PASSED_AUTHENTICATED_CHAT_RESTART"
    except Exception as error:
        # Never print upstream exception messages containing account details.
        report["failure_class"] = type(error).__name__
        report["failure_code"] = getattr(
            error, "code", "AUTHENTICATED_CHAT_NOT_QUALIFIED"
        )
    finally:
        await adapter.close()
        await gateway.shutdown()
        await service.close()
        report["original_auth_file_unchanged"] = (
            hashlib.sha256(auth_file.read_bytes()).digest() == source_digest
        )
        private_auth.unlink(missing_ok=True)
        report["isolated_auth_copy_removed"] = not private_auth.exists()
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    return report["result"] == "PASSED_AUTHENTICATED_CHAT_RESTART"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sdk-python", type=Path, required=True)
    parser.add_argument("--auth-file", type=Path, required=True)
    args = parser.parse_args()
    if os.name == "nt":
        raise SystemExit("Native Windows cleanup remains unqualified")
    if not asyncio.run(
        qualify(
            args.output.absolute(),
            args.sdk_python.absolute(),
            args.auth_file.absolute(),
        )
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
