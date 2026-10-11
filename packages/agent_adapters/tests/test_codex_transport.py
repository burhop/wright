import asyncio
import json

import pytest

from agent_adapters.codex_transport import (
    CodexRuntimeSettings,
    CodexSdkTransport,
    CodexTransportError,
)

TURN_INPUT = {
    "threadId": "thread",
    "model": "fixture-model",
    "input": [{"type": "text", "text": "fixture"}],
}


def transport(tmp_path, observer=None):
    return CodexSdkTransport(CodexRuntimeSettings(tmp_path), observer=observer)


async def fixture_transport(tmp_path, script, monkeypatch, observer=None):
    """A fixture process exercises pipe failures, not Codex/model qualification."""
    original = asyncio.create_subprocess_exec
    worker = tmp_path / "fixture.py"
    worker.write_text(script)

    async def launch(*argv, **kwargs):
        return await original(argv[0], "-I", str(worker), **kwargs)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", launch)
    return transport(tmp_path, observer)


@pytest.mark.asyncio
async def test_transport_recovers_notifications_that_arrive_before_turn_ack(
    tmp_path, monkeypatch
):
    client = await fixture_transport(
        tmp_path,
        """
import sys,json
for raw in sys.stdin:
 req=json.loads(raw)
 if req['method']=='turn/start':
  print(json.dumps({'kind':'notification','method':'turn/completed','params':{'turn':{'id':'turn','status':'failed'}}}),flush=True)
 print(json.dumps({'id':req['id'],'result':{'ok':True}}),flush=True)
""",
        monkeypatch,
    )
    try:
        await client.start()
        assert await client.request("turn/start", TURN_INPUT) == {"ok": True}
        events = [event async for event in client.events("turn")]
        assert events[0]["params"]["turn"]["status"] == "failed"
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_lost_worker_after_handoff_is_uncertain_without_sdk_started_event(
    tmp_path, monkeypatch
):
    client = await fixture_transport(
        tmp_path,
        """
import sys,json
for raw in sys.stdin:
 req=json.loads(raw)
 if req['method']=='turn/start':sys.exit(0)
 print(json.dumps({'id':req['id'],'result':{}}),flush=True)
""",
        monkeypatch,
    )
    try:
        await client.start()
        with pytest.raises(CodexTransportError) as failure:
            await client.request("turn/start", TURN_INPUT)
        assert failure.value.code == "CODEX_TRANSPORT_LOST"
        assert failure.value.outcome_uncertain is True
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_unknown_methods_fail_before_transport_handoff(tmp_path):
    client = transport(tmp_path)
    for method in (
        "thread/shellCommand",
        "process/spawn",
        "config/value/write",
        "account/login/start",
        "thread/goal/set",
    ):
        with pytest.raises(CodexTransportError, match="METHOD_UNAVAILABLE") as failure:
            await client.request(method, {})
        assert failure.value.outcome_uncertain is False


@pytest.mark.asyncio
async def test_stream_eof_never_implies_success(tmp_path, monkeypatch):
    client = await fixture_transport(
        tmp_path,
        """
import sys,json
for raw in sys.stdin:
 req=json.loads(raw)
 print(json.dumps({'id':req['id'],'result':{}}),flush=True)
 if req['method']=='turn/start':sys.exit(0)
""",
        monkeypatch,
    )
    try:
        await client.start()
        await client.request("turn/start", TURN_INPUT)
        with pytest.raises(CodexTransportError, match="TRANSPORT_LOST"):
            async for _ in client.events("turn"):
                pass
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_observer_records_client_scope_and_redacts_secrets(tmp_path, monkeypatch):
    records = []

    async def observe(record):
        records.append(record)

    client = await fixture_transport(
        tmp_path,
        """
import sys,json
for raw in sys.stdin:
 req=json.loads(raw)
 print(json.dumps({'kind':'call_started','id':req['id'],'method':req['method']}),flush=True)
 print(json.dumps({'id':req['id'],'result':{'api_key':'secret','state':'ready'}}),flush=True)
""",
        monkeypatch,
        observe,
    )
    try:
        await client.start()
    finally:
        await client.close()
    assert {record["capture_scope"] for record in records} == {"app_server_sdk_call"}
    assert [record["phase"] for record in records] == [
        "prepared",
        "sdk_call_started",
        "acknowledged",
    ]
    assert "secret" not in json.dumps(records)
    assert records[-1]["fields"]["api_key"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_symlinked_state_is_rejected_before_user_configuration_is_touched(
    tmp_path,
):
    personal = tmp_path / "personal"
    personal.mkdir()
    (personal / "config.toml").write_text("personal configuration")
    state = tmp_path / "state"
    state.symlink_to(personal, target_is_directory=True)
    client = transport(state)
    with pytest.raises(CodexTransportError, match="STATE_ROOT_INVALID"):
        await client.start()
    assert list(personal.iterdir()) == [personal / "config.toml"]
    assert (personal / "config.toml").read_text() == "personal configuration"


@pytest.mark.asyncio
async def test_relaxed_fields_fail_before_worker_or_observer(tmp_path):
    records = []

    async def observe(record):
        records.append(record)

    client = transport(tmp_path, observe)
    with pytest.raises(ValueError, match="Unsupported Codex request fields"):
        await client.request(
            "thread/start", {"model": "fixture", "sandbox": "danger-full-access"}
        )
    assert records == []
    assert client._handed_off == set()


@pytest.mark.asyncio
async def test_late_reply_is_not_a_success_receipt_or_automatic_retry(
    tmp_path, monkeypatch
):
    late_reply = asyncio.Event()
    phases = []

    async def observe(record):
        phases.append(record["phase"])
        if record["phase"] == "unclaimed_reply":
            late_reply.set()

    client = await fixture_transport(
        tmp_path,
        """
import sys,json,time
for raw in sys.stdin:
 req=json.loads(raw)
 if req['method']=='model/list':time.sleep(1.2)
 print(json.dumps({'id':req['id'],'result':{}}),flush=True)
""",
        monkeypatch,
        observe,
    )
    client.settings = CodexRuntimeSettings(tmp_path, timeout_seconds=1)
    try:
        await client.start()
        with pytest.raises(CodexTransportError, match="RPC_TIMEOUT") as failure:
            await client.request("model/list", {})
        assert failure.value.outcome_uncertain is True
        async with asyncio.timeout(2):
            await late_reply.wait()
        assert phases.count("prepared") == 2
        assert phases.count("acknowledged") == 1  # Initialization only.
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_event_overflow_fails_explicitly_instead_of_dropping_tool_evidence(
    tmp_path, monkeypatch
):
    client = await fixture_transport(
        tmp_path,
        """
import sys,json
for raw in sys.stdin:
 req=json.loads(raw)
 if req['method']=='turn/start':
  for number in range(129):
   print(json.dumps({'kind':'notification','method':'item/started','params':{'turnId':'turn','item':{'id':str(number)}}}),flush=True)
 print(json.dumps({'id':req['id'],'result':{}}),flush=True)
""",
        monkeypatch,
    )
    try:
        await client.start()
        with pytest.raises(CodexTransportError, match="EVENT_BUFFER_FULL") as failure:
            await client.request("turn/start", TURN_INPUT)
        assert failure.value.outcome_uncertain is True
    finally:
        await client.close()
