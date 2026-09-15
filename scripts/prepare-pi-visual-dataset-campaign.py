"""Prepare the reviewed fixed Pi/AgentCAD/OpenFOAM path; no CAD or solver dispatch."""

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import urllib.parse
import urllib.request

from workspace_service.workflow_source_execution import (
    _parse,
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
)
from workspace_service.workflow_integration_policy import (
    LOCAL_REVIEW_BINDING,
    LOCAL_REVIEW_DESTINATION,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (
    ROOT
    / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/raspberry-pi-enclosure.workflow.wflow"
)
BINDING = (
    ROOT
    / "tests/datasets/engineering-workflows/bindings/raspberry-pi-enclosure-visual.json"
)
PI_AGENTCAD_GUIDANCE = (
    "AgentCAD 0.6.0 runs source with __name__='__agentcad_script__': invoke main() "
    "unconditionally after defining it. Call the injected show_object(actual_shape) "
    "directly; never redefine or alias it. Store the exact staged script in a literal "
    "SOURCE_PATH and hash those bytes; never derive paths from __file__='<script>'. Use "
    "the supplied absolute input/output paths. For build123d 0.10.0 use Shape.rotate("
    "Axis, angle_degrees), Align enum members, RectangleRounded, and the boolean "
    "shape.is_valid property. Normalize every ShapeList result with positional "
    "Compound(shape_list), and combine disconnected results by flattening their solids "
    "into positional Compound([...]); never use Compound(children=[...]). Enumerate "
    "solids directly with list(shape.solids()) for both combination and one-at-a-time "
    "cutting. Never wrap shape.solids() in a temporary Compound and then read "
    "Compound.children: children is not the solid enumeration and can be empty."
)
spec = importlib.util.spec_from_file_location(
    "pi_fixed_draft_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py"
)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def add_scoped_file_inspection(
    sections, suffix, output, server_id="wright-workspace-files", *, inputs
):
    """Read actual CAD metadata/contracts through the enrolled workspace seam."""
    author = next(
        s
        for s in sections
        if s["kind"] == "task" and s["id"].startswith("author_cad_source_")
    )
    cad = next(
        s
        for s in sections
        if s["kind"] == "task" and s["id"].startswith("agentcad_enclosure_")
    )
    preparation = next(
        s
        for s in sections
        if s["kind"] == "task" and s["id"].startswith("prepare_cfd_case_")
    )
    identity = "inspect_cad_exports_" + suffix
    if any(s["id"] == identity for s in sections):
        return
    author["fields"]["prompt"] = (
        "Read the accepted design basis and fixed CFD contract from their durable workspace files before authoring; they are deliberately omitted from connected reference text to keep the model request bounded. "
        f"Use inspect_file(relativePath={output + '/design-basis.md'!r},includeText=true,maxTextBytes=4096) for the generated design basis, "
        f"and inspect_file(relativePath={inputs + '/fixed-cfd-contract.md'!r},includeText=true,maxTextBytes=4096) for the uploaded fixed CFD contract. "
        "Follow nextOffsetBytes until both complete documents have been read and retain every page plus the actual file hash; never truncate or replace either file with a summary. "
        + author["fields"]["prompt"]
    )
    files = cad["fields"]["settings"]["expected_files"].splitlines()
    inspection = {
        "kind": "task",
        "id": identity,
        "fields": {
            "name": "Inspect actual CAD exports and thermal contracts",
            "purpose": "Record actual same-run file metadata and explicit CAD-to-CFD contract identities before meshing",
            "step_type": "work",
            "performed_by": "ai_assisted",
            "group": None,
            "inputs": [],
            "outputs": [helpers.port(identity + "_result")],
            "tool": None,
            "reusable_step": None,
            "prompt": f"Use inspect_file on each actual expected CAD output {files!r}, relativePath exactly as listed, with includeText=false for every file including the two cfd-contract JSONs. Retain each actual sha256 and byte count in a compact lineage report; the complete durable files remain on disk for the fixed compiler and must not be copied into the model response. Check declared STEP/contract path identities against these actual file observations; report mismatches without modifying files. Do not read arbitrary host files or invent hash values. This is file/contract lineage inspection, not engineering-content validation.",
            "settings": {
                "authoring_template": "mcp-task",
                "mcp_server": server_id,
                "max_tool_calls": 18,
                "timeout_seconds": 600,
                "save_output": True,
                "output_filename": output + "/cad-export-inspection.json",
                "output_format": "json",
                "file_policy": "overwrite",
                "task_guidance": "Use only the scoped read-only inspect_file tool. Set includeText=false on every call, preserve actual file identities and report unresolved mismatches; never recreate CAD to get metadata. Inspect each expected file once, then return the compact lineage report immediately; do not retry a successful read or perform unrelated observations.",
            },
        },
    }
    sections.append(inspection)
    helpers.add_reference(
        sections,
        cad["id"] + "." + cad["id"] + "_result",
        inspection,
        "actual_cad_result",
    )
    helpers.add_reference(
        sections,
        identity + "." + identity + "_result",
        preparation,
        "actual_export_inspection",
    )
    for left, right in ((cad, inspection), (inspection, preparation)):
        sections.append(
            {
                "kind": "connection",
                "id": "inspection_sequence_" + right["id"],
                "fields": {
                    "type": "order",
                    "from": left["id"],
                    "to": right["id"],
                    "label": "inspect actual CAD file lineage before meshing",
                    "when": None,
                },
            }
        )


def prepare(args, directory, available):
    config = json.loads(BINDING.read_text(encoding="utf-8"))
    mapping = getattr(args, "server_map", {}) or {}
    if isinstance(mapping, str):
        mapping = json.loads(Path(mapping).read_text())["server_map"]

    def server(name):
        return mapping.get(name, name)

    scenario = json.loads((directory / "scenario.json").read_text())
    identity = scenario["scenario_id"]
    workspace = Path(args.workspace_root).resolve()
    draft = Path(args.draft_root).resolve() / identity / args.attempt
    if draft.exists():
        raise ValueError("Preserve existing prepared attempt")
    suffix = identity.replace("-", "_") + "_" + args.attempt.replace("-", "_")
    inputs = f"campaign/{identity}/{args.attempt}/inputs"
    output = f"campaign/{identity}/{args.attempt}/artifacts"
    source = (
        Path(args.instance_source).read_text(encoding="utf-8")
        if args.instance_source
        else TEMPLATE.read_text(encoding="utf-8").replace("__instance__", suffix)
    )
    sections = _parse(source)
    original = [s["id"] for s in sections if s["kind"] == "task"]
    edges = [s.copy() for s in sections if s["kind"] == "connection"]
    stages = {
        prefix: next(
            s
            for s in sections
            if s["kind"] == "task" and s["id"].startswith(prefix + "_")
        )
        for prefix in (
            "source_dimensions",
            "design_basis",
            "agentcad_enclosure",
            "cfd_compare",
        )
    }
    staged = []

    def stage(name, data, provenance):
        relative = inputs + "/" + name
        helpers.write_once(helpers.confined(workspace, relative), data)
        staged.append(
            {
                "path": relative,
                "sha256": helpers.digest(data),
                "size_bytes": len(data),
                **provenance,
            }
        )

    for path in sorted(directory.iterdir()):
        if path.is_file():
            stage(
                path.name,
                path.read_bytes(),
                {"original": path.relative_to(ROOT).as_posix()},
            )
    sources = [
        ROOT / "scripts" / name
        for name in (
            "pi_reference_mcp.py",
            "pi_reference_visual_mcp.py",
            "pi_cfd_operations.py",
            "pi_cfd_mcp.py",
        )
    ] + [ROOT / "scripts/pi_foam_boundary/wrightPrghFanPressure.C"]
    for path in sources:
        stage(
            path.name,
            path.read_bytes(),
            {"authored_source": path.relative_to(ROOT).as_posix()},
        )
    document = ROOT / "scripts/pi_cfd_contract.md"
    stage(
        "fixed-cfd-contract.md",
        document.read_bytes(),
        {"authored_contract": document.relative_to(ROOT).as_posix()},
    )
    context_names = list(
        dict.fromkeys(
            [
                scenario["files"]["user_profile"],
                scenario["files"]["prompt"],
                *scenario["files"]["context"],
                *[
                    p.name
                    for p in sorted(directory.iterdir())
                    if p.suffix.lower() in {".csv", ".tsv", ".txt", ".md"}
                ],
            ]
        )
    )
    human = "\n\n".join(
        "## Uploaded file: "
        + name
        + "\n\n"
        + (directory / name).read_text(encoding="utf-8")
        for name in context_names
    )
    authority = ROOT / "scripts/pi_prototype_design_authority.md"
    stage(
        "prototype-design-authority.md",
        authority.read_bytes(),
        {"authored_source": authority.relative_to(ROOT).as_posix()},
    )
    human += (
        "\n\n## Workflow prototype design authority (authored guidance, not customer/manufacturer data)\n\n"
        + authority.read_text(encoding="utf-8")
    )
    stage(
        "assembled-context.md",
        human.encode(),
        {
            "derived_from": context_names,
            "authored_guidance": authority.relative_to(ROOT).as_posix(),
        },
    )
    project = workspace / output / "agentcad-project"
    initialization = {
        "status": "requires_native_initialization",
        "project": str(project),
    }
    if args.initialize_agentcad:
        if project.exists():
            raise ValueError(
                "Native initialization requires a fresh disposable project"
            )
        project.mkdir(parents=True)
        command = [
            "uv",
            "run",
            "--isolated",
            "--python",
            "3.12",
            "--with",
            "agentcad[mcp]==0.6.0",
            "agentcad",
            "init",
            "--name",
            "pi-enclosure",
            "--build-dir",
            "build",
        ]
        result = subprocess.run(
            command, cwd=project, capture_output=True, text=True, timeout=300
        )
        initialization.update(
            status="native_initialized" if result.returncode == 0 else "failed",
            command=command,
            returncode=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        stage(
            "native-initialization.json",
            (json.dumps(initialization, indent=2) + "\n").encode(),
            {"native_prerequisite": True},
        )
        if result.returncode:
            raise ValueError(
                "Native AgentCAD initialization failed; retain recorded evidence"
            )
    else:
        stage(
            "native-initialization.json",
            json.dumps(initialization).encode(),
            {"native_prerequisite": False},
        )
    references = {
        key: helpers.add_file_input(sections, suffix, key, inputs + "/" + filename)
        for key, filename in (
            ("human_context", "assembled-context.md"),
            ("fixed_contract", "fixed-cfd-contract.md"),
            ("compiler_source", "pi_cfd_operations.py"),
            ("reference_source", "pi_reference_visual_mcp.py"),
            ("native_setup", "native-initialization.json"),
            ("styling_image", "concept.png"),
        )
    }
    next(s for s in sections if s["id"] == references["styling_image"].split(".")[0])[
        "fields"
    ]["outputs"][0]["kind"] = "reference_images"

    def new(prefix, title):
        task = {
            "kind": "task",
            "id": prefix + "_" + suffix,
            "fields": {
                "name": title,
                "purpose": title,
                "step_type": "work",
                "performed_by": "ai_assisted",
                "group": None,
                "inputs": [],
                "outputs": [],
                "settings": {},
                "tool": None,
                "reusable_step": None,
            },
        }
        sections.append(task)
        return task

    def bind(
        task,
        prompt,
        filename,
        tool_server=None,
        expected=(),
        include_human_context=True,
    ):
        task["fields"].update(
            step_type="work",
            performed_by="ai_assisted",
            prompt=prompt,
            inputs=[],
            outputs=[helpers.port(task["id"] + "_result")],
        )
        settings = {
            "save_output": True,
            "output_filename": output + "/" + filename,
            "output_format": "markdown" if filename.endswith(".md") else "json",
            "file_policy": "overwrite",
            "timeout_seconds": 600,
        }
        if tool_server:
            settings.update(
                authoring_template="mcp-task",
                mcp_server=server(tool_server),
                max_tool_calls=18,
                reference_inline_max_bytes=12000,
                expected_files="\n".join(output + "/" + path for path in expected),
                task_guidance="Exact selected tools only. No Blender/socket/bridge. Preserve actual same-run geometry/field lineage, disclosed modeling limits and failed results. Tool output summaries must stay below 12000 characters; retain full data on disk.",
            )
        task["fields"]["settings"] = settings
        if include_human_context:
            helpers.add_reference(
                sections, references["human_context"], task, "human_context"
            )
        return task["id"] + "." + task["id"] + "_result"

    if identity == "raspberry-pi-enclosure-03":
        fan_guidance = (
            "This case includes the exact uploaded synthetic fan curve; use those points only, retain pressure-boundary assumptions, "
            "never substitute a manufacturer curve or constant velocity. The fixed CFD contract requires a real, unique fan aperture "
            "on the Y=12.5 mm plane: create exactly one exposed CAD face for fan_inlet_a and fan_inlet_b, each 30 x 30 mm with "
            "X bounds 62.0..92.0 mm and Z bounds 9.0..39.0 mm. Do not expose the entire exterior Y=12.5 plane and do not "
            "satisfy this requirement by changing only the JSON selector. Model the surrounding front wall/baffle and subtract or "
            "cut the aperture so the final fluid region has one and only one face at that plane with those measured bounds. Before "
            "writing each cfd-contract JSON, inspect the final fluid shape's actual faces (including face bounding boxes and areas), "
            "assert that the selected fan face is unique and 900 mm^2, and record the observed face bounds in the contract evidence. "
            "Keep all other exterior boundaries consistent with the fixed contract and preserve the two requested styled variants."
        )
    else:
        fan_guidance = (
            "This case includes the exact uploaded synthetic fan curve; use those points only, retain pressure-boundary assumptions, never substitute a manufacturer curve or constant velocity."
            if config["scenarios"][identity]["fan"]
            else "This is a passive comparison with NO fan; omit fan_curve and fan boundary roles, do not require a fan selection or fan data."
        )
    research = bind(
        stages["source_dimensions"],
        f"Call retrieve_pi_primary_references once with operation_source_document={inputs + '/pi_reference_visual_mcp.py'!r}, output_directory={output + '/research'!r}. Then observe_pi_primary_page on manufacturer-drawing.pdf page1 full view. Inspect actual pixels, dimension leaders and drawing notes; use at most3fixed quadrant views if necessary. Observe insert-dimensions.jpg and insert-installation.jpg page1 full views for candidate ruthex RX-M2.5x5.7. Use read_pi_primary_text for manufacturer-product-brief.pdf page3 and insert-product.html (bounded4000characters, follow offsets when needed). Use at most8image observations total. Record exact source URL/PDF-or-image SHA/page/view and feature-to-dimension associations in an explicit table; separate manufacturer reference-only dimensions, absent measurements, customer goals and designer-selected prototype clearances. Do not claim pixels were viewed if native image observations are unavailable. Select supplier insert geometry from actual observed table and disclose omitted installation/rating tests. Preserve manufacturer reference-only warning; this is a concept prototype and CFD comparison, not production release. Missing production certification or physical fit validation does not by itself prevent documented prototype design. {fan_guidance}",
        "manufacturer-research.md",
        "wright-campaign-pi-visual-references",
        (
            "research/manufacturer-drawing.pdf",
            "research/manufacturer-product-brief.pdf",
            "research/manufacturer-cooler-drawing.pdf",
            "research/manufacturer-evidence.json",
            "research/supplier-evidence.json",
            "research/insert-product.html",
            "research/insert-dimensions.jpg",
            "research/insert-installation.jpg",
            "research/observations/manufacturer-drawing.pdf.page-1.full.png",
            "research/observations/insert-dimensions.jpg.page-1.full.png",
            "research/observations/insert-installation.jpg.page-1.full.png",
        ),
    )
    helpers.add_reference(
        sections,
        references["reference_source"],
        stages["source_dimensions"],
        "fixed_retrieval_source",
    )
    basis = bind(
        stages["design_basis"],
        "Write the complete engineering design basis from actual manufacturer evidence, original prompt/context/image and fixed CFD contract. Preserve both actual requested styled variants, heat locations/loads, shell conduction, dimensions, mounts/service features where actually requested. Explicitly map board-local load coordinates to CAD coordinates. Name actual fluid/shell/board/source regions and exterior boundary planes before CAD. Use laminar ideal-gas buoyant air and disclosed material assumptions. Explain whether an exterior air region resolves shell convection or exterior solid faces are prescribed ambient; never silently equate them. For a steady heating brief, propose the version2 steady iteration/write profile and CAD-surface mesh grading in the fixed contract, preserving actual loads, regions, materials and domain. State iterations as iterations, never seconds; retain unvalidated convergence and targets. Use a legacy transient only when the brief explicitly needs time behavior, with a separately justified measured execution budget. Distinguish manufacturer facts from your own prototype design choices: select seam height, fillets, feet, light opening, clearances, screw lengths and boss layout as documented design assumptions within the customer constraints; use sourced board/insert geometry. Do not demand production qualification to generate the requested prototype. Preserve unresolved fit/rating checks in the document without claiming validation. Keep the complete document at or below 12000 characters by using compact tables and avoiding repeated rationale. "
        + fan_guidance,
        "design-basis.md",
    )
    helpers.add_reference(
        sections, research, stages["design_basis"], "retrieved_primary_evidence"
    )
    helpers.add_reference(
        sections,
        references["styling_image"],
        stages["design_basis"],
        "human_styling_image",
        "reference_images",
    )
    helpers.add_reference(
        sections,
        references["fixed_contract"],
        stages["design_basis"],
        "supported_physics",
    )
    review = new(
        "review_design",
        "Review sourced enclosure design and explicit thermal assumptions",
    )
    review["fields"].update(
        step_type="review",
        performed_by="engineer",
        instructions="Review the actual sourced two-variant design basis and explicit material/domain/fan/convergence assumptions before CAD. Integration auto review authorizes local generation only.",
        settings={
            "authoring_template": "external-action-approval",
            "action_kind": "local_review",
            "approval_binding": LOCAL_REVIEW_BINDING,
            "approval_destination": LOCAL_REVIEW_DESTINATION,
            "approval_settings": {"review_task_id": review["id"]},
            "approval_action": {"kind": "local_review", "mode": "review_only"},
        },
    )
    helpers.add_reference(sections, basis, review, "design_to_review")
    author = new(
        "author_cad_source", "Author actual AgentCAD enclosure and CFD region exports"
    )
    heats = config["scenarios"][identity]["heat_regions"]
    extra = [
        f"{region}-{variant}.step"
        for region in ["board", *heats]
        for variant in ("a", "b")
    ] + ["cfd-contract-a.json", "cfd-contract-b.json"]
    required = [
        name for name in config["expected_geometry"] if name != "geometry-lineage.json"
    ] + extra
    bind(
        author,
        f"Use write_text_document to create {output}/enclosure-source.py as executable build123d CAD source. Read the accepted design basis and fixed CFD contract. Native project: {project}; its setup receipt is attached. Build both requested styled, vented enclosure alternatives with their openings, mounts, service clearances and actual heat loads. Export {config['expected_geometry']!r} plus the closed region files {extra!r}. Treat every listed basename as an exact API contract: preserve every underscore and hyphen exactly in export paths, geometry-lineage.json and cfd-contract-a/b.json. In particular, a safe lowercase region name such as power_interface must export power_interface-a.step and power_interface-b.step; never substitute power-interface-a.step or another punctuation alias. Before finishing, inspect the authored source and verify that every export/contract filename pattern exactly matches this list. enclosure-a/b STEP and matching STL contain only PETG shell, lid and panel material, with at most 64 closed solids; they contain no board, inserts, heat sources or display assembly. Construct mutually exclusive final regions: subtract the complete board, brass inserts and heat sources from PETG; subtract complete brass-insert outer solids and embedded heat sources from the board; subtract every final material solid from the fluid domain. Subtract fluid cutters one solid at a time, never as a multi-solid Compound. Perform every material-region Boolean per target solid and per cutter solid. Never subtract a cutter from a multi-solid target Compound. Define a helper that starts with each item from list(shape.solids()), subtracts each item from list(cutter.solids()) from each surviving target fragment, flattens list(boolean_result.solids()) after every cut, and returns Compound(all_surviving_fragments). Use that helper for PETG, board and fluid material construction. Keep the individual brass-insert cylinders as a list for Boolean operations and create their exported Compound only after all material subtractions. This is required because OpenCascade can retain overlapping fragments when either side of a subtraction is a multi-solid Compound. Export and reference these same final shapes. petg_shell points to the matching PETG-only STEP; board, brass_inserts and each heat source point to their exact STEP. Never export overlapping regions. Do not add pairwise pre-export Compound intersection checks: a valid empty result can raise Null TopoDS_Shape and the fixed compiler performs the authoritative overlap check. Fluid STEP is the actual air domain after subtraction, including exterior air when selected. When constructing an exterior air Box from a specified minimum corner, use align=(Align.MIN, Align.MIN, Align.MIN) before positioning it; a default-centered Box makes that position its center. Treat these measured coordinates as non-negotiable geometry invariants: the PETG floor must occupy Z=0.0..2.5 mm, the interior fluid target must start at Z=2.5 mm, and the final fluid bounding_box() must retain zmin=2.5, zmax=45.5, xmin=2.5, xmax=142.5, ymin=12.5 and ymax=107.5 after every material subtraction. Do not place the floor at Z=2.0 or otherwise allow any floor/solid to raise the final fluid zmin above 2.5. Before export, read the final fluid shape bounding_box() and require its six outer plane coordinates to equal the intended domain bounds. Write those observed plane coordinates, not constructor inputs, as the contract boundary selectors. The contract evidence must use this exact bounded object shape: fluid_step_sha256 as a 64-character lowercase hex string; fluid_domain_observed_bounds_mm as an object with exactly x_min, x_max, y_min, y_max, z_min and z_max numeric keys; fan_inlet_face and outlet_face as objects with exactly inspection_method, matching_face_count, selected_face_index, observed_bounds_mm and observed_area_mm2 keys, where observed_bounds_mm uses the same six named keys. Never encode domain or face bounds as a six-item list, and never use area_mm2, matching_count or selected_face aliases. Preserve heat coordinates and loads. Contracts a/b use supported keys, exact workspace-relative paths and hashes, materials, heat_w, unambiguous CAD plane selectors, mm units, gravity and the accepted numerical/mesh profile. {fan_guidance} Use safe lowercase region names. Write geometry-lineage.json with actual hashes and transforms. {PI_AGENTCAD_GUIDANCE} This step writes source only; never execute it here.",
        "cad-authoring.json",
        "wright-workspace-files",
        ("enclosure-source.py",),
        include_human_context=False,
    )
    helpers.add_reference(sections, references["native_setup"], author, "native_setup")
    run_matches = [
        tool
        for tool in available
        if tool["server_id"] == server("agentcad") and tool["tool_name"] == "run"
    ]
    if len(run_matches) != 1:
        raise ValueError("Required selected tool unavailable: agentcad/run")
    run_binding = run_matches[0]
    cad_task = stages["agentcad_enclosure"]
    cad_task["fields"].update(
        step_type="work",
        performed_by="configured_tool",
        inputs=[],
        outputs=[helpers.port(cad_task["id"] + "_result")],
        prompt="",
        instructions=(
            "Execute the already-authored, same-run AgentCAD source exactly once. "
            "The separate following inspection stage verifies the exported files."
        ),
        tool=None,
        reusable_step=None,
    )
    cad_task["fields"]["settings"] = {
        "authoring_template": "mcp-tool",
        "mcp_server": server("agentcad"),
        "mcp_tool": run_binding["name"],
        "mcp_schema_digest": run_binding["schema_digest"],
        "mcp_arguments": json.dumps(
            {
                "script": str(workspace / output / "enclosure-source.py"),
                "output": "pi-comparison",
                "cwd": str(project),
                "build_dir": "build",
                "preview": False,
                "view": False,
                "diff": False,
            },
            separators=(",", ":"),
        ),
        "output_format": "json",
        "save_output": True,
        "output_filename": output + "/cad-execution.json",
        "file_policy": "overwrite",
        "expected_files": "\n".join(output + "/" + path for path in required),
        "timeout_seconds": 600,
        "mcp_source_contract": "agentcad-build123d-0.10",
    }
    cad = cad_task["id"] + "." + cad_task["id"] + "_result"
    # The author-to-CAD dependency is carried by the ordered process chain. The
    # direct tool receives the exact durable workspace path above, so attaching
    # the author's narrative response as an unused argument would be invalid.
    foam_run_matches = [
        tool
        for tool in available
        if tool["server_id"] == server("foam-agent-csml-rpi")
        and tool["tool_name"] == "run"
    ]
    if len(foam_run_matches) != 1:
        raise ValueError("Required selected tool unavailable: foam-agent-csml-rpi/run")
    foam_run_binding = foam_run_matches[0]

    def configure_foam_run(task, case_dir, filename):
        """Run the fixed case directly; field qualification happens afterward."""
        task["fields"].update(
            step_type="work",
            performed_by="configured_tool",
            inputs=[],
            outputs=[helpers.port(task["id"] + "_result")],
            prompt="",
            instructions=(
                "Execute the already-compiled same-run OpenFOAM case exactly once. "
                "The final fixed collection step verifies solver records and fields."
            ),
            tool=None,
            reusable_step=None,
        )
        task["fields"]["settings"] = {
            "authoring_template": "mcp-tool",
            "mcp_server": server("foam-agent-csml-rpi"),
            "mcp_tool": foam_run_binding["name"],
            "mcp_schema_digest": foam_run_binding["schema_digest"],
            "mcp_arguments": json.dumps(
                {"request": {"case_dir": case_dir, "timeout": 540}},
                separators=(",", ":"),
            ),
            "output_format": "json",
            "save_output": True,
            "output_filename": output + "/" + filename,
            "file_policy": "overwrite",
            "timeout_seconds": 600,
        }
        return task["id"] + "." + task["id"] + "_result"

    preparation_a = new(
        "prepare_cfd_case",
        "Compile alternative A CAD regions into a conjugate heat-transfer mesh",
    )
    bind(
        preparation_a,
        f"Call prepare_pi_cfd_variant exactly once with operation_source_document={inputs + '/pi_cfd_operations.py'!r}, output_directory={output!r}, contract_document={output + '/cfd-contract-a.json'!r}, variant='a'. This fixed compiler imports the actual same-run AgentCAD STEP regions, rejects overlaps/missing boundaries, performs real conformal meshing and checkMesh, and writes a one-variant fixed Allrun. Read its receipt and foam_case_dir. Do not replace CAD or alter the accepted thermal model. Save a compact report; full mesh/source/geometry evidence remains in files.",
        "cfd-preparation-a-report.json",
        "wright-campaign-pi-cfd",
        ("cfd-preparation-a.json",),
    )
    helpers.add_reference(sections, cad, preparation_a, "actual_cad_contract_a")
    helpers.add_reference(
        sections, references["compiler_source"], preparation_a, "fixed_compiler_source"
    )
    foam_case_a = (
        "/workspace/campaign/" + identity + "/" + args.attempt + "/pi-cfd/variant-a"
    )
    solve_a = new(
        "solve_cfd_variant_a", "Run actual OpenFOAM CHT for enclosure alternative A"
    )
    solved_a = configure_foam_run(solve_a, foam_case_a, "cfd-run-a-report.json")
    # The direct solver call uses the exact case path above. Its ordered edge
    # ensures preparation completes first without creating an unused argument.
    preparation_b = new(
        "prepare_cfd_variant_b",
        "Compile alternative B CAD regions into a conjugate heat-transfer mesh",
    )
    bind(
        preparation_b,
        f"Call prepare_pi_cfd_variant exactly once with operation_source_document={inputs + '/pi_cfd_operations.py'!r}, output_directory={output!r}, contract_document={output + '/cfd-contract-b.json'!r}, variant='b'. Use the same fixed compiler and accepted numerical profile as alternative A. Import the actual same-run AgentCAD STEP regions, reject overlaps/missing boundaries, perform real meshing/checkMesh, and retain the exact receipt and foam_case_dir. Never alter CAD or physics to pass.",
        "cfd-preparation-b-report.json",
        "wright-campaign-pi-cfd",
        ("cfd-preparation-b.json",),
    )
    helpers.add_reference(sections, cad, preparation_b, "actual_cad_contract_b")
    helpers.add_reference(
        sections, references["compiler_source"], preparation_b, "fixed_compiler_source"
    )
    foam_case_b = (
        "/workspace/campaign/" + identity + "/" + args.attempt + "/pi-cfd/variant-b"
    )
    solved_b = configure_foam_run(
        stages["cfd_compare"], foam_case_b, "cfd-run-b-report.json"
    )
    # As with variant A, the ordered edge carries the execution dependency.
    collection = new(
        "collect_cfd_results",
        "Collect actual same-run fields and two-variant comparison",
    )
    bind(
        collection,
        f"After actual Foam-Agent run, call collect_pi_cfd_comparison once with operation_source_document={inputs + '/pi_cfd_operations.py'!r}, output_directory={output!r}. It requires completed matching solver records and actual nonempty computed fields; no input copies or design-target values may substitute. Summarize the real region temperatures, pressure/flow observations and unresolved physical/convergence assumptions against the original requirements. Preserve both variants and explain that content validity remains unmeasured.",
        "cfd-handoff.md",
        "wright-campaign-pi-cfd",
        ("cfd-comparison.json", "cfd-fields.zip"),
    )
    helpers.add_reference(sections, solved_a, collection, "actual_solver_run_a")
    helpers.add_reference(sections, solved_b, collection, "actual_solver_run_b")
    chain = [
        stages["source_dimensions"],
        stages["design_basis"],
        review,
        author,
        stages["agentcad_enclosure"],
        preparation_a,
        solve_a,
        preparation_b,
        stages["cfd_compare"],
        collection,
    ]
    existing = {(edge["fields"]["from"], edge["fields"]["to"]) for edge in edges}
    for left, right in zip(chain, chain[1:]):
        if (left["id"], right["id"]) not in existing:
            sections.append(
                {
                    "kind": "connection",
                    "id": "sequence_" + right["id"],
                    "fields": {
                        "type": "order",
                        "from": left["id"],
                        "to": right["id"],
                        "label": "complete canonical engineering sequence",
                        "when": None,
                    },
                }
            )
    add_scoped_file_inspection(
        sections, suffix, output, server("wright-workspace-files"), inputs=inputs
    )
    rendered = helpers.render(sections)
    validate_workspace_authoring_shape(rendered)
    plan = compile_prompt_workflow(rendered)
    selected = []
    for alias, names in config["allowed_tools"].items():
        for name in names:
            matches = [
                tool
                for tool in available
                if tool["server_id"] == server(alias) and tool["tool_name"] == name
            ]
            if len(matches) != 1:
                raise ValueError(
                    "Required selected tool unavailable: " + alias + "/" + name
                )
            selected.append(matches[0])
    draft.mkdir(parents=True)
    target = draft / "bound.workflow.wflow"
    target.write_text(rendered, encoding="utf-8")
    report = {
        "schema_version": 1,
        "scenario_id": identity,
        "template_id": scenario["template_id"],
        "attempt_id": args.attempt,
        "status": "prepared_not_dispatched",
        "source": str(target),
        "source_sha256": helpers.digest(rendered.encode()),
        "template_source_sha256": helpers.digest(TEMPLATE.read_bytes()),
        "requires_template_instance_api": not bool(args.instance_source),
        "workspace_root": str(workspace),
        "output_root": output,
        "input_manifest": staged,
        "tool_allowlist": selected,
        "expected_outputs": scenario["expected_outputs"],
        "compiled_stages": [step.id for step in plan.steps],
        "preserved_original_stages": original,
        "preserved_original_edges": [edge["id"] for edge in edges],
        "expected_tool_created_files": [
            path for step in plan.steps for path in step.expected_files
        ],
        "native_initialization": initialization["status"],
        "approval_policy_request": {
            "mode": "auto",
            "scope": "integration_test",
            "test_destinations": [],
        },
        "recorded_implementation": "Actual AgentCAD plus fixed CAD-region compiler and native Foam-Agent/OpenFOAM; no Blender",
        "blockers": []
        if initialization["status"] == "native_initialized"
        else ["Native AgentCAD project initialization required before enrollment"],
    }
    helpers.publish_input_binding_evidence(report, directory)
    (draft / "staging-manifest.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "scenario_id": identity,
        "draft": str(target),
        "stages": len(plan.steps),
        "executed": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument(
        "--draft-root",
        default=str(ROOT / ".local-run/feature-081-live/pi-visual-campaign-drafts"),
    )
    parser.add_argument("--attempt", default="attempt-003")
    parser.add_argument("--instance-source")
    parser.add_argument("--scenario")
    parser.add_argument("--server-map")
    parser.add_argument("--initialize-agentcad", action="store_true")
    parser.add_argument("--api", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--session", default="wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a"
    )
    args = parser.parse_args()
    with urllib.request.urlopen(
        args.api
        + "/api/workspace/workflow-sources/tools?session_id="
        + urllib.parse.quote(args.session),
        timeout=60,
    ) as response:
        available = json.load(response)["tools"]
    rows = []
    for directory in sorted(
        (
            ROOT
            / "tests/datasets/engineering-workflows/scenarios/raspberry-pi-enclosure"
        ).iterdir()
    ):
        identity = json.loads((directory / "scenario.json").read_text())["scenario_id"]
        if not args.scenario or args.scenario == identity:
            rows.append(prepare(args, directory, available))
    print(json.dumps({"prepared": rows, "dispatched": False}, indent=2))
