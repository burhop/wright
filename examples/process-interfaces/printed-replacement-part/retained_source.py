"""Prepare a new digital consumer of retained geometry, never replay its producer."""

import hashlib
import json
from pathlib import Path
import re
import struct


def qualify(bindings):
    selected = bindings.get("retained_geometry_source")
    if selected is None:
        return None
    if not isinstance(selected, dict) or set(selected) != {
        "mesh",
        "observations",
        "origin",
    }:
        raise ValueError(
            "Pin the retained mesh, actual observations and producer origin"
        )
    if not bindings.get("geometry_operation_files"):
        raise ValueError(
            "Retained geometry requires an explicit qualified repair operation"
        )
    result = {}
    for role, reference in selected.items():
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
            raise ValueError("Pin each retained source path and SHA-256")
        path = Path(reference["path"])
        limit = 4_000_084 if role == "mesh" else 65536
        if not path.is_file() or path.stat().st_size > limit:
            raise ValueError("Retained source inputs must be bounded regular files")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != reference["sha256"]:
            raise ValueError("Retained source input changed: " + role)
        result[role] = (raw, str(path))
    mesh = result["mesh"][0]
    if len(mesh) < 84:
        raise ValueError("Retain an actual bounded binary STL")
    triangles = struct.unpack_from("<I", mesh, 80)[0]
    if not 0 < triangles <= 80000 or len(mesh) != 84 + 50 * triangles:
        raise ValueError("Retain an actual bounded binary STL")
    observations = json.loads(result["observations"][0])
    origin = json.loads(result["origin"][0])
    required = {
        "producer_run_id",
        "producer_source_path",
        "producer_source_sha256",
        "producer_status",
        "mesh_sha256",
        "observations_sha256",
        "engineering_acceptance",
    }
    if (
        not isinstance(observations, dict)
        or not observations
        or not isinstance(origin, dict)
        or set(origin) != required
        or not isinstance(origin["producer_run_id"], str)
        or not origin["producer_run_id"]
        or not isinstance(origin["producer_source_path"], str)
        or not origin["producer_source_path"].startswith("workflows/")
        or not isinstance(origin["producer_source_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", origin["producer_source_sha256"])
        or origin["producer_status"] not in {"failed", "succeeded", "cancelled"}
        or origin["engineering_acceptance"] is not False
        or origin["mesh_sha256"] != hashlib.sha256(mesh).hexdigest()
        or origin["observations_sha256"]
        != hashlib.sha256(result["observations"][0]).hexdigest()
    ):
        raise ValueError(
            "Retained producer origin must bind the nonaccepted actual inputs"
        )
    return result


def configure(flow, retained, qualified_geometry, create, repair, report):
    """Reuse supplied file evidence through the existing exact MCP/file-dependency path."""
    refs = {}
    for role, filename, kind in (
        ("mesh", "retained-source.stl", "workspace_file"),
        (
            "observations",
            "retained-construction-observations.json",
            "engineering_document",
        ),
        ("origin", "retained-producer-origin.json", "engineering_document"),
    ):
        raw, original = retained[role]
        refs[role] = flow.input_bytes(filename, raw, original=original, kind=kind)
    old_mesh = create["id"] + ".source_mesh"
    old_result = create["id"] + "." + create["id"] + "_result"
    preserved = []
    for section in flow.sections:
        if section is create:
            continue
        if section["kind"] == "connection":
            fields = section["fields"]
            if fields["to"].split(".")[0] in {create["id"], repair["id"]}:
                continue
            if fields["from"] == old_mesh:
                fields["from"] = refs["mesh"]
            elif fields["from"] == old_result:
                fields["from"] = refs["observations"]
            elif fields["from"] == create["id"]:
                continue
        preserved.append(section)
    flow.sections = preserved
    repair["fields"]["inputs"] = []
    operation = flow.input_bytes(
        "retained-repair-call.json",
        qualified_geometry["repair"][0],
        original=qualified_geometry["repair"][1],
    )
    argument_port = flow.reference(operation, repair, "exact_arguments")
    flow.exact_mcp(
        repair,
        flow.select(repair["fields"]["settings"]["mcp_server"], "execute_blender_code"),
        argument_port,
        ("source_mesh.stl", "repaired_mesh.stl", "mesh-preview.png"),
        "mesh-repair-report.json",
    )
    source_port = flow.reference(
        refs["mesh"], repair, "actual_source", "workspace_file"
    )
    repair["fields"]["settings"]["mcp_file_dependencies"] = {
        source_port: flow.input_root + "/retained-source.stl"
    }
    repair["fields"]["settings"]["timeout_seconds"] = 360
    flow.file_outputs(
        repair,
        {
            "source_mesh": flow.output + "/source_mesh.stl",
            "repaired_mesh": flow.output + "/repaired_mesh.stl",
            "mesh_preview": flow.output + "/mesh-preview.png",
        },
    )
    flow.reference(refs["origin"], report, "retained_producer_origin")
    report["fields"]["prompt"] += (
        " Construction belongs to the supplied retained producer, not this consumer. "
        "Describe its exact run/source/artifact lineage and terminal status without "
        "claiming the failed producer completed. This run performs new repair/slicing "
        "and full original assessment; input origin records are supplied evidence, "
        "not authenticated engineering acceptance."
        " The repair operation must actually import the retained STL and export the "
        "unmodified imported geometry as this consumer's source_mesh.stl before repair. "
        "That native export is derived geometry, not byte identity with the retained STL."
    )
    for section in flow.sections:
        if section["kind"] == "workflow":
            section["fields"]["name"] += " — retained geometry consumer"
    connected = {
        section["fields"][endpoint].split(".")[0]
        for section in flow.sections
        if section["kind"] == "connection"
        for endpoint in ("from", "to")
    }
    # Construction-only inputs have no runtime consumer in this new process.
    # Their staged bytes remain in the preparation's input/provenance inventory.
    flow.sections = [
        section
        for section in flow.sections
        if section["kind"] != "input" or section["id"] in connected
    ]
    return {"source_mesh": (repair, "source_mesh", "workspace_file")}
