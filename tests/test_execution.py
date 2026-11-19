import hashlib
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest
from mcp.types import CallToolResult, TextContent
from wright_workflow import WorkflowSourceExecutionError, parse, resume, run
from wright_workflow.bindings import qualify
from wright_workflow.checkpoint import own_run
from wright_workflow.transport import Sessions

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "handoff"
SOURCE = (EXAMPLE / "length.workflow.wflow").read_text("utf-8")


def configuration():
    return runpy.run_path(str(EXAMPLE / "configure.py"))["configuration"]()


def test_real_two_provider_handoff(tmp_path):
    bindings = configuration()
    receipt = run(parse(SOURCE), {}, bindings, tmp_path)
    assert receipt["status"] == "completed"
    one, two = receipt["attempts"]
    produced = receipt["ports"]["writer.coordinates"]
    measurement = receipt["ports"]["reader.measurement"]["value"]
    assert produced == two["consumed"]["writer.coordinates"]
    assert produced["attempt"] == one["id"]
    assert produced["size"] == 18
    assert measurement == {
        "length_mm": 5,
        "sha256": hashlib.sha256(
            (tmp_path / "files" / produced["path"]).read_bytes()
        ).hexdigest(),
    }
    assert measurement["sha256"] == produced["sha256"]
    assert run(SOURCE, {}, bindings, tmp_path) == receipt


def fake_transport(monkeypatch, behavior):
    description = runpy.run_path(str(EXAMPLE / "provider.py"))["description"]
    calls = []

    async def resolve(self, step):
        if step.server_id not in self.bindings:
            raise WorkflowSourceExecutionError(
                "WORKFLOW_NOT_READY", "missing server", "Configure its binding."
            )
        server = self.bindings[step.server_id]
        info = SimpleNamespace(name="example-" + step.tool_name, version="1.0.0")
        return qualify(
            step, server, info, {step.tool_name: description(step.tool_name)}
        )

    async def call(self, step, tool, arguments):
        calls.append(step.id)
        if step.id == "writer":
            (self.root / "points.csv").write_bytes(b"x,y\n0,0\n3,4\n")
            if behavior == "lost":
                raise ConnectionError("test transport interrupted")
        return CallToolResult(
            content=[TextContent(type="text", text="test observation")],
            isError=behavior == "failure",
        )

    monkeypatch.setattr(Sessions, "resolve", resolve)
    monkeypatch.setattr(Sessions, "call", call)
    return calls


@pytest.mark.parametrize(
    "mode,status", [("lost", "outcome_unknown"), ("failure", "failed")]
)
def test_interrupted_or_failed_call_is_not_replayed(
    monkeypatch, tmp_path, mode, status
):
    calls = fake_transport(monkeypatch, mode)
    bindings = configuration()
    receipt = run(SOURCE, {}, bindings, tmp_path)
    assert receipt["status"] == receipt["attempts"][0]["outcome"] == status
    assert run(SOURCE, {}, bindings, tmp_path) == receipt
    assert calls == ["writer"]
    assert not receipt["ports"]


@pytest.mark.parametrize(
    "change", ["missing", "revision", "approval", "unknown_capability"]
)
def test_readiness_checks_all_bindings_before_first_tool(monkeypatch, tmp_path, change):
    calls = fake_transport(monkeypatch, "")
    config = configuration()
    source = SOURCE
    if change == "missing":
        del config["reader"]
    elif change == "revision":
        config["reader"]["build"] = "2.0.0"
    elif change == "approval":
        config["reader"]["tools"]["measure_length"]["required_approvals"] = ["engineer"]
    else:
        source = source.replace(
            '"mcp_arguments":', '"future_required_check":true,"mcp_arguments":'
        )
    with pytest.raises(WorkflowSourceExecutionError):
        run(source, {}, config, tmp_path)
    assert calls == []


def waiting_source():
    fields = {
        "name": "Enter quantity",
        "purpose": "Declare a typed response",
        "step_type": "work",
        "group": None,
        "performed_by": "engineer",
        "inputs": [],
        "outputs": [
            {
                "key": "answer",
                "name": "Answer",
                "kind": "structured_result",
                "item": None,
                "required": True,
                "quantity": "one",
                "description": "Entered quantity",
            }
        ],
        "prompt": None,
        "tool": None,
        "reusable_step": None,
        "settings": {
            "authoring_template": "human-input",
            "human_interaction": {
                "version": 2,
                "kind": "input",
                "instructions": "Enter quantity",
                "response_schema": {
                    "type": "object",
                    "properties": {"quantity": {"type": "integer", "minimum": 1}},
                    "additionalProperties": False,
                    "required": ["quantity"],
                },
                "output_port": "answer",
            },
        },
    }
    return (
        SOURCE.split("task writer")[0]
        + "task ask\n"
        + "\n".join("  " + key + ": " + json.dumps(v) for key, v in fields.items())
        + "\nend\n"
    )


def test_declared_wait_same_run_duplicate_stale_and_invalid_responses(tmp_path):
    waiting = run(waiting_source(), {}, {}, tmp_path)
    assert waiting["status"] == "waiting_input"
    answer = {"subject": waiting["pending"]["subject"], "value": {"quantity": 2}}
    with pytest.raises(WorkflowSourceExecutionError, match="pending subject"):
        resume(tmp_path, dict(answer, subject="previous-revision"))
    with pytest.raises(ValueError):
        resume(tmp_path, dict(answer, value={"quantity": 0}))
    final = resume(tmp_path, answer)
    assert final["status"] == "completed" and final["run_id"] == waiting["run_id"]
    assert final["ports"]["ask.answer"]["value"] == {"quantity": 2}
    assert resume(tmp_path, answer) == final
    with pytest.raises(WorkflowSourceExecutionError, match="different recorded answer"):
        resume(tmp_path, dict(answer, value={"quantity": 3}))


def test_abandoned_in_flight_checkpoint_recovers_as_unknown(tmp_path):
    with own_run(tmp_path) as store:
        store.save(
            {
                "status": "in_flight",
                "attempts": [{"id": "exact-request", "outcome": "in_flight"}],
            }
        )
    with own_run(tmp_path) as store:
        assert store.read() == {
            "status": "outcome_unknown",
            "attempts": [{"id": "exact-request", "outcome": "outcome_unknown"}],
        }
