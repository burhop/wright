"""Private local-review approval and same-run continuation; no engineering authority."""

import argparse
import asyncio
import json
import hashlib
import sqlite3
from pathlib import Path

from checkpoint_probe import connection, await_reply, read_until
from reasoning_probe import SOURCE
from workspace_service.workflow_integration_policy import (
    WorkflowIntegrationPolicyService,
    LOCAL_REVIEW_BINDING,
    LOCAL_REVIEW_DESTINATION,
)

REVIEW = """
task review
  name: "Review the synthetic inspection brief"
  purpose: "Qualify a human review port without approving engineering work"
  step_type: review
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
    receipt = state / "continuation-probe.json"
    evidence = {
        "scope": "synthetic private review, no engineering approval or external dispatch",
        "native_working_view": True,
        "calls": [],
    }
    if receipt.exists():
        evidence = json.loads(receipt.read_text())
        if "decision" in evidence:
            return await finish(state, evidence, receipt)
        if "start_receipt" not in evidence:
            raise ValueError("Inspect retained state; this phase cannot be replayed")
    async with connection(state, evidence, receipt) as call:
        if "start_receipt" in evidence:
            workspace = evidence["workspace"]
            scope = {key: workspace[key] for key in ("workspace_id", "session_id")}
            source = evidence["source"]
            subject = {
                **scope,
                "path": source["path"],
                "source_digest": source["storage_digest"],
            }
            started = evidence["start_receipt"]
        else:
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
                    "inspection-brief.md", "outputs/inspection-brief.md"
                ).replace(
                    '"output_format":"markdown"',
                    '"authoring_template":"ai-prompt","file_policy":"indexed","save_output":true,"output_format":"markdown"',
                )
                + REVIEW.replace(
                    '{"authoring_template":"manual-review"}',
                    json.dumps(
                        {
                            "authoring_template": "external-action-approval",
                            "action_kind": "local_review",
                            "approval_binding": LOCAL_REVIEW_BINDING,
                            "approval_destination": LOCAL_REVIEW_DESTINATION,
                            "approval_settings": {"review_task_id": "review"},
                            "approval_action": {
                                "kind": "local_review",
                                "mode": "review_only",
                            },
                        }
                    ),
                ),
            )
            evidence["source"] = source
            subject = {
                **scope,
                "path": source["path"],
                "source_digest": source["storage_digest"],
            }
            prepared = await call("wright_process_prepare", **subject, bindings=[])
            with sqlite3.connect(state / "wright.sqlite") as db:
                root = Path(
                    db.execute(
                        "SELECT local_path FROM engineering_workspaces WHERE workspace_id=?",
                        (scope["workspace_id"],),
                    ).fetchone()[0]
                )
            staged = root / "inputs" / "private-fixture.txt"
            staged.parent.mkdir(exist_ok=True)
            staged.write_text(
                "Synthetic private continuation fixture; no engineering approval.\n"
            )
            digest = hashlib.sha256(staged.read_bytes()).hexdigest()
            grant = WorkflowIntegrationPolicyService(
                str(state / "wright.sqlite"), enabled=True
            ).enroll(
                campaign_id="desktop-private-continuation",
                dataset_id="synthetic-review",
                dataset_digest=digest,
                workspace_id=scope["workspace_id"],
                source_path=source["path"],
                source_digest=source["storage_digest"],
                input_files={"inputs/private-fixture.txt": digest},
                output_root="outputs",
                allowed_tools=[],
                approval_mode="manual",
            )
            evidence["private_enrollment"] = grant
            started = await call(
                "wright_process_start",
                **subject,
                input_snapshot_id=prepared["snapshot_id"],
                input_digest=prepared["digest"],
                request_id="private-review-start-01",
                integration_policy_digest=grant,
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
            "decision": "approved",
            "reason": "Private fixture only: verify continuation; not engineering approval",
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
    await finish(state, evidence, receipt)


async def finish(state, evidence, receipt):
    if (
        evidence.get("continue_intent")
        or evidence.get("continue_receipt")
        or evidence.get("status") == "passed"
    ):
        raise ValueError("Continuation already submitted; inspect saved run instead")
    workspace = evidence["workspace"]
    scope = {key: workspace[key] for key in ("workspace_id", "session_id")}
    source = evidence["source"]
    started = evidence["start_receipt"]
    decision = evidence["decision_request"]
    checkpoint = {
        "checkpoint_id": decision["checkpoint_id"],
        "subject_digest": decision["subject_digest"],
    }
    reads = {
        **scope,
        "path": source["path"],
        "source_digest": source["storage_digest"],
        "run_id": started["run_id"],
    }
    async with connection(state, evidence, receipt) as call:
        observed = await call("wright_process_read", **reads)
        recorded = next(
            row
            for row in observed["interactions"]
            if row["checkpoint_id"] == checkpoint["checkpoint_id"]
        )
        assert recorded["decision"]["request_id"] == decision["request_id"]
        assert recorded["decision"]["decision"] == "approved"
        evidence["reopened_decision"] = observed
        actions = observed["actions"]
        action = next(
            item
            for item in actions
            if item["action_id"] == "continue-" + checkpoint["checkpoint_id"]
        )
        assert (
            action["enabled"]
            and action["subject_digest"] == checkpoint["subject_digest"]
        )
        request = {
            **scope,
            "path": source["path"],
            "expected_storage_digest": source["storage_digest"],
            "operation": "continue",
            "action_id": action["action_id"],
            "subject_digest": checkpoint["subject_digest"],
            "request_id": "private-continuation-01",
        }
        evidence["continue_intent"] = request
        receipt.write_text(json.dumps(evidence, indent=2))
        evidence["continue_receipt"] = await call(
            "wright_process_ui_update", request=request
        )
        completed = await read_until(call, reads, {"completed", "failed"})
        assert completed["state"] == "completed", completed
        evidence["completed"] = completed
        evidence["status"] = "passed"
        receipt.write_text(json.dumps(evidence, indent=2))
        print(json.dumps({"status": "passed", "run_id": started["run_id"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    asyncio.run(main(parser.parse_args().state_dir.resolve(strict=True)))
