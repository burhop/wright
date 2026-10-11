"""Freeze optional qualified provider inputs; never execute their code locally."""

import hashlib
import json
import re
from pathlib import Path


def geometry_operation_modes(bindings):
    mode = bindings.get("geometry_operation_mode", "ai_task")
    if not isinstance(mode, str) or mode not in ("ai_task", "configured_tool"):
        raise ValueError("Select the supported geometry operation mode explicitly")
    if "geometry_operation_modes" not in bindings:
        return {"construction": mode, "repair": mode}
    selected = bindings["geometry_operation_modes"]
    if (
        not isinstance(selected, dict)
        or set(selected) != {"construction", "repair"}
        or any(
            not isinstance(value, str) or value not in ("ai_task", "configured_tool")
            for value in selected.values()
        )
    ):
        raise ValueError("Select both supported geometry operation modes explicitly")
    return dict(selected)


def construction_binding(bindings):
    """Select an explicit independent producer without changing repair ownership."""
    selected = bindings.get("construction_binding")
    if selected is None and "construction_binding" not in bindings:
        return {
            "server": bindings["geometry_server"],
            "tool": "execute_blender_code",
            "outputs": {"source_mesh": "source_mesh.stl"},
        }
    if (
        not isinstance(selected, dict)
        or set(selected) != {"server", "tool", "outputs"}
        or any(not isinstance(selected[key], str) or not selected[key].strip()
               for key in ("server", "tool"))
        or geometry_operation_modes(bindings)["construction"] != "configured_tool"
    ):
        raise ValueError("An explicit construction binding requires a configured tool, server, tool and output mapping")
    outputs = selected["outputs"]
    if (
        not isinstance(outputs, dict)
        or outputs.get("source_mesh") != "source_mesh.stl"
        or len(outputs) > 16
        or any(not isinstance(role, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", role)
               or not isinstance(filename, str)
               or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", filename)
               or ".." in filename for role, filename in outputs.items())
        or len(set(outputs.values())) != len(outputs)
        or "source-model-report.json" in outputs.values()
    ):
        raise ValueError("Declare unique bounded construction output filenames and retain source_mesh.stl")
    return {"server": selected["server"], "tool": selected["tool"], "outputs": dict(outputs)}


def qualified_geometry_inputs(bindings):
    from workspace_service.workflow_run_paths import TOKEN, VERSION

    modes = geometry_operation_modes(bindings)
    version = bindings.get("run_path_template", "")
    if version not in ("", VERSION):
        raise ValueError("Declare the supported run-path version before staging geometry inputs")
    selected = bindings.get("geometry_operation_files")
    if selected is None:
        if "configured_tool" in modes.values():
            raise ValueError("Supply the pinned basis and both qualified geometry operations")
        return {}
    if not isinstance(selected, dict) or set(selected) != {
        "basis",
        "construction",
        "repair",
    }:
        raise ValueError(
            "Supply the pinned basis and both qualified geometry operations"
        )
    result = {}
    for role, reference in selected.items():
        if not isinstance(reference, dict) or set(reference) != {"path", "sha256"}:
            raise ValueError("Pin each qualified geometry input path and SHA-256")
        path = Path(reference["path"])
        if not path.is_file() or path.stat().st_size > 65536:
            raise ValueError("Qualified geometry inputs must be bounded regular files")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != reference["sha256"]:
            raise ValueError("Qualified geometry input changed: " + role)
        value = json.loads(raw)
        if role == "basis":
            if (
                not isinstance(value, dict)
                or not isinstance(value.get("proposed_geometry"), dict)
                or not value["proposed_geometry"]
                or value.get("engineering_acceptance") is not False
            ):
                raise ValueError(
                    "The supplied geometry basis must remain a nonaccepted proposal"
                )
        elif (
            not isinstance(value, dict)
            or set(value) != {"code"}
            or not isinstance(value["code"], str)
            or not value["code"].strip()
        ):
            raise ValueError("Supply the selected provider's explicit code argument")
        if role != "basis" and version and TOKEN not in value["code"]:
            raise ValueError(
                "A reusable geometry recipe must explicitly declare its run-id paths; fixed recipes are not rewritten"
            )
        result[role] = (raw, str(path))
    return result
