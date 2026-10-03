"""Prepare the original heat case for Wright; does not execute or grant reviews."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "process_example_definition", Path(__file__).resolve().parents[1] / "definition.py"
)
definition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(definition)
REPO = definition.REPO


def prepare(workspace, attempt, tools, bindings):
    """Providers/paths are explicit configuration, never discovered by guessing."""
    project = Path(bindings["cad_project"]).resolve(strict=True)
    workspace = Path(workspace).resolve(strict=True)
    if not project.is_relative_to(workspace):
        raise ValueError("The disposable CAD project must belong to this workspace")
    manifest_path = project / "build/agentcad.json"
    manifest = json.loads(manifest_path.read_bytes())
    if (
        manifest.get("runtime") != "build123d"
        or Path(manifest.get("project_root", "")).resolve() != project
        or manifest.get("versions") != []
    ):
        raise ValueError(
            "Initialize a fresh empty project/build for this exact root and selected runtime before preparation"
        )
    cad, files, solver = (
        bindings[key] for key in ("cad_server", "files_server", "solver_server")
    )
    mount = bindings["solver_workspace"].rstrip("/")
    if not mount.startswith("/") or ".." in mount.split("/"):
        raise ValueError("Use the existing solver's explicit absolute workspace mount")
    # Fail before staging if any required selected capability is missing.
    for server, names in [
        (cad, ("context", "docs", "run", "measure")),
        (files, ("write_text_document", "inspect_file")),
        (solver, ("run_simulation",)),
    ]:
        for name in names:
            if (
                len(
                    [
                        item
                        for item in tools
                        if item.get("server_id") == server
                        and item.get("tool_name") == name
                        and item.get("schema_digest")
                    ]
                )
                != 1
            ):
                raise ValueError(
                    "Required fresh configured capability is missing: "
                    + server
                    + "/"
                    + name
                )
    flow = definition.Definition(
        "heat-spreader-sizing", workspace, attempt, tools,
        run_path_template=bindings.get("run_path_template", ""),
    )
    for server, names in [
        (cad, ("context", "docs", "run", "measure")),
        (files, ("write_text_document", "inspect_file")),
        (solver, ("run_simulation",)),
    ]:
        for name in names:
            flow.select(server, name)
    frozen = json.loads(
        (REPO / "examples/process-interfaces/proof-bindings.json").read_bytes()
    )
    frozen = next(item for item in frozen["cases"] if item["template_id"] == flow.case)
    refs = {}
    for item in frozen["inputs"]:
        original = REPO / item["path"]
        data = original.read_bytes()
        if definition.sha(data) != item["sha256"]:
            raise ValueError("Original assignment changed: " + item["path"])
        kind = (
            "reference_images" if original.suffix == ".png" else "engineering_document"
        )
        refs[original.name] = flow.input_bytes(
            original.name, data, original=item["path"], kind=kind
        )
    profile_path = REPO / frozen["baseline_profile"]["path"]
    if (
        definition.sha(profile_path.read_bytes())
        != frozen["baseline_profile"]["sha256"]
    ):
        raise ValueError("Original validation profile changed")
    profile = json.loads(profile_path.read_bytes())
    requirements = "\n".join(
        item["id"] + ": " + item["text"] for item in profile["baseline"]["requirements"]
    )
    requirements_ref = flow.input_bytes("requirements.md", requirements.encode())
    basis = flow.original("define_thermal_case")
    basis_result = flow.ai(
        basis,
        "Record only the supplied case's exact basis and mandatory requirements. Preserve 100 mm length, 40/60 mm widths, 2 mm thickness, k=200 W/(m K), 4 W uniform full X=100 mm face, full X=0 face at 25 C, four insulated longitudinal faces, synthetic comparative density=2700 kg/m3, 45 C limit. Preserve <=2% analytical rise agreement/refinement and <=1% heat imbalance. No material certification, physical qualification or invented critic review. Numerical results have not been computed yet.",
        "thermal-basis.md",
        format="markdown",
    )
    for name, source in refs.items():
        flow.reference(
            source,
            basis,
            name.replace(".", "_"),
            "reference_images" if name.endswith(".png") else "engineering_document",
        )
    flow.reference(requirements_ref, basis, "mandatory_requirements")
    coverage = json.loads((profile_path.parent / "coverage.json").read_bytes())
    selected = next(
        item["full_profile"]
        for item in coverage["scenarios"]
        if item["scenario_id"] == "heat-spreader-sizing-01"
    )
    basis_review = flow.stage(
        "review_basis", "Review the thermal model and original limits"
    )
    flow.review(
        basis_review,
        "Review these exact basis bytes and original engineering assumptions. No physical acceptance follows.",
        profile={
            "profile_ref": selected["profile_ref"],
            "requirement_ids": sorted(
                item["id"]
                for item in profile["baseline"]["requirements"]
                if item["review_required"]
            ),
        },
    )
    flow.reference(basis_result, basis_review, "basis")
    preflight = flow.stage(
        "cad_documentation", "Read the selected CAD project and authoring instructions"
    )
    docs = flow.ai(
        preflight,
        f"Call context(cwd={str(project)!r},build_dir='build'), docs(section='quickstart',cwd={str(project)!r},build_dir='build') and docs(section='helpers',cwd={str(project)!r},build_dir='build'). Return actual project identity and exact source authoring instructions. Empty geometry is expected before the next stage. Report missing configuration; do not execute geometry here.",
        "cad-documentation.json",
        server=cad,
        calls=3,
    )
    flow.reference(basis_result, preflight, "reviewed_basis")
    author = flow.stage("author_cad", "Author the exact plate candidates")
    absolute_output = workspace / flow.output
    source_path = absolute_output / "plate-source.py"
    source_guidance = (REPO / "scripts/agentcad_source_contract.py").read_bytes()
    guidance_ref = flow.input_bytes(
        "selected-cad-source-contract.txt",
        source_guidance,
        original="scripts/agentcad_source_contract.py",
    )
    flow.ai(
        author,
        f"Inspect {flow.output}/plate-source.py first. If absent, use write_text_document once to create it, text/plain, real build123d source. If present on a later run, read all bytes and compare against the exact connected basis and source contract before explicitly reporting reuse; never overwrite or pretend to create it. A mismatch blocks this stage and requires an explicitly revised source path before a new run. Follow the supplied selected-runtime source contract and actual CAD docs. Write source that, when executed by the next declared CAD stage, constructs both baseline_40=100x40x2 and revision_60=100x60x2 unperforated rectangles in mm with minimum corner (0,0,0). The source must export each actual STEP to {absolute_output}/<case_id>.step, reopen each STEP with the native kernel, measure bounding-box x/y/z, and write {absolute_output}/geometry-measurements.json with cases indexed by those exact IDs containing dimensions_mm as x/y/z and step_sha256 of actual exported bytes. Call injected show_object on actual shapes. Invoke main unconditionally if used; __file__ is not the input pathname. Use explicit supplied paths. This authoring stage is complete once its source is created and checked. Do not execute CAD here or mark this stage blocked because STEP/measurement exports do not yet exist: the next declared native CAD operation produces them. No solver or acceptance results here.",
        "cad-authoring.json",
        server=files,
        expected=("plate-source.py",),
        calls=4,
    )
    flow.reference(docs, author, "cad_docs")
    flow.reference(basis_result, author, "basis")
    flow.reference(guidance_ref, author, "source_contract")
    flow.file_outputs(author, {"cad_source": flow.output + "/plate-source.py"})
    geometry = flow.original("create_plate_geometry")
    arguments = dict(
        script=str(source_path),
        output="plates" + ("_" + definition.RUN_PATH_TOKEN if flow.run_path_template else ""),
        cwd=str(project),
        build_dir="build",
        preview=False,
        view=False,
        diff=False,
    )
    cad_call = flow.input_bytes(
        "cad-call.json", (json.dumps(arguments, indent=2) + "\n").encode(),
        run_paths=bool(flow.run_path_template),
    )
    argument_port = flow.reference(cad_call, geometry, "exact_arguments")
    flow.exact_mcp(
        geometry,
        flow.select(cad, "run"),
        argument_port,
        ("baseline_40.step", "revision_60.step", "geometry-measurements.json"),
        "cad-execution.json",
    )
    source_port = flow.reference(
        author["id"] + ".cad_source", geometry, "authored_source", "workspace_file"
    )
    geometry["fields"]["settings"]["mcp_file_dependencies"] = {
        source_port: flow.output + "/plate-source.py"
    }
    geometry_roles = flow.file_outputs(
        geometry,
        {
            name + "_geometry": flow.output + "/" + name + ".step"
            for name in ("baseline_40", "revision_60")
        },
    )
    flow.file_outputs(
        geometry, {"geometry_measurements": flow.output + "/geometry-measurements.json"}
    )
    observed = flow.stage(
        "measure_candidates", "Reopen and measure the exported candidates"
    )
    observed_result = flow.ai(
        observed,
        f"Call measure(file={str(absolute_output / 'baseline_40.step')!r},cwd={str(project)!r},build_dir='build') and measure(file={str(absolute_output / 'revision_60.step')!r},cwd={str(project)!r},build_dir='build'). Retain each actual result and dimensions. Preserve any upstream creation error separately from measured native geometry; do not rerun creation or claim a successful creation receipt. Fail if a measured candidate is invalid, missing or mismatched. This read-back is not physical qualification.",
        "cad-readback.json",
        server=cad,
        calls=2,
    )
    flow.reference(
        geometry["id"] + "." + geometry["id"] + "_result", observed, "creation_response"
    )
    numerical = (REPO / "scripts/engineering/heat_conduction_skfem.py").read_bytes()
    numerical_ref = flow.input_bytes(
        "heat_conduction_skfem.py",
        numerical,
        original="scripts/engineering/heat_conduction_skfem.py",
    )
    config = dict(
        output_root=mount + "/" + flow.output,
        alternatives_csv=mount + "/" + flow.input_root + "/alternatives.csv",
        geometry_root=mount + "/" + flow.output,
        geometry_measurements=mount + "/" + flow.output + "/geometry-measurements.json",
    )
    solver_arguments = dict(
        solver="skfem",
        input_content="HEAT_CONFIG = "
        + repr(config)
        + "\nexec(compile("
        + repr(numerical.decode())
        + ", 'heat_conduction_skfem.py', 'exec'))\n",
        job_name=config["output_root"],
        critic_approved=False,
    )
    solver_call = flow.input_bytes(
        "solver-call.json", (json.dumps(solver_arguments, indent=2) + "\n").encode(),
        run_paths=bool(flow.run_path_template),
    )
    solve = flow.stage(
        "compute_fields", "Compute coarse and refined temperature fields"
    )
    solver_port = flow.reference(solver_call, solve, "exact_arguments")
    expected = tuple(
        name + "-" + level + "-temperature." + extension
        for name in ("baseline_40", "revision_60")
        for level in ("coarse", "fine")
        for extension in ("csv", "vtu")
    ) + (
        "heat-balance.json",
        "mesh-comparison.json",
        "sizing-decision.json",
        "geometry-analysis-correspondence.json",
    )
    flow.exact_mcp(
        solve,
        flow.select(solver, "run_simulation"),
        solver_port,
        expected,
        "solver-execution.json",
    )
    dependency_ports = {}
    for role, path in geometry["fields"]["settings"]["expected_file_ports"].items():
        key = flow.reference(geometry["id"] + "." + role, solve, role, "workspace_file")
        dependency_ports[key] = path
    solve["fields"]["settings"]["mcp_file_dependencies"] = dependency_ports
    solver_roles = flow.file_outputs(
        solve,
        {
            **{
                name + "_" + level: flow.output
                + "/"
                + name
                + "-"
                + level
                + "-temperature.csv"
                for name in ("baseline_40", "revision_60")
                for level in ("coarse", "fine")
            },
            "decision": flow.output + "/sizing-decision.json",
            "correspondence": flow.output + "/geometry-analysis-correspondence.json",
        },
    )
    verify = flow.original("solve_and_verify")
    verified = flow.ai(
        verify,
        "Inspect the actual heat-balance.json, mesh-comparison.json, sizing-decision.json and geometry-analysis-correspondence.json in the supplied exact output root. Follow paginated inspect_file text until all JSON is read. Compare the actual two candidate temperatures, mass, original limit, analytical agreement, refinement, heat balance and exact STEP hashes. Keep critic_approved=false and pending independent critic explicit. Preserve failures and unsupported evidence; never invent a pass or execute another solver. Native comparisons are not physical qualification.",
        "thermal-verification.json",
        server=files,
        calls=16,
    )
    flow.reference(
        solve["id"] + "." + solve["id"] + "_result", verify, "computed_result"
    )
    flow.reference(basis_result, verify, "basis")
    flow.reference(observed_result, verify, "cad_readback")
    flow.reference(numerical_ref, verify, "reviewable_solver_source")
    validation = flow.validator(
        "heat-spreader-sizing-01-full",
        {
            "basis": (basis, basis["id"] + "_result", "engineering_document"),
            **geometry_roles,
            **solver_roles,
        },
    )
    final = flow.stage(
        "analysis_review", "Review the sizing decision and current findings"
    )
    flow.review(
        final,
        "Review exact candidate fields, CAD correspondence, independent checks and 082 findings. Preserve any measured mandatory failures and pending critic. Execution does not establish engineering acceptance.",
    )
    flow.reference(verified, final, "comparison")
    flow.reference(validation["id"] + ".assessment", final, "assessment")
    return flow.save(
        [
            basis,
            basis_review,
            preflight,
            author,
            geometry,
            observed,
            solve,
            verify,
            validation,
            final,
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--attempt", required=True)
    parser.add_argument(
        "--tools",
        required=True,
        type=Path,
        help="Fresh Wright workflow-source tools export",
    )
    parser.add_argument("--bindings", required=True, type=Path)
    args = parser.parse_args()
    tools = json.loads(args.tools.read_bytes())
    result = prepare(
        args.workspace,
        args.attempt,
        tools["tools"] if isinstance(tools, dict) else tools,
        json.loads(args.bindings.read_bytes()),
    )
    print(
        json.dumps(
            {
                key: result[key]
                for key in ("status", "source_path", "step_count", "physical_dispatch")
            },
            indent=2,
        )
    )
