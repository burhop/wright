"""Stage full heat-spreader workflows using actual AgentCAD and OASiS operations."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/heat-spreader-sizing.workflow.wflow"
spec = importlib.util.spec_from_file_location("heat_draft_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def prepare(args, directory, tools):
    manifest = json.loads((directory / "scenario.json").read_text(encoding="utf-8"))
    identity = manifest["scenario_id"]
    suffix = identity.replace("-", "_") + "_" + args.attempt.replace("-", "_")
    workspace = Path(args.workspace_root).resolve()
    draft = Path(args.draft_root).resolve() / identity / args.attempt
    if draft.exists():
        raise ValueError("Draft attempt already exists")
    inputs = f"campaign/{identity}/{args.attempt}/inputs"
    output = f"campaign/{identity}/{args.attempt}/artifacts"
    project = workspace / output / "agentcad-project"
    if args.initialize_agentcad:
        if project.exists():
            raise ValueError("Native init requires new disposable project")
        project.mkdir(parents=True)
        command = ["uv", "run", "--isolated", "--python", "3.12", "--with", "agentcad[mcp]==0.6.0",
                   "agentcad", "init", "--name", "heat-link", "--build-dir", "build"]
        result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=300, check=False)
        (project.parent / "native-initialization.json").write_text(json.dumps({"command": command,
            "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, indent=2))
        if result.returncode:
            raise RuntimeError("Actual native initialization failed")
    source = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(source)
    original = {}
    for prefix in ("define_thermal_case", "create_plate_geometry", "solve_and_verify"):
        matches = [s for s in sections if s["kind"] == "task" and s["id"].startswith(prefix + "_")]
        if len(matches) != 1:
            raise ValueError("Missing original stage: " + prefix)
        original[prefix] = matches[0]
    staged = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            relative = inputs + "/" + path.name
            h.write_once(h.confined(workspace, relative), path.read_bytes())
            staged.append({"path": relative, "sha256": h.digest(path.read_bytes()), "original": path.relative_to(ROOT).as_posix()})
    names = [manifest["files"]["user_profile"], manifest["files"]["prompt"], *manifest["files"]["context"]]
    context = "\n\n".join("## Uploaded " + name + "\n" + (directory / name).read_text(encoding="utf-8") for name in names)
    numerical = (ROOT / "scripts/engineering/heat_conduction_skfem.py").read_bytes()
    for name, data in (("assembled-context.md", context.encode()), ("heat_conduction_skfem.py", numerical)):
        relative = inputs + "/" + name
        h.write_once(h.confined(workspace, relative), data)
        staged.append({"path": relative, "sha256": h.digest(data), "role": "reviewable_operation_source" if name.endswith(".py") else "assembled_context"})
    brief = h.add_file_input(sections, suffix, "human_context", inputs + "/assembled-context.md")
    image = h.add_file_input(sections, suffix, "thermal_sketch", inputs + "/concept.png")
    next(s for s in sections if s["id"] == image.split(".")[0])["fields"]["outputs"][0]["kind"] = "reference_images"

    def task(prefix, title):
        value = {"kind": "task", "id": prefix + "_" + suffix, "fields": {"name": title, "purpose": title,
                 "step_type": "work", "group": None, "performed_by": "ai_assisted", "inputs": [],
                 "outputs": [], "settings": {}, "tool": None, "reusable_step": None}}
        sections.append(value)
        return value

    def bind(step, prompt, server=None, files=(), filename=None, format="json", customer_context=True):
        f = step["fields"]
        f.update(step_type="work", performed_by="ai_assisted", prompt=prompt, inputs=[], outputs=[h.port(step["id"] + "_result")])
        f["settings"] = {"output_format": format, "save_output": True,
            "output_filename": output + "/" + (filename or step["id"].split("_" + suffix)[0] + ".json"), "file_policy": "overwrite"}
        if server:
            f["settings"].update(authoring_template="mcp-task", mcp_server=server, expected_files="\n".join(output + "/" + p for p in files),
                max_tool_calls=15, timeout_seconds=600, task_guidance="Execute only actual enrolled tools; retain source and file identity. Report errors; never replace engineering operations with reports or example fields.")
        if customer_context:
            h.add_reference(sections, brief, step, "original_customer_context")
        return step["id"] + "." + step["id"] + "_result"

    basis = bind(original["define_thermal_case"], "Produce the thermal basis from all original human inputs and sketch. Preserve every CSV candidate, SI conversion, conductivity, density, heat flux, cold temperature, insulation and limit. For the copper case preserve total interface resistance0.15K/W, converted separately using each actual interface area. Do not invent material certifications or extra physics. Record that the supplied numerical source is a real FE operation and analytical comparison is separate.", filename="thermal-basis.md", format="markdown")
    h.add_reference(sections, image, original["define_thermal_case"], "input_sketch", "reference_images")
    review = task("review_thermal_basis", "Review exact thermal boundaries and units")
    review["fields"].update(step_type="review", performed_by="engineer", instructions="Review the exact original thermal basis, interface units and candidate list.",
        settings={"authoring_template": "external-action-approval", "action_kind": "local_review",
            "approval_binding": {"server": "wright", "tool": "review_artifacts", "schema": h.digest(b"wright.local_review.v1")},
            "approval_destination": {"kind": "local_review", "id": "workspace"},
            "approval_settings": {"review_task_id": review["id"]}, "approval_action": {"kind": "local_review", "mode": "review_only"}})
    preflight = task("preflight_heat_project", "Verify disposable AgentCAD project")
    preflight_result = bind(preflight, f"Current task: verify the already initialized disposable project and retrieve its source-authoring documentation. Call actual AgentCAD context(cwd={str(project)!r},build_dir='build'), then docs(section='quickstart',cwd={str(project)!r},build_dir='build') and docs(section='helpers',cwd={str(project)!r},build_dir='build'). Success means the response identifies the initialized build123d project at this cwd and retains the actual import/export/show_object documentation for the next authoring stage. An empty model registry and absence of plate source or solver outputs are expected at this stage: subsequent authoring, CAD and FE tasks create them. Return the actual project identity and ready_for_authoring=true when initialization is present; otherwise report the concrete initialization failure. Full-workflow customer goals are background context, not completion criteria for this project check.", "agentcad", customer_context=False)
    author = task("author_plate_source", "Author actual parametric plates and measurements")
    cases = [line.split(",")[0] for line in (directory / "alternatives.csv").read_text(encoding="utf-8").splitlines()[1:] if line]
    cad_source = str(workspace / output / "plate-source.py")
    authored = bind(author,
        f"Use write_text_document to create {output}/plate-source.py text/plain with real build123d source for all exact alternatives in {workspace / inputs / 'alternatives.csv'}. "
        f"{h.AGENTCAD_ENTRYPOINT_GUIDANCE}"
        f"Create unperforated rectangular solids with origin0,0,0 and declared X-length/Y-width/Z-thickness mm. Export each as {workspace / output}/<case_id>.step. "
        f"Reopen exported STEP through kernel and save actual bounding-box dimensions_mm with x/y/z and step_sha256, indexed by exact case_id in {workspace / output / 'geometry-measurements.json'}. "
        "Use the supplied installed-runtime quickstart/helpers for supported build123d imports, exports and show_object. Write actual Python True/False/None literals. Measurements must come from reopened CAD. Call show_object on actual solids. This stage authors only; original geometry stage executes it.",
        "wright-workspace-files", ("plate-source.py",))
    h.add_reference(sections, basis, author, "reviewed_basis")
    h.add_reference(sections, preflight_result, author, "project_state")
    geometry = bind(original["create_plate_geometry"], f"Execute AgentCAD run(script={cad_source!r},output='plates',cwd={str(project)!r},build_dir='build',preview=False,view=False,diff=False). Inspect the actual AgentCAD result and retain native model/source history and generated paths. The next confined file-observation task reads exported measurements and STEP hashes; do not claim unobserved file content or require an unavailable file reader at this CAD step. No analytic proxy geometry.",
        "agentcad", tuple(name + ".step" for name in cases) + ("geometry-measurements.json",))
    h.add_reference(sections, authored, original["create_plate_geometry"], "authored_cad_source")
    observe = task("inspect_plate_exports", "Read actual plate measurements and STEP identities")
    observed = bind(observe, f"Call inspect_file for {output}/geometry-measurements.json with includeText=true; follow nextOffsetBytes until all text is observed. Also call inspect_file(includeText=false) for each actual STEP under {output}: {json.dumps([name + '.step' for name in cases])}. Return actual text and metadata, preserving every candidate, measurement and SHA256 for solver preflight. Report missing or changed files; no geometry correctness claim follows from file presence.", "wright-workspace-files", filename="cad-file-observations.json", customer_context=False)
    h.add_reference(sections, geometry, observe, "native_execution_result")
    solver_inputs = task("prepare_exact_fe_call", "Prepare recorded numerical solver call")
    container_output = args.container_workspace.rstrip("/") + "/" + output
    config = {"output_root": container_output, "alternatives_csv": args.container_workspace.rstrip("/") + "/" + inputs + "/alternatives.csv",
              "geometry_root": container_output, "geometry_measurements": container_output + "/geometry-measurements.json"}
    execution_source = "HEAT_CONFIG = " + repr(config) + "\nexec(compile(" + repr(numerical.decode()) + ", 'heat_conduction_skfem.py', 'exec'))\n"
    invocation = {"solver": "skfem", "input_content": execution_source, "job_name": container_output, "critic_approved": False}
    call_path = inputs + "/exact-solver-call.json"
    data = json.dumps(invocation, indent=2).encode()
    h.write_once(h.confined(workspace, call_path), data)
    staged.append({"path": call_path, "sha256": h.digest(data), "role": "exact_recorded_numerical_operation"})
    invocation_ref = h.add_file_input(sections, suffix, "exact_solver_arguments", call_path)
    prepared = bind(solver_inputs, "Review the supplied exact solver invocation against reviewed input and actual CAD measurements. Report geometry hashes, boundary units, total-resistance area conversion and all candidate names. Preserve the invocation byte content; no invented critic approval. Stop with an actionable error if its setup differs from approved input.", filename="solver-preflight.json")
    h.add_reference(sections, invocation_ref, solver_inputs, "exact_solver_call")
    h.add_reference(sections, geometry, solver_inputs, "actual_cad_and_measurements")
    h.add_reference(sections, observed, solver_inputs, "observed_measurements_and_hashes")
    expected = tuple(name + "-" + level + "-temperature." + extension for name in cases for level in ("coarse", "fine") for extension in ("vtu", "csv")) + ("heat-balance.json", "mesh-comparison.json", "sizing-decision.json")
    selected_solver = next((tool for tool in tools if tool["server_id"] == args.oasis_server_id and tool["tool_name"] == "run_simulation"), None)
    if not selected_solver or not selected_solver.get("name") or not selected_solver.get("schema_digest"):
        raise ValueError("Direct OASiS execution requires its actual qualified tool name and schema digest")
    execute = task("execute_recorded_fe_call", "Execute exact native conduction operation once")
    fields = execute["fields"]
    fields.update(step_type="work",performed_by="configured_tool",prompt="",inputs=[],outputs=[h.port(execute["id"]+"_result")],
        instructions="Execute the immutable connected numerical request once. Preserve critic_approved=false and the provider's unverified/pending-independent-critic warning. Runtime records actual expected-file presence and hashes; no engineering correctness attestation follows.")
    fields["settings"] = {"authoring_template":"mcp-tool","mcp_server":args.oasis_server_id,
        "mcp_tool":selected_solver["name"],"mcp_schema_digest":selected_solver["schema_digest"],
        "mcp_arguments_source":"connection","mcp_arguments_input":execute["id"]+"_exact_solver_arguments",
        "mcp_arguments":"{}","timeout_seconds":600,"output_format":"json","save_output":True,
        "output_filename":output+"/solver-execution.json","file_policy":"overwrite",
        "expected_files":"\n".join(output+"/"+name for name in expected)}
    h.add_reference(sections, invocation_ref, execute, "exact_solver_arguments")
    executed = execute["id"]+"."+execute["id"]+"_result"
    bind(original["solve_and_verify"],
        f"Complete the original thermal sizing verification using the actual preceding native FE operation. Call inspect_file(includeText=true,maxTextBytes=4096) for {output}/heat-balance.json, {output}/mesh-comparison.json and {output}/sizing-decision.json; follow nextOffsetBytes until all three JSON documents are observed. "
        f"Call inspect_file(includeText=false) for each computed raw field under {output}: {json.dumps([name for name in expected if name.endswith(('.vtu','.csv'))])}. Preserve actual hashes and byte counts for all files. "
        "Report each candidate's computed temperature, mass, declared temperature limit, analytical agreement, mesh sensitivity, and input/removed heat balance. Preserve the original two-percent analytical agreement and mesh-stability checks, one-percent heat-balance check, and required selected maximum at or below its declared limit. Use the native JSON checks and values; retain observed failures, no-candidate outcomes and every numerical/model limitation without inventing passes. "
        "The preceding OASiS call deliberately used critic_approved=false. Its result remains unverified pending an independent critic; preserve that warning explicitly. Successful execution, original numerical comparisons and file presence do not constitute OASiS verification or physical qualification. Do not dispatch a solver again, invent critic approval, replace raw fields, or add a separate deferred campaign correctness-validation program; its valid-data counter remains zero.",
        "wright-workspace-files", filename="thermal-verification-report.json", customer_context=False)
    original["solve_and_verify"]["fields"]["settings"]["max_tool_calls"] = 24
    h.add_reference(sections, executed, original["solve_and_verify"], "actual_native_solver_result")
    h.add_reference(sections, prepared, original["solve_and_verify"], "preflight")
    h.add_reference(sections, observed, original["solve_and_verify"], "actual_geometry")
    chain = [original["define_thermal_case"], review, preflight, author, original["create_plate_geometry"], observe, solver_inputs, execute, original["solve_and_verify"]]
    for before, after in zip(chain, chain[1:]):
        sections.append({"kind": "connection", "id": "sequence_" + after["id"], "fields": {"type": "order", "from": before["id"], "to": after["id"], "label": "complete thermal process", "when": None}})
    rendered = h.render(sections)
    validate_workspace_authoring_shape(rendered)
    plan = compile_prompt_workflow(rendered)
    allowed = []
    for server, names in {"agentcad": ["context", "docs", "run", "measure", "inspect"], "wright-workspace-files": ["write_text_document", "inspect_file"], args.oasis_server_id: ["run_simulation"]}.items():
        for name in names:
            match = next((t for t in tools if t["server_id"] == server and t["tool_name"] == name), None)
            if match is None:
                raise ValueError("Missing actual workspace tool: " + server + "/" + name)
            allowed.append(match)
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(rendered, encoding="utf-8")
    report = {"schema_version": 1, "scenario_id": identity, "attempt_id": args.attempt, "template_id": manifest["template_id"],
        "status": "prepared_not_dispatched", "source": str(target), "source_sha256": h.digest(rendered.encode()),
        "template_source_sha256": h.digest(TEMPLATE.read_bytes()), "workspace_root": str(workspace), "output_root": output,
        "input_manifest": staged, "tool_allowlist": allowed, "expected_outputs": manifest["expected_outputs"],
        "expected_tool_created_files": [p for s in plan.steps for p in s.expected_files], "requires_template_instance_api": not bool(args.instance_source),
        "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": []},
        "native_initialization_requested": args.initialize_agentcad, "blockers": ["Full CAD/solver workflow has not run; native init/context must succeed"],
        "preserved_original_stages": [s["id"] for s in original.values()]}
    h.publish_input_binding_evidence(report, directory)
    (draft / "staging-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"scenario_id": identity, "draft": str(target), "stages": len(plan.steps), "staged_files": len(staged), "executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oasis-server-id", required=True)
    parser.add_argument("--workspace-root", default=str(ROOT / ".local-run/feature-081-live/oasis-workspace"))
    parser.add_argument("--container-workspace", default="/workspace",
                        help="Container mount matching workspace-root; use /campaign-workspace for the demo workspace.")
    parser.add_argument("--draft-root", default=str(ROOT / ".local-run/feature-081-live/heat-campaign-drafts"))
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument("--initialize-agentcad", action="store_true")
    args = parser.parse_args()
    if args.instance_source and not args.scenario:
        parser.error("--instance-source requires --scenario")
    with urllib.request.urlopen(args.api + "/api/workspace/workflow-sources/tools?session_id=" + urllib.parse.quote(args.session), timeout=30) as response:
        tools = json.load(response)["tools"]
    rows = []
    for directory in sorted((ROOT / "tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing").iterdir()):
        if not args.scenario or json.loads((directory / "scenario.json").read_text(encoding="utf-8"))["scenario_id"] == args.scenario:
            rows.append(prepare(args, directory, tools))
    if not rows:
        raise ValueError("No matching scenario")
    print(json.dumps({"prepared": rows, "executed": False}, indent=2))


if __name__ == "__main__":
    main()
