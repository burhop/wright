"""Read-only enrolled batch audit; never dispatches an engineering tool."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import time
import urllib.parse
import urllib.request


def digest(data):
    return hashlib.sha256(data).hexdigest()


def declared_paths_for_task(section):
    """Return static task outputs, including a bound external-action receipt."""
    settings = section["fields"].get("settings") or {}
    raw_files = settings.get("expected_files", "")
    files = (
        [path.strip() for path in raw_files.splitlines() if path.strip()]
        if isinstance(raw_files, str)
        else list(raw_files or [])
    )
    declared = []
    if settings.get("save_output") and settings.get("output_filename"):
        declared.append(settings["output_filename"])
    declared.extend(files)
    if settings.get("authoring_template") == "external-action-approval":
        approval = settings.get("approval_settings") or {}
        if isinstance(approval, str):
            try:
                approval = json.loads(approval)
            except ValueError:
                approval = {}
        receipt_path = approval.get("receipt_path") if isinstance(approval, dict) else None
        if isinstance(receipt_path, str) and receipt_path.strip():
            declared.append(receipt_path.strip())
    return declared, files


def audit(args):
    root = Path(__file__).resolve().parents[1]
    for package in (root / "packages").glob("*/src"):
        sys.path.insert(0, str(package))
    from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow
    from core.redaction import redact_validation_payload
    from engineering_dataset_campaign import load_dataset, matches

    batch_path = Path(args.manifest)
    batch_bytes = batch_path.read_bytes()
    batch = json.loads(batch_bytes)
    state = json.loads(Path(args.campaign_state).read_text(encoding="utf-8"))
    inventory = {row["scenario_id"]: row for row in state["datasets"]}
    inputs = root / "tests/datasets/engineering-workflows"
    configuration = json.loads((inputs / "campaign.json").read_text(encoding="utf-8"))
    templates = root / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates"
    session = batch["cases"][0]["session_id"]
    url = args.api + "/api/workspace/workflow-sources/tools?" + urllib.parse.urlencode({"session_id": session})
    with urllib.request.urlopen(url, timeout=30) as response:
        available = json.load(response)["tools"]
    current = {(t["server_id"], t["name"], t["schema_digest"]) for t in available}
    db = sqlite3.connect(Path(args.database).resolve().as_uri() + "?mode=ro", uri=True)
    rows = []
    for case in batch["cases"]:
        errors, warnings = [], []
        row = {"scenario_id": case["scenario_id"], "attempt_id": case["attempt_id"], "errors": errors, "warnings": warnings}
        rows.append(row)

        def error(code, **details):
            errors.append({"code": code, **details})

        workspace = Path(case["workspace_root"]).resolve()
        source_path = (workspace / case["source_path"]).resolve()
        if not source_path.is_relative_to(workspace):
            error("source_path_escape")
            row["status"] = "fail"
            continue
        source = source_path.read_text(encoding="utf-8")
        if digest(source.encode()) != case["source_digest"]:
            error("source_digest_changed")
        saved = db.execute("SELECT g.document,r.revoked_at FROM workflow_integration_grants g LEFT JOIN workflow_integration_revocations r USING(policy_digest) WHERE g.policy_digest=?", (case["integration_policy_digest"],)).fetchone()
        if not saved:
            error("grant_missing")
            row["status"] = "fail"
            continue
        grant = json.loads(saved[0])
        if saved[1] is not None:
            error("grant_revoked")
        if grant["expires_at"] <= time.time():
            error("grant_expired")
        for key, case_key in (("source_path", "source_path"), ("source_digest", "source_digest"), ("dataset_id", "scenario_id"), ("dataset_digest", "dataset_digest"), ("output_root", "output_root")):
            if grant[key] != case[case_key]:
                error("grant_identity_mismatch", field=key)
        allowed = {(t["server_id"], t["name"], t["schema_digest"]) for t in grant["allowed_tools"]}
        for server, name, schema in sorted(allowed - current):
            error("granted_tool_unavailable_or_changed", server=server, name=name, schema_digest=schema)
        original = inventory[case["scenario_id"]]
        fresh = load_dataset(inputs / "scenarios" / original["path"] / "scenario.json", inputs, configuration)
        for key, expected in (("digest", case["dataset_digest"]), ("template_digest", case["template_digest"])):
            if fresh[key] != expected or original[key] != expected:
                error("original_corpus_identity_changed", field=key)
        if fresh["expected_outputs"] != original["expected_outputs"]:
            error("original_output_roles_changed")
        input_hashes = set(grant["input_files"].values())
        for relative, expected in grant["input_files"].items():
            file = (workspace / relative).resolve()
            if not file.is_relative_to(workspace) or not file.is_file() or digest(file.read_bytes()) != expected:
                error("staged_input_missing_or_changed", path=relative)
        sections = _parse(source)
        workflow_id = next(s["id"] for s in sections if s["kind"] == "workflow")
        template_source = (templates / (fresh["template_id"] + ".workflow.wflow")).read_text(encoding="utf-8")
        original_tasks = {s["id"] for s in _parse(template_source.replace("__instance__", workflow_id)) if s["kind"] == "task"}
        source_tasks = {s["id"] for s in sections if s["kind"] == "task"}
        if original_tasks - source_tasks:
            error("original_semantic_stages_missing", ids=sorted(original_tasks - source_tasks))
        try:
            compiled = compile_prompt_workflow(source)
            if set(case["required_step_ids"]) != {s.id for s in compiled.steps} or len(case["required_step_ids"]) != len(compiled.steps):
                error("required_stage_set_changed")
        except Exception as failure:
            error("canonical_compile_failed", detail=str(failure))
        static_count = dynamic_count = max_files = 0
        declared = []
        input_names = {Path(path).name for path in grant["input_files"]}
        for section in sections:
            if section["kind"] != "task":
                continue
            settings = section["fields"].get("settings") or {}
            template = settings.get("authoring_template")
            server = settings.get("mcp_server", "")
            if template == "mcp-tool":
                static_count += 1
                name, schema = settings.get("mcp_tool", ""), settings.get("mcp_schema_digest", "")
                identity = (server, name, schema)
                if not name.startswith(server + "__") or not schema:
                    error("static_tool_not_fully_pinned", step=section["id"], server=server, name=name, schema_digest=schema)
                if identity not in allowed or identity not in current:
                    error("static_tool_not_in_exact_grant_and_discovery", step=section["id"], server=server, name=name)
            elif template == "mcp-task":
                dynamic_count += 1
                selected = [item for item in allowed if item[0] == server] if server else list(allowed)
                if not selected:
                    error("dynamic_task_has_no_authorized_tools", step=section["id"], server=server)
            task_declared, files = declared_paths_for_task(section)
            max_files = max(max_files, len(files))
            if len(files) > 16:
                error("expected_files_exceed_16", step=section["id"], count=len(files))
            declared.extend(task_declared)
            for relative in task_declared:
                file = (workspace / relative).resolve()
                if not file.is_relative_to(workspace / case["output_root"]):
                    error("declared_output_outside_output_root", step=section["id"], path=relative)
                if file.is_file() and digest(file.read_bytes()) in input_hashes:
                    error("existing_declared_artifact_is_input_copy", step=section["id"], path=relative)
                elif Path(relative).name in input_names:
                    warnings.append({"code": "declared_output_shares_input_basename", "step": section["id"], "path": relative, "meaning": "Name overlap alone does not establish copied bytes; review operation output contract."})
        role_matches = {role["role"]: [name for name in declared if any(matches(name.removeprefix(case["output_root"] + "/"), p) for p in role["patterns"])] for role in fresh["expected_outputs"]}
        for role, paths in role_matches.items():
            if not paths:
                warnings.append({"code": "output_role_has_no_static_declared_match", "role": role, "meaning": "Dynamic artifacts may satisfy this role; inspect exporter contract."})
        slug = Path(case["source_path"]).name.removesuffix(".workflow.wflow")
        run_records = []
        for path in (workspace / "runs" / slug).glob("*.json"):
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if record.get("execution_context", {}).get("integration_policy_digest") == case["integration_policy_digest"]:
                    run_records.append({"run_id": record.get("run_id"), "status": record.get("status")})
            except (OSError, ValueError):
                pass
        row.update(status="fail" if errors else "review" if warnings else "pass", original_stages=len(original_tasks), required_stages=len(case["required_step_ids"]), staged_inputs=len(grant["input_files"]), granted_tools=len(allowed), static_tool_nodes=static_count, dynamic_tool_nodes=dynamic_count, max_expected_files_per_node=max_files, output_roles={key: bool(value) for key, value in role_matches.items()}, observed_run_records=run_records)
    db.close()
    result = {"at": datetime.now(timezone.utc).isoformat(), "scope": "Read-only source/grant/corpus/file-presence preflight. No engineering validation or native calls.", "manifest": str(batch_path), "manifest_sha256": digest(batch_bytes), "manifest_unchanged": batch_path.read_bytes() == batch_bytes, "cases": rows, "summary": {"cases": len(rows), "passed": sum(r["status"] == "pass" for r in rows), "review": sum(r["status"] == "review" for r in rows), "failed": sum(r["status"] == "fail" for r in rows)}}
    destination = Path(args.output)
    destination.write_text(json.dumps(redact_validation_payload(result), indent=2) + "\n", encoding="utf-8")
    return {"output": str(destination), **result["summary"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("manifest", "database", "campaign-state", "output"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    print(json.dumps(audit(parser.parse_args())))
