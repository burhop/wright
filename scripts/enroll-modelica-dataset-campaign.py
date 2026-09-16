"""Instantiate, prepare, save and enroll Modelica heater cases; never dispatch execution."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request


def request(api, method, path, payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    with urllib.request.urlopen(urllib.request.Request(api + path, data=body, method=method, headers={"Content-Type": "application/json"}), timeout=120) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--campaign-state", default="artifacts/engineering-workflow-datasets/status.json")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    args = parser.parse_args()
    if not re.fullmatch(r"attempt-[A-Za-z0-9-]{1,40}", args.attempt):
        parser.error("--attempt must be a confined attempt identifier")
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    template = request(args.api, "GET", "/api/workspace/workflow-source-templates/water-heater-sizing")["template"]
    catalog = request(args.api, "GET", "/api/workspace/workflow-sources/tools?session_id=" + args.session)
    catalog["tools"] = [tool for tool in catalog["tools"] if tool["server_id"] == args.server_id]
    tool_path = root / ("modelica-tool-catalog-" + args.attempt + ".json")
    tool_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    cases = []
    for index in range(1, 4):
        identity = f"water-heater-sizing-{index:02d}"
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
            payload = {"session_id": args.session, "template_version": template["version"], "expected_source_digest": template["source_digest"], "workflow_path": path, "request_id": f"campaign-{identity}-{args.attempt}"}
            (directory / "instance-request.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            # Exact request identity is preserved for an uncertain HTTP response.
            instance = request(args.api, "POST", "/api/workspace/workflow-source-templates/water-heater-sizing/instances", payload)
            saved.write_text(json.dumps(instance, indent=2) + "\n", encoding="utf-8")
        original = directory / "original.workflow.wflow"
        original.write_text(instance["source"], encoding="utf-8")
        draft_root = directory / "prepared"
        prepared = draft_root / identity / args.attempt / "staging-manifest.json"
        if not prepared.exists():
            subprocess.run([sys.executable, "scripts/prepare-modelica-dataset-campaign.py", "--workspace-root", args.workspace_root, "--draft-root", str(draft_root), "--server-id", args.server_id, "--scenario", identity, "--instance-source", str(original), "--tool-catalog", str(tool_path), "--attempt", args.attempt], check=True, timeout=120)
        subprocess.run([sys.executable, "scripts/enroll_engineering_dataset_case.py", "--prepared", str(prepared), "--campaign-state", args.campaign_state, "--database", args.database, "--session", args.session, "--source-path", path, "--output", str(execution), "--api", args.api], check=True, timeout=180)
        cases.append(json.loads(execution.read_text(encoding="utf-8")))
    combined = root / ("modelica-" + args.attempt + ".json")
    combined.write_text(json.dumps({"schema_version": 1, "cases": cases}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "enrolled_not_dispatched", "cases": len(cases), "manifest": str(combined)}))


if __name__ == "__main__":
    main()
