"""Prepare full bracket revision studies with actual CAD and recorded CalculiX."""
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
TEMPLATE = ROOT / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/lightweight-equipment-bracket.workflow.wflow"
BINDING = ROOT / "tests/datasets/engineering-workflows/bindings/lightweight-equipment-bracket.json"
spec = importlib.util.spec_from_file_location("bracket_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


PROVISIONAL_REVISION_SCOPES = {
    "lightweight-equipment-bracket-01": (
        "Choose milled shelf/wall pockets or retained ribs in nonfunctional material. "
        "Keep the supplied camera contact surface, hole-center clearance zones, wall attachment and envelope intact."
    ),
    "lightweight-equipment-bracket-02": (
        "Choose symmetric openings in the two existing triangular ribs first; nonfunctional plate pockets may supplement them. "
        "Keep the full no-pocket instrument-pad volume, back/instrument bores and unobstructed cable corridor intact. "
        "Treat the supplied material-around-bolt-bores requirement conservatively as a radial ligament measured from the bore surface, not from its centerline."
    ),
    "lightweight-equipment-bracket-03": (
        "Choose symmetric cheek pockets and, if useful, nonfunctional base pockets within the supplied two-setup milling capability. "
        "Keep the pivot-bearing annuli, complete crossbar outside faces, datum/contact faces, bolt-bore edge distances and empty service-access region intact."
    ),
}

PROVISIONAL_REVISION_GUIDANCE = (
    "This workflow explicitly authorizes engineering design choices for one provisional baseline/revision study within the uploaded constraints. "
    "A missing customer pocket drawing is a design variable to resolve here, not missing evidence that forbids a revision. "
    "Select one concrete reproducible candidate now, before review, using the scenario's provisional_geometry_authority in the connected solver contract. "
    "Prefer simple symmetric milled pockets with the fewest distinct profiles/setups, minimum permitted tool radii and conservatively retained webs; "
    "choose exact dimensions that seek the original mass target without relaxing any constraint. "
    "The basis must contain a numbered Boolean-operation/parameter table: parent solid, local datum and axes, profile type and exact coordinates/vertices, "
    "corner radii, cut direction, depth or through extent, symmetry transforms, retained wall/ligament dimensions and protected-region exclusions. "
    "Every selected curve transition or cutter-access treatment must also be source-ready and deterministic: state the exact radius, construction side, "
    "centers and tangent endpoints, or give one exact geometric construction that uniquely determines them. A lower bound such as 'R3 minimum', "
    "a qualitative instruction such as 'tangent blend', or an implementation-time choice is not a complete reviewed operation. Delete an optional "
    "transition before review when it cannot be fully defined; source authoring may not choose its geometry after approval. "
    "Dimension any necessary manufacturability fillets explicitly, record their effect on the stated nominal baseline, and apply common features consistently to both variants; "
    "do not silently alter baseline primitives, holes, envelope, interfaces or manufacturing requirements. "
    "Label every selected pocket/fillet dimension and interpretation as an authored provisional engineering assumption, not an uploaded measurement, supplier fact or verified geometry. "
    "Do not infer dimensions by scaling the concept sketch. Leave measured mass, strength, deflection and mesh convergence pending actual CAD/solver operations, "
    "but do not leave the candidate geometry itself unspecified merely because it was not supplied. "
    "The existing review gate must review these exact choices before source authoring. If no target-meeting candidate is established, still select a conservative feasible "
    "nonzero-removal candidate for evaluation and retain the original target as an unproven acceptance criterion; never promise the target will pass. "
    "A genuine conflict among mandatory constraints must be named explicitly and remains a blocker, not waived by provisional status. "
)


def prepare(args, directory, tools):
    config = json.loads(BINDING.read_text(encoding="utf-8"))
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
            raise ValueError("Native initialization needs a new disposable project")
        project.mkdir(parents=True)
        command = ["uv", "run", "--isolated", "--python", "3.12", "--with", "agentcad[mcp]==0.6.0", "agentcad", "init", "--name", "bracket-study", "--build-dir", "build"]
        result = subprocess.run(command, cwd=project, capture_output=True, text=True, timeout=300, check=False)
        (project.parent / "native-initialization.json").write_text(json.dumps({"command": command, "cwd": str(project), "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}, indent=2))
        if result.returncode:
            raise RuntimeError("Native AgentCAD initialization failed")
    source = Path(args.instance_source).read_text(encoding="utf-8") if args.instance_source else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    sections = _parse(source)
    original = {}
    for prefix in ("define_load_case", "create_bracket", "solve_and_compare"):
        found = [s for s in sections if s["kind"] == "task" and s["id"].startswith(prefix + "_")]
        if len(found) != 1:
            raise ValueError("Missing original task: " + prefix)
        original[prefix] = found[0]
    staged = []
    def stage(name, data, role):
        relative = inputs + "/" + name
        h.write_once(h.confined(workspace, relative), data)
        staged.append({"path": relative, "sha256": h.digest(data), "role": role})
    for path in sorted(directory.iterdir()):
        if path.is_file():
            stage(path.name, path.read_bytes(), "original_customer_input")
    names = [manifest["files"]["user_profile"], manifest["files"]["prompt"], *manifest["files"]["context"]]
    context = "\n\n".join("## Uploaded " + name + "\n" + (directory / name).read_text(encoding="utf-8") for name in names)
    stage("assembled-context.md", context.encode(), "assembled_context")
    selected = {**config, "selected_scenario": config["scenarios"][identity],
        "provisional_geometry_authority": {
            "status": "authored_provisional_engineering_design_not_customer_or_supplier_evidence",
            "scenario_id": identity,
            "scope": PROVISIONAL_REVISION_SCOPES[identity],
            "selection_and_disclosure": PROVISIONAL_REVISION_GUIDANCE,
            "approval": "existing_review_bracket_basis_before_authoring",
            "constraint_precedence": "Original uploaded geometry, loads, material, manufacturing constraints and acceptance targets remain controlling.",
            "release_authorized": False,
        }}
    stage("selected-solver-contract.json", json.dumps(selected, indent=2).encode(), "explicit_operation_and_approximation")
    stage("calculix_recorded_fields.py", (ROOT / "scripts/engineering/calculix_recorded_fields.py").read_bytes(), "reviewable_output_only_native_operation")
    brief = h.add_file_input(sections, suffix, "human_context", inputs + "/assembled-context.md")
    contract = h.add_file_input(sections, suffix, "solver_contract", inputs + "/selected-solver-contract.json")
    image = h.add_file_input(sections, suffix, "bracket_sketch", inputs + "/concept.png")
    next(s for s in sections if s["id"] == image.split(".")[0])["fields"]["outputs"][0]["kind"] = "reference_images"

    def task(prefix, title):
        value = {"kind": "task", "id": prefix + "_" + suffix, "fields": {"name": title, "purpose": title,
            "step_type": "work", "group": None, "performed_by": "ai_assisted", "inputs": [], "outputs": [], "settings": {}, "tool": None, "reusable_step": None}}
        sections.append(value)
        return value

    def bind(step, prompt, server=None, files=(), filename=None, format="json", customer_context=True):
        f = step["fields"]
        f.update(step_type="work", performed_by="ai_assisted", prompt=prompt, inputs=[], outputs=[h.port(step["id"] + "_result")])
        f["settings"] = {"output_format": format, "save_output": True,
            "output_filename": output + "/" + (filename or step["id"].split("_" + suffix)[0] + ".json"), "file_policy": "overwrite"}
        if server:
            f["settings"].update(authoring_template="mcp-task", mcp_server=server, expected_files="\n".join(output + "/" + p for p in files),
                max_tool_calls=16, timeout_seconds=600, task_guidance="Use actual enrolled tools only. Preserve exact native sources, original resource digests, per-run identities and files. No fixture geometry/results, no silent retry with unknown dispatched outcome, no fabrication or hardware action.")
        if customer_context:
            h.add_reference(sections, brief, step, "original_user_inputs")
            h.add_reference(sections, contract, step, "selected_solver_contract")
        return step["id"] + "." + step["id"] + "_result"

    basis = bind(original["define_load_case"], "Create the exact baseline/revision design and mechanical basis from every uploaded prompt, dimension/hole/load table, manufacturing rule and sketch. Preserve all coordinates, single-solid design, tool radius/wall/keepouts, material69000MPa/nu0.33/density2700 and actual load vector. Explicitly declare Casys equal-selected-node total-force distribution as an approximation to uniform patch traction; optional gravity is excluded, never silently merged. Declare an evaluated stress region/singularity treatment while preserving all unfiltered stress values, mesh comparison3mm/2mm and original target. Require exact load-pad face imprints and a centroid vertex for actual displacement sampling. Describe the explicit separate output-only reaction/FRD solve and original-vs-second-run lineage before review. Unknown measured or supplier evidence stays unresolved. " + PROVISIONAL_REVISION_GUIDANCE, filename="mechanical-basis.md", format="markdown")
    h.add_reference(sections, image, original["define_load_case"], "original_sketch", "reference_images")
    review = task("review_bracket_basis", "Review exact loads, geometry and solver assumptions")
    review["fields"].update(step_type="review", performed_by="engineer", instructions="Review the exact dimensional and mechanical basis, loading approximation and explicit second output-only solve. Review the fully dimensioned provisional revision operation table, each disclosed authored assumption and every protected-region/manufacturing constraint before authoring. Provisional approval authorizes the recorded study geometry, not a claim that acceptance targets pass or production release.",
        settings={"authoring_template": "external-action-approval", "action_kind": "local_review",
            "approval_binding": {"server": "wright", "tool": "review_artifacts", "schema": h.digest(b"wright.local_review.v1")},
            "approval_destination": {"kind": "local_review", "id": "workspace"}, "approval_settings": {"review_task_id": review["id"]},
            "approval_action": {"kind": "local_review", "mode": "review_only"}})
    preflight = task("preflight_bracket_project", "Verify isolated AgentCAD project")
    preflight_result = bind(preflight, f"Current task is only to verify the initialized disposable project: call actual AgentCAD context(cwd={str(project)!r},build_dir='build'). Return actual project identity and ready_for_authoring=true if initialized. An empty model registry and absence of CAD source, geometry or solver results are expected: later tasks create those outputs. Report only concrete missing initialization as failure; the full-workflow engineering goals are not this project's completion criteria.", "agentcad", customer_context=False)
    author = task("author_bracket_source", "Author baseline and lightweight revision CAD")
    cad_source = str(workspace / output / "bracket-source.py")
    authored = bind(author,
        f"Use write_text_document to write {output}/bracket-source.py as actual build123d/OCP source. Derive exact baseline and legitimate lighter revision from {workspace / inputs}, reviewed basis and selected contract. "
        "Implement the exact numbered provisional geometry operations and dimensions selected in the reviewed basis for both baseline and revision. "
        "These disclosed engineering choices are authorized study inputs even when no customer pocket drawing exists; do not refuse solely because they are provisional or results remain unmeasured. "
        "Record the implemented operation/parameter table and assumption attribution in model-measurements.json alongside actual reopened geometry measurements. "
        "Do not substitute a new unreviewed pocket design after the gate; if an essential parameter is absent or violates a mandatory constraint, identify that precise defect. "
        f"{h.AGENTCAD_ENTRYPOINT_GUIDANCE}"
        "Both exported candidates must each be one connected solid, with all original holes, datum/envelope, contact surfaces and cable/service keepouts. Use real pocket/rib operations respecting supplied milling radii/walls, no changed loads or targets. "
        "Imprint exact load-patch boundaries onto the external face and split that patch into faces meeting at its exact centroid vertex. Use native face-imprint topology (for example OCP BRepFeat_SplitShape), not extra disconnected solids or a hole at the centroid. Tight Gmsh Surface In BoundingBox selections need complete imprinted faces. "
        f"Export actual {workspace / output / 'baseline.step'} and revised.step. Reopen exports to inspect single solid, volume/mass and hole/patch/centroid features. Write model-measurements.json and actual mass-comparison.csv under {workspace / output}. "
        f"Write fea-requests.json with four exact recorded static argument objects for baseline/revised x coarse3mm/fine2mm, with stable unique request_id prefixes {identity}-{args.attempt}, actual STEP SHA256, /inputs/{output}/<variant>.step, element_order2, material69000MPa/nu0.33, exact tight cylinder fixture boxes, all load-patch boxes and supplied total load vector. No arbitrary decks or body/gravity loads. Include variant/mesh labels outside the closed arguments object. "
        "Call show_object on actual CAD solids for native history. This step authors source; the next original CAD stage executes the actual kernel.",
        "wright-workspace-files", ("bracket-source.py",))
    h.add_reference(sections, basis, author, "reviewed_basis")
    h.add_reference(sections, preflight_result, author, "actual_project_state")
    geometry = bind(original["create_bracket"], f"Execute actual AgentCAD run(script={cad_source!r},output='brackets',cwd={str(project)!r},build_dir='build',preview=False,view=False,diff=False). Inspect actual native execution result; the next confined file-observation task reads exported STEP identities, measurements, mass comparison and solver arguments. Each candidate must be one solid; fail on missing pad/centroid topology instead of using a broad substitute load face. Do not require an unavailable file reader at this CAD step or claim unobserved file contents.",
        "agentcad", ("baseline.step", "revised.step", "model-measurements.json", "mass-comparison.csv", "fea-requests.json"))
    h.add_reference(sections, authored, original["create_bracket"], "executed_source")
    observe = task("inspect_bracket_exports", "Read actual bracket measurements and recorded solver requests")
    observed = bind(observe, f"Call inspect_file(includeText=true) for each actual {output}/model-measurements.json, {output}/mass-comparison.csv and {output}/fea-requests.json. Follow nextOffsetBytes until complete. Call inspect_file(includeText=false) for {output}/baseline.step and {output}/revised.step. Return full exact closed solver argument objects and actual file text/identities, without inventing or modifying requests, mass values or hashes. File presence is not engineering validation.", "wright-workspace-files", filename="cad-file-observations.json", customer_context=False)
    h.add_reference(sections, geometry, observe, "native_execution_result")
    solve_step = task("recorded_revision_solves", "Run both revisions and mesh levels through recorded CalculiX")
    solves = bind(solve_step, f"Use actual arguments from {workspace / output / 'fea-requests.json'} for baseline/revised x coarse/fine. For each use calculix_mesh_preflight with only its exact supported subset(step_path,expected_step_sha256,mesh_size_mm,element_order,selections); inspect actual nonempty fixture/load selections and node bounds. Then call calculix_solve_static_recorded with its exact closed arguments. Preserve each run's real runId, STEP hash, request identity, mesh counts, original observations and sealed resource list in returned JSON. On a lost result use calculix_run_get for the same request_id; never blindly dispatch a new request. No point loads or enlarged patch substitute, no fake fields. Return four labels mapped to actual results for the next explicit field-expansion stage.",
        args.solver_server_id, filename="recorded-solver-runs.json")
    h.add_reference(sections, geometry, solve_step, "actual_models_and_requests")
    h.add_reference(sections, observed, solve_step, "observed_solver_arguments_and_hashes")
    expansions = []
    field_results = []
    for variant in ("baseline", "revised"):
        for mesh in ("coarse", "fine"):
            label = f"{variant}-{mesh}"
            expansion = task(f"expand_{variant}_{mesh}_fields", f"Export {label} fields and explicitly solve for reactions and FRD")
            expected = tuple(f"fea/{label}/{path}" for path in (
                "original/job.inp", "original/job.dat", "original/displacement-field.csv", "original/stress-field.csv",
                "native-field-expansion/job.frd", "native-field-expansion/displacement-field.csv",
                "native-field-expansion/stress-field.csv", "reaction-forces.json", "field-expansion-receipt.json"))
            fields = bind(expansion, f"For the completed {label} recorded run only, call export_recorded_fields_and_reactions(run_id=<actual>,expected_step_sha256=<actual>,output_directory='{output}/fea/{label}'). This is an explicit separate native solve adding RF/FRD output requests only. Preserve original nine sealed resources/full DAT, exact patch diff, second native command/input/output hashes, reactions and full displacement/stress fields. Report unresolved centroid-node sampling; never call nearest-node values the exact centroid. Do not present second-run output as original Casys output, do not repeat ambiguous native output directories, and do not modify a physical deck.", args.field_server_id, expected, filename=f"{label}-field-expansion-results.json")
            h.add_reference(sections, solves, expansion, "actual_recorded_run_identities")
            expansions.append(expansion)
            field_results.append((label, fields))
    bind(original["solve_and_compare"], "Complete the original structural comparison from the actual prior kernel and solver operations: baseline/revised mass and target reduction, exact-centroid displacement (or explicit unresolved sampling), full raw stress peaks separately from declared evaluated stress treatment, original coarse/fine response changes and original5percent requirement, support reaction force/moment, supplied0.5mm/120MPa limits and machining constraints. Preserve failures/unachieved targets; never infer correctness from successful solver or file presence. Explain equal-node load approximation and fixed-bearing simplification, retain unfiltered fields and distinguish sealed original solves from the explicit output-only native expansions. A raw singular maximum must not be declared a meaningful evaluated design stress. If stress-region sampling is unresolved, make that limitation explicit and do not mark the bracket engineering-qualified. Return a concrete analysis report with source/run/file identities and comparison tables.", filename="analysis-report.md", format="markdown")
    h.add_reference(sections, geometry, original["solve_and_compare"], "actual_cad_mass")
    h.add_reference(sections, observed, original["solve_and_compare"], "observed_cad_mass_and_measurements")
    h.add_reference(sections, solves, original["solve_and_compare"], "original_numerical_observations")
    for label, fields in field_results:
        h.add_reference(sections, fields, original["solve_and_compare"], label.replace("-", "_") + "_fields_and_reactions")
    chain = [original["define_load_case"], review, preflight, author, original["create_bracket"], observe, solve_step, *expansions, original["solve_and_compare"]]
    for before, after in zip(chain, chain[1:]):
        sections.append({"kind": "connection", "id": "sequence_" + after["id"], "fields": {"type": "order", "from": before["id"], "to": after["id"], "label": "full structural revision sequence", "when": None}})
    rendered = h.render(sections)
    validate_workspace_authoring_shape(rendered)
    plan = compile_prompt_workflow(rendered)
    allowed = []
    for server, names in {"agentcad": ["context", "docs", "run", "inspect", "measure"], "wright-workspace-files": ["write_text_document", "inspect_file"],
                          args.solver_server_id: ["calculix_mesh_preflight", "calculix_solve_static_recorded", "calculix_run_get"], args.field_server_id: ["export_recorded_fields_and_reactions"]}.items():
        for name in names:
            tool = next((t for t in tools if t["server_id"] == server and t["tool_name"] == name), None)
            if tool is None:
                raise ValueError("Missing required real tool: " + server + "/" + name)
            allowed.append(tool)
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(rendered, encoding="utf-8")
    report = {"schema_version": 1, "scenario_id": identity, "attempt_id": args.attempt, "template_id": manifest["template_id"],
        "status": "prepared_not_dispatched", "source": str(target), "source_sha256": h.digest(rendered.encode()),
        "template_source_sha256": h.digest(TEMPLATE.read_bytes()), "workspace_root": str(workspace), "output_root": output,
        "input_manifest": staged, "tool_allowlist": allowed, "expected_outputs": manifest["expected_outputs"],
        "expected_tool_created_files": [p for s in plan.steps for p in s.expected_files], "requires_template_instance_api": not bool(args.instance_source),
        "approval_policy_request": {"mode": "auto", "scope": "integration_test", "test_destinations": []},
        "native_initialization_requested": args.initialize_agentcad,
        "blockers": ["Full geometry/selection/solver/field/comparison graph has not executed"], "preserved_original_stages": [s["id"] for s in original.values()]}
    h.publish_input_binding_evidence(report, directory)
    (draft / "staging-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"scenario_id": identity, "draft": str(target), "stages": len(plan.steps), "staged_files": len(staged), "executed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solver-server-id", default="91ae7c8e-9b16-45fb-ae96-b08bee1e0d02")
    parser.add_argument("--field-server-id", default="ef468fc1-cf00-4551-8cc7-0425b8d7052d")
    parser.add_argument("--workspace-root", default=str(ROOT / ".local-run/feature-081-live/bracket-campaign-workspace"))
    parser.add_argument("--draft-root", default=str(ROOT / ".local-run/feature-081-live/bracket-campaign-drafts"))
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
    for directory in sorted((ROOT / "tests/datasets/engineering-workflows/scenarios/lightweight-equipment-bracket").iterdir()):
        if not args.scenario or json.loads((directory / "scenario.json").read_text(encoding="utf-8"))["scenario_id"] == args.scenario:
            rows.append(prepare(args, directory, tools))
    if not rows:
        raise ValueError("No matching bracket scenario")
    print(json.dumps({"prepared": rows, "executed": False}, indent=2))


if __name__ == "__main__":
    main()
