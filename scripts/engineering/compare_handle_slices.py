"""Passive two-orientation comparison for the existing Printed02 handle example.

The selected independent Python provider executes this workflow operation. It
uses Wright's existing package inspector; it never slices, prints or approves.
"""

import hashlib
import json
from pathlib import Path


def _read(root, relative, maximum=64 * 1024 * 1024):
    path = (root / relative).resolve(strict=True)
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Comparison input must stay inside the workspace")
    if not 0 < path.stat().st_size <= maximum:
        raise ValueError("Comparison input exceeds its read bound")
    return path.read_bytes()


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _publish(root, relative, raw):
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or not path.parent.is_dir():
        raise ValueError("Selection output needs a declared workspace directory")
    with path.open("xb") as stream:
        stream.write(raw)
    return {"path": relative, "sha256": _sha(raw), "bytes": len(raw)}


def inspect_alternatives(config, inspect_package, read_toolpaths):
    """Publish measured facts before a separate selection decision is supplied."""
    root = Path(config["workspace_root"]).resolve(strict=True)
    alternatives = config["alternatives"]
    if set(alternatives) != {"pads_down", "side"}:
        raise ValueError("The handle study requires pads-down and side alternatives")
    if len({(root / a["slice_package"]).resolve() for a in alternatives.values()}) != 2:
        raise ValueError("Each orientation needs its own actual slice package")
    if len({(root / a["source_mesh"]).resolve() for a in alternatives.values()}) != 2:
        raise ValueError("Each orientation needs its exact source mesh")
    if len({(root / a["output_root"]).resolve() for a in alternatives.values()}) != 2:
        raise ValueError("Each inspection needs its own fresh output directory")
    for alternative in alternatives.values():
        selector = alternative.get("provider_observation")
        if not isinstance(selector, dict) or not selector.get("arguments"):
            raise ValueError("Both alternatives require recorded observation selectors")
        # This qualified provider uses the same declared workspace mount for
        # source/output in the invocation and response. No basename guessing.
        for field, role in (("source", "source_mesh"), ("output", "slice_package")):
            expected = (root / alternative[role]).resolve(strict=True)
            for identity in (
                selector["arguments"],
                alternative["expected_response_fields"],
            ):
                value = identity.get(field)
                if (
                    not isinstance(value, str)
                    or (root / value).resolve(strict=True) != expected
                ):
                    raise ValueError(
                        "Observed source/output must identify the inspected mesh/package"
                    )
    destination = (root / config["comparison_output"]).resolve()
    if (
        destination.exists()
        or not destination.is_relative_to(root)
        or not destination.parent.is_dir()
    ):
        raise ValueError("Comparison requires a fresh workspace output")
    comparison = {
        "schema_version": "wright.handle-slice-comparison/1",
        "alternatives": {},
        "engineering_acceptance": False,
        "limitations": [
            "Nominal toolpath segments are not support area or physical strength.",
            "Time and material usage are not inferred from segment counts.",
            "Selection and manufacturing acceptance require the reviewed requirements.",
        ],
    }
    for name, alternative in alternatives.items():
        result = inspect_package(
            {**alternative, "workspace_root": str(root), "legacy_previews": True},
            read_toolpaths,
        )
        evidence = json.loads(_read(root, result["slice_evidence"]["path"]))
        if not evidence.get("provider_observation"):
            raise ValueError(
                "Inspection did not retain the selected observation identity"
            )
        summary = json.loads(_read(root, result["toolpath_summary"]["path"]))
        preview = alternative["output_root"] + "/slice-preview.png"
        comparison["alternatives"][name] = {
            "source_mesh": {
                "path": alternative["source_mesh"],
                "sha256": evidence["source_sha256"],
            },
            "package": {
                "path": alternative["slice_package"],
                "sha256": evidence["package_sha256"],
            },
            "native_preview": {
                "path": preview,
                "sha256": _sha(_read(root, preview, 8 * 1024 * 1024)),
            },
            "inspection": result,
            "observed_layer_count": summary["layer_count"],
            "observed_path_segments": summary["path_segments"],
            "provider_observation": evidence.get("provider_observation"),
        }
    raw = json.dumps(comparison, sort_keys=True, allow_nan=False).encode()
    return {
        "comparison": _publish(root, config["comparison_output"], raw),
        **comparison,
    }


def retain_selection(config):
    """Retain a proposed selection; this never creates engineering approval."""
    root = Path(config["workspace_root"]).resolve(strict=True)
    raw = _read(root, config["comparison"], 1024 * 1024)
    if _sha(raw) != config["comparison_sha256"]:
        raise ValueError("The measured comparison changed before selection")
    comparison = json.loads(raw)
    if comparison.get("schema_version") != "wright.handle-slice-comparison/1":
        raise ValueError("A measured handle comparison is required")
    if config["selected"] not in {"pads_down", "side"}:
        raise ValueError("Select one inspected orientation")
    reason = config.get("rationale")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 8000:
        raise ValueError(
            "Retain a bounded engineering rationale for the proposed selection"
        )
    if (
        set(comparison.get("alternatives", {})) != {"pads_down", "side"}
        or comparison.get("engineering_acceptance") is not False
    ):
        raise ValueError("Both unapproved inspected alternatives are required")
    # A choice relies on both alternatives, not only the retained package.
    for alternative in comparison["alternatives"].values():
        for role in ("source_mesh", "package", "native_preview"):
            reference = alternative[role]
            maximum = 8 * 1024 * 1024 if role == "native_preview" else 64 * 1024 * 1024
            if _sha(_read(root, reference["path"], maximum)) != reference["sha256"]:
                raise ValueError("An inspected file changed before selection")
    selected = comparison["alternatives"][config["selected"]]
    contents = {}
    for role, maximum in (
        ("package", 64 * 1024 * 1024),
        ("native_preview", 8 * 1024 * 1024),
    ):
        reference = selected[role]
        data = _read(root, reference["path"], maximum)
        if _sha(data) != reference["sha256"]:
            raise ValueError("An inspected file changed before selection")
        contents[role] = data
    support_reference = None
    if "support_output" in config:
        # Preserve both alternatives' nominal evidence before publishing a choice.
        for alternative in comparison["alternatives"].values():
            reference = alternative["inspection"]["support_preview"]
            data = _read(root, reference["path"])
            if _sha(data) != reference["sha256"]:
                raise ValueError("Inspected support evidence changed before selection")
        support_reference = selected["inspection"]["support_preview"]
        contents["support"] = _read(root, support_reference["path"])
        if _sha(contents["support"]) != support_reference["sha256"]:
            raise ValueError("Inspected support evidence changed before selection")
    destinations = [
        config[k] for k in ("package_output", "preview_output", "selection_output")
    ]
    if support_reference is not None:
        destinations.append(config["support_output"])
    resolved = [(root / value).resolve() for value in destinations]
    if len(set(resolved)) != len(destinations) or any(
        p.exists() or not p.is_relative_to(root) or not p.parent.is_dir()
        for p in resolved
    ):
        raise ValueError("Selection requires distinct fresh workspace outputs")
    package = _publish(root, config["package_output"], contents["package"])
    preview = _publish(root, config["preview_output"], contents["native_preview"])
    result = {
        "schema_version": "wright.handle-slice-selection/1",
        "comparison": {"path": config["comparison"], "sha256": _sha(raw)},
        "selected_orientation": config["selected"],
        "rationale": reason,
        "decision_kind": "proposed_selection_not_engineering_approval",
        "original_package": selected["package"],
        "retained_package": package,
        "native_preview": preview,
        "engineering_acceptance": False,
    }
    if support_reference is not None:
        result["original_support_evidence"] = support_reference
        result["retained_support_evidence"] = _publish(
            root, config["support_output"], contents["support"]
        )
    result_raw = json.dumps(result, sort_keys=True, allow_nan=False).encode()
    return {
        **result,
        "selection_record": _publish(root, config["selection_output"], result_raw),
    }
