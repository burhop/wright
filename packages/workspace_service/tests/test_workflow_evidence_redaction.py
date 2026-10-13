"""Credentials can flow in memory but cannot escape through recorded evidence."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workspace_service.workflow_run_record import record_workflow_run


class Files:
    def __init__(self):
        self.writes = []

    async def write_generated(self, root, path, content, policy):
        self.writes.append(json.loads(content))
        target = Path(root) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf8")
        return path


@pytest.mark.asyncio
async def test_transfer_response_stays_usable_but_records_events_and_api_are_redacted(
    tmp_path,
):
    files = Files()
    events = []
    secret = "transient-test-transfer.a/b=="
    response = json.dumps(
        {
            "download": {
                "command": f"curl -H 'X-Download-Ticket: {secret}' https://files.example/item.step"
            }
        }
    )
    event = {"kind": "step_completed", "task_id": "export", "response": response}
    context = {"credential_binding_digest": "a" * 64, "max_tokens": 4096}

    async def observe(value):
        events.append(value)

    async def execute(emit):
        await emit(event)
        # The next connected capability still receives the actual one-use value.
        assert json.loads(event["response"])["download"]["command"].find(secret) >= 0
        return {"run_id": "transfer-test", "steps": [event], "outputs": []}

    result = await record_workflow_run(
        service=SimpleNamespace(files=files),
        workspace_dir=str(tmp_path),
        source_path="workflows/transfer.workflow.wflow",
        source_digest="b" * 64,
        execution_context=context,
        run_id="transfer-test",
        execute=execute,
        on_event=observe,
    )
    for value in [*files.writes, events, result]:
        assert secret not in json.dumps(value)
    stored = json.loads((tmp_path / result["run_log_path"]).read_text())
    assert stored["status"] == "completed"
    assert stored["execution_context"] == context
    assert json.loads(stored["result"]["steps"][0]["response"])["download"][
        "command"
    ].endswith("https://files.example/item.step")
    assert secret in event["response"]


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["_input_request", "_approval_request"])
async def test_sensitive_continuation_is_rejected_before_any_checkpoint_storage(
    tmp_path, kind
):
    files = Files()
    secret = "fake-continuation-test"

    async def execute(emit):
        return {
            "run_id": "checkpoint-test",
            "steps": [],
            kind: {
                "continuation": {
                    "responses": {"headers": {"X-Download-Ticket": secret}}
                },
            },
        }

    # No checkpoint service is present: the guard must run before either owner.
    with pytest.raises(ValueError, match="credential-bearing"):
        await record_workflow_run(
            service=SimpleNamespace(files=files),
            workspace_dir=str(tmp_path),
            source_path="workflows/checkpoint.workflow.wflow",
            source_digest="c" * 64,
            workspace_id="test",
            run_id="checkpoint-test",
            execute=execute,
        )
    assert files.writes[-1]["status"] == "failed"
    assert secret not in json.dumps(files.writes)
