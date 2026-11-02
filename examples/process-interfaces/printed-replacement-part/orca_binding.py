"""Explicit authored Orca binding; not a vendor adapter or execution authority."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

from core.process_validation import ValidationProfile

KIND = "orca-shell-3mf-v1"
ROTATIONS = {
    "pads_down": [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
    "side": [[1, 0, 0], [0, 0, 1], [0, -1, 0]],
}
CENTER = [128, 128]
EFFECTIVE = {
    "printer_model": "Bambu Lab P1S",
    "nozzle_diameter": ["0.4"],
    "layer_height": "0.2",
    "wall_loops": "5",
    "sparse_infill_density": "40%",
    "filament_type": ["PETG"],
    "enable_support": "1",
    "support_type": "tree(auto)",
    "tree_support_wall_count": "0",
}


def qualify(bindings, scenario_id):
    selected = bindings.get("slice_binding")
    if selected is None:
        return None
    required = {
        "kind",
        "engine_version",
        "executable",
        "workspace_mount",
        "selected_orientation",
        "original_process_profile",
    }
    if not isinstance(selected, dict) or set(selected) != required:
        raise ValueError("Declare the exact versioned slice_binding fields")
    if (
        scenario_id != "printed-replacement-part-02"
        or selected["kind"] != KIND
        or selected["engine_version"] != "2.4.2"
        or selected["executable"] != "/opt/orca/AppRun"
        or not isinstance(selected["selected_orientation"], str)
        or selected["selected_orientation"] not in ROTATIONS
    ):
        raise ValueError(
            "Unsupported scenario, engine, executable or orientation binding"
        )
    mount = selected["workspace_mount"]
    if (
        not isinstance(mount, str)
        or not re.fullmatch(r"/[A-Za-z0-9_/-]+", mount)
        or ".." in mount.split("/")
    ):
        raise ValueError("Declare the selected slicer workspace mount")
    reference = selected["original_process_profile"]
    if (
        not isinstance(reference, dict)
        or set(reference) != {"path", "sha256"}
        or not isinstance(reference.get("path"), str)
        or not isinstance(reference.get("sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", reference["sha256"]) is None
    ):
        raise ValueError(
            "Pin the original process profile before the explicit engine mapping"
        )
    paths = [Path(reference["path"]), Path(bindings["profiles"]["process"]["path"])]
    if any(not p.is_file() or not 0 < p.stat().st_size <= 1024 * 1024 for p in paths):
        raise ValueError("Profile input exceeds its explicit bound")
    raw, candidate = [p.read_bytes() for p in paths]
    if len(raw) > 1024 * 1024 or hashlib.sha256(raw).hexdigest() != reference["sha256"]:
        raise ValueError("Original process profile changed")
    original = json.loads(raw)
    if (
        not isinstance(original, dict)
        or original.get("tree_support_wall_count") != "-1"
    ):
        raise ValueError("Declare the original automatic support-wall profile")
    mapped = {**original, "tree_support_wall_count": "0"}
    if json.loads(candidate) != mapped:
        raise ValueError(
            "Only the declared automatic support-wall mapping is permitted"
        )
    return {
        **selected,
        "workspace_mount": mount.rstrip("/"),
        "original_process_bytes": raw,
        "mapped_process_sha256": hashlib.sha256(candidate).hexdigest(),
        "profile_mapping": {
            "tree_support_wall_count": {
                "original": "-1",
                "selected": "0",
                "meaning": "automatic support wall count",
            }
        },
    }


def arguments(flow, binding, input_path, output_root):
    mount = binding["workspace_mount"]
    return {
        "command": [
            binding["executable"],
            "--debug",
            "2",
            "--datadir",
            "/tmp/orca-data",
            "--load-settings",
            mount + "/" + flow.input_root + "/machine-profile.json",
            "--load-settings",
            mount + "/" + flow.input_root + "/process-profile.json",
            "--load-filaments",
            mount + "/" + flow.input_root + "/filament-profile.json",
            "--slice",
            "0",
            "--mstpp",
            "45",
            "--export-3mf",
            "slice_package.gcode.3mf",
            "--export-settings",
            mount + "/" + output_root + "/effective-settings.json",
            "--outputdir",
            mount + "/" + output_root,
            mount + "/" + input_path,
        ],
        "directory": mount,
        "timeout": 60,
    }


def derived_profile(original, orientation):
    value = deepcopy(original)
    value["id"] = "printed-replacement-part-02-orca-2_4_2-" + orientation.replace(
        "_", "-"
    )
    value["version"] = "1"
    lineage = next(c for c in value["checks"] if c["id"] == "slice-lineage")
    lineage["parameters"].update(
        expected_operation="actual_local_orca_slice", prepared_role="prepared_3mf"
    )
    lineage["parameters"]["related_roles"].append("prepared_3mf")

    def add(identity, role, reader, selector, expected, requirements, parameters=None):
        value["checks"].append(
            dict(
                id=identity,
                version="1",
                requirement_ids=requirements,
                subject_role=role,
                reader=reader,
                selector=selector,
                constraint={"operator": "equals", "expected": expected},
                evidence_method="independent_measurement"
                if reader == "printing"
                else "structured_value",
                parameters=parameters or {},
            )
        )

    add(
        "prepared-geometry-lineage",
        "slice_package",
        "printing",
        "package/model-correspondence",
        True,
        ["PRINT02-MESH-LINEAGE", "PRINT02-ORIENTATION"],
        {
            "operation": "prepared_mesh_correspondence",
            "related_roles": ["repaired_mesh", "prepared_3mf"],
            "rotation": ROTATIONS[orientation],
            "build_center_xy_mm": CENTER,
            "tolerance_mm": 1e-4,
        },
    )
    add(
        "actual-engine-header",
        "slice_package",
        "printing",
        "package/engine-header",
        True,
        ["PRINT02-SLICE"],
        {
            "operation": "package_text_prefix",
            "entry": "Metadata/plate_1.gcode",
            "prefix": "; generated by OrcaSlicer 2.4.2 on ",
        },
    )
    add(
        "native-result-success",
        "native_result",
        "structured",
        "/return_code",
        0,
        ["PRINT02-SLICE"],
    )
    for name, expected in EFFECTIVE.items():
        add(
            "effective-" + name.replace("_", "-"),
            "effective_settings",
            "structured",
            "/" + name,
            expected,
            ["PRINT02-SLICE"],
        )
    other = "side" if orientation == "pads_down" else "pads_down"
    for check in list(value["checks"]):
        if check["id"] != "slice-package-inventory" and check["id"] in {
            item["id"] for item in original["checks"]
        }:
            continue
        clone = deepcopy(check)
        clone["id"] = "comparison-" + clone["id"]
        clone["subject_role"] = "comparison_" + clone["subject_role"]
        if clone["parameters"].get("operation") == "prepared_mesh_correspondence":
            clone["parameters"].update(
                rotation=ROTATIONS[other],
                prepared_role="comparison_prepared_3mf",
                related_roles=["repaired_mesh", "comparison_prepared_3mf"],
            )
        value["checks"].append(clone)
    return ValidationProfile.model_validate(value)


def amend_validator(flow, definition, validator, original, binding, extra_sources):
    selected = derived_profile(original, binding["selected_orientation"])
    profile_ref = flow.input_bytes(
        "orca-full-profile.json",
        selected.model_dump_json(indent=2).encode(),
        kind="workspace_file",
    )
    settings = validator["fields"]["settings"]["validation"]
    settings["profile"] = {
        "source": "workspace",
        "name": flow.input_root + "/orca-full-profile.json",
        "reference": selected.reference().model_dump(mode="json"),
    }
    settings["baseline"] = selected.baseline.reference().model_dump(mode="json")
    for role, (producer, key, kind) in extra_sources.items():
        settings["subjects"][role] = flow.reference(
            producer["id"] + "." + key, validator, "validate_" + role, kind
        )
    original_ref = (
        ValidationProfile.model_validate(original).reference().model_dump(mode="json")
    )
    original_resource = "packages/workspace_service/src/workspace_service/process_validation/profiles/printed-replacement-part-02.json"
    original_path = definition.resource(original_resource)
    original_validation_ref = flow.input_bytes(
        "original-validation-profile.json",
        original_path.read_bytes(),
        original=original_resource,
        kind="workspace_file",
    )
    metadata = {
        key: value for key, value in binding.items() if key != "original_process_bytes"
    }
    metadata.update(
        original_validation_profile=original_ref,
        derived_validation_profile=selected.reference().model_dump(mode="json"),
        baseline=selected.baseline.reference().model_dump(mode="json"),
        operation="actual_local_orca_slice",
        engineering_acceptance=False,
    )
    metadata_ref = flow.input_bytes(
        "orca-binding.json", (json.dumps(metadata, indent=2) + "\n").encode()
    )
    original_profile_ref = flow.input_bytes(
        "original-process-profile.json",
        binding["original_process_bytes"],
        original=binding["original_process_profile"]["path"],
        kind="workspace_file",
    )
    return [
        (original_validation_ref, "original_validation_profile", "workspace_file"),
        (profile_ref, "selected_validation_profile", "workspace_file"),
        (metadata_ref, "explicit_engine_binding", "engineering_document"),
        (
            original_profile_ref,
            "original_process_before_engine_mapping",
            "workspace_file",
        ),
    ]
