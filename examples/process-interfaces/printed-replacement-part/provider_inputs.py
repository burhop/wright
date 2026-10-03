"""Freeze optional qualified provider inputs; never execute their code locally."""

import hashlib
import json
from pathlib import Path


def qualified_geometry_inputs(bindings):
    from workspace_service.workflow_run_paths import TOKEN, VERSION

    mode = bindings.get("geometry_operation_mode", "ai_task")
    if not isinstance(mode, str) or mode not in ("ai_task", "configured_tool"):
        raise ValueError("Select the supported geometry operation mode explicitly")
    version = bindings.get("run_path_template", "")
    if version not in ("", VERSION):
        raise ValueError("Declare the supported run-path version before staging geometry inputs")
    selected = bindings.get("geometry_operation_files")
    if selected is None:
        if mode == "configured_tool":
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
