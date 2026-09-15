"""Install the qualified, source-bound evidence operations in the demo workspace."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def request(api, method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(api + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--qualification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    proof = json.loads(args.qualification.read_text())
    source = (ROOT / "scripts/engineering_evidence_mcp.py").read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    if (proof.get("status") != "passed" or proof.get("operation_sha256") != digest
            or {r["route"] for r in proof["routes"] if r["status"] == "passed"} != {"direct", "gateway"}):
        raise ValueError("Current exact source requires successful direct and gateway evidence")
    snapshot = ROOT / ".local-run/feature-081-live/sources" / ("engineering-evidence-" + digest[:16]) / "operations.py"
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if snapshot.exists() and snapshot.read_bytes() != source:
        raise ValueError("Existing immutable source snapshot differs")
    if not snapshot.exists():
        snapshot.write_bytes(source)
    workspace = args.workspace.resolve(strict=True)
    command = ["docker", "run", "--rm", "-i", "--entrypoint", "python",
               "-v", f"{workspace.as_posix()}:/work",
               "-v", f"{snapshot.as_posix()}:/opt/engineering_evidence_mcp.py:ro",
               "-e", "WRIGHT_EVIDENCE_WORKSPACE=/work",
               "-e", 'WRIGHT_EVIDENCE_ORIGINS=["https://sendcutsend.com"]',
               proof["image"], "/opt/engineering_evidence_mcp.py"]
    report = json.loads(args.output.read_text()) if args.output.exists() else {
        "source_sha256": digest, "command": command, "qualification": str(args.qualification.resolve()),
        "operations": [], "campaign_execution": False}
    if report["source_sha256"] != digest or report["command"] != command:
        raise ValueError("Existing installation differs; inspect it before changing the host")

    def persist():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")

    if "server_id" not in report:
        created = request(args.api, "POST", "/api/mcp/servers", {
            "name": "Engineering evidence operations — campaign " + digest[:12], "type": "stdio",
            "command": command, "default_enabled": False, "category": "engineering", "risk_level": "medium",
            "deployment_mode": "local-only", "installed_version": digest,
            "description": "Selected clean-container public supplier reference retrieval and same-attempt artifact manifest. Exact executed source, output confinement and configured HTTPS origins; no supplier account or order operations. Local qualification only."})
        report["server_id"] = created["server_id"]
        report["operations"].append({"stage": "register", "result": created})
        persist()
    identity = report["server_id"]
    for stage, method, path, body in [
        ("install", "POST", "/api/mcp/servers/" + identity + "/install?session_id=" + urllib.parse.quote(args.session), None),
        ("enable_demo", "POST", "/api/workspace/tools/toggle", {"session_id": args.session, "server_id": identity, "is_enabled": True}),
        ("activate", "PATCH", "/api/mcp/servers/" + identity, {"is_active": True}),
    ]:
        if any(item["stage"] == stage for item in report["operations"]):
            continue
        result = request(args.api, method, path, body)
        report["operations"].append({"stage": stage, "result": result})
        persist()
    tools = request(args.api, "GET", "/api/workspace/workflow-sources/tools?session_id=" + urllib.parse.quote(args.session))["tools"]
    report["tools"] = [t for t in tools if t["server_id"] == identity]
    report["status"] = "installed_discovered" if {t["tool_name"] for t in report["tools"]} == {
        "retrieve_public_references", "read_reference_text", "collect_artifact_manifest"} else "discovery_incomplete"
    persist()
    print(json.dumps({"status": report["status"], "server_id": identity, "tools": len(report["tools"])}))


if __name__ == "__main__":
    main()
