"""Prepare the original digital manufacturing case; never execute or approve it."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from urllib.parse import urlsplit

spec = importlib.util.spec_from_file_location(
    "process_example_definition", Path(__file__).resolve().parents[1] / "definition.py"
)
definition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(definition)
REPO = definition.REPO


def prepare(workspace, attempt, tools, bindings):
    workspace = Path(workspace).resolve(strict=True)
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
    if (
        not isinstance(bindings["slice_success_contract"], str)
        or not bindings["slice_success_contract"].strip()
    ):
        raise ValueError("Record the selected provider's qualified success contract")
    geometry, files, slicer, inspection = (
        bindings[key]
        for key in (
            "geometry_server",
            "files_server",
            "slicer_server",
            "inspection_server",
        )
    )
    mount = bindings["inspection_workspace"].rstrip("/")
    if not mount.startswith("/") or ".." in mount.split("/"):
        raise ValueError(
            "Use the selected inspection provider’s absolute workspace mount"
        )
    required = [
        (geometry, ("execute_blender_code",)),
        (files, ("write_text_document", "inspect_file")),
        (slicer, ("slice_model_file",)),
        (inspection, ("run_simulation",)),
    ]
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
    frozen = json.loads(
        (REPO / "examples/process-interfaces/proof-bindings.json").read_bytes()
    )
    frozen = next(
        item
        for item in frozen["cases"]
        if item["template_id"] == "printed-replacement-part"
    )
    profile_path = REPO / frozen["baseline_profile"]["path"]
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
        original = REPO / item["path"]
        data = original.read_bytes()
        if definition.sha(data) != item["sha256"]:
            raise ValueError("Original assignment changed: " + item["path"])
        assignment.append((item, original, data))
    flow = definition.Definition("printed-replacement-part", workspace, attempt, tools)
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
        "reference_dimension_mm": 38.0,
        "units": "mm",
    }
    requirements = "\n".join(
        item["id"] + ": " + item["text"] for item in profile["baseline"]["requirements"]
    )
    requirements_ref = flow.input_bytes("requirements.md", requirements.encode())
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
        "Record the original supplied dimensions and unresolved design interpretations. Preserve the 38 mm maximum diameter, 18 mm overall height including 2 mm front hub, six equally spaced shallow scallops, >=33 mm minimum grip, nominal 1 mm exposed rounds and subtle grip dots. The D socket uses the 6.00 mm round boundary and 5.20 mm across-flat shaft with 0.20 mm radial and flat clearance, 10 mm blind depth and >=3 mm material above it. No insert, set screw, taper or keyway. Preserve PETG/P1S 0.4/0.20 mm/four walls/35% profiles, proposed +/-0.25 mm non-mating tolerance and original human-review requirements. No geometry, fit, strength, standards or print-success claim yet. Do not ask undeclared runtime questions; record interpretation for the next declared review.",
        "geometry-basis.json",
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
        "Review the exact basis, supplied image scale and unresolved geometry/socket interpretations. This digital process does not establish fit, strength or printing success.",
    )
    flow.reference(basis_result, basis_review, "basis")
    absolute_output = workspace / flow.output
    create = flow.original("create_mesh")
    source_result = flow.ai(
        create,
        f"Use the existing Blender execute_blender_code tool to construct the reviewed focus wheel from the actual supplied image and dimensions. Work only with uniquely named owned objects and actual geometry. Export binary STL in explicit millimetres at {str(absolute_output / 'source_mesh.stl')!r}. Preserve the complete original feature requirements; do not substitute a cylinder/cube or infer verified fit. Keep <=80000 triangles. Return compact actual construction observations and unresolved limits; Wright retains the exact tool call. Use guarded bpy/bmesh/mathutils modelling and Blender STL export only: no open/pathlib/os/sys/hashlib/runpy/subprocess/network/handlers/timers/drivers/addon operations or raw filesystem calls. Do not overwrite unrelated objects. Geometry failure is explicit; no fabricated export or verdict.",
        "source-model-report.json",
        server=geometry,
        expected=("source_mesh.stl",),
        calls=2,
    )
    flow.reference(basis_result, create, "reviewed_basis")
    flow.reference(requirements_ref, create, "requirements")
    flow.reference(
        refs["concept.png"], create, "original_reference", "reference_images"
    )
    source_roles = flow.file_outputs(
        create, {"source_mesh": flow.output + "/source_mesh.stl"}
    )
    repair = flow.original("repair_measure_orient")
    repair_result = flow.ai(
        repair,
        f"Consume the actual source STL at {str(absolute_output / 'source_mesh.stl')!r} using Blender STL import into uniquely owned objects; preserve its bytes. Inspect actual bounds, topology, degenerate geometry, normals and mating features. Merge coincident vertices only with explicitly recorded small mm tolerance, repair normals/degeneracy and export a distinct binary STL at {str(absolute_output / 'repaired_mesh.stl')!r}, <=80000 triangles. Keep original dimensions/features. Compare socket-up orientation with the source orientation and describe actual support consequences, including the raised hub; never promise zero supports from appearance. Retain a real geometry-only preview at {str(absolute_output / 'mesh-preview.png')!r}; it is not a support/toolpath preview. Measure post-transform bounds and topology. Use guarded bpy/bmesh/mathutils modelling, render, STL import/export only, with no raw filesystem/network/process APIs or unrelated object deletion. Return compact actual before/after measurements, applied repair/transform and remaining review limits. Fail if closed manifold geometry or intended features cannot be preserved.",
        "mesh-repair-report.json",
        server=geometry,
        expected=("repaired_mesh.stl", "mesh-preview.png"),
        calls=2,
    )
    flow.reference(
        create["id"] + ".source_mesh", repair, "actual_source", "workspace_file"
    )
    flow.reference(source_result, repair, "construction_report")
    flow.reference(requirements_ref, repair, "requirements")
    repaired_roles = flow.file_outputs(
        repair,
        {
            "repaired_mesh": flow.output + "/repaired_mesh.stl",
            "mesh_preview": flow.output + "/mesh-preview.png",
        },
    )
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
        "slice-call.json", (json.dumps(arguments, indent=2) + "\n").encode()
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
            role: flow.input_root + "/" + role + "-profile.json" for role in profiles
        },
        "gcode_entry": "Metadata/plate_1.gcode",
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
                    "input_content": input_content,
                    "job_name": flow.relative + "/package-inspection",
                    "critic_approved": False,
                },
                indent=2,
            )
            + "\n"
        ).encode(),
    )
    argument_port = flow.reference(inspection_call, inspect_step, "exact_arguments")
    flow.exact_mcp(
        inspect_step,
        flow.select(inspection, "run_simulation"),
        argument_port,
        (
            "slice-evidence.json",
            "support-preview.json",
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
        repair["id"] + ".repaired_mesh", inspect_step, "slice_source", "workspace_file"
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
    report = flow.stage(
        "summarize_preparation",
        "Record measured preparation facts and outstanding engineering review",
    )
    report_result = flow.ai(
        report,
        "Use inspect_file to read the actual geometry reports, slice evidence and recorded package/mesh hashes. Summarize construction, socket interpretation, repair, orientation/support consequences, exact PETG settings and nominal toolpaths. Separate design values from measured dimensions and future physical fit. The preview is nominal toolpath data, not completed printing. Retain all original mandatory limits and unresolved review requirements. Do not invent measurements, successful printing, fit, strength or a critic/human verdict.",
        "source-report.json",
        server=files,
        calls=8,
    )
    for reference, key in [
        (source_result, "construction"),
        (repair_result, "repair"),
        (inspect_step["id"] + ".slice_evidence", "slice_evidence"),
        (inspect_step["id"] + ".support_preview", "support_preview"),
    ]:
        flow.reference(
            reference,
            report,
            key,
            "workspace_file"
            if key in ("slice_evidence", "support_preview")
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
    flow.reference(
        slice_step["id"] + ".slice_package", transfer, "exact_package", "workspace_file"
    )
    flow.reference(report_result, transfer, "preparation_review")
    for role, reference in profiles.items():
        flow.reference(reference, transfer, role + "_profile")
    sources = {
        **source_roles,
        "repaired_mesh": repaired_roles["repaired_mesh"],
        **slice_roles,
        **inspect_roles,
        **report_roles,
        "transfer_receipt": (transfer, "receipt", "workspace_file"),
    }
    validator = flow.validator("printed-replacement-part-01", sources)
    final_review = flow.stage(
        "review_preparation",
        "Review final digital preparation and exact engineering findings",
    )
    flow.review(
        final_review,
        "Review the original socket, grip, orientation/support, tolerance and action-scope requirements against exact outputs. This process cannot certify fit, strength, accuracy or a physical print.",
    )
    flow.reference(validator["id"] + ".assessment", final_review, "assessment")
    return flow.save(
        [
            basis,
            basis_review,
            create,
            repair,
            slice_step,
            response_step,
            inspect_step,
            report,
            transfer,
            validator,
            final_review,
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
