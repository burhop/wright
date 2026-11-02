"""Prepare the original digital manufacturing case; never execute or approve it."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlsplit

from core.process_validation import ResourceBudget

spec = importlib.util.spec_from_file_location(
    "process_example_definition", Path(__file__).resolve().parents[1] / "definition.py"
)
definition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(definition)
REPO = definition.REPO

provider_spec = importlib.util.spec_from_file_location(
    "printed_provider_inputs", Path(__file__).with_name("provider_inputs.py")
)
provider_inputs = importlib.util.module_from_spec(provider_spec)
provider_spec.loader.exec_module(provider_inputs)

retained_spec = importlib.util.spec_from_file_location(
    "printed_retained_source", Path(__file__).with_name("retained_source.py")
)
retained_source = importlib.util.module_from_spec(retained_spec)
retained_spec.loader.exec_module(retained_source)

gate_spec = importlib.util.spec_from_file_location(
    "printed_early_repair_gate", Path(__file__).with_name("repair_gate.py")
)
repair_gate = importlib.util.module_from_spec(gate_spec)
gate_spec.loader.exec_module(repair_gate)

native_spec = importlib.util.spec_from_file_location(
    "printed_native_inspection", Path(__file__).with_name("native_inspection.py")
)
native_inspection = importlib.util.module_from_spec(native_spec)
native_spec.loader.exec_module(native_inspection)

orientation_spec = importlib.util.spec_from_file_location(
    "printed_orientation_stages", Path(__file__).with_name("orientation_stages.py")
)
orientation_stages = importlib.util.module_from_spec(orientation_spec)
orientation_spec.loader.exec_module(orientation_stages)

scenario_spec = importlib.util.spec_from_file_location(
    "printed_scenario_inputs", Path(__file__).with_name("scenario_inputs.py")
)
scenario_inputs = importlib.util.module_from_spec(scenario_spec)
scenario_spec.loader.exec_module(scenario_inputs)


def _local_module(module_name):
    local_spec = importlib.util.spec_from_file_location(
        module_name, Path(__file__).with_name(module_name + ".py")
    )
    local_module = importlib.util.module_from_spec(local_spec)
    local_spec.loader.exec_module(local_module)
    return local_module


orca_binding, orca_stages, run_disclosure = (
    _local_module(name) for name in ("orca_binding", "orca_stages", "run_disclosure")
)


def prepare(workspace, attempt, tools, bindings):
    workspace = Path(workspace).resolve(strict=True)
    frozen, scenario_asset = scenario_inputs.load(REPO, bindings)
    scenario_id = frozen["scenario_id"]
    is_handle = scenario_id == scenario_inputs.HANDLE
    orca = orca_binding.qualify(bindings, scenario_id)
    workflow_id = bindings.get("workflow_id")
    if workflow_id is not None and (
        not isinstance(workflow_id, str)
        or not definition.re.fullmatch(r"[a-z][a-z0-9_]{0,159}", workflow_id)
    ):
        raise ValueError("Declare a valid exact workflow source identifier")
    if orca:
        instruction_name = "printed-replacement-part-02.orca-instructions.json"
        raw = (Path(__file__).with_name("scenarios") / instruction_name).read_bytes()
        instructions = json.loads(raw)
        if (
            instructions["scenario_id"] != scenario_id
            or instructions["binding_kind"] != orca_binding.KIND
        ):
            raise ValueError("Orca instruction binding mismatch")
        frozen = {**frozen, "instructions": instruction_name}
        scenario_asset = (raw, instructions)
    qualified_geometry = provider_inputs.qualified_geometry_inputs(bindings)
    if is_handle and qualified_geometry:
        if json.loads(qualified_geometry["basis"][0]).get("scenario_id") != scenario_id:
            raise ValueError(
                "Configured geometry basis does not match the handle scenario"
            )
    modes = provider_inputs.geometry_operation_modes(bindings)
    configured_construction = modes["construction"] == "configured_tool"
    configured_repair = modes["repair"] == "configured_tool"
    construction = provider_inputs.construction_binding(bindings)
    retained = retained_source.qualify(bindings)
    compare_orientations = bindings.get("orientation_comparison", False)
    if type(compare_orientations) is not bool:
        raise ValueError("Declare orientation_comparison as a boolean")
    if (
        compare_orientations
        and not is_handle
        and (retained or not configured_construction)
    ):
        raise ValueError(
            "The integrated orientation study requires the current configured native producer"
        )
    native_check = None
    if "native_inspection_operation" in bindings:
        native_check = native_inspection.qualify(
            bindings["native_inspection_operation"],
            construction,
            configured=configured_construction,
            retained=retained,
        )
    completion = None
    if "repair_completion_operation" in bindings:
        if retained:
            raise ValueError(
                "Declare a separate retained-source early gate; do not bind it to an absent new producer"
            )
        if not configured_repair:
            raise ValueError(
                "The repair-completion record requires an explicit configured repair operation"
            )
        completion = repair_gate.qualify(bindings["repair_completion_operation"])
    if retained and "construction_binding" in bindings:
        raise ValueError(
            "A retained source has no new construction producer; remove the construction binding"
        )
    validation_budget = (
        ResourceBudget.model_validate(bindings["validation_resource_budget"])
        if "validation_resource_budget" in bindings
        else None
    )
    destination = bindings["simulator_destination"]
    parsed = urlsplit(destination)
    if (
        parsed.scheme != "test"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or "%" in destination
        or "\\" in destination
        or any(part in {".", ".."} for part in parsed.path.split("/"))
    ):
        raise ValueError(
            "This digital example requires an explicit test:// destination"
        )
    if not orca and (
        not isinstance(bindings["slice_success_contract"], str)
        or not bindings["slice_success_contract"].strip()
    ):
        raise ValueError("Record the selected provider's qualified success contract")
    geometry_guidance = bindings.get("geometry_guidance")
    if (
        not isinstance(geometry_guidance, str)
        or not geometry_guidance.strip()
        or len(geometry_guidance.encode("utf-8")) > 8192
    ):
        raise ValueError("Record bounded qualified geometry application guidance")
    geometry, slicer, inspection = (
        bindings[key]
        for key in (
            "geometry_server",
            "slicer_server",
            "inspection_server",
        )
    )
    files = bindings.get("files_server", "") if orca else bindings["files_server"]
    mount = bindings["inspection_workspace"].rstrip("/")
    if not mount.startswith("/") or ".." in mount.split("/"):
        raise ValueError(
            "Use the selected inspection provider’s absolute workspace mount"
        )
    required = [
        (geometry, ("execute_blender_code",)),
        (slicer, ("shell_execute" if orca else "slice_model_file",)),
        (inspection, ("run_simulation",)),
    ]
    if not orca:
        required.append((files, ("write_text_document", "inspect_file")))
    if configured_construction:
        required.append((construction["server"], (construction["tool"],)))
    if completion:
        required.append((completion[0]["server"], (completion[0]["tool"],)))
    if native_check:
        required.append((native_check[0]["server"], (native_check[0]["tool"],)))
    for server, names in required:
        for name in names:
            matches = [
                item
                for item in tools
                if item.get("server_id") == server
                and item.get("tool_name") == name
                and item.get("schema_digest")
            ]
            if len(matches) != 1:
                raise ValueError(
                    "Required fresh configured capability is missing: "
                    + server
                    + "/"
                    + name
                )
    profile_path = definition.resource(frozen["baseline_profile"]["path"])
    if (
        definition.sha(profile_path.read_bytes())
        != frozen["baseline_profile"]["sha256"]
    ):
        raise ValueError("Original validation profile changed")
    profile = json.loads(profile_path.read_bytes())
    profile_bytes = {}
    for role in ("machine", "process", "filament"):
        selected = bindings["profiles"][role]
        raw = Path(selected["path"]).read_bytes()
        if definition.sha(raw) != selected["sha256"]:
            raise ValueError("Selected provider configuration changed: " + role)
        profile_bytes[role] = raw
    for check in profile["checks"]:
        role = check["subject_role"].removesuffix("_profile")
        if role in profile_bytes and check["reader"] == "structured":
            key = check["selector"].removeprefix("/")
            if (
                json.loads(profile_bytes[role]).get(key)
                != check["constraint"]["expected"]
            ):
                raise ValueError(
                    "Selected profiles do not meet the original requirement: "
                    + check["id"]
                )
    assignment = []
    for item in frozen["inputs"]:
        original = definition.resource(item["path"])
        data = original.read_bytes()
        if definition.sha(data) != item["sha256"]:
            raise ValueError("Original assignment changed: " + item["path"])
        assignment.append((item, original, data))
    flow = definition.Definition(
        "printed-replacement-part",
        workspace,
        attempt,
        tools,
        run_path_template=bindings.get("run_path_template", ""),
    )
    for server, names in required:
        for name in names:
            flow.select(server, name)
    refs = {}
    for item, original, data in assignment:
        refs[original.name] = flow.input_bytes(
            original.name,
            data,
            original=item["path"],
            kind="reference_images"
            if original.suffix == ".png"
            else "engineering_document",
        )
    original_image = flow.original("image_and_scale")
    original_image["fields"]["settings"] = {
        "input_mode": "workspace-file",
        "workspace_file": flow.input_root + "/concept.png",
        "reference_dimension_mm": frozen.get("reference_dimension_mm", 38.0),
        "units": "mm",
    }
    requirements = "\n".join(
        item["id"] + ": " + item["text"] for item in profile["baseline"]["requirements"]
    )
    requirements_ref = flow.input_bytes("requirements.md", requirements.encode())
    guidance_ref = flow.input_bytes(
        "geometry-capability-guidance.md", geometry_guidance.encode()
    )
    profiles = {
        role: flow.input_bytes(
            role + "-profile.json",
            raw,
            original=bindings["profiles"][role]["path"],
            kind="workspace_file",
        )
        for role, raw in profile_bytes.items()
    }
    basis = flow.stage(
        "define_geometry_basis",
        "Interpret the original wheel and manufacturing requirements",
    )
    basis_result = flow.ai(
        basis,
        "Prepare a complete proposed digital geometry design for the next declared review, separating supplied requirements from your proposed construction choices. Preserve the 38 mm maximum diameter, 18 mm overall height including 2 mm front hub, six equally spaced shallow scallops, >=33 mm minimum grip, nominal 1 mm exposed rounds and subtle grip dots. The D socket uses the 6.00 mm round boundary and 5.20 mm across-flat shaft with 0.20 mm radial and flat clearance, 10 mm blind depth and >=3 mm material above it. No insert, set screw, taper or keyway. Preserve PETG/P1S 0.4/0.20 mm/four walls/35% profiles, proposed +/-0.25 mm non-mating tolerance and original human-review requirements. Propose explicit numeric scallop profile/depth/phase, hub diameter, dot count/dimensions/placement and exposed-edge treatment within the original limits; derive and record the D-boundary/flat construction and depth direction. These are design proposals, not additional requirements or verified fit. Distinguish decisions that must be resolved at this declared basis review from later inspection of actual geometry, supports and final package. Do not leave a predictable construction choice to a later unattended question. No geometry, fit, strength, standards or print-success claim yet. Do not ask runtime questions; output one complete proposal for the declared review."
        " Keep the entire response below 3000 characters. Return only one valid JSON object, with no markdown, comments or trailing commas. Use these keys: supplied_requirements (short object), proposed_geometry (numeric dimensions plus short construction descriptions for scallops, hub, dots, rounds, socket and orientation), basis_review (short list of proposed choices requiring this review), remaining_verification (short list), engineering_acceptance (false). Expressions must be JSON strings; do not put equations in numeric values. Do not repeat input documents or provide lengthy rationale.",
        "geometry-basis.json",
    )
    if qualified_geometry:
        raw, original = qualified_geometry["basis"]
        retained_basis = flow.input_bytes(
            "configured-geometry-basis.json", raw, original=original
        )
        flow.reference(retained_basis, basis, "supplied_geometry_basis")
        basis["fields"]["prompt"] += (
            " This run supplies an explicit prior proposed geometry basis. Retain its numeric "
            "construction choices exactly instead of proposing replacements. It remains a "
            "proposal for this run's declared review, not engineering acceptance. Actual "
            "geometry and all original mandatory checks still follow."
        )
    for name, reference in refs.items():
        flow.reference(
            reference,
            basis,
            name.replace(".", "_"),
            "reference_images" if name.endswith(".png") else "engineering_document",
        )
    flow.reference(requirements_ref, basis, "mandatory_requirements")
    basis_review = flow.stage(
        "review_basis",
        "Review wheel dimensions, socket interpretation and original limits",
    )
    flow.review(
        basis_review,
        "Review the exact basis, supplied image scale and proposed geometry/socket interpretations. This digital process does not establish fit, strength or printing success.",
    )
    flow.reference(basis_result, basis_review, "basis")
    if is_handle:
        for name, reference in refs.items():
            flow.reference(
                reference,
                basis_review,
                "original_" + name.replace(".", "_"),
                "reference_images"
                if name.endswith(".png")
                else "engineering_document",
            )
        flow.reference(requirements_ref, basis_review, "original_requirements")
        if qualified_geometry:
            flow.reference(retained_basis, basis_review, "configured_geometry_basis")
    if configured_construction or configured_repair:
        flow.reference(guidance_ref, basis_review, "qualified_application_guidance")
    absolute_output = workspace / flow.output

    def complete_handle_blender_arguments(role, raw):
        original_prompt = next(
            data for _, path, data in assignment if path.name == "prompt.txt"
        )
        complete = {**json.loads(raw), "user_prompt": original_prompt.decode("utf-8")}
        content = (json.dumps(complete, ensure_ascii=False, indent=2) + "\n").encode(
            "utf-8"
        )
        invocation = flow.input_bytes(
            role + "-blender-call.json",
            content,
            run_paths=bool(flow.run_path_template),
        )
        reviewed_invocation = flow.input_bytes(
            role + "-blender-call-review.json", content
        )
        flow.reference(
            reviewed_invocation, basis_review, role + "_complete_blender_arguments"
        )
        return invocation

    create = flow.original("create_mesh")
    if configured_construction:
        # The fixed operation consumes JSON, not an image. Keep the original
        # scaled reference in the AI interpretation and its declared review.
        image_connection = flow.original("image_to_mesh")
        image_connection["fields"]["to"] = basis["id"] + ".mesh_source_image_in"
        image_connection["fields"]["label"] = (
            "original scaled reference for proposed basis"
        )
        basis["fields"]["inputs"].extend(create["fields"]["inputs"])
        create["fields"]["inputs"] = []
    source_result = flow.ai(
        create,
        f"Use the existing Blender execute_blender_code tool to construct the reviewed focus wheel from the actual supplied image and dimensions. Wright runs this stage only after consuming its declared exact-subject basis review. The reviewed_basis input remains the unchanged proposed design; use the design released by that order barrier rather than treating its earlier proposal status as a new runtime question. A labelled integration-test decision permits digital construction only and is not human engineering acceptance; retain final measured-feature/support/package review. Work only with uniquely named owned objects and actual geometry. Export binary STL in explicit millimetres at {str(absolute_output / 'source_mesh.stl')!r}. Preserve the complete original feature requirements; do not substitute a cylinder/cube or infer verified fit. Keep <=80000 triangles. Return compact actual construction observations and unresolved physical limits; Wright retains the exact tool call. Do not request an undeclared review or missing construction choice. If the released design cannot be implemented within original limits, return an explicit blocked technical outcome instead of making up evidence. Use guarded bpy/bmesh/mathutils modelling and Blender STL export only: no open/pathlib/os/sys/hashlib/runpy/subprocess/network/handlers/timers/drivers/addon operations or raw filesystem calls. Do not overwrite unrelated objects. Geometry failure is explicit; no fabricated export or verdict.",
        "source-model-report.json",
        server=geometry,
        expected=("source_mesh.stl",),
        calls=2,
        timeout=360,
    )
    create["fields"]["prompt"] += (
        " The connected original_user_prompt is the user's supplied text, distinct from "
        "these task instructions and reviewed_basis. Preserve that original text verbatim "
        "in user_prompt for each execute_blender_code call; do not replace it with a task "
        "summary. Interpret the actual connected original_reference image with the supplied "
        "38 mm scale and written dimensions governing. The connected original_context and "
        "original_user_profile retain manufacturing and use constraints. A configured "
        "recipe does not replace those inputs or establish measured compliance."
    )
    if qualified_geometry:
        raw, original = qualified_geometry["construction"]
        invocation = flow.input_bytes(
            "construction-provider-arguments.json",
            raw,
            original=original,
            run_paths=bool(flow.run_path_template)
            and not (
                is_handle
                and configured_construction
                and construction["tool"] == "execute_blender_code"
            ),
        )
        if (
            is_handle
            and configured_construction
            and construction["tool"] == "execute_blender_code"
        ):
            flow.reference(invocation, basis_review, "construction_pinned_arguments")
            invocation = complete_handle_blender_arguments("construction", raw)
        argument_port = flow.reference(invocation, create, "qualified_operation")
        if configured_construction:
            flow.exact_mcp(
                create,
                flow.select(construction["server"], construction["tool"]),
                argument_port,
                tuple(construction["outputs"].values()),
                "source-model-report.json",
            )
            create["fields"]["settings"]["timeout_seconds"] = 360
            reviewed_operation = flow.input_bytes(
                "construction-operation-review.json", raw, original=original
            )
            flow.reference(reviewed_operation, basis_review, "construction_operation")
        else:
            create["fields"]["prompt"] += (
                " Use the code argument in qualified_operation as the supplied native construction "
                "recipe. Submit it unchanged to execute_blender_code; do not invent another "
                "modelling algorithm or replace its dimensions. Its export path and owned names "
                "are configured for this fresh run. Keep actual tool observations and failures. "
                "This is reuse of a prior qualified operation, not new AI-authored geometry code "
                "or proof of compliance. If its input design differs from reviewed_basis, stop "
                "with a technical mismatch before executing it."
            )
    if not configured_construction:
        flow.reference(basis_result, create, "reviewed_basis")
        flow.reference(requirements_ref, create, "requirements")
        flow.reference(guidance_ref, create, "qualified_application_guidance")
        flow.reference(refs["prompt.txt"], create, "original_user_prompt")
        flow.reference(refs["context.md"], create, "original_context")
        flow.reference(refs["user-profile.md"], create, "original_user_profile")
        flow.reference(
            refs["concept.png"], create, "original_reference", "reference_images"
        )
    construction_roles = flow.file_outputs(
        create,
        {
            role: flow.output + "/" + filename
            for role, filename in construction["outputs"].items()
        },
    )
    # The retained profile binds exact declared subjects, not every deliverable.
    # Added native outputs remain inspectable ports; their checks need an explicit
    # additional profile rather than changing the original eighteen-check gate.
    source_roles = {"source_mesh": construction_roles["source_mesh"]}
    native_steps, native_review_refs = ([], [])
    if native_check:
        native_steps, native_review_refs = native_inspection.add(
            flow,
            definition,
            native_check,
            create,
            construction,
        )
    repair = flow.original("repair_measure_orient")
    repair_result = flow.ai(
        repair,
        f"Consume the actual source STL at {str(absolute_output / 'source_mesh.stl')!r} using Blender STL import into uniquely owned objects; preserve its bytes. Inspect actual bounds, topology, degenerate geometry, normals and mating features. Merge coincident vertices only with explicitly recorded small mm tolerance, repair normals/degeneracy and export a distinct binary STL at {str(absolute_output / 'repaired_mesh.stl')!r}, <=80000 triangles. Keep original dimensions/features. Compare socket-up orientation with the source orientation and describe actual support consequences, including the raised hub; never promise zero supports from appearance. Retain a real geometry-only preview at {str(absolute_output / 'mesh-preview.png')!r}; it is not a support/toolpath preview. Measure post-transform bounds and topology. Use guarded bpy/bmesh/mathutils modelling, render, STL import/export only, with no raw filesystem/network/process APIs or unrelated object deletion. Return compact actual before/after measurements, applied repair/transform and remaining review limits. Fail if closed manifold geometry or intended features cannot be preserved.",
        "mesh-repair-report.json",
        server=geometry,
        expected=("repaired_mesh.stl", "mesh-preview.png"),
        calls=2,
        timeout=360,
    )
    if qualified_geometry:
        raw, original = qualified_geometry["repair"]
        invocation = flow.input_bytes(
            "repair-provider-arguments.json",
            raw,
            original=original,
            run_paths=bool(flow.run_path_template)
            and not (is_handle and configured_repair),
        )
        if is_handle and configured_repair:
            flow.reference(invocation, basis_review, "repair_pinned_arguments")
            invocation = complete_handle_blender_arguments("repair", raw)
        argument_port = flow.reference(invocation, repair, "qualified_operation")
        if configured_repair:
            flow.exact_mcp(
                repair,
                flow.select(geometry, "execute_blender_code"),
                argument_port,
                ("repaired_mesh.stl", "mesh-preview.png"),
                "mesh-repair-report.json",
            )
            repair["fields"]["settings"]["timeout_seconds"] = 360
            reviewed_operation = flow.input_bytes(
                "repair-operation-review.json", raw, original=original
            )
            flow.reference(reviewed_operation, basis_review, "repair_operation")
            reviewed_operations = (
                "construction and repair" if configured_construction else "repair"
            )
            basis_review["fields"]["instructions"] += (
                " This process invokes the supplied "
                + reviewed_operations
                + " arguments exactly. "
                "Check the connected operation templates against the proposed basis and original requirements "
                "before releasing this barrier. Operation hashes and all inputs remain part "
                "of this exact review subject; the run-resolved call arguments are retained "
                "separately. This is not measured or physical acceptance."
            )
        else:
            repair["fields"]["prompt"] += (
                " Use the code argument in qualified_operation as the supplied native inspection/repair "
                "recipe. Submit it unchanged to execute_blender_code rather than generating another "
                "algorithm. It consumes this run's actual source file and uses uniquely owned "
                "objects and a separate preview scene. Retain the real measurements, exported "
                "file verification and all unresolved feature/support/physical limits. A provider "
                "error remains explicit; never claim an absent output."
            )
    actual_source_port = flow.reference(
        create["id"] + ".source_mesh", repair, "actual_source", "workspace_file"
    )
    repair["fields"]["settings"]["mcp_file_dependencies"] = {
        actual_source_port: flow.output + "/source_mesh.stl"
    }
    if not configured_repair:
        flow.reference(source_result, repair, "construction_report")
        flow.reference(requirements_ref, repair, "requirements")
        flow.reference(guidance_ref, repair, "qualified_application_guidance")
        flow.reference(refs["prompt.txt"], repair, "original_user_prompt")
        flow.reference(refs["context.md"], repair, "original_context")
        flow.reference(refs["user-profile.md"], repair, "original_user_profile")
        repair["fields"]["prompt"] += (
            " Retain the connected original_user_prompt verbatim in user_prompt for "
            "each execute_blender_code call. Preserve the original_context and "
            "original_user_profile; a construction summary does not replace them."
        )
    repaired_roles = flow.file_outputs(
        repair,
        {
            "repaired_mesh": flow.output + "/repaired_mesh.stl",
            "mesh_preview": flow.output + "/mesh-preview.png",
        },
    )
    early_repair_steps = []
    if completion:
        early_repair_steps = list(
            repair_gate.add(
                flow,
                definition,
                completion,
                profile,
                create,
                repair,
                files,
            )
        )
    geometry_review_steps = []
    if is_handle:
        review = flow.stage(
            "review_geometry_before_slice", "Review handle geometry before slicing"
        )
        flow.review(review, scenario_asset[1]["geometry_review"])
        for reference, role, kind in [
            (repair["id"] + ".repaired_mesh", "actual_repaired_mesh", "workspace_file"),
            (repair["id"] + ".mesh_preview", "geometry_only_preview", "workspace_file"),
            (source_result, "construction_observations", "engineering_document"),
            (repair_result, "repair_observations", "engineering_document"),
            (requirements_ref, "original_requirements", "engineering_document"),
            *[
                (
                    ref,
                    "original_" + name.replace(".", "_"),
                    "reference_images"
                    if name.endswith(".png")
                    else "engineering_document",
                )
                for name, ref in refs.items()
            ],
        ]:
            flow.reference(reference, review, role, kind)
        geometry_review_steps.append(review)
    if orca:
        selected = orca_stages.add(
            flow, definition, orca_binding, orca, bindings, repair, profiles
        )
        slice_step, inspect_step = (
            selected[key] for key in ("slice_step", "inspect_step")
        )
        slice_roles, inspect_roles = selected["slice_roles"], selected["inspect_roles"]
        orientation_review_refs = selected["review_refs"]
        preparation_steps = selected["chain"]
    else:
        slice_step = flow.original("supports_and_slice")
        arguments = {
            "source": str(absolute_output / "repaired_mesh.stl"),
            "plate": 1,
            "output": str(absolute_output / "slice_package.gcode.3mf"),
            "orient": False,
            "arrange": True,
            "confirm": True,
        }
        arguments_ref = flow.input_bytes(
            "slice-call.json",
            (json.dumps(arguments, indent=2) + "\n").encode(),
            run_paths=bool(flow.run_path_template),
        )
        argument_port = flow.reference(arguments_ref, slice_step, "exact_arguments")
        flow.exact_mcp(
            slice_step,
            flow.select(slicer, "slice_model_file"),
            argument_port,
            ("slice_package.gcode.3mf",),
            "slicer-execution.json",
        )
        repaired_port = flow.reference(
            repair["id"] + ".repaired_mesh",
            slice_step,
            "selected_geometry",
            "workspace_file",
        )
        slice_step["fields"]["settings"]["mcp_file_dependencies"] = {
            repaired_port: flow.output + "/repaired_mesh.stl"
        }
        for role, reference in profiles.items():
            key = flow.reference(
                reference, slice_step, role + "_configuration", "workspace_file"
            )
            slice_step["fields"]["settings"]["mcp_file_dependencies"][key] = (
                flow.input_root + "/" + role + "-profile.json"
            )
        slice_roles = flow.file_outputs(
            slice_step,
            {
                "slice_package": flow.output + "/slice_package.gcode.3mf",
            },
        )
        response_step = flow.stage(
            "retain_slice_response",
            "Retain the actual slicer response for package inspection",
        )
        response_port = flow.reference(
            slice_step["id"] + "." + slice_step["id"] + "_result",
            response_step,
            "actual_response",
        )
        flow.exact_mcp(
            response_step,
            flow.select(files, "write_text_document"),
            response_port,
            ("slice-provider-response.json",),
            "response-retention-receipt.json",
        )
        response_step["fields"]["settings"].update(
            mcp_arguments_source="fields",
            mcp_argument_ports=json.dumps({response_port: "content"}),
            mcp_arguments=json.dumps(
                {
                    "relativePath": flow.output + "/slice-provider-response.json",
                    "mediaType": "application/json",
                    "overwrite": False,
                }
            ),
        )
        flow.file_outputs(
            response_step,
            {"provider_response": flow.output + "/slice-provider-response.json"},
        )
        reader_path = (
            REPO
            / "packages/workspace_service/src/workspace_service/process_interfaces/representations.py"
        )
        operation_path = REPO / "scripts/engineering/inspect_manufacturing_package.py"
        reader = reader_path.read_bytes()
        operation = operation_path.read_bytes()
        reader_ref = flow.input_bytes(
            "passive-representations.py",
            reader,
            original=reader_path.relative_to(REPO).as_posix(),
            kind="workspace_file",
        )
        operation_ref = flow.input_bytes(
            "inspect_manufacturing_package.py",
            operation,
            original=operation_path.relative_to(REPO).as_posix(),
            kind="workspace_file",
        )
        config = {
            "workspace_root": mount,
            "source_mesh": flow.output + "/repaired_mesh.stl",
            "slice_package": flow.output + "/slice_package.gcode.3mf",
            "provider_response": flow.output + "/slice-provider-response.json",
            "output_root": flow.output,
            "profiles": {
                role: flow.input_root + "/" + role + "-profile.json"
                for role in profiles
            },
            "gcode_entry": "Metadata/plate_1.gcode",
            "nominal_layer_section": bindings.get("nominal_layer_section"),
            "success_field": "ok",
            "expected_response_fields": {
                "source": arguments["source"],
                "output": arguments["output"],
                "plate": 1,
            },
            "success_contract": bindings["slice_success_contract"],
            "operation_label": next(
                check["parameters"]["expected_operation"]
                for check in profile["checks"]
                if check["parameters"].get("operation") == "slice_binding"
            ),
        }
        inspect_step = flow.stage(
            "inspect_slice_handoff",
            "Inspect actual package, profile and nominal toolpath correspondence",
        )
        input_content = (
            "import hashlib\nfrom pathlib import Path\nreader_source=Path("
            + repr(mount + "/" + flow.input_root + "/passive-representations.py")
            + ").read_bytes()\nassert hashlib.sha256(reader_source).hexdigest()=="
            + repr(definition.sha(reader))
            + "\noperation_source=Path("
            + repr(mount + "/" + flow.input_root + "/inspect_manufacturing_package.py")
            + ").read_bytes()\nassert hashlib.sha256(operation_source).hexdigest()=="
            + repr(definition.sha(operation))
            + '\nreader_namespace={"__name__":"passive_reader"}\nexec(compile(reader_source,"passive-representations.py","exec"),reader_namespace)\noperation_namespace={"__name__":"package_inspection"}\nexec(compile(operation_source,"inspect_manufacturing_package.py","exec"),operation_namespace)\nprint(operation_namespace["run"]('
            + repr(config)
            + ',reader_namespace["read_3mf_toolpaths"]))\n'
        )
        inspection_call = flow.input_bytes(
            "inspection-call.json",
            (
                json.dumps(
                    {
                        "solver": bindings["inspection_backend"],
                        "input_content": input_content,
                        "job_name": (
                            flow.output if flow.run_path_template else flow.relative
                        )
                        + "/package-inspection",
                        "critic_approved": False,
                    },
                    indent=2,
                )
                + "\n"
            ).encode(),
            run_paths=bool(flow.run_path_template),
        )
        argument_port = flow.reference(inspection_call, inspect_step, "exact_arguments")
        flow.exact_mcp(
            inspect_step,
            flow.select(inspection, "run_simulation"),
            argument_port,
            (
                "slice-evidence.json",
                "support-preview.json",
                "toolpath-summary.json",
                "machine-profile.json",
                "process-profile.json",
                "filament-profile.json",
            ),
            "package-inspection-result.json",
        )
        dependencies = {}
        for role in ("slice_package",):
            key = flow.reference(
                slice_step["id"] + "." + role, inspect_step, role, "workspace_file"
            )
            dependencies[key] = slice_step["fields"]["settings"]["expected_file_ports"][
                role
            ]
        key = flow.reference(
            response_step["id"] + ".provider_response",
            inspect_step,
            "provider_response",
            "workspace_file",
        )
        dependencies[key] = flow.output + "/slice-provider-response.json"
        key = flow.reference(
            repair["id"] + ".repaired_mesh",
            inspect_step,
            "slice_source",
            "workspace_file",
        )
        dependencies[key] = flow.output + "/repaired_mesh.stl"
        for key, reference in [
            ("reader", reader_ref),
            ("operation", operation_ref),
            *[(role, reference) for role, reference in profiles.items()],
        ]:
            port = flow.reference(reference, inspect_step, key, "workspace_file")
            filename = {
                "reader": "passive-representations.py",
                "operation": "inspect_manufacturing_package.py",
            }.get(key, key + "-profile.json")
            dependencies[port] = flow.input_root + "/" + filename
        inspect_step["fields"]["settings"]["mcp_file_dependencies"] = dependencies
        inspect_roles = flow.file_outputs(
            inspect_step,
            {
                "slice_evidence": flow.output + "/slice-evidence.json",
                "support_preview": flow.output + "/support-preview.json",
                **{
                    role + "_profile": flow.output + "/" + role + "-profile.json"
                    for role in profiles
                },
            },
        )
        flow.file_outputs(
            inspect_step, {"toolpath_summary": flow.output + "/toolpath-summary.json"}
        )
        orientation_steps, orientation_review_refs = ([], [])
        if compare_orientations:
            orientation_steps, orientation_review_refs = orientation_stages.add(
                flow,
                definition,
                bindings,
                create,
                construction,
                scenario=frozen if is_handle else None,
                repaired=repair if is_handle else None,
            )
        preparation_steps = [
            slice_step,
            response_step,
            inspect_step,
            *orientation_steps,
        ]
    report = flow.stage(
        "summarize_preparation",
        "Record measured preparation facts and outstanding engineering review",
    )
    report_result = flow.ai(
        report,
        "The connected construction and repair results and original requirements are supplied reference material. Read those results directly; do not guess report filenames or reread supplied content. Use inspect_file exactly once for each connected slice_evidence and toolpath_summary workspace-file reference, using its verified relative path with includeText=true and maxTextBytes=32768, within the selected workspace reader schema. If either record is truncated or unavailable, report that exact limitation instead of treating an incomplete inspection as complete. Those bounded records contain the actual package/mesh identity and profile observations; do not read raw profiles, G-code or the full support preview. Return the report after those two inspections; Wright saves it, so do not call a writing tool. Summarize construction, socket interpretation, repair, orientation/support consequences, exact PETG settings and nominal toolpaths. Separate design values from measured dimensions and future physical fit. The preview is nominal toolpath data, not completed printing. Retain all original mandatory limits and unresolved review requirements. Do not invent measurements, successful printing, fit, strength or a critic/human verdict. Return one compact JSON object under 6000 characters, with artifact_lineage, geometry_observations, preparation_observations, outstanding_requirements, limitations and engineering_acceptance=false.",
        "source-report.json",
        server=None if orca else files,
        calls=2,
        timeout=360,
    )
    if orca:
        report["fields"]["settings"]["reference_inline_max_bytes"] = 32768
        flow.reference(
            selected["comparison_reference"],
            report,
            "orientation_comparison",
            "workspace_file",
        )
    else:
        report["fields"]["settings"]["mcp_task_tools"] = ["inspect_file"]
    for reference, key in [
        (source_result, "construction"),
        (repair_result, "repair"),
        (inspect_step["id"] + ".slice_evidence", "slice_evidence"),
        (inspect_step["id"] + ".toolpath_summary", "toolpath_summary"),
    ]:
        flow.reference(
            reference,
            report,
            key,
            "workspace_file"
            if key in ("slice_evidence", "toolpath_summary")
            else "engineering_document",
        )
    flow.reference(requirements_ref, report, "requirements")
    report_roles = {
        "source_report": (report, report["id"] + "_result", "engineering_document")
    }
    transfer = flow.original("authorize_transfer")
    transfer["fields"]["outputs"] = [definition.port("receipt", "workspace_file")]
    transfer["fields"]["settings"] = {
        "authoring_template": "external-action-approval",
        "action_kind": "printer_transfer",
        "approval_binding": {
            "server": "wright",
            "tool": "test_handoff",
            "schema": definition.sha(b"wright.integration_test_handoff.v1"),
        },
        "approval_destination": {
            "kind": "integration_test",
            "id": bindings["simulator_destination"],
        },
        "approval_settings": {
            "material": "PETG",
            "nozzle_mm": "0.4",
            "package_path": flow.output + "/slice_package.gcode.3mf",
            "receipt_path": flow.output + "/simulated-transfer-receipt.json",
            "simulation": True,
        },
        "approval_action": {
            "kind": "printer_transfer",
            "mode": "transfer_only",
            "simulation": True,
        },
    }
    if flow.run_path_template:
        transfer_settings = transfer["fields"]["settings"]
        transfer_settings["approval_settings"].pop("receipt_path")
        # The connected workspace_file already pins the actual package bytes.
        # A second literal authority-setting path would refer to another run.
        transfer_settings["approval_settings"].pop("package_path")
        transfer_settings.update(
            run_path_template=flow.run_path_template,
            output_filename=flow.output + "/simulated-transfer-receipt.json",
        )
    flow.reference(
        slice_step["id"] + ".slice_package", transfer, "exact_package", "workspace_file"
    )
    flow.reference(report_result, transfer, "preparation_review")
    for role, reference in profiles.items():
        flow.reference(reference, transfer, role + "_profile", "workspace_file")
    if retained:
        source_roles = retained_source.configure(
            flow, retained, qualified_geometry, create, repair, report
        )
    sources = {
        **source_roles,
        "repaired_mesh": repaired_roles["repaired_mesh"],
        **slice_roles,
        **inspect_roles,
        **report_roles,
        "transfer_receipt": (transfer, "receipt", "workspace_file"),
    }
    validator = flow.validator(
        scenario_id,
        sources,
        budget=validation_budget.model_dump(mode="json") if validation_budget else None,
        scenario_id=scenario_id,
    )
    binding_review_refs = []
    if orca:
        binding_review_refs = orca_binding.amend_validator(
            flow, definition, validator, profile, orca, selected["extra_sources"]
        )
        for reference, role, kind in binding_review_refs:
            flow.reference(reference, basis_review, role, kind)
    final_review = flow.stage(
        "review_preparation",
        "Review final digital preparation and exact engineering findings",
    )
    flow.review(
        final_review,
        "Review the original socket, grip, orientation/support, tolerance and action-scope requirements against exact outputs. This process cannot certify fit, strength, accuracy or a physical print.",
        profile={
            "profile_ref": validator["fields"]["settings"]["validation"]["profile"][
                "reference"
            ],
            "requirement_ids": sorted(
                requirement["id"]
                for requirement in profile["baseline"]["requirements"]
                if requirement["review_required"]
            ),
        },
    )
    flow.reference(requirements_ref, final_review, "original_requirements")
    for role, (producer, key, kind) in sources.items():
        flow.reference(producer["id"] + "." + key, final_review, role, kind)
    for reference, role, kind in [
        *native_review_refs,
        *orientation_review_refs,
        *binding_review_refs,
    ]:
        flow.reference(reference, final_review, role, kind)
    if is_handle:
        scenario_inputs.apply(
            flow,
            frozen,
            scenario_asset,
            basis=basis,
            basis_review=basis_review,
            create=create,
            repair=repair,
            report=report,
            final_review=final_review,
            qualified=qualified_geometry,
            configured_construction=configured_construction,
            configured_repair=configured_repair,
        )
    if workflow_id is not None:
        workflow = next(
            section for section in flow.sections if section["kind"] == "workflow"
        )
        workflow["id"] = workflow_id
    if is_handle:
        transformation = {
            "schema_version": 1,
            "starter_id": frozen["starter_id"],
            "workflow_id": next(
                section["id"]
                for section in flow.sections
                if section["kind"] == "workflow"
            ),
            "source_template": "printed-replacement-part",
            "scenario_id": scenario_id,
            "role_to_task_id": {
                "review_intent": basis_review["id"],
                "create_mesh": create["id"],
                "repair_measure": repair["id"],
                "review_geometry": geometry_review_steps[0]["id"],
                "compare_preparations": next(
                    step["id"]
                    for step in preparation_steps
                    if step["id"].startswith("compare_orientations_")
                ),
                "review_preparation": final_review["id"],
                "inspect_package": validator["id"],
            },
            "additional_task_ids": {
                "define_geometry_basis": basis["id"],
                "supports_and_slice": slice_step["id"],
                "authorize_transfer": transfer["id"],
            },
            "execution_authority": False,
        }
        ref = flow.input_bytes(
            "source-transformation.json",
            (json.dumps(transformation, indent=2) + "\n").encode(),
        )
        flow.reference(ref, basis_review, "accepted_source_transformation")
        run_disclosure.attach(flow, basis_review)
    return flow.save(
        [
            basis,
            basis_review,
            *([] if retained else [create]),
            *native_steps,
            repair,
            *early_repair_steps,
            *geometry_review_steps,
            *preparation_steps,
            report,
            transfer,
            final_review,
            validator,
        ]
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--tools", required=True, type=Path)
    parser.add_argument("--bindings", required=True, type=Path)
    args = parser.parse_args()
    result = prepare(
        args.workspace,
        args.attempt,
        json.loads(args.tools.read_bytes()),
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
