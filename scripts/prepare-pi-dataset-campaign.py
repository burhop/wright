"""Prepare full canonical Pi/AgentCAD/OpenFOAM drafts without executing any tools.

The original four semantic stages remain. Explicit preparation, approval and
collection steps bridge their real tool contracts. Drafts are not readiness
evidence; actual normal-API runs must satisfy host and policy preflight.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import urllib.parse
import urllib.request

from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow, validate_workspace_authoring_shape

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "tests/datasets/engineering-workflows/bindings/raspberry-pi-enclosure.json"
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/raspberry-pi-enclosure.workflow.wflow"
_spec = importlib.util.spec_from_file_location("campaign_draft_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py")
helpers = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helpers)


def prepare(args, scenario_dir, available):
    config = json.loads(BINDING.read_text())
    manifest = json.loads((scenario_dir / "scenario.json").read_text())
    identity = manifest["scenario_id"]
    suffix = identity.replace("-", "_") + "_" + args.attempt.replace("-", "_")
    workspace = Path(args.workspace_root).resolve()
    draft = Path(args.draft_root).resolve() / identity / args.attempt
    if draft.exists():
        raise ValueError("Draft attempt exists; preserve it and select a new attempt.")
    output = f"campaign/{identity}/{args.attempt}/artifacts"
    inputs_root = f"campaign/{identity}/{args.attempt}/inputs"
    foam_relative = f"campaign/{identity}/{args.attempt}"
    foam_case = "/workspace/" + foam_relative
    foam_host = str((ROOT / config["host_requirements"]["foam_mount_host"] / foam_relative).resolve())
    original = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(original)
    stages = {}
    for prefix in ("source_dimensions", "design_basis", "agentcad_enclosure", "cfd_compare"):
        matches = [s for s in sections if s["kind"] == "task" and s["id"].startswith(prefix + "_")]
        if len(matches) != 1:
            raise ValueError("Original canonical Pi stage is missing or ambiguous: " + prefix)
        stages[prefix] = matches[0]
    staged = []
    for path in sorted(scenario_dir.iterdir()):
        if path.is_file():
            data = path.read_bytes()
            target = f"{inputs_root}/{path.name}"
            helpers.write_once(helpers.confined(workspace, target), data)
            staged.append({"path": target, "sha256": helpers.digest(data), "size_bytes": len(data),
                           "original": path.relative_to(ROOT).as_posix()})
    human_text = "\n\n".join((scenario_dir / name).read_text(encoding="utf-8") for name in
                              [manifest["files"]["user_profile"], manifest["files"]["prompt"], *manifest["files"]["context"]])
    text_path = inputs_root + "/assembled-context.md"
    helpers.write_once(helpers.confined(workspace, text_path), human_text.encode())
    staged.append({"path": text_path, "sha256": helpers.digest(human_text.encode()),
                   "derived_from": [manifest["files"]["user_profile"], manifest["files"]["prompt"], *manifest["files"]["context"]]})
    brief = helpers.add_file_input(sections, suffix, "human_context", text_path)
    image = helpers.add_file_input(sections, suffix, "styling_image", inputs_root + "/concept.png")
    image_input = next(s for s in sections if s["id"] == image.split(".")[0])
    image_input["fields"]["outputs"][0]["kind"] = "reference_images"

    def task(prefix, title):
        value = dict(kind="task", id=prefix + "_" + suffix, fields={"name": title, "purpose": title,
                     "step_type": "work", "group": None, "performed_by": "ai_assisted", "inputs": [],
                     "outputs": [], "settings": {}, "tool": None, "reusable_step": None})
        sections.append(value)
        return value

    def bind(value, prompt, server=None, expected=(), format="json", filename=None):
        fields = value["fields"]
        fields.update(step_type="work", performed_by="ai_assisted", prompt=prompt, inputs=[],
                      outputs=[helpers.port(value["id"] + "_result")])
        fields["settings"] = {"output_format": format, "save_output": True,
                              "output_filename": output + "/" + (filename or value["id"].split("_" + suffix)[0] + ".json"),
                              "file_policy": "overwrite"}
        if server:
            fields["settings"].update(authoring_template="mcp-task", mcp_server=server,
                expected_files="\n".join(output + "/" + p for p in expected), max_tool_calls=20,
                timeout_seconds=600, task_guidance="Use only the enrolled tools. Save every executed source and its input/output hashes. Do not fabricate files or results. No real hardware/supplier actions.")
        helpers.add_reference(sections, brief, value, "human_context")
        return value["id"] + "." + value["id"] + "_result"

    source_ref = bind(stages["source_dimensions"],
        "Retrieve official Raspberry Pi 5 mechanical drawing and connector/cooling references from these manufacturer locations: "
        + json.dumps(config["manufacturer_sources"]) + f". Save actual retrieved PDF bytes as {output}/manufacturer-drawing.pdf and extracted text/table plus URL/date/digest in {output}/manufacturer-evidence.json. "
        "Retain the manufacturer's approximate/reference-only limitation; do not treat omitted connectors/accessories as established dimensions. "
        f"Use a recorded Python operation through Blender's execution bridge. PDF extraction interpreter: {args.pdf_python}; requires pypdf installed before dispatch. "
        f"Exact workspace root: {workspace}. Original styling sketch is not manufacturer evidence.",
        "blender-mcp-ahujasid", ("manufacturer-drawing.pdf", "manufacturer-evidence.json"))
    basis_ref = bind(stages["design_basis"],
        "Write the complete reviewable enclosure design basis using retrieved manufacturer evidence and the original human context/image. "
        "Preserve all two-variant styling, loads, shell conduction, fan-curve and mounting requirements. Separate sourced dimensions, synthetic customer assumptions and unresolved accessory data. "
        "Do not invent measured fan data, inserts, IP ratings or certification. Define the exact CAD and thermal domain frames before modeling.",
        format="markdown", filename="design-basis.md")
    helpers.add_reference(sections, source_ref, stages["design_basis"], "manufacturer_evidence")
    helpers.add_reference(sections, image, stages["design_basis"], "original_sketch", "reference_images")
    review = task("review_design", "Review exact enclosure design basis")
    review["fields"].update(step_type="review", performed_by="engineer", instructions="Review the exact sourced design basis and disclosed assumptions before CAD.",
        settings={"authoring_template": "external-action-approval", "action_kind": "local_review",
                  "approval_binding": {"server": "wright", "tool": "review_artifacts", "schema": helpers.digest(b"wright.local_review.v1")},
                  "approval_destination": {"kind": "local_review", "id": "workspace"},
                  "approval_settings": {"review_task_id": review["id"]},
                  "approval_action": {"kind": "local_review", "mode": "review_only"}})
    init = task("initialize_cad_project", "Initialize isolated AgentCAD project")
    project = str((workspace / output / "agentcad-project").resolve())
    init_ref = bind(init,
        f"Initialize only this new disposable AgentCAD project: {project}. Through the recorded Blender Python bridge invoke the installed pinned environment with arguments "
        "['uv','run','--isolated','--python','3.12','--with','agentcad[mcp]==0.6.0','agentcad','init','--name','pi-enclosure','--build-dir','build'] using that cwd. "
        f"Inspect existing state before any retry; never overwrite unrelated data. Save the actual command, exit status and source as {output}/cad-project-initialization.json.",
        "blender-mcp-ahujasid", ("cad-project-initialization.json",))
    script = task("author_cad_source", "Create AgentCAD build123d source from design basis")
    script_ref = bind(script,
        f"Use write_text_document to create {output}/enclosure-source.py as text/plain. It must be executable build123d Python for AgentCAD 0.6.0. "
        f"{helpers.AGENTCAD_ENTRYPOINT_GUIDANCE}"
        f"Read the exact accepted design basis at {workspace / output / 'design-basis.md'}. Author both requested alternatives; retain frame/units and use actual boolean CAD geometry for each shell, board/source surrogate, openings and fluid volume. "
        f"Export each through build123d export_step/export_stl under {workspace / output}; required names: {json.dumps(config['expected_geometry'])}. "
        "Write geometry-lineage.json with actual exported-byte hashes, source frames, variant IDs and unit scale. Use show_object on actual geometry for AgentCAD's own native version output. "
        "Do not run CAD in this authoring step; do not substitute a block/domain template unrelated to the sourced geometry.",
        "wright-workspace-files", ("enclosure-source.py",))
    helpers.add_reference(sections, basis_ref, script, "reviewed_design")
    helpers.add_reference(sections, init_ref, script, "project")
    cad_ref = bind(stages["agentcad_enclosure"],
        f"Read AgentCAD docs if needed and execute the actual script {workspace / output / 'enclosure-source.py'} using agentcad run with cwd={project}, build_dir='build', output='enclosure-study', preview=False, view=False, diff=False. "
        "Use actual run-returned identities. Inspect/measure the actual exported alternatives for workflow evidence, without claiming this existence-testing phase qualifies correctness. "
        f"Required output files under {workspace / output}: {json.dumps(config['expected_geometry'])}. Report failures honestly; never rerun an unknown mutation.",
        "agentcad", config["expected_geometry"])
    helpers.add_reference(sections, script_ref, stages["agentcad_enclosure"], "authored_source")
    helpers.add_reference(sections, basis_ref, stages["agentcad_enclosure"], "accepted_design")
    prep = task("prepare_cfd_case", "Prepare CAD-derived OpenFOAM cases")
    prep_ref = bind(prep,
        f"Use the recorded Blender Python execution bridge to prepare new actual OpenFOAM 10 cases under {foam_host} (container mapping {foam_case}). "
        f"Read {workspace / output / 'design-basis.md'} and the same-run AgentCAD exports/geometry-lineage.json. Copy their exact bytes into each case and record hashes; do not substitute geometry. "
        "Author each mesh and heat-transfer case from those geometries, including actual shell conduction and separate air/solid regions using chtMultiRegionFoam. Preserve buoyancy, synthetic load patches and fan curve requirements; state unsupported features explicitly. "
        "Use blockMesh/snappyHexMesh with proper mm-to-m conversion and region/surface identity. Read installed /opt/openfoam10/tutorials/heatTransfer/chtMultiRegionFoam only as dictionary syntax references. Never run a tutorial instead of the CAD model. "
        "Create a parent Allrun that runs both alternatives, retains actual solver fields, invokes foamToVTK and a recorded PyVista extraction script using /opt/conda/envs/FoamAgent/bin/python, and writes cfd-comparison.json from computed fields. "
        "An exception/nonzero solver exit must produce an explicit ERROR and stop. Place results under nonnumeric results/ names; upstream Foam run cleans numerical time directories on retry. "
        f"Save the complete executed preparation source and case file/digest manifest as {output}/cfd-preparation.json. This step authors/stages only; the next canonical Foam-Agent stage performs the real solve.",
        "blender-mcp-ahujasid", ("cfd-preparation.json",))
    helpers.add_reference(sections, cad_ref, prep, "actual_cad")
    helpers.add_reference(sections, basis_ref, prep, "thermal_design")
    solve = stages["cfd_compare"]
    solve_ref = bind(solve,
        f"Execute the prepared CAD-derived comparison with the exact Foam-Agent run tool: request={{'case_dir':{foam_case!r},'timeout':540}}. "
        "Only run is enrolled. It executes actual Allrun without requiring Foam-Agent model access. Do not call plan/input_writer/review/visualization with the protocol-only key. "
        "Preserve errors and actual returned log paths. Tool success alone does not establish expected output files.", "foam-agent-csml-rpi")
    helpers.add_reference(sections, prep_ref, solve, "case_manifest")
    collect = task("collect_cfd_results", "Collect same-run CFD fields and comparison")
    bind(collect,
        f"After successful actual Foam-Agent run, use recorded Blender Python code to read only {foam_host}/results. "
        f"Copy its cfd-comparison.json to {workspace / output / 'cfd-comparison.json'} and package actual VTK/field outputs from both variants to {workspace / output / 'cfd-fields.zip'}. "
        "Require nonempty real computed fields and preserve their run/source/geometry hashes. Retain solver logs separately. Never produce comparison numbers from the design targets or analytical correlations and never claim engineering validation. "
        "If the solver/preparation step failed or fields are absent, stop without creating substitute outputs.",
        "blender-mcp-ahujasid", ("cfd-comparison.json", "cfd-fields.zip"))
    helpers.add_reference(sections, solve_ref, collect, "solver_result")
    chain = [stages["source_dimensions"], stages["design_basis"], review, init, script,
             stages["agentcad_enclosure"], prep, solve, collect]
    existing_edges = {(s["fields"].get("from"), s["fields"].get("to")) for s in sections if s["kind"] == "connection"}
    for previous, following in zip(chain, chain[1:]):
        if (previous["id"], following["id"]) not in existing_edges:
            sections.append(dict(kind="connection", id="sequence_" + following["id"],
                fields={"type": "order", "from": previous["id"], "to": following["id"], "label": "complete canonical engineering sequence", "when": None}))
    source = helpers.render(sections)
    validate_workspace_authoring_shape(source)
    plan = compile_prompt_workflow(source)
    selected = []
    for server, names in config["allowed_tools"].items():
        for name in names:
            match = next((t for t in available if t["server_id"] == server and t["tool_name"] == name), None)
            if match is None:
                raise ValueError("Required workspace tool unavailable: " + server + "/" + name)
            selected.append(match)
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(source, encoding="utf-8")
    report = {"schema_version": 1, "scenario_id": identity, "attempt_id": args.attempt,
              "template_id": manifest["template_id"], "status": "prepared_not_dispatched",
              "template_source_sha256": helpers.digest(TEMPLATE.read_bytes()), "source_sha256": helpers.digest(source.encode()),
              "source": str(target), "workspace_root": str(workspace), "output_root": output,
              "requires_template_instance_api": not bool(args.instance_source),
              "preserved_original_stages": [s.id for s in plan.steps], "input_manifest": staged,
              "tool_allowlist": selected, "expected_outputs": manifest["expected_outputs"],
              "expected_tool_created_files": [p for s in plan.steps for p in s.expected_files],
              "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": []},
              "blockers": ["PDF interpreter must supply actual pypdf extraction before dispatch",
                           "Exact isolated AgentCAD initialization, Docker bridge access and CAD-derived CFD setup need runtime preflight",
                           "No real kernel/mesher/solver execution has validated these prepared bindings"]}
    helpers.publish_input_binding_evidence(report, scenario_dir)
    (draft / "staging-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"scenario_id": identity, "draft": str(target), "stages": len(plan.steps), "files": len(staged), "executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", default=str(ROOT / ".local-run/feature-081-live/pi-campaign-workspace"))
    parser.add_argument("--draft-root", default=str(ROOT / ".local-run/feature-081-live/pi-campaign-drafts"))
    parser.add_argument("--attempt", default="attempt-001")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument("--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a")
    parser.add_argument("--scenario")
    parser.add_argument("--instance-source")
    parser.add_argument("--pdf-python", default=str(ROOT / ".venv/Scripts/python.exe"))
    args = parser.parse_args()
    if args.instance_source and not args.scenario:
        parser.error("--instance-source requires --scenario")
    uri = args.api + "/api/workspace/workflow-sources/tools?session_id=" + urllib.parse.quote(args.session)
    with urllib.request.urlopen(uri, timeout=30) as response:
        tools = json.load(response)["tools"]
    rows = []
    for directory in sorted((ROOT / "tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure").iterdir()):
        identity = json.loads((directory / "scenario.json").read_text())["scenario_id"]
        if not args.scenario or identity == args.scenario:
            rows.append(prepare(args, directory, tools))
    if not rows:
        raise ValueError("No matching Pi scenario")
    print(json.dumps({"prepared": rows, "executed": False}, indent=2))


if __name__ == "__main__":
    main()
