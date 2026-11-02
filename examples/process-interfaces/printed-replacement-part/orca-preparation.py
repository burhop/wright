"""Accepted standard-format preparation and passive inspection operations.

Executed only by a declared existing external Python capability. No slicer,
machine command, workflow executor or approval is implemented here.
"""

import hashlib
import io
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def locations(config):
    root = Path(config["workspace_root"]).resolve(strict=True)

    def path(relative, *, existing=True):
        value = (root / relative).resolve(strict=existing)
        if not value.is_relative_to(root):
            raise ValueError("Keep operation files in the declared workspace")
        return value

    def read(relative, maximum=64 * 1024 * 1024):
        value = path(relative)
        if not value.is_file() or not 0 < value.stat().st_size <= maximum:
            raise ValueError("Operation input exceeds its explicit bound")
        return value.read_bytes()

    def write(relative, raw):
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("Operation output exceeds its explicit bound")
        value = path(relative, existing=False)
        value.parent.mkdir(parents=True, exist_ok=True)
        with value.open("xb") as stream:
            stream.write(raw)
        return dict(path=relative, sha256=sha(raw), bytes=len(raw))

    return read, write


def encode(value):
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode()


def prepare(config, geometry):
    read, write = locations(config)
    raw = read(config["source_mesh"])
    triangles = geometry["stl_triangles"](raw)
    matrix = geometry["expected_transform"](
        triangles, config["rotation"], config["build_center_xy_mm"]
    )
    ns = geometry["CORE"]
    ET.register_namespace("", ns)

    def tag(name):
        return "{" + ns + "}" + name

    model = ET.Element(tag("model"), {"unit": "millimeter"})
    resources = ET.SubElement(model, tag("resources"))
    # Original profile requires object_1.model in the native output. Actual
    # provider execution must confirm that member; the check is never relaxed.
    obj = ET.SubElement(
        resources, tag("object"), {"id": "1", "type": "model", "name": "object"}
    )
    mesh = ET.SubElement(obj, tag("mesh"))
    vertices = list(dict.fromkeys(p for t in triangles for p in t))
    index = {p: i for i, p in enumerate(vertices)}
    vertex_nodes = ET.SubElement(mesh, tag("vertices"))
    for point in vertices:
        ET.SubElement(
            vertex_nodes,
            tag("vertex"),
            dict(zip(("x", "y", "z"), (format(v, ".17g") for v in point))),
        )
    face_nodes = ET.SubElement(mesh, tag("triangles"))
    for face in triangles:
        ET.SubElement(
            face_nodes,
            tag("triangle"),
            dict(zip(("v1", "v2", "v3"), (str(index[p]) for p in face))),
        )
    build = ET.SubElement(model, tag("build"))
    ET.SubElement(
        build,
        tag("item"),
        {
            "objectid": "1",
            "transform": " ".join(format(v, ".17g") for row in matrix for v in row[:3]),
        },
    )
    types = b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    relations = b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    stream = io.BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        for name, content in [
            ("[Content_Types].xml", types),
            ("_rels/.rels", relations),
            (
                "3D/3dmodel.model",
                ET.tostring(model, encoding="utf-8", xml_declaration=True),
            ),
        ]:
            info = ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            archive.writestr(info, content)
    prepared = stream.getvalue()
    facts = geometry["correspondence"](
        raw, prepared, prepared, config["rotation"], config["build_center_xy_mm"]
    )
    output = config["output_root"]
    result = dict(
        source_sha256=sha(raw),
        prepared_sha256=sha(prepared),
        orientation=config["orientation"],
        geometry=facts,
        engineering_acceptance=False,
    )
    write(output + "/prepared-model.3mf", prepared)
    write(output + "/preparation-evidence.json", encode(result))
    return result


def inspect(config, geometry, read_toolpaths):
    read, write = locations(config)
    source = read(config["source_mesh"])
    output = config["output_root"]
    prepared = read(output + "/prepared-model.3mf")
    package = read(output + "/slice_package.gcode.3mf")
    response_raw = read(output + "/slice-provider-response.json", 1024 * 1024)
    response = json.loads(response_raw)
    # The existing gateway retains {content:[...]} for unstructured MCP output;
    # it records isError separately and rejects true before publishing this result.
    # Text (including warnings) supplies no native success verdict.
    if (
        not isinstance(response, dict)
        or response.get("isError", False) is not False
        or not isinstance(response.get("content"), list)
        or any(
            not isinstance(item, dict)
            or item.get("type") != "text"
            or not isinstance(item.get("text"), str)
            for item in response["content"]
        )
    ):
        raise ValueError("Unsupported retained shell MCP response")
    native_raw = read(output + "/result.json", 1024 * 1024)
    native = json.loads(native_raw)
    if type(native.get("return_code")) is not int or native["return_code"] != 0:
        raise ValueError("The actual native result does not report success")
    effective_raw = read(output + "/effective-settings.json", 1024 * 1024)
    effective = json.loads(effective_raw)
    if any(
        effective.get(key) != value
        for key, value in config["effective_settings"].items()
    ):
        raise ValueError(
            "Actual effective slicer settings differ from the accepted profile"
        )
    facts = geometry["correspondence"](
        source, prepared, package, config["rotation"], config["build_center_xy_mm"]
    )
    gcode = geometry["archive_members"](package)["Metadata/plate_1.gcode"].decode(
        "utf-8"
    )
    if not any(
        line.startswith(config["engine_header"]) for line in gcode.splitlines()[:32]
    ):
        raise ValueError(
            "Actual package does not identify the selected engine revision"
        )
    view = read_toolpaths(
        package,
        sha(package),
        entry="Metadata/plate_1.gcode",
        section=config["nominal_layer_section"],
    )
    if not view.get("layers"):
        raise ValueError("No actual nominal layered paths were observed")
    profiles = {}
    for role, reference in config["profiles"].items():
        raw = read(reference, 1024 * 1024)
        if sha(raw) != config["profile_sha256"][role]:
            raise ValueError("Configured profile identity changed")
        profiles[role] = write(output + "/" + role + "-profile.json", raw)
    evidence = dict(
        operation="actual_local_orca_slice",
        simulation=False,
        exit_code=native["return_code"],
        exit_code_basis="Exact native result.json return_code, separately from retained MCP text",
        source_sha256=sha(source),
        prepared_sha256=sha(prepared),
        package_sha256=sha(package),
        provider_response_sha256=sha(response_raw),
        native_result_sha256=sha(native_raw),
        effective_settings_sha256=sha(effective_raw),
        profiles=profiles,
        geometry=facts,
        orientation=config["orientation"],
        engineering_acceptance=False,
    )
    preview = write(output + "/support-preview.json", encode(view))
    summary = dict(
        format="wright.gcode.toolpath-summary.v1",
        source_view=preview,
        package_sha256=sha(package),
        source_sha256=sha(source),
        prepared_sha256=sha(prepared),
        orientation=config["orientation"],
        layer_count=len(view["layers"]),
        provenance=view["provenance"],
        geometry=facts,
        path_segments={
            kind: sum(len(layer[kind]) for layer in view["layers"])
            for kind in ("model", "support", "unclassified")
        },
        path_length_mm={
            kind: sum(
                math.hypot(c - a, d - b)
                for layer in view["layers"]
                for a, b, c, d in layer[kind]
            )
            for kind in ("model", "support", "unclassified")
        },
        nominal_path_frame="G-code coordinates; not original model coordinates",
        configured_extruder_offset=effective.get("extruder_offset"),
        reported_usage=[
            line
            for line in gcode.splitlines()
            if line.startswith(("; filament used [", "; model printing time:"))
        ][:8],
        engineering_acceptance=False,
    )
    return dict(
        slice_evidence=write(output + "/slice-evidence.json", encode(evidence)),
        support_preview=preview,
        toolpath_summary=write(output + "/toolpath-summary.json", encode(summary)),
        engineering_acceptance=False,
    )


def compare(config):
    read, write = locations(config)
    cases = {}
    for name, output in config["cases"].items():
        summary = json.loads(read(output + "/toolpath-summary.json", 65536))
        if (
            summary["source_sha256"] != sha(read(config["source_mesh"]))
            or summary["package_sha256"]
            != sha(read(output + "/slice_package.gcode.3mf"))
            or summary["prepared_sha256"] != sha(read(output + "/prepared-model.3mf"))
            or summary["source_view"]["sha256"]
            != sha(read(output + "/support-preview.json"))
        ):
            raise ValueError(
                "Orientation comparison no longer matches its exact inputs"
            )
        cases[name] = summary
    result = dict(
        cases=cases,
        selected_orientation=config["selected_orientation"],
        engineering_acceptance=False,
        physical_acceptance=False,
    )
    write(config["output_root"] + "/orientation-comparison.json", encode(result))
    return result
