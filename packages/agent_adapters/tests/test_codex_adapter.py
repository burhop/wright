"""Deterministic adapter ownership/recovery contracts; no model qualification."""

import asyncio
import sqlite3
from types import SimpleNamespace

import pytest
import pytest_asyncio

from agent_adapters.base import AgentChatRequest
from agent_adapters.codex import CodexAdapter
from agent_adapters.codex_transport import CodexRuntimeSettings, CodexTransportError
from agent_adapters.workflow_instructions import embedded_instruction_set
from data_vault.agent_platform_repository import (
    AgentPlatformConflict,
    AgentPlatformRepository,
)


class Runtime:
    def __init__(self, settings, observer):
        self.observer = observer
        self.calls = []
        self.turns = []
        self.config = {"model_provider": "qualification"}
        self.account = None
        self.fail_start = False
        self.fail_events = False
        self.wait = None
        self.reroute = False
        self.closed = False

    async def start(self):
        return {}

    async def close(self):
        self.closed = True

    def thread(self):
        return {
            "id": "thread",
            "model": "gpt-6.1-sol",
            "cliVersion": "0.162.1",
            "createdAt": 1,
            "turns": self.turns,
        }

    async def request(self, method, params):
        self.calls.append((method, params))
        if method == "config/read":
            return {"config": self.config}
        if method == "account/read":
            return {"account": self.account}
        if method == "model/list":
            return {
                "data": [
                    {
                        "model": "gpt-6.1-sol",
                        "supportedReasoningEfforts": [{"reasoningEffort": "high"}],
                    }
                ]
            }
        if method in {"thread/start", "thread/read", "thread/resume"}:
            return {"thread": self.thread()}
        if method == "turn/start":
            self.turns.append(
                {
                    "id": f"turn-{len(self.turns)}",
                    "status": "inProgress",
                    "items": [
                        {
                            "id": "user",
                            "type": "userMessage",
                            "content": params["input"],
                        },
                        {"id": "assistant", "type": "agentMessage", "text": "hello"},
                    ],
                }
            )
            if self.fail_start:
                raise CodexTransportError("CODEX_RPC_TIMEOUT", outcome_uncertain=True)
            return {"turn": self.turns[-1]}
        if method == "turn/interrupt":
            self.turns[-1]["status"] = "interrupted"
            self.wait.set()
        return {}

    async def events(self, turn_id):
        if self.fail_events:
            raise CodexTransportError("CODEX_TRANSPORT_LOST", outcome_uncertain=True)
        if self.wait is not None:
            await self.wait.wait()
        turn = self.turns[-1]
        if self.reroute:
            yield {
                "method": "model/rerouted",
                "params": {
                    "threadId": "thread",
                    "turnId": turn_id,
                    "toModel": "alternate",
                },
            }
            return
        yield {
            "method": "item/agentMessage/delta",
            "params": {"threadId": "thread", "turnId": turn_id, "delta": "hello"},
        }
        if turn["status"] == "inProgress":
            turn["status"] = "completed"
        yield {
            "method": "turn/completed",
            "params": {"threadId": "thread", "turn": turn},
        }


@pytest_asyncio.fixture
async def setup(tmp_path):
    db = tmp_path / "state.db"
    with sqlite3.connect(db) as connection:
        connection.execute(
            "CREATE TABLE engineering_workspaces (workspace_id TEXT, local_path TEXT)"
        )
        connection.execute(
            "CREATE TABLE workspace_agent_sessions (workspace_id TEXT, session_id TEXT, agent_id TEXT, is_archived INTEGER DEFAULT 0)"
        )
        connection.execute(
            "INSERT INTO engineering_workspaces VALUES (?,?)",
            ("workspace", str(tmp_path)),
        )
    runtime = Runtime(None, None)
    adapter = CodexAdapter(
        str(db),
        CodexRuntimeSettings(tmp_path / "runtime"),
        repository=AgentPlatformRepository(str(db)),
        model="gpt-6.1-sol",
        auth_method="fixture",
        transport_factory=lambda *a, **kw: runtime,
    )
    session = await adapter.create_session(str(tmp_path))
    with sqlite3.connect(db) as connection:
        connection.execute(
            "INSERT INTO workspace_agent_sessions(workspace_id,session_id,agent_id) VALUES (?,?,?)",
            ("workspace", session.session_id, "codex"),
        )
    return SimpleNamespace(
        adapter=adapter, runtime=runtime, session=session, db=db, root=tmp_path
    )


async def chat(setup, attempt="attempt", **kwargs):
    return [
        event
        async for event in setup.adapter.stream_chat(
            AgentChatRequest(
                setup.session.session_id, "question", trace_id=attempt, **kwargs
            )
        )
    ]


def starts(runtime):
    return len([call for call in runtime.calls if call[0] == "turn/start"])


@pytest.mark.asyncio
async def test_chat_success_history_and_duplicate_attempt_cannot_resubmit(setup):
    events = await chat(setup)
    assert events[0].data["content"] == "hello"
    assert events[-1].data["status"] == "completed"
    assert [
        message.role
        for message in await setup.adapter.get_chat_history(setup.session.session_id)
    ] == ["user", "assistant"]
    repeated = await chat(setup)
    assert repeated[-1].data["status"] == "failed"
    assert starts(setup.runtime) == 1


@pytest.mark.asyncio
async def test_lost_acknowledgement_holds_session_without_replaying(setup):
    setup.runtime.fail_start = True
    assert (await chat(setup))[-1].data["status"] == "unknown"
    setup.runtime.fail_start = False
    assert (await chat(setup, "different-attempt"))[-1].data["status"] == "failed"
    assert starts(setup.runtime) == 1
    with pytest.raises(AgentPlatformConflict, match="manual reconciliation"):
        await setup.adapter.get_chat_history(setup.session.session_id)


@pytest.mark.asyncio
async def test_known_turn_is_reconciled_after_restart_without_submission(setup):
    setup.runtime.fail_events = True
    assert (await chat(setup))[-1].data["status"] == "unknown"
    setup.runtime.turns[0]["status"] = "completed"
    setup.runtime.fail_events = False
    await setup.adapter.close()
    restarted = CodexAdapter(
        str(setup.db),
        setup.adapter.settings,
        repository=AgentPlatformRepository(str(setup.db)),
        model="gpt-6.1-sol",
        auth_method="fixture",
        transport_factory=lambda *a, **kw: setup.runtime,
    )
    assert [row.session_id for row in await restarted.list_sessions()] == [
        setup.session.session_id
    ]
    assert len(await restarted.get_chat_history(setup.session.session_id)) == 2
    assert (
        restarted.repository.get_turn(setup.session.session_id, "attempt").status
        == "completed"
    )
    assert starts(setup.runtime) == 1


@pytest.mark.asyncio
async def test_cancel_acknowledgement_waits_for_interrupted_terminal_receipt(setup):
    setup.runtime.wait = asyncio.Event()
    task = asyncio.create_task(chat(setup))
    for _ in range(20):
        if setup.adapter._active:
            break
        await asyncio.sleep(0)
    assert await setup.adapter.cancel_chat(setup.session.session_id)
    events = await asyncio.wait_for(task, 1)
    assert events[-1].data["status"] == "interrupted"
    assert (
        setup.adapter.repository.get_turn(setup.session.session_id, "attempt").status
        == "interrupted"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "drift", ["config", "instructions", "account", "model", "effort", "workspace"]
)
async def test_configuration_drift_is_rejected_before_submission(setup, drift):
    kwargs = {}
    if drift == "config":
        setup.runtime.config["changed"] = True
    elif drift == "instructions":
        values = embedded_instruction_set().model_dump(mode="json")
        # A different valid inspectable instruction set rather than a broken digest.
        from agent_adapters.workflow_instructions import (
            load_default_workflow_instructions,
        )

        values = load_default_workflow_instructions().model_dump(mode="json")
        values["overrides"] = [
            {"origin": "test", "roles": ["chat"], "text": "Changed chat instructions."}
        ]
        kwargs["instruction_set"] = values
    elif drift == "account":
        setup.runtime.account = {"type": "apiKey"}
    elif drift == "model":
        setup.adapter.model = "different-model"
    elif drift == "effort":
        setup.adapter.effort = "low"
    else:
        with sqlite3.connect(setup.db) as connection:
            connection.execute(
                "UPDATE engineering_workspaces SET local_path='/different'"
            )
    result = await chat(setup, **kwargs)
    assert result[-1].data["status"] == "failed"
    assert starts(setup.runtime) == 0


@pytest.mark.asyncio
async def test_restricted_authoring_and_attachments_fail_before_runtime(setup):
    assert not (await setup.adapter.get_invocation_capabilities()).available
    assert not (await setup.adapter.get_invocation_capabilities()).no_tools
    before = len(setup.runtime.calls)
    assert (await chat(setup, attachments=["image"]))[-1].data["status"] == "failed"
    assert (await chat(setup, invocation_context=object()))[-1].data[
        "status"
    ] == "failed"
    assert len(setup.runtime.calls) == before


@pytest.mark.asyncio
async def test_model_reroute_is_held_without_accepting_alternate_model(setup):
    setup.runtime.reroute = True
    assert (await chat(setup))[-1].data["status"] == "unknown"
    assert (
        setup.adapter.repository.get_turn(setup.session.session_id, "attempt").status
        == "unknown"
    )


@pytest.mark.asyncio
async def test_fresh_thread_history_does_not_read_unmaterialized_native_file(setup):
    before = list(setup.runtime.calls)
    assert await setup.adapter.get_chat_history(setup.session.session_id) == []
    assert setup.runtime.calls == before


@pytest.mark.asyncio
async def test_external_mcp_configuration_blocks_chat_before_submission(setup):
    setup.runtime.config["mcp_servers"] = {"external": {"command": "not-authorized"}}
    events = await chat(setup)
    assert events[-1].data["status"] == "failed"
    assert not setup.runtime.turns


def test_production_factory_rejects_unqualified_auth_and_configuration(
    monkeypatch, tmp_path
):
    from agent_adapters.codex import create_codex_engine

    monkeypatch.setenv("WRIGHT_CODEX_CHAT_EXPERIMENTAL", "1")
    monkeypatch.setenv("WRIGHT_CODEX_STATE_ROOT", str(tmp_path))
    monkeypatch.setenv("WRIGHT_CODEX_MODEL", "gpt-6.1-sol")
    monkeypatch.setenv("WRIGHT_CODEX_AUTH_METHOD", "apiKey")
    with pytest.raises(ValueError, match="Only ChatGPT"):
        create_codex_engine(str(tmp_path / "state.db"), repository=None)
    monkeypatch.setenv("WRIGHT_CODEX_AUTH_METHOD", "chatgpt")
    home = tmp_path / "home"
    home.mkdir()
    (home / "config.toml").write_text(
        '[mcp_servers.external]\ncommand="not-authorized"\n'
    )
    with pytest.raises(ValueError, match="configuration profile"):
        create_codex_engine(str(tmp_path / "state.db"), repository=None)
