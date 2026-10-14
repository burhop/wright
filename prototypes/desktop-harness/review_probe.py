"""Real private review wait/decision/reopen; synthetic decisions only, no dispatch."""

import argparse
import asyncio
import json
from pathlib import Path

from checkpoint_probe import connection, await_reply, read_until
from reasoning_probe import SOURCE

REVIEW = """
task review
  name: "Review the synthetic inspection brief"
  purpose: "Qualify a human review port without approving engineering work"
  step_type: work
  group: null
  performed_by: engineer
  inputs: [{"key":"evidence","kind":"engineering_document","name":"Brief","item":null,"required":true,"quantity":"one","description":"Private test brief"}]
  outputs: []
  instructions: "Private fixture only: inspect the brief. A test decision is not engineering approval."
  settings: {"authoring_template":"manual-review"}
  tool: null
  reusable_step: null
end
connection brief_review
  type: item
  from: "brief.brief_response"
  to: "review.evidence"
  label: "Exact private test output"
  when: null
end
"""


async def main(state):
    receipt = state / "review-probe.json"
    if receipt.exists():
        raise ValueError("Preserve existing review evidence; use fresh state")
    evidence = {
        "scope": "synthetic private review, no engineering approval or external dispatch",
        "native_working_view": True,
        "calls": [],
    }
    async with connection(state, evidence, receipt) as call:
        workspace = await call(
            "wright_workspace_create", name="Private native review proof"
        )
        scope = {key: workspace[key] for key in ("workspace_id", "session_id")}
        evidence["workspace"] = workspace
        source = await call(
            "wright_workflow_create",
            **scope,
            path="workflows/native-review.workflow.wflow",
            source=SOURCE.replace(
                '"output_format":"markdown"',
                '"authoring_template":"ai-prompt","file_policy":"indexed","save_output":true,"output_format":"markdown"',
            )
            + REVIEW,
        )
        evidence["source"] = source
        subject = {
            **scope,
            "path": source["path"],
            "source_digest": source["storage_digest"],
        }
        prepared = await call("wright_process_prepare", **subject, bindings=[])
        started = await call(
            "wright_process_start",
            **subject,
            input_snapshot_id=prepared["snapshot_id"],
            input_digest=prepared["digest"],
            request_id="private-review-start-01",
        )
        evidence["start_receipt"] = started
        await await_reply(state, evidence, receipt, call, scope, "review_brief")
        reads = {**subject, "run_id": started["run_id"]}
        waiting = await read_until(
            call, reads, {"waiting_human", "failed", "completed"}
        )
        if waiting["state"] != "waiting_human":
            raise ValueError("Expected actual persisted review wait")
        evidence["waiting"] = waiting
    # A new MCP process must observe the same durable review, not regenerate it.
    async with connection(state, evidence, receipt) as call:
        reopened = await call("wright_process_read", **reads)
        checkpoint = reopened["interactions"][0]
        assert (
            checkpoint["checkpoint_id"] == waiting["interactions"][0]["checkpoint_id"]
        )
        decision = {
            **scope,
            "path": source["path"],
            "expected_storage_digest": source["storage_digest"],
            "operation": "decide",
            "checkpoint_id": checkpoint["checkpoint_id"],
            "subject_digest": checkpoint["subject_digest"],
            "decision": "changes_requested",
            "reason": "Synthetic fixture: missing measured hole locations",
            "request_id": "private-review-decision-01",
        }
        evidence["stale_denied"] = await call(
            "wright_process_ui_update",
            expect_error=True,
            request={
                **decision,
                "subject_digest": "0" * 64,
                "request_id": "stale-review-control",
            },
        )
        evidence["decision"] = await call("wright_process_ui_update", request=decision)
        evidence["decision_request"] = decision
    async with connection(state, evidence, receipt) as call:
        observed = await call("wright_process_read", **reads)
        recorded = next(
            row
            for row in observed["interactions"]
            if row["checkpoint_id"] == checkpoint["checkpoint_id"]
        )
        assert recorded["decision"]["request_id"] == decision["request_id"]
        assert recorded["decision"]["decision"] == "changes_requested"
        evidence["reopened_decision"] = observed
        evidence["status"] = "passed"
        receipt.write_text(json.dumps(evidence, indent=2))
        print(json.dumps({"status": "passed", "run_id": started["run_id"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    asyncio.run(main(parser.parse_args().state_dir.resolve(strict=True)))
