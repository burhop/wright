"""Create actual sheet-metal instances, bind revised inputs and enroll; never run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import urllib.request


def request(api, method, path, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    with urllib.request.urlopen(urllib.request.Request(
        api.rstrip("/") + path, data=body, method=method,
        headers={"Content-Type": "application/json"},
    ), timeout=120) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--evidence-server-id", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--attempt", default="attempt-003")
    parser.add_argument("--scenario", choices=[f"sheet-metal-supplier-handoff-{i:02d}" for i in range(1, 4)])
    parser.add_argument("--campaign-state", default="artifacts/engineering-workflow-datasets/status.json")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    args = parser.parse_args()
    if not args.attempt.startswith("attempt-") or not args.attempt[8:].isdigit():
        parser.error("Use a numbered attempt identity")
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    template = request(args.api, "GET", "/api/workspace/workflow-source-templates/sheet-metal-supplier-handoff")["template"]
    cases = []
    for index in range(1, 4):
        identity = f"sheet-metal-supplier-handoff-{index:02d}"
        if args.scenario and identity != args.scenario:
            continue
        directory = root / identity / args.attempt
        directory.mkdir(parents=True, exist_ok=True)
        execution = directory / "execution.json"
        if execution.exists():
            cases.append(json.loads(execution.read_text(encoding="utf-8")))
            continue
        path = f"workflows/campaign-{identity}-{args.attempt}.workflow.wflow"
        saved = directory / "template-instance.json"
        if saved.exists():
            instance = json.loads(saved.read_text(encoding="utf-8"))
        else:
            payload = {
                "session_id": args.session, "template_version": template["version"],
                "expected_source_digest": template["source_digest"], "workflow_path": path,
                "request_id": f"campaign-{identity}-{args.attempt}",
            }
            pending = directory / "instance-request.json"
            if pending.exists() and json.loads(pending.read_text(encoding="utf-8")) != payload:
                raise ValueError("Existing instance request changed; inspect uncertain creation")
            pending.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            # Template API supplies immutable provenance and honors this request ID.
            instance = request(args.api, "POST", "/api/workspace/workflow-source-templates/sheet-metal-supplier-handoff/instances", payload)
            saved.write_text(json.dumps(instance, indent=2) + "\n", encoding="utf-8")
        original = directory / "original.workflow.wflow"
        original.write_text(instance["source"], encoding="utf-8")
        draft_root = directory / "prepared"
        prepared = draft_root / identity / args.attempt / "staging-manifest.json"
        if not prepared.exists():
            subprocess.run([
                sys.executable, "scripts/prepare-sheet-metal-dataset-campaign.py",
                "--workspace-root", args.workspace_root, "--draft-root", str(draft_root),
                "--evidence-server-id", args.evidence_server_id, "--scenario", identity,
                "--instance-source", str(original), "--attempt", args.attempt,
                "--api", args.api, "--session", args.session,
            ], check=True, timeout=150)
        subprocess.run([
            sys.executable, "scripts/enroll_engineering_dataset_case.py", "--prepared", str(prepared),
            "--campaign-state", args.campaign_state, "--database", args.database,
            "--session", args.session, "--source-path", path, "--output", str(execution), "--api", args.api,
        ], check=True, timeout=180)
        cases.append(json.loads(execution.read_text(encoding="utf-8")))
    combined = root / f"sheet-metal-{args.attempt}.json"
    combined.write_text(json.dumps({"schema_version": 1, "cases": cases}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "enrolled_not_dispatched", "cases": len(cases), "manifest": str(combined)}))


if __name__ == "__main__":
    main()
