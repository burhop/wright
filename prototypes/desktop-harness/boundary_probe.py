"""Read/rejection-only probes against retained isolated MCP evidence."""

import argparse
import asyncio
import copy
import json
from pathlib import Path

import httpx

from checkpoint_probe import connection


async def main(state):
    output = state / "boundary-probe.json"
    if output.exists():
        raise ValueError("Preserve previous boundary evidence")
    completed = json.loads((state / "protocol-probe.json").read_text())
    checkpoint = json.loads((state / "checkpoint-probe.json").read_text())
    evidence = {"scope": "isolated prototype, read/rejection-only", "calls": []}
    scope = {k: completed["workspace"][k] for k in ("workspace_id", "session_id")}
    async with connection(state, evidence, output) as call:
        evidence["wrong_workspace_denial"] = await call(
            "wright_workflow_read",
            expect_error=True,
            workspace_id=checkpoint["workspace"]["workspace_id"],
            session_id=scope["session_id"],
            path=completed["source"]["path"],
        )
        answer = json.loads((state / "desktop-protocol-answer.json").read_text())
        stale = {
            **answer,
            "request_digest": "0" * 64,
            "response_id": "deliberate-stale-reply",
        }
        evidence["stale_reply_denial"] = await call(
            "wright_reasoning_answer",
            **scope,
            **stale,
            expect_error=True,
        )
        evidence["duplicate_consumed_reply_denial"] = await call(
            "wright_reasoning_answer",
            **scope,
            **answer,
            expect_error=True,
        )
        for name, record in (("inspection", completed), ("checkpoint", checkpoint)):
            workspace = record["workspace"]
            snapshot = await call(
                "wright_process_read",
                workspace_id=workspace["workspace_id"],
                session_id=workspace["session_id"],
                path=record["source"]["path"],
                source_digest=record["source"]["storage_digest"],
                run_id=record["start_receipt"]["run_id"],
            )
            assert snapshot["state"] == "completed"
            assert snapshot["outputs"] == record["final_snapshot"]["outputs"]
            evidence[name + "_unchanged"] = {
                "run_id": snapshot["context"]["run_id"],
                "state": snapshot["state"],
                "outputs": snapshot["outputs"],
            }
    api = json.loads((state / "preview.json").read_text())["api_url"]
    async with httpx.AsyncClient(base_url=api, trust_env=False, timeout=10) as http:
        unauthorized = await http.get("/api/desktop/connection")
        assert unauthorized.status_code == 401
        evidence["unauthenticated_denial"] = unauthorized.status_code
        headers = {
            "Authorization": "Bearer " + (state / ".preview-api-token").read_text()
        }
        binding = json.loads((state / "desktop-binding.json").read_text())
        drift = copy.deepcopy(binding)
        drift["connection_id"] = "deliberately-different-frozen-profile"
        rejected = await http.post(
            "/api/desktop/connect",
            headers=headers,
            json={"client_id": "drift-probe", "binding": drift},
        )
        assert rejected.status_code == 409
        evidence["drift_denial"] = {
            "status": rejected.status_code,
            "body": rejected.json(),
        }
        final = (await http.get("/api/desktop/connection", headers=headers)).json()
        assert not final["connected"] and final["binding"] == binding
        evidence["connection_unchanged"] = final
    evidence["status"] = "passed"
    output.write_text(json.dumps(evidence, indent=2))
    print(json.dumps({"status": "passed", "evidence": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    args = parser.parse_args()
    asyncio.run(main(args.state_dir.resolve(strict=True)))
