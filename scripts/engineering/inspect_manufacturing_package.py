"""Passive inspection of an actual geometry/package handoff.

Run through a configured existing engineering Python provider. This operation
does not slice, execute machine commands, transfer files, or approve a design.
The caller supplies the qualified provider's success contract and the existing
Wright passive toolpath reader; provider protocols remain external.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def run(config, read_toolpaths):
    workspace = Path(config["workspace_root"]).resolve(strict=True)

    def path(relative):
        candidate = (workspace / relative).resolve(strict=True)
        if not candidate.is_relative_to(workspace) or not candidate.is_file():
            raise ValueError(
                "Inspection input must be a file in its declared workspace"
            )
        return candidate

    def read(relative, maximum=32 * 1024 * 1024):
        source = path(relative)
        if not 0 < source.stat().st_size <= maximum:
            raise ValueError("Inspection input exceeds its explicit read bound")
        return source.read_bytes()

    def sha(raw):
        return hashlib.sha256(raw).hexdigest()

    response_raw = read(config["provider_response"], 1024 * 1024)
    response = json.loads(response_raw)
    # Wright retains structured content directly, or the standard MCP content
    # envelope. The selected provider returns exactly one JSON text block.
    if isinstance(response, dict) and "content" in response:
        content = response["content"]
        if (
            response.get("isError", False) is not False
            or not isinstance(content, list)
            or len(content) != 1
            or not isinstance(content[0], dict)
            or content[0].get("type") != "text"
            or not isinstance(content[0].get("text"), str)
        ):
            raise ValueError(
                "The recorded provider response has an unsupported MCP envelope"
            )
        response = json.loads(content[0]["text"])
    if (
        not isinstance(response, dict)
        or response.get(config["success_field"]) is not True
    ):
        raise ValueError("The qualified provider did not report a successful slice")
    if any(
        response.get(field) != expected
        for field, expected in config["expected_response_fields"].items()
    ):
        raise ValueError(
            "Provider response does not identify the configured geometry/package"
        )
    mesh = read(config["source_mesh"])
    package = read(config["slice_package"])
    package_digest = sha(package)
    view = read_toolpaths(
        package,
        package_digest,
        entry=config["gcode_entry"],
        **(
            {"section": config["nominal_layer_section"]}
            if config.get("nominal_layer_section") is not None
            else {}
        ),
    )
    if not view.get("layers"):
        raise ValueError("No actual layered extrusion paths were observed")
    output = (workspace / config["output_root"]).resolve(strict=True)
    if not output.is_relative_to(workspace) or not output.is_dir():
        raise ValueError("Inspection output must remain inside its declared workspace")

    def publish(filename, value):
        raw = (
            json.dumps(
                value, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            )
            + "\n"
        ).encode()
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("Derived inspection exceeds its output bound")
        with (output / filename).open("xb") as stream:
            stream.write(raw)
        return {
            "path": config["output_root"] + "/" + filename,
            "sha256": sha(raw),
            "bytes": len(raw),
        }

    if set(config["profiles"]) != {"machine", "process", "filament"}:
        raise ValueError("Exactly the three configured profile roles are required")
    profile_bytes = {
        role: read(reference, 1024 * 1024)
        for role, reference in config["profiles"].items()
    }
    destinations = [
        "slice-evidence.json",
        "support-preview.json",
        *[role + "-profile.json" for role in profile_bytes],
    ]
    if any((output / name).exists() for name in destinations):
        raise ValueError(
            "Choose a fresh inspection output; existing evidence is retained"
        )
    retained_profiles = {}
    for role, raw in profile_bytes.items():
        with (output / (role + "-profile.json")).open("xb") as stream:
            stream.write(raw)
        retained_profiles[role] = {
            "path": config["output_root"] + "/" + role + "-profile.json",
            "sha256": sha(raw),
        }

    evidence = {
        "operation": config["operation_label"],
        "simulation": False,
        "exit_code": 0,
        "exit_code_basis": config["success_contract"],
        "provider_response_sha256": sha(response_raw),
        "source_sha256": sha(mesh),
        "package_sha256": package_digest,
        "profiles": retained_profiles,
        "engineering_acceptance": False,
    }
    return {
        "method": "Passive recorded-package inspection; no slicer or machine command executed",
        "slice_evidence": publish("slice-evidence.json", evidence),
        "support_preview": publish("support-preview.json", view),
        "engineering_acceptance": False,
    }
