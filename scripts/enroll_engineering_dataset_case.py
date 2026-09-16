"""Save a prepared canonical instance and enroll exact local campaign authority.

This trusted local management command is deliberately separate from the public
API. It stages no credentials and starts no execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request
import importlib.util

from workspace_service.workflow_integration_policy import WorkflowIntegrationPolicyService
from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape


def api_request(api, method, path, payload=None):
    raw = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(api.rstrip("/") + path, data=raw, method=method,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def validate_tool_bindings(plan, allowed_tools, current_tools):
    """Reject stale or unqualified direct bindings before saving/enrollment."""
    def identity(tool):
        return tool["server_id"], tool["name"], tool["schema_digest"]

    allowed = {identity(tool) for tool in allowed_tools}
    current = {identity(tool) for tool in current_tools}
    if not allowed.issubset(current):
        raise ValueError("An enrolled tool identity is unavailable or stale in the current workspace")
    for step in plan.steps:
        if step.tool_name and (step.server_id, step.tool_name, step.schema_digest) not in allowed:
            raise ValueError("Direct MCP step requires an enrolled qualified tool name and current schema: " + step.id)
        if step.agent_task and not any(server == step.server_id for server, _, _ in allowed):
            raise ValueError("Agent task requires an enrolled current server tool set: " + step.id)


def enroll(args):
    destination = Path(args.output)
    if destination.exists():
        raise ValueError("An execution manifest already exists; inspect it before re-enrolling")
    report = json.loads(Path(args.prepared).read_text(encoding="utf-8"))
    status = json.loads(Path(args.campaign_state).read_text(encoding="utf-8"))
    scenario = next(s for s in status["datasets"] if s["scenario_id"] == report["scenario_id"])
    if report.get("requires_template_instance_api"):
        raise ValueError("Prepare from an actual API-created template instance first")
    source = Path(report["source"]).read_text(encoding="utf-8")
    validate_workspace_authoring_shape(source)
    plan = compile_prompt_workflow(source)
    expected = hashlib.sha256(source.encode()).hexdigest()
    if expected != report["source_sha256"] or scenario["template_digest"] != report["template_source_sha256"]:
        raise ValueError("Prepared source/template identity changed")
    workspace = Path(report["workspace_root"]).resolve()
    binding_evidence = report.get("input_binding_evidence")
    if binding_evidence:
        spec = importlib.util.spec_from_file_location("engineering_dataset_input_bindings",Path(__file__).with_name("engineering_dataset_input_bindings.py"))
        bindings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bindings)
        raw = Path(binding_evidence["path"]).read_bytes()
        if bindings.digest(raw) != binding_evidence["sha256"]:
            raise ValueError("Prepared input binding evidence changed")
        bindings.validate_bindings(json.loads(raw),workspace_root=str(workspace),source_path=report["source"],
            expected_case={"scenario_id":scenario["scenario_id"],"attempt_id":report["attempt_id"],"source_digest":expected,"dataset_digest":scenario["digest"]})
    for item in report["input_manifest"]:
        path = (workspace / item["path"]).resolve()
        if not path.is_relative_to(workspace) or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Staged input changed or escaped the workspace")
    tools = api_request(args.api, "GET", "/api/workspace/workflow-sources/tools?"
                        + urllib.parse.urlencode({"session_id": args.session}))["tools"]
    validate_tool_bindings(plan, report["tool_allowlist"], tools)
    query = urllib.parse.urlencode({"session_id": args.session, "path": args.source_path})
    current = api_request(args.api, "GET", "/api/workspace/workflow-sources?" + query)
    # Existing matching bytes make enrollment restartable after a lost PUT reply.
    if current["storage_digest"] != expected:
        original = {s["id"] for s in _parse(current["source"]) if s["kind"] == "task"}
        if not original.issubset({s.id for s in plan.steps}):
            raise ValueError("Prepared source omitted original canonical stages")
        current = api_request(args.api, "PUT", "/api/workspace/workflow-sources", {
            "session_id": args.session, "path": args.source_path, "source": source,
            "expected_storage_revision": current["storage_revision"],
            "expected_storage_digest": current["storage_digest"], "semantic_change_validated": True,
        })
    if current["storage_digest"] != expected:
        raise ValueError("Accepted API source differs from prepared bytes")
    policy = WorkflowIntegrationPolicyService(args.database, enabled=True)
    policy_digest = policy.enroll(
        campaign_id=status["campaign_id"], dataset_id=scenario["scenario_id"],
        dataset_digest=scenario["digest"], workspace_id=current["workspace_id"],
        source_path=args.source_path, source_digest=expected,
        input_files={i["path"]: i["sha256"] for i in report["input_manifest"]},
        output_root=report["output_root"], allowed_tools=report["tool_allowlist"],
        approval_mode=status["approval_mode"],
        test_destinations=(report["approval_policy_request"].get("test_destinations", [])
                           + ([report["approval_policy_request"]["destination"]]
                              if report["approval_policy_request"].get("destination") else [])),
        expires_at=int(time.time()) + 7 * 86400,
    )
    manifest = dict(
        scenario_id=scenario["scenario_id"], attempt_id=report["attempt_id"],
        session_id=args.session, workspace_root=str(workspace), source_path=args.source_path,
        source_digest=expected, dataset_digest=scenario["digest"],
        template_digest=scenario["template_digest"], required_step_ids=[s.id for s in plan.steps],
        output_root=report["output_root"], integration_policy_digest=policy_digest,
    )
    if binding_evidence:
        manifest.update(input_binding_contract="wright.input-bindings.v1",input_binding_evidence=binding_evidence)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"scenario_id": scenario["scenario_id"], "manifest": str(destination), "status": "enrolled_not_dispatched"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("prepared", "campaign-state", "database", "session", "source-path", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    print(json.dumps(enroll(parser.parse_args())))


if __name__ == "__main__":
    main()
