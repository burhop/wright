"""Passive inspection of an actual geometry/package handoff.

Run through a configured existing engineering Python provider. This operation
does not slice, execute machine commands, transfer files, or approve a design.
The caller supplies the qualified provider's success contract and the existing
Wright passive toolpath reader; provider protocols remain external.
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import zipfile


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

    def publish(filename, value, *, maximum_bytes=64 * 1024 * 1024):
        raw = (
            json.dumps(
                value, ensure_ascii=False, separators=(",", ":"), allow_nan=False
            )
            + "\n"
        ).encode()
        if len(raw) > maximum_bytes:
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
        "toolpath-summary.json",
        *[role + "-profile.json" for role in profile_bytes],
    ]
    if any((output / name).exists() for name in destinations):
        raise ValueError(
            "Choose a fresh inspection output; existing evidence is retained"
        )
    legacy = None
    if config.get("legacy_previews"):
        # Preserve historical example representations without a second parser,
        # slicer-specific comments, a fixed bed size or fabricated support mesh.
        populated = [layer for layer in view["layers"]
                     if layer["model"] or layer["support"] or layer["unclassified"]]
        layer = max(populated, key=lambda item: len(item["support"]))
        moves = [segment for kind in ("model", "support", "unclassified")
                 for segment in layer[kind]]
        xs = [coordinate for a, b, c, d in moves for coordinate in (a, c)]
        ys = [-coordinate for a, b, c, d in moves for coordinate in (b, d)]
        left, top = min(xs) - 3, min(ys) - 3
        width, height = max(xs) - left + 3, max(ys) - top + 3

        def paths(segments):
            return " ".join(f"M{a:.3f},{-b:.3f}L{c:.3f},{-d:.3f}"
                            for a, b, c, d in segments)

        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{left:.3f} {top:.3f} {width:.3f} {height:.3f}">'
               f'<path d="{paths(layer["model"])}" fill="none" stroke="#344b5a" stroke-width="0.25"/>'
               f'<path d="{paths(layer["support"])}" fill="none" stroke="#d65012" stroke-width="0.35"/>'
               f'<path d="{paths(layer["unclassified"])}" fill="none" stroke="#777777" stroke-width="0.25"/></svg>').encode()
        preview_entry = config.get("preview_entry", config["gcode_entry"].removesuffix(".gcode") + ".png")
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            members = [item for item in archive.infolist() if item.filename == preview_entry]
            if len(members) != 1 or not 8 <= members[0].file_size <= 8 * 1024 * 1024:
                raise ValueError("Actual package preview is missing, ambiguous or exceeds its bound")
            png = archive.read(members[0])
        if png[:8] != b"\x89PNG\r\n\x1a\n" or len(svg) > 64 * 1024 * 1024:
            raise ValueError("Actual package preview is invalid or exceeds its bound")
        if any((output / name).exists() for name in ("support-preview.svg", "slice-preview.png")):
            raise ValueError("Choose fresh legacy preview outputs; existing evidence is retained")
        legacy = {"support-preview.svg": svg, "slice-preview.png": png}
    retained_profiles = {}
    for role, raw in profile_bytes.items():
        with (output / (role + "-profile.json")).open("xb") as stream:
            stream.write(raw)
        retained_profiles[role] = {
            "path": config["output_root"] + "/" + role + "-profile.json",
            "sha256": sha(raw),
        }
    if legacy is not None:
        for filename, raw in legacy.items():
            with (output / filename).open("xb") as stream:
                stream.write(raw)

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
    preview = publish("support-preview.json", view)
    summary = {
        "format": "wright.gcode.toolpath-summary.v1",
        "source_view": preview,
        "package_sha256": package_digest,
        "layer_count": len(view["layers"]),
        "path_segments": {
            kind: sum(len(layer[kind]) for layer in view["layers"])
            for kind in ("model", "support", "unclassified")
        },
        "provenance": view["provenance"],
        "engineering_acceptance": False,
    }
    return {
        "method": "Passive recorded-package inspection; no slicer or machine command executed",
        "slice_evidence": publish("slice-evidence.json", evidence),
        "support_preview": preview,
        "toolpath_summary": publish(
            "toolpath-summary.json", summary, maximum_bytes=65536
        ),
        "engineering_acceptance": False,
    }
