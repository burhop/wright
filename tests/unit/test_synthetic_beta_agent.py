"""Protocol fixtures only: no model calls or customer/VM claims."""

import importlib.util
import json
import sys
import time
from pathlib import Path

import pytest

MODULE = Path(__file__).resolve().parents[2] / "scripts/synthetic_beta_testing/agent.py"
SPEC = importlib.util.spec_from_file_location("synthetic_beta_agent", MODULE)
agent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(agent)

SERVER = r"""
import json,sys,time
mode=sys.argv[1]
def send(value): print(json.dumps(value),flush=True)
for line in sys.stdin:
 m=json.loads(line); method=m.get('method'); identity=m.get('id')
 if method=='initialize':
  assert m['params']['capabilities']['experimentalApi'] is True
  send({'id':identity,'result':{'userAgent':'fixture-server'}})
 elif method=='thread/start':
  p=m['params']; assert p['ephemeral'] is True and p['cwd']=='/tmp/customer'
  assert p['approvalPolicy']=='never' and p['baseInstructions']==p['developerInstructions']
  send({'id':identity,'result':{'thread':{'id':'thread-1','ephemeral': mode!='persisted','turns':[]},'cwd':'/tmp/customer','model':'other' if mode=='wrong-model' else p['model'],'modelProvider':'fixture','reasoningEffort':'medium','instructionSources':['/repo/AGENTS.md'] if mode=='inherited' else []}})
 elif method=='turn/start':
  if mode=='hang': time.sleep(10);continue
  if mode=='early':
   send({'method':'turn/started','params':{'threadId':'thread-1','turn':{'id':'turn-1'}}})
  send({'id':identity,'result':{'turn':{'id':'turn-1','status':'inProgress'}}})
  if mode=='bad-json': print('not JSON',flush=True);continue
  if mode=='approval':
   send({'id':77,'method':'item/commandExecution/requestApproval','params':{}});continue
  if mode=='builtin':
   send({'method':'item/started','params':{'threadId':'thread-1','turnId':'turn-1','item':{'id':'bad','type':'commandExecution'}}});continue
  if mode=='eof': break
  if mode=='failed':
   send({'method':'turn/completed','params':{'threadId':'thread-1','turn':{'id':'turn-1','status':'failed'}}});continue
  tool='unknown' if mode=='unknown' else 'desktop'
  send({'id':88,'method':'item/tool/call','params':{'tool':tool,'arguments':{'action':'screenshot'},'callId':'call-1','threadId':'other' if mode=='wrong-scope' else 'thread-1','turnId':'turn-1'}})
 elif identity==88 and 'result' in m:
  send({'method':'thread/tokenUsage/updated','params':{'threadId':'thread-1','turnId':'turn-1','tokenUsage':{'total':{'inputTokens':123,'outputTokens':45,'totalTokens':168},'last':{'totalTokens':168}}}})
  send({'method':'item/completed','params':{'threadId':'thread-1','turnId':'turn-1','item':{'id':'comment','type':'agentMessage','phase':'commentary','text':'interim'}}})
  send({'method':'item/completed','params':{'threadId':'thread-1','turnId':'turn-1','item':{'id':'reason','type':'reasoning','content':['do not capture hidden reasoning']}}})
  if mode!='no-final': send({'method':'item/completed','params':{'threadId':'thread-1','turnId':'turn-1','item':{'id':'final','type':'agentMessage','phase':'final_answer','text':'{"observed":"fixture result"}'}}})
  send({'method':'turn/completed','params':{'threadId':'thread-1','turn':{'id':'turn-1','status':'completed'}}})
"""

TOOLS = [
    {
        "type": "function",
        "name": "desktop",
        "description": "Visible guest interaction",
        "inputSchema": {"type": "object"},
    }
]


def run(tmp_path, mode="success", callback=None, timeout=3, output_schema=None):
    server = tmp_path / "server.py"
    server.write_text(SERVER)
    return agent.run_agent(
        [sys.executable, "-u", str(server), mode],
        "Versioned fixture instructions",
        "Fixture task session_id=customer-1",
        TOOLS,
        callback
        or (
            lambda name, arguments: {
                "text": "event-1",
                "image_url": "data:image/png;base64,AAAA",
            }
        ),
        timeout,
        tmp_path / "output",
        output_schema=output_schema,
    )


def test_protocol_tools_final_and_observable_provenance(tmp_path):
    calls = []

    def callback(name, arguments):
        calls.append((name, arguments))
        return {"text": "event-1", "image_url": "data:image/png;base64,AAAA"}

    result = run(tmp_path, callback=callback)
    assert result["status"] == "completed"
    assert result["resolved_model"] == "gpt-6.1-sol"
    assert result["resolved_effort"] == "medium"
    assert result["usage"]["total"]["totalTokens"] == 168
    assert result["upstream_revision"] is None
    assert json.loads(result["final_text"])["observed"] == "fixture result"
    assert calls == [("desktop", {"action": "screenshot"})]
    transcript = (tmp_path / "output/transport.jsonl").read_text()
    assert "data:image/png;base64" not in transcript
    assert "do not capture hidden reasoning" not in transcript
    assert "image_data_sha256" in transcript
    assert result["process_exit_code"] is not None


def test_output_schema_is_forwarded_exactly_and_recorded(tmp_path):
    schema = {
        "type": "object",
        "properties": {"session_id": {"enum": ["customer-1"]}},
        "required": ["session_id"],
        "additionalProperties": False,
    }
    result = run(tmp_path, output_schema=schema)
    messages = [
        json.loads(line)["message"]
        for line in (tmp_path / "output/transport.jsonl").read_text().splitlines()
    ]
    turn = next(
        message for message in messages if message.get("method") == "turn/start"
    )
    assert turn["params"]["outputSchema"] == schema
    import hashlib

    expected = hashlib.sha256(
        json.dumps(schema, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert result["output_schema_sha256"] == expected


@pytest.mark.parametrize(
    "mode,needle",
    [
        ("unknown", "unknown dynamic"),
        ("wrong-scope", "another scope"),
        ("wrong-model", "resolved model"),
        ("inherited", "inherited instruction"),
        ("persisted", "not confirmed ephemeral"),
        ("bad-json", "not JSONL"),
        ("approval", "unexpected server request"),
        ("builtin", "unexpected built-in"),
        ("failed", "ended failed"),
        ("eof", "closed before"),
        ("no-final", "no final"),
    ],
)
def test_protocol_violation_fails_and_retains_attempt(tmp_path, mode, needle):
    calls = []
    result = run(
        tmp_path, mode, callback=lambda *args: calls.append(args) or {"text": "seen"}
    )
    assert result["status"] == "failed"
    assert needle in result["error"]
    assert (tmp_path / "output/agent-result.json").is_file()
    if mode in {"unknown", "wrong-scope", "wrong-model", "inherited", "approval"}:
        assert calls == []


def test_turn_deadline_stops_process_without_retry(tmp_path):
    started = time.monotonic()
    result = run(tmp_path, "hang", timeout=0.15)
    assert result["status"] == "timed_out"
    assert time.monotonic() - started < 2
    assert result["process_exit_code"] is not None


def test_callback_deadline_does_not_deliver_late_result(tmp_path):
    def callback(name, arguments):
        time.sleep(0.5)
        return {"text": "late-result"}

    result = run(tmp_path, callback=callback, timeout=0.15)
    assert result["status"] == "timed_out"
    assert "late-result" not in (tmp_path / "output/transport.jsonl").read_text()


def test_callback_exception_is_not_leaked_into_model_context(tmp_path):
    def callback(name, arguments):
        raise RuntimeError("private credential = do not leak")

    result = run(tmp_path, callback=callback)
    assert result["status"] == "completed"
    transcript = (tmp_path / "output/transport.jsonl").read_text()
    assert "private credential" not in transcript
    assert "Desktop action failed" in transcript


def test_output_directory_cannot_overwrite_previous_attempt(tmp_path):
    run(tmp_path)
    with pytest.raises(ValueError, match="fresh"):
        run(tmp_path)


def test_dynamic_tool_names_are_unique_before_launch(tmp_path):
    with pytest.raises(ValueError, match="unique"):
        agent.run_agent(
            ["false"],
            "instructions",
            "task",
            TOOLS + TOOLS,
            lambda *args: {},
            1,
            tmp_path / "output",
        )


def test_tool_images_cannot_request_external_resources():
    with pytest.raises(agent.AgentProtocolError, match="inline"):
        agent.normalize_tool_result(
            {"image_url": "https://example.invalid/private.png"}
        )


def test_redaction_preserves_usage_without_credentials():
    value = agent.redact_record(
        {
            "access_token": "secret",
            "text": "Bearer abc123 sk-12345678901234567890",
            "inputTokens": 17,
        }
    )
    assert "secret" not in json.dumps(value)
    assert "abc123" not in value["text"]
    assert value["inputTokens"] == 17
