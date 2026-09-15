"""Prepare complete canonical drill-jig runs with a real AgentCAD substitution.

Only staging and compile validation occur here. Original task semantic IDs and
the explicit alignment/keepout step remain; actual tools run through Wright.
"""
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
BINDING = ROOT / "tests/datasets/engineering-workflows/bindings/parametric-drill-jig.json"
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/parametric-drill-jig.workflow.wflow"
CIRCLE_CENTER_GUIDANCE = (
    "For extracted circular edges in build123d 0.10.0, first require edge.geom_type == GeomType.CIRCLE, then use edge.arc_center (a property) for the underlying circle center and edge.radius for its radius. "
    "Edge.center() defaults to position_at(0.5), a point on the curve, and must not be used as the hole/axis center. Apply the supplied datum transform to the actual arc_center coordinates. "
    "Do not move geometry, shift supplied hole coordinates, substitute bounding-box centers or loosen extraction/alignment tolerances to compensate for a center-query API mistake. "
)
_spec = importlib.util.spec_from_file_location("campaign_draft_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py")
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)


def prepare(args, directory, tools):
    config = json.loads(BINDING.read_text())
    manifest = json.loads((directory / "scenario.json").read_text())
    identity = manifest["scenario_id"]
    suffix = identity.replace("-", "_") + "_" + args.attempt.replace("-", "_")
    workspace = Path(args.workspace_root).resolve()
    draft = Path(args.draft_root).resolve() / identity / args.attempt
    if draft.exists():
        raise ValueError("Draft attempt already exists; inspect it and choose a new attempt.")
    inputs_root = f"campaign/{identity}/{args.attempt}/inputs"
    output = f"campaign/{identity}/{args.attempt}/artifacts"
    project = str((workspace / output / "agentcad-project").resolve())
    initialization = "requires_native_agentcad_init"
    if args.initialize_agentcad:
        project_path = Path(project)
        if project_path.exists():
            raise ValueError("Native initialization requires a new disposable project directory.")
        project_path.mkdir(parents=True)
        command = ["uv", "run", "--isolated", "--python", "3.12", "--with",
                   "agentcad[mcp]==0.6.0", "agentcad", "init", "--name", "drill-jig",
                   "--build-dir", "build"]
        result = subprocess.run(command, cwd=project, capture_output=True, text=True,
                                timeout=300, check=False)
        evidence = {"command": command, "cwd": project, "returncode": result.returncode,
                    "stdout": result.stdout, "stderr": result.stderr}
        (project_path.parent / "native-project-initialization.json").write_text(
            json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        if result.returncode:
            raise RuntimeError("Native AgentCAD initialization failed; inspect recorded evidence.")
        initialization = "native_agentcad_init_completed_requires_context_preflight"
    source = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(source)
    stages = {}
    for prefix in ("validate_inputs", "generate_jig", "check_alignment"):
        matches = [s for s in sections if s["kind"] == "task" and s["id"].startswith(prefix + "_")]
        if len(matches) != 1:
            raise ValueError("Missing or ambiguous original jig stage: " + prefix)
        stages[prefix] = matches[0]
    staged = []
    for path in sorted(directory.iterdir()):
        if path.is_file():
            data = path.read_bytes()
            relative = inputs_root + "/" + path.name
            helpers.write_once(helpers.confined(workspace, relative), data)
            staged.append({"path": relative, "sha256": helpers.digest(data), "size_bytes": len(data),
                           "original": path.relative_to(ROOT).as_posix()})
    names = [manifest["files"]["user_profile"], manifest["files"]["prompt"], *manifest["files"]["context"]]
    text = "\n\n".join("## Uploaded file: " + name + "\n\n" + (directory / name).read_text(encoding="utf-8") for name in names)
    context_path = inputs_root + "/assembled-context.md"
    helpers.write_once(helpers.confined(workspace, context_path), text.encode())
    staged.append({"path": context_path, "sha256": helpers.digest(text.encode()), "derived_from": names})
    brief = helpers.add_file_input(sections, suffix, "human_context", context_path)
    image = helpers.add_file_input(sections, suffix, "jig_sketch", inputs_root + "/concept.png")
    next(s for s in sections if s["id"] == image.split(".")[0])["fields"]["outputs"][0]["kind"] = "reference_images"

    def task(prefix, title):
        value = dict(kind="task", id=prefix + "_" + suffix, fields={"name": title, "purpose": title,
            "step_type": "work", "group": None, "performed_by": "ai_assisted", "inputs": [],
            "outputs": [], "settings": {}, "tool": None, "reusable_step": None})
        sections.append(value)
        return value

    def bind(value, prompt, server=None, expected=(), filename=None, format="json", customer_context=True):
        fields = value["fields"]
        fields.update(step_type="work", performed_by="ai_assisted", prompt=prompt, inputs=[],
                      outputs=[helpers.port(value["id"] + "_result")])
        fields["settings"] = {"output_format": format, "save_output": True,
            "output_filename": output + "/" + (filename or value["id"].split("_" + suffix)[0] + ".json"),
            "file_policy": "overwrite"}
        if server:
            fields["settings"].update(authoring_template="mcp-task", mcp_server=server,
                expected_files="\n".join(output + "/" + name for name in expected), max_tool_calls=18,
                timeout_seconds=600, task_guidance="Only enrolled actual tools may execute. Preserve original user data and exact source/output lineage. No hardware operations. Do not claim a file or measurement exists unless the tool produced it.")
        if customer_context:
            helpers.add_reference(sections, brief, value, "original_human_context")
        return value["id"] + "." + value["id"] + "_result"

    def bind_native_run(value, script, label, expected):
        selected = next(t for t in tools if t["server_id"] == "agentcad" and t["tool_name"] == "run")
        value["fields"].update(step_type="work", performed_by="configured_tool", tool=None,
            reusable_step=None, inputs=[], outputs=[helpers.port(value["id"] + "_result")], prompt="",
            instructions="Execute the exact authored AgentCAD source once and retain its complete native response and required output files.")
        value["fields"]["settings"] = {"authoring_template": "mcp-tool", "mcp_server": "agentcad",
            "mcp_tool": selected["name"], "mcp_schema_digest": selected["schema_digest"],
            "mcp_source_contract": "agentcad-build123d-0.10",
            "mcp_arguments": json.dumps({"script": script, "output": label, "cwd": project,
                "build_dir": "build", "preview": False, "view": False, "diff": False}),
            "output_format": "json", "save_output": True,
            "output_filename": output + "/" + value["id"].split("_" + suffix)[0] + ".json",
            "file_policy": "overwrite", "timeout_seconds": 600,
            "expected_files": "\n".join(output + "/" + name for name in expected)}
        return value["id"] + "." + value["id"] + "_result"

    basis = bind(stages["validate_inputs"],
        "Create the reviewed design basis from the original uploaded prompt, profile, context, hole/bushing/keepout tables and sketch. "
        "Explicitly preserve datum transform, drill direction, every hole coordinate, bushing body/flange stackup, declared slip clearances, clamp occupied volumes and access windows. "
        "Tables control geometry. Their bushing sizes are synthetic customer data, not retrieved supplier facts. "
        "Record unresolved physical retention/fit/machining matters without altering holes or guessing tolerances. Preserve each specific rail, tube or keyed annular design intent.",
        filename="jig-design-basis.md", format="markdown")
    helpers.add_reference(sections, image, stages["validate_inputs"], "original_sketch", "reference_images")
    review = task("review_jig_basis", "Review exact jig design basis")
    review["fields"].update(step_type="review", performed_by="engineer", instructions="Review exact coordinate, fit and keepout decisions before generating CAD.",
        settings={"authoring_template": "external-action-approval", "action_kind": "local_review",
            "approval_binding": {"server": "wright", "tool": "review_artifacts", "schema": helpers.digest(b"wright.local_review.v1")},
            "approval_destination": {"kind": "local_review", "id": "workspace"},
            "approval_settings": {"review_task_id": review["id"]},
            "approval_action": {"kind": "local_review", "mode": "review_only"}})
    init = task("initialize_jig_project", "Verify disposable AgentCAD jig project")
    init_result = bind(init,
        f"Call actual AgentCAD context(cwd={project!r},build_dir='build') to verify the disposable project initialized by the native prerequisite setup. "
        "Require an initialized build123d project; fail if missing or interrupted. Do not initialize through another application's script bridge or fabricate state. "
        "Also call docs for the quickstart and helpers sections with the same cwd and build_dir. Retain the relevant actual build123d import, export, geometry and show_object usage in this response so the next source-authoring step uses the installed runtime contract. "
        "An empty version history and absence of CAD source are expected: the following authoring and geometry tasks create them. This task succeeds when actual context proves initialization and the requested documentation is returned. "
        "Return the actual context, prerequisite state and source-authoring documentation for the following CAD operations.",
        "agentcad", filename="project-preflight.json", customer_context=False)
    author = task("author_jig_source", "Author parametric jig and drawing source")
    code_path = str((workspace / output / "jig-source.py").resolve())
    bind(author,
        f"Create {output}/jig-source.py through write_text_document as text/plain. Author actual build123d Python source for AgentCAD 0.6.0. "
        f"{helpers.AGENTCAD_ENTRYPOINT_GUIDANCE}"
        f"Set SOURCE_PATH = {code_path!r} for actual generator-source hashing; this is the exact script argument used by the following run task. "
        f"Set OUTPUT_DIR = {str((workspace / output).resolve())!r} and PROJECT_DIR = {project!r}; exports belong in OUTPUT_DIR, while AgentCAD runs with PROJECT_DIR as cwd. "
        f"The accepted design basis is {workspace / output / 'jig-design-basis.md'}; controlling tables are {workspace / inputs_root}. "
        "Read hole, bushing and keepout CSVs from those exact paths. Build the requested complete jig with flange counterbores, datum contacts, clamp exclusions, orientation marks and access windows. "
        "Do not drill the workpiece, move supplied holes or change an existing notch. Use explicit kernel solid operations; export actual jig STEP/STL. "
        "Join datum fences, plate and connector features through finite-area interfaces: an edge-only meeting produces a nonmanifold solid. Use outside-workpiece shoulders/corner material where needed, preserving all supplied locating planes, hole coordinates and keepouts. "
        "Generate a real DXF hole-location drawing in millimetres from the constructed model's circular edges/axes, preserving datum transform; do not return a prose drawing. Use actual supported build123d drawing export or an explicit recorded DXF writer over extracted geometry. "
        f"{CIRCLE_CENTER_GUIDANCE}"
        f"Export under {workspace / output}: {json.dumps(config['expected_generated_files'])}. cad-lineage.json records actual file hashes and the source/table/transform identity. "
        "Use the supplied installed-runtime documentation for show_object and supported imports/exports. Write valid Python, including Python True/False/None literals in dictionaries. "
        "Call show_object on the actual jig for AgentCAD's own native version. Before finishing, call inspect_file on the complete written source and correct it once if any `.is_valid()` call remains; build123d 0.10 requires the `.is_valid` boolean property. "
        "This step authors source only; the following original generate_jig step executes the real kernel.",
        "wright-workspace-files", ("jig-source.py",))
    helpers.add_reference(sections, basis, author, "accepted_design")
    helpers.add_reference(sections, init_result, author, "project_initialized")
    generated = bind_native_run(stages["generate_jig"], code_path, "jig", config["expected_generated_files"])
    # Fixed native arguments read the just-authored file. The explicit sequence
    # below retains approval/authoring dependencies without JSON argument edges.
    checker = task("author_jig_inspection", "Author inspection of actual exported jig")
    check_path = str((workspace / output / "inspect-jig-source.py").resolve())
    bind(checker,
        f"Use write_text_document to create {output}/inspect-jig-source.py as text/plain. This independent build123d/OCP inspection must reopen actual {workspace / output / 'jig.step'} rather than importing the generator source or trusting its dimension claims. "
        f"{helpers.AGENTCAD_ENTRYPOINT_GUIDANCE}"
        f"Set SOURCE_PATH = {check_path!r} for actual inspection-source hashing; this is the exact script argument used by the following inspection run. "
        f"Set OUTPUT_DIR = {str((workspace / output).resolve())!r} and PROJECT_DIR = {project!r}; read the actual model and write the report at the supplied OUTPUT_DIR paths. "
        f"Read actual controlling CSVs from {workspace / inputs_root}. Extract cylindrical seat axes/radii and flange pocket dimensions; compare datum-transformed hole positions and clearances. "
        f"{CIRCLE_CENTER_GUIDANCE}"
        "Compute actual boolean intersection volumes with supplied clamp and chip-access keepout solids and record stackup. Preserve the original workflow's dimensional checks and report observed failures/unresolved evidence rather than inventing pass. "
        f"Write actual observations, input/model hashes, datum transform and check results to {workspace / output / 'dimension-report.json'}. Use show_object on the reopened actual jig for AgentCAD run output. "
        "Before finishing, call inspect_file on the complete written source and correct it once if any `.is_valid()` call remains; build123d 0.10 requires the `.is_valid` boolean property. "
        "Do not modify or regenerate jig.step in this inspection. No physical-fit or qualified manufacturing claim is permitted.",
        "wright-workspace-files", ("inspect-jig-source.py",))
    helpers.add_reference(sections, generated, checker, "actual_model_result")
    helpers.add_reference(sections, basis, checker, "accepted_requirements")
    bind_native_run(stages["check_alignment"], check_path, "inspection", config["expected_checked_files"])
    stages["check_alignment"]["fields"]["settings"]["output_filename"] = output + "/inspection-execution.json"
    observe = task("inspect_jig_exports", "Read actual independent jig inspection and native file identities")
    bind(observe, f"Call inspect_file(includeText=true,maxTextBytes=8192,offsetBytes=0) for {output}/dimension-report.json and {output}/cad-lineage.json, following nextOffsetBytes until complete with maxTextBytes=8192 on every page. Do not request larger pages or embed native execution JSON; retain the complete files and observe every page. Call inspect_file(includeText=false) for {output}/jig.step, {output}/jig.stl and {output}/hole-layout.dxf. Preserve the actual independent dimensional failures, unresolved evidence and file hashes in the observation report. Never infer physical-fit qualification from successful execution or file presence.", "wright-workspace-files", filename="cad-file-observations.json", customer_context=False)
    # This task reads the sealed files directly. Order edges below require both
    # native runs to finish without embedding their redundant response bodies.
    chain = [stages["validate_inputs"], review, init, author, stages["generate_jig"], checker, stages["check_alignment"], observe]
    for earlier, later in zip(chain, chain[1:]):
        sections.append(dict(kind="connection", id="sequence_" + later["id"], fields={"type": "order",
            "from": earlier["id"], "to": later["id"], "label": "full jig engineering sequence", "when": None}))
    rendered = helpers.render(sections)
    validate_workspace_authoring_shape(rendered)
    plan = compile_prompt_workflow(rendered)
    allowlist = []
    for server, names in config["allowed_tools"].items():
        for name in names:
            item = next((t for t in tools if t["server_id"] == server and t["tool_name"] == name), None)
            if item is None:
                raise ValueError("Required workspace tool missing: " + server + "/" + name)
            allowlist.append(item)
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(rendered, encoding="utf-8")
    report = {"schema_version": 1, "scenario_id": identity, "attempt_id": args.attempt,
        "template_id": manifest["template_id"], "status": "prepared_not_dispatched", "source": str(target),
        "template_source_sha256": helpers.digest(TEMPLATE.read_bytes()), "source_sha256": helpers.digest(rendered.encode()),
        "workspace_root": str(workspace), "output_root": output,
        "requires_template_instance_api": not bool(args.instance_source), "preserved_original_stages": [s.id for s in plan.steps],
        "input_manifest": staged, "tool_allowlist": allowlist, "expected_outputs": manifest["expected_outputs"],
        "expected_tool_created_files": [p for s in plan.steps for p in s.expected_files],
        "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": []},
        "selected_substitution": config["selected_substitution"],
        "native_project_initialization": initialization,
        "blockers": ["Native AgentCAD initialization prerequisite and real MCP context preflight must pass before CAD generation",
                     "Generated CAD, extracted-geometry DXF and independent inspection source have not executed"]}
    helpers.publish_input_binding_evidence(report, directory)
    (draft / "staging-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"scenario_id": identity, "draft": str(target), "stages": len(plan.steps), "files": len(staged), "executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", default=str(ROOT / ".local-run/feature-081-live/jig-campaign-workspace"))
    parser.add_argument("--draft-root", default=str(ROOT / ".local-run/feature-081-live/jig-campaign-drafts"))
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument("--initialize-agentcad", action="store_true",
                        help="Run pinned native AgentCAD init in each new disposable project; never generates CAD.")
    args = parser.parse_args()
    if args.instance_source and not args.scenario:
        parser.error("--instance-source requires --scenario")
    uri = args.api + "/api/workspace/workflow-sources/tools?session_id=" + urllib.parse.quote(args.session)
    with urllib.request.urlopen(uri, timeout=30) as response:
        tools = json.load(response)["tools"]
    rows = []
    for directory in sorted((ROOT / "tests/datasets/engineering-workflows/scenarios/parametric-drill-jig").iterdir()):
        identity = json.loads((directory / "scenario.json").read_text())["scenario_id"]
        if not args.scenario or identity == args.scenario:
            rows.append(prepare(args, directory, tools))
    if not rows:
        raise ValueError("No matching jig scenario")
    print(json.dumps({"prepared": rows, "executed": False}, indent=2))


if __name__ == "__main__":
    main()
