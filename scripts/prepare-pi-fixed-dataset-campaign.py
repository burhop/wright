"""Prepare the reviewed fixed Pi/AgentCAD/OpenFOAM path; no CAD or solver dispatch."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape
from workspace_service.workflow_integration_policy import LOCAL_REVIEW_BINDING, LOCAL_REVIEW_DESTINATION

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT/"packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/raspberry-pi-enclosure.workflow.wflow"
BINDING = ROOT/"tests/datasets/engineering-workflows/bindings/raspberry-pi-enclosure-fixed.json"
spec = importlib.util.spec_from_file_location("pi_fixed_draft_helpers", ROOT/"scripts/prepare-printed-dataset-campaign.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def prepare(args, directory, available):
    config = json.loads(BINDING.read_text(encoding="utf-8"))
    mapping = getattr(args, "server_map", {}) or {}
    if isinstance(mapping, str):
        mapping = json.loads(Path(mapping).read_text())["server_map"]
    def server(name):
        return mapping.get(name, name)
    scenario = json.loads((directory/"scenario.json").read_text())
    identity = scenario["scenario_id"]
    workspace = Path(args.workspace_root).resolve()
    draft = Path(args.draft_root).resolve()/identity/args.attempt
    if draft.exists():
        raise ValueError("Preserve existing prepared attempt")
    suffix = identity.replace("-", "_")+"_"+args.attempt.replace("-", "_")
    inputs = f"campaign/{identity}/{args.attempt}/inputs"
    output = f"campaign/{identity}/{args.attempt}/artifacts"
    source = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(source)
    original = [s["id"] for s in sections if s["kind"] == "task"]
    edges = [s.copy() for s in sections if s["kind"] == "connection"]
    stages = {prefix: next(s for s in sections if s["kind"] == "task" and s["id"].startswith(prefix+"_")) for prefix in ("source_dimensions", "design_basis", "agentcad_enclosure", "cfd_compare")}
    staged = []
    def stage(name, data, provenance):
        relative = inputs+"/"+name
        helpers.write_once(helpers.confined(workspace, relative), data)
        staged.append({"path": relative, "sha256": helpers.digest(data), "size_bytes": len(data), **provenance})
    for path in sorted(directory.iterdir()):
        if path.is_file():
            stage(path.name, path.read_bytes(), {"original": path.relative_to(ROOT).as_posix()})
    sources = [ROOT/"scripts"/name for name in ("pi_reference_mcp.py", "pi_cfd_operations.py", "pi_cfd_mcp.py")]+[ROOT/"scripts/pi_foam_boundary/wrightPrghFanPressure.C"]
    for path in sources:
        stage(path.name, path.read_bytes(), {"authored_source": path.relative_to(ROOT).as_posix()})
    document = ROOT/"specs/081-engineering-workflow-templates/dataset-campaign/pi-fixed-runtime.md"
    stage("fixed-cfd-contract.md", document.read_bytes(), {"authored_contract": document.relative_to(ROOT).as_posix()})
    human = "\n\n".join("## Uploaded file: "+name+"\n\n"+(directory/name).read_text(encoding="utf-8") for name in [scenario["files"]["user_profile"], scenario["files"]["prompt"], *scenario["files"]["context"]])
    stage("assembled-context.md", human.encode(), {"derived_from": scenario["files"]})
    project = workspace/output/"agentcad-project"
    initialization = {"status": "requires_native_initialization", "project": str(project)}
    if args.initialize_agentcad:
        if project.exists():
            raise ValueError("Native initialization requires a fresh disposable project")
        project.mkdir(parents=True)
        command = ["uv", "run", "--isolated", "--python", "3.12", "--with", "agentcad[mcp]==0.6.0", "agentcad", "init", "--name", "pi-enclosure", "--build-dir", "build"]
        result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=300)
        initialization.update(status="native_initialized" if result.returncode == 0 else "failed", command=command, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
        stage("native-initialization.json", (json.dumps(initialization, indent=2)+"\n").encode(), {"native_prerequisite": True})
        if result.returncode:
            raise ValueError("Native AgentCAD initialization failed; retain recorded evidence")
    else:
        stage("native-initialization.json", json.dumps(initialization).encode(), {"native_prerequisite": False})
    references = {key: helpers.add_file_input(sections, suffix, key, inputs+"/"+filename) for key, filename in (("human_context", "assembled-context.md"), ("fixed_contract", "fixed-cfd-contract.md"), ("compiler_source", "pi_cfd_operations.py"), ("reference_source", "pi_reference_mcp.py"), ("native_setup", "native-initialization.json"), ("styling_image", "concept.png"))}
    next(s for s in sections if s["id"] == references["styling_image"].split(".")[0])["fields"]["outputs"][0]["kind"] = "reference_images"
    def new(prefix, title):
        task = {"kind": "task", "id": prefix+"_"+suffix, "fields": {"name": title, "purpose": title, "step_type": "work", "performed_by": "ai_assisted", "group": None, "inputs": [], "outputs": [], "settings": {}, "tool": None, "reusable_step": None}}
        sections.append(task)
        return task
    def bind(task, prompt, filename, tool_server=None, expected=()):
        task["fields"].update(step_type="work", performed_by="ai_assisted", prompt=prompt, inputs=[], outputs=[helpers.port(task["id"]+"_result")])
        settings = {"save_output": True, "output_filename": output+"/"+filename, "output_format": "markdown" if filename.endswith(".md") else "json", "file_policy": "overwrite", "timeout_seconds": 600}
        if tool_server:
            settings.update(authoring_template="mcp-task", mcp_server=server(tool_server), max_tool_calls=12, expected_files="\n".join(output+"/"+path for path in expected), task_guidance="Exact selected tools only. No Blender/socket/bridge. Preserve actual same-run geometry/field lineage, disclosed modeling limits and failed results. Tool output summaries must stay below 12000 characters; retain full data on disk.")
        task["fields"]["settings"] = settings
        helpers.add_reference(sections, references["human_context"], task, "human_context")
        return task["id"]+"."+task["id"]+"_result"
    research = bind(stages["source_dimensions"], f"Call retrieve_pi_manufacturer_references once with operation_source_document={inputs+'/pi_reference_mcp.py'!r}, output_directory={output+'/research'!r}. Then call read_pi_reference_page with that operation source and research_directory={output+'/research'!r}: manufacturer-drawing.pdf page1, manufacturer-product-brief.pdf page3, manufacturer-cooler-drawing.pdf page1; follow next_offset only where relevant dimensions are cut. Each page is bounded to4000characters. Summarize exact sourced board/connector dimensions, revision/digest and approximate-reference limits. The cooler drawing supplies context only, not fan selection. Never substitute the human sketch for manufacturer evidence. Retain actual retrieved PDFs; no arbitrary browser/code calls.", "manufacturer-research.md", "wright-campaign-pi-references", ("research/manufacturer-drawing.pdf", "research/manufacturer-product-brief.pdf", "research/manufacturer-cooler-drawing.pdf", "research/manufacturer-evidence.json"))
    helpers.add_reference(sections, references["reference_source"], stages["source_dimensions"], "fixed_retrieval_source")
    basis = bind(stages["design_basis"], "Write the complete engineering design basis from actual manufacturer evidence, original prompt/context/image and fixed CFD contract. Preserve both actual requested styled variants, heat locations/loads, shell conduction, dimensions, mounts/service features and fan curve. Explicitly map board-local load coordinates to CAD coordinates. Name actual fluid/shell/board/source regions and exterior boundary planes before CAD. Use laminar ideal-gas buoyant air and disclosed material assumptions. Explain whether an exterior air region resolves shell convection or exterior solid faces are prescribed ambient; never silently equate them. For fan case use the exact synthetic tabulated inlet pressure boundary, disclose unresolved blades/duct details. Select explicit bounded transient duration/time step and record that steady-state/convergence/targets remain unvalidated. Do not invent missing accessory dimensions, manufacturer limits or measurement data.", "design-basis.md")
    helpers.add_reference(sections, research, stages["design_basis"], "retrieved_primary_evidence")
    helpers.add_reference(sections, references["styling_image"], stages["design_basis"], "human_styling_image", "reference_images")
    helpers.add_reference(sections, references["fixed_contract"], stages["design_basis"], "supported_physics")
    review = new("review_design", "Review sourced enclosure design and explicit thermal assumptions")
    review["fields"].update(step_type="review", performed_by="engineer", instructions="Review the actual sourced two-variant design basis and explicit material/domain/fan/convergence assumptions before CAD. Integration auto review authorizes local generation only.", settings={"authoring_template": "external-action-approval", "action_kind": "local_review", "approval_binding": LOCAL_REVIEW_BINDING, "approval_destination": LOCAL_REVIEW_DESTINATION, "approval_settings": {"review_task_id": review["id"]}, "approval_action": {"kind": "local_review", "mode": "review_only"}})
    helpers.add_reference(sections, basis, review, "design_to_review")
    author = new("author_cad_source", "Author actual AgentCAD enclosure and CFD region exports")
    heats = config["scenarios"][identity]["heat_regions"]
    extra = [f"{region}-{variant}.step" for region in ["board", *heats] for variant in ("a", "b")]+["cfd-contract-a.json", "cfd-contract-b.json"]
    required = [name for name in config["expected_geometry"] if name != "geometry-lineage.json"]+extra
    authored = bind(author, f"Use write_text_document to create {output}/enclosure-source.py, executable build123d CAD source for AgentCAD0.6.0. Read the exact accepted design-basis.md and fixed CFD contract. Native project is {project}; its actual setup receipt is attached. Construct both real requested styled/vented enclosure alternatives with all openings, service/mount/clearance features; no prerequisite/tutorial/fixture geometry. Export the original STEP/STL files {config['expected_geometry']!r}, plus exact closed board/heat-source region STEP files {extra!r}. Enclosure STEP may contain multiple explicit closed shell/lid solids with common material. Fluid STEP must be the actual air domain minus every solid; include the reviewed exterior air domain if selected. Keep heat-region coordinates/loads from the actual CSV/design basis. Export named source regions {heats!r}. Write cfd-contract-a.json and b with only supported JSON keys, exact workspace-relative region STEP paths and actual hashes, materials, heatW, actual unambiguous CAD plane selectors, units mm, gravity and transient settings. Fan case retains the exact uploaded curve. Contract regions use the matching enclosure/fluid/board/source STEP exports. All names must be safe lowercase identifiers. Record geometry-lineage.json with actual file hashes/frame transforms. {helpers.AGENTCAD_ENTRYPOINT_GUIDANCE} Use show_object for actual AgentCAD native version output. This step writes CAD source only; never execute it here.", "cad-authoring.json", "wright-workspace-files", ("enclosure-source.py",))
    for key in ("fixed_contract", "native_setup"):
        helpers.add_reference(sections, references[key], author, key)
    helpers.add_reference(sections, basis, author, "accepted_design")
    cad = bind(stages["agentcad_enclosure"], f"Use actual AgentCAD docs/run/inspect/measure as needed. Execute {workspace/output/'enclosure-source.py'} with cwd={str(project)!r}, build_dir='build', output='pi-comparison', preview=False, view=False,diff=False. Require actual native CAD outputs {required!r}; preserve source/frame/region hashes in geometry-lineage.json and CFD contracts. Do not replay an unknown mutation. No Blender or substitute geometry.", "cad-execution.json", "agentcad", required)
    helpers.add_reference(sections, authored, stages["agentcad_enclosure"], "authored_cad")
    helpers.add_reference(sections, basis, stages["agentcad_enclosure"], "accepted_design")
    preparation = new("prepare_cfd_case", "Compile actual CAD regions into conjugate heat-transfer meshes")
    prepared = bind(preparation, f"Call prepare_pi_cfd_comparison exactly once with operation_source_document={inputs+'/pi_cfd_operations.py'!r}, output_directory={output!r}, contract_documents={[output+'/cfd-contract-a.json',output+'/cfd-contract-b.json']!r}. This fixed compiler imports actual same-run AgentCAD STEP regions, rejects overlaps/missing boundaries, performs real conformal meshing and checkMesh, and writes fixed Allrun. Read its actual receipt, including foam_case_dir. Do not replace CAD or alter the accepted thermal model to pass. Save only a compact report; full mesh/source/geometry evidence remains in files.", "cfd-preparation-report.json", "wright-campaign-pi-cfd", ("cfd-preparation.json",))
    helpers.add_reference(sections, cad, preparation, "actual_cad_contracts")
    helpers.add_reference(sections, references["compiler_source"], preparation, "fixed_compiler_source")
    foam_case = "/workspace/campaign/"+identity+"/"+args.attempt+"/pi-cfd"
    solved = bind(stages["cfd_compare"], f"Call only actual Foam-Agent run with request={{'case_dir':{foam_case!r},'timeout':540}}. It runs the fixed parent Allrun for both actual CAD-derived alternatives, using actual OpenFOAM CHT and tabulated fan pressure where selected. No model-dependent Foam tools are authorized. Treat nonempty errors or missing computed fields as failure, even if upstream reports success. A completed matching child may return its recorded result; an unresolved mutation must not be replayed. Report actual logs and explicit transient/convergence limitations; do not fabricate comparison values.", "cfd-run-report.json", "foam-agent-csml-rpi")
    helpers.add_reference(sections, prepared, stages["cfd_compare"], "actual_mesh_preparation")
    collection = new("collect_cfd_results", "Collect actual same-run fields and two-variant comparison")
    bind(collection, f"After actual Foam-Agent run, call collect_pi_cfd_comparison once with operation_source_document={inputs+'/pi_cfd_operations.py'!r}, output_directory={output!r}. It requires completed matching solver records and actual nonempty computed fields; no input copies or design-target values may substitute. Summarize the real region temperatures, pressure/flow observations and unresolved physical/convergence assumptions against the original requirements. Preserve both variants and explain that content validity remains unmeasured.", "cfd-handoff.md", "wright-campaign-pi-cfd", ("cfd-comparison.json", "cfd-fields.zip"))
    helpers.add_reference(sections, solved, collection, "actual_solver_run")
    chain = [stages["source_dimensions"], stages["design_basis"], review, author, stages["agentcad_enclosure"], preparation, stages["cfd_compare"], collection]
    existing = {(edge["fields"]["from"], edge["fields"]["to"]) for edge in edges}
    for left, right in zip(chain, chain[1:]):
        if (left["id"], right["id"]) not in existing:
            sections.append({"kind": "connection", "id": "sequence_"+right["id"], "fields": {"type": "order", "from": left["id"], "to": right["id"], "label": "complete canonical engineering sequence", "when": None}})
    rendered = helpers.render(sections)
    validate_workspace_authoring_shape(rendered)
    plan = compile_prompt_workflow(rendered)
    selected = []
    for alias, names in config["allowed_tools"].items():
        for name in names:
            matches = [tool for tool in available if tool["server_id"] == server(alias) and tool["tool_name"] == name]
            if len(matches) != 1:
                raise ValueError("Required selected tool unavailable: "+alias+"/"+name)
            selected.append(matches[0])
    draft.mkdir(parents=True)
    target = draft/"bound.workflow.wflow"
    target.write_text(rendered, encoding="utf-8")
    report = {"schema_version": 1, "scenario_id": identity, "template_id": scenario["template_id"], "attempt_id": args.attempt, "status": "prepared_not_dispatched", "source": str(target), "source_sha256": helpers.digest(rendered.encode()), "template_source_sha256": helpers.digest(TEMPLATE.read_bytes()), "requires_template_instance_api": not bool(args.instance_source), "workspace_root": str(workspace), "output_root": output, "input_manifest": staged, "tool_allowlist": selected, "expected_outputs": scenario["expected_outputs"], "compiled_stages": [step.id for step in plan.steps], "preserved_original_stages": original, "preserved_original_edges": [edge["id"] for edge in edges], "expected_tool_created_files": [path for step in plan.steps for path in step.expected_files], "native_initialization": initialization["status"], "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": []}, "recorded_implementation": "Actual AgentCAD plus fixed CAD-region compiler and native Foam-Agent/OpenFOAM; no Blender", "blockers": [] if initialization["status"] == "native_initialized" else ["Native AgentCAD project initialization required before enrollment"]}
    helpers.publish_input_binding_evidence(report, directory)
    (draft/"staging-manifest.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    return {"scenario_id": identity, "draft": str(target), "stages": len(plan.steps), "executed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--draft-root", default=str(ROOT/".local-run/feature-081-live/pi-fixed-campaign-drafts"))
    parser.add_argument("--attempt", default="attempt-002")
    parser.add_argument("--instance-source")
    parser.add_argument("--scenario")
    parser.add_argument("--server-map")
    parser.add_argument("--initialize-agentcad", action="store_true")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    args = parser.parse_args()
    with urllib.request.urlopen(args.api+"/api/workspace/workflow-sources/tools?session_id="+urllib.parse.quote(args.session), timeout=60) as response:
        available = json.load(response)["tools"]
    rows = []
    for directory in sorted((ROOT/"tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure").iterdir()):
        identity = json.loads((directory/"scenario.json").read_text())["scenario_id"]
        if not args.scenario or args.scenario == identity:
            rows.append(prepare(args, directory, available))
    print(json.dumps({"prepared": rows, "dispatched": False}, indent=2))
