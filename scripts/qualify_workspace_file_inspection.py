"""Read-only inspector prerequisite proof; never enrolls or dispatches a workflow."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import uuid

from tool_registry.gateway_models import GatewaySessionContext
from workspace_service.workspace_file_inspection import WorkspaceFileInspector
from workspace_service.workspace_path import WorkspacePath


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-manifest", required=True)
    parser.add_argument("--filename", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    manifest = json.loads(Path(args.execution_manifest).read_text(encoding="utf-8"))
    paths = WorkspacePath(manifest["workspace_root"])
    output_root = paths.resolve(manifest["output_root"])
    session = GatewaySessionContext("inspection-prerequisite", "wright-native-workflow", "inspection-prerequisite", str(paths.root), "legacy")
    inspector = WorkspaceFileInspector()
    observations = []
    for filename in args.filename:
        relative = manifest["output_root"] + "/" + filename
        target = paths.resolve(relative, must_exist=True)
        if not target.is_relative_to(output_root):
            raise ValueError("Prerequisite observation escapes the named attempt")
        before = target.read_bytes()
        arguments = {"relativePath":relative,"maxTextBytes":32768}
        request = uuid.uuid4().hex
        # This is an isolated provider prerequisite, not a new/live policy grant.
        inspector.grant(request_id=request,session_id=session.session_id,workspace_id=session.workspace_id,
            workspace_path=str(paths.root),arguments=arguments,expected_sha256=hashlib.sha256(before).hexdigest(),
            policy_digest="isolated-read-only-prerequisite-no-campaign-dispatch")
        value = inspector.inspect(session,arguments,request)
        if target.read_bytes() != before:
            raise ValueError("Prerequisite must leave actual outputs unchanged")
        observations.append(value)
    report = {"status":"passed", "qualification_only":True, "workflow_dispatched":False,
        "existing_grants_changed":False,"source_attempt":manifest["attempt_id"],"source_scenario":manifest["scenario_id"],
        "observations":observations}
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"passed","files":len(observations),"qualification_only":True}))


if __name__ == "__main__":
    main()
