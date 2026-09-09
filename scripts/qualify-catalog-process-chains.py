"""Run three real product-design chains through Wright's MCP gateway.

This is an opt-in qualification runner. Run it only in a disposable Wright
environment with the prerequisites for the selected curated integrations. The
runner creates temporary engineering artifacts, verifies every handoff and
records hashes and numerical oracles in one evidence document. It never changes
the base image or promotes catalog entries.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager, closing
from datetime import UTC, date, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import struct
import subprocess
import tempfile
import traceback
import xml.etree.ElementTree as ET
import zipfile

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_IDS = (
    "brep-mcp",
    "oasis-open-fem-agent",
    "autocad-mcp-u-c4n",
    "kicad-mcp-blwfish",
    "rosbag-mcp-pypi",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def digest(value: object) -> str:
    return sha256_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    )


def result_text(result) -> str:
    values = []
    for item in result.content:
        value = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
        if value is not None:
            values.append(value)
    return "\n".join(values)


def json_result(result) -> dict:
    payload = json.loads(result_text(result))
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, dict):
        raise AssertionError("Tool did not return a JSON object")
    return payload


@asynccontextmanager
async def client_session(command, env_overrides=None, cwd=None):
    if isinstance(command, str):
        async with httpx.AsyncClient(
            timeout=60, trust_env=False, follow_redirects=False
        ) as http:
            from mcp.client.streamable_http import streamable_http_client

            async with streamable_http_client(command, http_client=http) as (
                read,
                write,
                _,
            ):
                async with ClientSession(read, write) as client:
                    yield client
        return
    child_env = dict(os.environ)
    child_env.update(env_overrides or {})
    async with stdio_client(
        StdioServerParameters(
            command=command[0], args=command[1:], env=child_env, cwd=cwd
        )
    ) as (read, write):
        async with ClientSession(read, write) as client:
            yield client


def inspect_stl(path: Path, expected_dimensions, expected_volume) -> dict:
    raw = path.read_bytes()
    if not 0 < len(raw) < 10 * 1024 * 1024:
        raise AssertionError("Missing or oversized STL")
    if len(raw) >= 84 and 84 + 50 * struct.unpack_from("<I", raw, 80)[0] == len(raw):
        points = [
            struct.unpack_from("<fff", raw, start + 12 + offset * 12)
            for start in range(84, len(raw), 50)
            for offset in range(3)
        ]
    else:
        points = [
            tuple(map(float, values))
            for values in re.findall(
                rb"vertex\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)", raw
            )
        ]
    if len(points) < 36 or len(points) % 3:
        raise AssertionError("STL has no usable triangle mesh")
    dimensions = [
        max(point[axis] for point in points) - min(point[axis] for point in points)
        for axis in range(3)
    ]
    if any(
        abs(actual - expected) > 0.001
        for actual, expected in zip(dimensions, expected_dimensions)
    ):
        raise AssertionError(f"Unexpected STL dimensions: {dimensions}")
    volume = 0.0
    for offset in range(0, len(points), 3):
        a, b, c = points[offset : offset + 3]
        volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6
    volume = abs(volume)
    if abs(volume - expected_volume) > max(0.01, expected_volume * 0.002):
        raise AssertionError(f"Unexpected STL volume: {volume}")
    return {
        "path": path.name,
        "format": "STL",
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "dimensions_mm": dimensions,
        "volume_mm3": volume,
    }


def inspect_step(path: Path) -> dict:
    raw = path.read_bytes()
    if not 500 < len(raw) < 20 * 1024 * 1024:
        raise AssertionError("Missing or oversized STEP artifact")
    if not raw.startswith(b"ISO-10303-21;") or b"END-ISO-10303-21;" not in raw:
        raise AssertionError("Incomplete STEP exchange file")
    return {
        "path": path.name,
        "format": "STEP AP242",
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
    }


def inspect_brep_export(directory: Path, dimensions, expected_volume=None) -> dict:
    stl_files = sorted(directory.glob("*.stl"))
    step_files = sorted([*directory.glob("*.step"), *directory.glob("*.stp")])
    if len(stl_files) != 1 or len(step_files) != 1:
        raise AssertionError("BREP export did not produce one STL and one STEP")
    volume = expected_volume if expected_volume is not None else math.prod(dimensions)
    return {
        "stl": inspect_stl(stl_files[0], dimensions, volume),
        "step": inspect_step(step_files[0]),
    }


def parse_dxf(path: Path) -> dict[str, list[list[tuple[int, str]]]]:
    raw = path.read_bytes()
    if not 500 < len(raw) < 5 * 1024 * 1024:
        raise AssertionError("Missing or oversized DXF")
    lines = raw.decode("utf-8", errors="replace").splitlines()
    if len(lines) % 2:
        raise AssertionError("DXF group-code stream is incomplete")
    pairs = []
    for offset in range(0, len(lines), 2):
        try:
            code = int(lines[offset].strip())
        except ValueError as error:
            raise AssertionError("DXF contains an invalid group code") from error
        pairs.append((code, lines[offset + 1].strip()))
    entities = []
    in_entities = False
    current = None
    for index, pair in enumerate(pairs):
        if pair == (0, "SECTION") and index + 1 < len(pairs):
            in_entities = pairs[index + 1] == (2, "ENTITIES")
            continue
        if in_entities and pair == (0, "ENDSEC"):
            if current:
                entities.append(current)
            break
        if not in_entities:
            continue
        if pair[0] == 0:
            if current:
                entities.append(current)
            current = {"type": pair[1], "pairs": []}
        elif current:
            current["pairs"].append(pair)
    by_type: dict[str, list[list[tuple[int, str]]]] = {}
    for entity in entities:
        by_type.setdefault(entity["type"], []).append(entity["pairs"])
    return by_type


def inspect_dxf(path: Path, *, width, height, holes, centerline) -> dict:
    by_type = parse_dxf(path)
    counts = {key: len(value) for key, value in by_type.items()}
    expected_counts = {"LWPOLYLINE": 1, "CIRCLE": len(holes), "LINE": 1}
    if counts != expected_counts:
        raise AssertionError(f"DXF entity inventory changed: {counts}")
    rectangle = by_type["LWPOLYLINE"][0]
    xs = [float(value) for code, value in rectangle if code == 10]
    ys = [float(value) for code, value in rectangle if code == 20]
    vertices = {(round(x, 6), round(y, 6)) for x, y in zip(xs, ys)}
    expected_vertices = {(0.0, 0.0), (width, 0.0), (width, height), (0.0, height)}
    if vertices != expected_vertices:
        raise AssertionError(f"DXF outline changed: {vertices}")
    circles = set()
    for values in by_type["CIRCLE"]:
        grouped = {code: value for code, value in values if code in {10, 20, 40}}
        circles.add(tuple(round(float(grouped[code]), 6) for code in (10, 20, 40)))
    if circles != set(holes):
        raise AssertionError(f"DXF holes changed: {circles}")
    line = {
        code: value
        for code, value in by_type["LINE"][0]
        if code in {10, 20, 11, 21}
    }
    actual_line = tuple(round(float(line[code]), 6) for code in (10, 20, 11, 21))
    if actual_line != centerline:
        raise AssertionError(f"DXF centerline changed: {actual_line}")
    raw = path.read_bytes()
    return {
        "path": path.name,
        "format": "DXF",
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "entity_counts": counts,
        "outline_mm": [width, height],
        "holes_mm": sorted([list(value) for value in circles]),
        "centerline_mm": list(actual_line),
    }


def inspect_vtu(path: Path, field_name: str, components: int) -> dict:
    raw = path.read_bytes()
    if not 1000 < len(raw) < 20 * 1024 * 1024:
        raise AssertionError("Missing or oversized VTU result")
    tree = ET.fromstring(raw)
    field = next(
        node
        for node in tree.findall(".//{*}PointData/{*}DataArray")
        if node.attrib.get("Name") == field_name
    )
    values = [float(value) for value in (field.text or "").split()]
    points_node = tree.find(".//{*}Points/{*}DataArray")
    if points_node is None:
        raise AssertionError("VTU has no mesh points")
    coordinates = [float(value) for value in (points_node.text or "").split()]
    if len(coordinates) < 300 or len(values) * 3 != len(coordinates) * components:
        raise AssertionError("VTU mesh or result field is incomplete")
    if not all(math.isfinite(value) for value in values + coordinates):
        raise AssertionError("VTU contains non-finite values")
    points = [coordinates[index : index + 3] for index in range(0, len(coordinates), 3)]
    nodal_values = [
        values[index : index + components] for index in range(0, len(values), components)
    ]
    axes = [coordinates[index::3] for index in range(3)]
    outcome = {
        "path": path.name,
        "format": "VTU",
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        "point_count": len(coordinates) // 3,
        "components": components,
        "bounds": [[min(axis), max(axis)] for axis in axes],
        "field": field_name,
        "field_min": min(values),
        "field_max": max(values),
    }
    if field_name == "displacement_m":
        magnitudes = [math.sqrt(sum(value**2 for value in node)) for node in nodal_values]
        fixed = [
            magnitudes[index]
            for index, point in enumerate(points)
            if abs(point[0] - min(axes[0])) < 1e-12
        ]
        if not fixed or max(fixed) > 1e-12:
            raise AssertionError("Structural VTU violates its fixed boundary condition")
        outcome.update(
            field_magnitude_max=max(magnitudes),
            fixed_boundary_magnitude_max=max(fixed),
        )
    elif field_name == "temperature_K":
        boundary = [
            nodal_values[index][0]
            for index, point in enumerate(points)
            if abs(point[0] - min(axes[0])) < 1e-12
            or abs(point[0] - max(axes[0])) < 1e-12
            or abs(point[1] - min(axes[1])) < 1e-12
            or abs(point[1] - max(axes[1])) < 1e-12
        ]
        if not boundary or max(abs(value - 298.15) for value in boundary) > 1e-8:
            raise AssertionError("Thermal VTU violates its ambient boundary condition")
        outcome["boundary_temperature_K"] = [min(boundary), max(boundary)]
    return outcome


def inspect_board(path: Path, *, width_mm, height_mm, reference="R1") -> dict:
    script = r'''import json, pcbnew, sys
board = pcbnew.LoadBoard(sys.argv[1])
box = board.GetBoardEdgesBoundingBox()
footprints = []
for item in board.GetFootprints():
    pos = item.GetPosition()
    footprints.append({
        "reference": item.GetReference(),
        "value": item.GetValue(),
        "x_mm": pcbnew.ToMM(pos.x),
        "y_mm": pcbnew.ToMM(pos.y),
        "pads": item.GetPadCount(),
    })
print(json.dumps({
    "width_mm": pcbnew.ToMM(box.GetWidth()),
    "height_mm": pcbnew.ToMM(box.GetHeight()),
    "footprints": footprints,
}))
'''
    process = subprocess.run(
        ["/usr/bin/python3", "-c", script, str(path)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    payload = json.loads(process.stdout)
    if abs(payload["width_mm"] - width_mm) > 0.2 or abs(
        payload["height_mm"] - height_mm
    ) > 0.2:
        raise AssertionError(f"Unexpected KiCad board envelope: {payload}")
    match = next(
        (item for item in payload["footprints"] if item["reference"] == reference), None
    )
    if match is None or match["pads"] != 2:
        raise AssertionError("Expected two-pad validation footprint is missing")
    if abs(match["x_mm"] - width_mm / 2) > 0.001 or abs(
        match["y_mm"] - height_mm / 2
    ) > 0.001:
        raise AssertionError("Validation footprint is not at the expected board center")
    raw = path.read_bytes()
    return {
        "path": path.name,
        "format": "KiCad PCB",
        "bytes": len(raw),
        "sha256": sha256_bytes(raw),
        **payload,
    }


def inspect_fabrication(directory: Path, board_stem: str) -> dict:
    gerber_extensions = {
        ".gbr",
        ".gtl",
        ".gbl",
        ".gta",
        ".gba",
        ".gtp",
        ".gbp",
        ".gto",
        ".gbo",
        ".gts",
        ".gbs",
        ".gm1",
    }
    gerbers = sorted(
        path for path in directory.iterdir() if path.suffix in gerber_extensions
    )
    drills = sorted(directory.glob("*.drl"))
    archives = sorted(directory.parent.glob(f"{directory.name}*.zip"))
    if len(gerbers) < 3 or not drills or len(archives) != 1:
        raise AssertionError("Incomplete KiCad fabrication package")
    for path in gerbers:
        raw = path.read_bytes()
        if b"%FS" not in raw or b"M02*" not in raw:
            raise AssertionError(f"Invalid Gerber file: {path.name}")
    with zipfile.ZipFile(archives[0]) as archive:
        names = set(archive.namelist())
    expected = {path.name for path in [*gerbers, *drills]}
    if not expected <= names:
        raise AssertionError("Fabrication archive omitted generated files")
    return {
        "board_stem": board_stem,
        "gerber_count": len(gerbers),
        "drill_count": len(drills),
        "archive": archives[0].name,
        "archive_sha256": sha256_file(archives[0]),
        "files": {path.name: sha256_file(path) for path in [*gerbers, *drills]},
    }


async def generate_rosbag(root: Path, topic: str, timestamp_ns: int, payload: dict) -> Path:
    bag = root / "bag"
    source = r'''from pathlib import Path
from rosbags.rosbag2 import Writer
from rosbags.typesys import Stores, get_typestore
import sys

bag = Path(sys.argv[1])
topic = sys.argv[2]
timestamp = int(sys.argv[3])
value = sys.argv[4]
typestore = get_typestore(Stores.ROS2_HUMBLE)
String = typestore.types["std_msgs/msg/String"]
with Writer(bag, version=9) as writer:
    connection = writer.add_connection(topic, String.__msgtype__, typestore=typestore)
    message = String(data=value)
    writer.write(
        connection,
        timestamp,
        typestore.serialize_cdr(message, String.__msgtype__),
    )
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = ""
    process = await asyncio.create_subprocess_exec(
        "uv",
        "run",
        "--isolated",
        "--python",
        "3.12",
        "--with",
        "rosbags==0.11.5",
        "python",
        "-c",
        source,
        str(bag),
        topic,
        str(timestamp_ns),
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout, stderr = await process.communicate()
    if process.returncode:
        raise AssertionError(
            "ROSBag generation failed: "
            + (stderr or stdout).decode(errors="replace")[-1000:]
        )
    return bag


def inspect_rosbag(bag: Path, topic: str, timestamp_ns: int, expected: dict) -> dict:
    database = next(bag.glob("*.db3"))
    metadata = bag / "metadata.yaml"
    with sqlite3.connect(database) as connection:
        topics = connection.execute(
            "SELECT id, name, type, serialization_format FROM topics ORDER BY id"
        ).fetchall()
        messages = connection.execute(
            "SELECT topic_id, timestamp, data FROM messages ORDER BY timestamp"
        ).fetchall()
    if topics != [(1, topic, "std_msgs/msg/String", "cdr")]:
        raise AssertionError(f"Unexpected ROSBag topic schema: {topics}")
    if len(messages) != 1 or messages[0][1] != timestamp_ns:
        raise AssertionError("Unexpected ROSBag message inventory")
    raw = bytes(messages[0][2])
    length = struct.unpack_from("<I", raw, 4)[0]
    decoded = json.loads(raw[8 : 8 + length - 1].decode())
    if decoded != expected:
        raise AssertionError("ROSBag evidence payload changed")
    return {
        "path": bag.name,
        "format": "ROS 2 SQLite bag",
        "database_sha256": sha256_file(database),
        "metadata_sha256": sha256_file(metadata),
        "topic": topic,
        "timestamp_ns": timestamp_ns,
        "message": decoded,
    }


def artifact_records(paths) -> list[dict]:
    records = []
    for path in paths:
        records.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return records


def create_handoff(*, producer, consumer, revision, units, paths, data) -> dict:
    payload = {
        "producer": producer,
        "consumer": consumer,
        "revision": revision,
        "units": units,
        "artifacts": artifact_records(paths),
        "data": data,
    }
    return {**payload, "manifest_sha256": digest(payload)}


def accept_handoff(handoff: dict, *, producer, consumer, revision) -> dict:
    unsigned = {key: value for key, value in handoff.items() if key != "manifest_sha256"}
    if handoff.get("manifest_sha256") != digest(unsigned):
        raise ValueError("Handoff manifest signature mismatch")
    if (
        handoff["producer"] != producer
        or handoff["consumer"] != consumer
        or handoff["revision"] != revision
    ):
        raise ValueError("Handoff identity mismatch")
    for artifact in handoff["artifacts"]:
        path = Path(artifact["path"])
        if path.stat().st_size != artifact["bytes"] or sha256_file(path) != artifact["sha256"]:
            raise ValueError("Handoff artifact hash mismatch")
    corrupted = json.loads(json.dumps(handoff))
    corrupted["manifest_sha256"] = "0" * 64
    try:
        accept_handoff_unchecked(corrupted)
    except ValueError:
        fail_closed = True
    else:
        raise AssertionError("Handoff accepted a corrupted manifest")
    return {
        "status": "accepted",
        "manifest_sha256": handoff["manifest_sha256"],
        "artifact_count": len(handoff["artifacts"]),
        "identity": [producer, consumer, revision],
        "units": handoff["units"],
        "corrupted_manifest_rejected": fail_closed,
    }


def accept_handoff_unchecked(handoff: dict) -> None:
    unsigned = {key: value for key, value in handoff.items() if key != "manifest_sha256"}
    if handoff.get("manifest_sha256") != digest(unsigned):
        raise ValueError("Handoff manifest signature mismatch")


class WrightGateway:
    def __init__(self, service, session_id: str, calls: list[dict]):
        self.service = service
        self.session_id = session_id
        self.calls = calls
        self.sequence = 0

    async def call(self, server_id: str, tool_name: str, arguments: dict):
        name = f"{server_id}__{tool_name}"
        approvals = self.service.workspace_approvals_for_model_call(
            self.session_id, name
        )
        self.sequence += 1
        result = await self.service.call_tool(
            self.session_id,
            f"chain-{self.sequence:03d}",
            name,
            arguments,
            workspace_approvals=approvals,
        )
        self.calls.append(
            {
                "sequence": self.sequence,
                "server_id": server_id,
                "tool": tool_name,
                "approvals": sorted(approvals),
                "status": "failed" if result.is_error else "passed",
            }
        )
        if result.is_error:
            raise AssertionError(
                f"Wright gateway call failed for {name}: {result_text(result)[:500]}"
            )
        return result


async def export_box(gateway: WrightGateway, output: Path, dimensions) -> dict:
    output.mkdir()
    width, depth, height = dimensions
    code = (
        'import { box } from "brepjs";\n'
        f"export const expected = {{ volume: {width * depth * height}, tolerancePct: 0.1 }};\n"
        f"export default () => box({width}, {depth}, {height});\n"
    )
    await gateway.call(
        "brep-mcp",
        "export_part",
        {
            "code": code,
            "outDir": str(output),
            "formats": {"step": True, "stl": True},
        },
    )
    return inspect_brep_export(output, dimensions)


async def export_two_hole_bracket(
    gateway: WrightGateway, output: Path, dimensions, holes
) -> dict:
    output.mkdir()
    width, depth, height = dimensions
    removed = sum(math.pi * radius**2 * height for _, _, radius in holes)
    expected_volume = width * depth * height - removed
    hole_code = "\n".join(
        f"  result = unwrap(cut(result, cylinder({radius}, {height}, "
        f"{{ at: [{x}, {y}, 0] }})));"
        for x, y, radius in holes
    )
    code = (
        'import { box, cylinder, cut, unwrap } from "brepjs";\n'
        f"export const expected = {{ volume: {expected_volume}, tolerancePct: 0.2 }};\n"
        "export default () => {\n"
        f"  let result = box({width}, {depth}, {height});\n"
        f"{hole_code}\n"
        "  return result;\n"
        "};\n"
    )
    await gateway.call(
        "brep-mcp",
        "export_part",
        {
            "code": code,
            "outDir": str(output),
            "formats": {"step": True, "stl": True},
        },
    )
    artifact = inspect_brep_export(output, dimensions, expected_volume)
    if abs(artifact["stl"]["volume_mm3"] - expected_volume) > expected_volume * 0.002:
        raise AssertionError("Two-hole bracket volume changed")
    artifact["holes_mm"] = [list(hole) for hole in holes]
    artifact["expected_volume_mm3"] = expected_volume
    return artifact


async def create_drawing(
    gateway: WrightGateway,
    output: Path,
    *,
    width,
    height,
    holes,
    centerline,
) -> dict:
    await gateway.call(
        "autocad-mcp-u-c4n",
        "drawing_new",
        {"template": None, "bootstrap": False},
    )
    await gateway.call(
        "autocad-mcp-u-c4n",
        "entity_create_rectangle",
        {"x1": 0, "y1": 0, "x2": width, "y2": height},
    )
    for x, y, radius in holes:
        await gateway.call(
            "autocad-mcp-u-c4n",
            "entity_create_circle",
            {"cx": x, "cy": y, "radius": radius},
        )
    await gateway.call(
        "autocad-mcp-u-c4n",
        "entity_create_line",
        {
            "x1": centerline[0],
            "y1": centerline[1],
            "x2": centerline[2],
            "y2": centerline[3],
        },
    )
    await gateway.call(
        "autocad-mcp-u-c4n",
        "drawing_save_as",
        {"path": str(output), "format": "dxf"},
    )
    return inspect_dxf(
        output,
        width=width,
        height=height,
        holes=holes,
        centerline=centerline,
    )


def structural_script(*, length_m, height_m, thickness_m, load_n, young_pa, poisson):
    return f'''from skfem import MeshTri, Basis, ElementTriP1, ElementVector, asm, solve, condense, LinearForm
from skfem.models.elasticity import linear_elasticity, lame_parameters
import meshio
import numpy as np

length = {length_m!r}
height = {height_m!r}
thickness = {thickness_m!r}
load = {load_n!r}
young = {young_pa!r}
poisson = {poisson!r}
mesh = MeshTri.init_tensor(np.linspace(0.0, length, 41), np.linspace(0.0, height, 13))
basis = Basis(mesh, ElementVector(ElementTriP1()))
lambda_, mu = lame_parameters(young, poisson)
stiffness = asm(linear_elasticity(lambda_, mu), basis) * thickness
right = basis.boundary(lambda x: np.isclose(x[0], length))
@LinearForm
def end_load(v, w):
    return (load / height) * v[1]
forces = asm(end_load, right)
fixed = basis.get_dofs(lambda x: np.isclose(x[0], 0.0)).all()
displacement = solve(*condense(stiffness, forces, D=fixed))
nodal = displacement.reshape((-1, 2)).T
vectors = np.column_stack([nodal.T, np.zeros(nodal.shape[1])])
points = np.column_stack([mesh.p.T, np.zeros(mesh.p.shape[1])])
meshio.write("result.vtu", meshio.Mesh(points, [("triangle", mesh.t.T)], point_data={{"displacement_m": vectors}}), binary=False)
print({{"max_displacement_m": float(np.linalg.norm(vectors, axis=1).max()), "nodes": int(mesh.p.shape[1])}})
'''


def thermal_script(*, width_m, height_m, conductivity, thickness_m, heat_flux):
    return f'''from skfem import MeshTri, Basis, ElementTriP1, asm, solve, condense
from skfem.models.poisson import laplace, unit_load
import meshio
import numpy as np

width = {width_m!r}
height = {height_m!r}
conductivity = {conductivity!r}
thickness = {thickness_m!r}
heat_flux = {heat_flux!r}
ambient = 298.15
mesh = MeshTri.init_tensor(np.linspace(0.0, width, 41), np.linspace(0.0, height, 33))
basis = Basis(mesh, ElementTriP1())
matrix = conductivity * thickness * asm(laplace, basis)
source = heat_flux * asm(unit_load, basis)
boundary = basis.get_dofs().all()
rise = solve(*condense(matrix, source, D=boundary))
temperature = ambient + rise
points = np.column_stack([mesh.p.T, np.zeros(mesh.p.shape[1])])
meshio.write("result.vtu", meshio.Mesh(points, [("triangle", mesh.t.T)], point_data={{"temperature_K": temperature}}), binary=False)
print({{"min_temperature_K": float(temperature.min()), "max_temperature_K": float(temperature.max()), "nodes": int(len(temperature))}})
'''


async def run_simulation(
    gateway: WrightGateway, *, job_name: str, script: str, field: str, components: int
) -> dict:
    result = await gateway.call(
        "oasis-open-fem-agent",
        "run_simulation",
        {
            "solver": "skfem",
            "input_content": script,
            "job_name": job_name,
            "critic_approved": True,
        },
    )
    payload = json_result(result)
    if payload.get("status") != "completed" or payload.get("trustworthy_result") is not True:
        raise AssertionError(f"OASiS did not return verified results: {payload}")
    result_path = Path(payload["work_dir"]) / "result.vtu"
    oracle = inspect_vtu(result_path, field, components)
    oracle["verification"] = payload.get("verification")
    oracle["job_name"] = job_name
    oracle["input_sha256"] = sha256_bytes(script.encode())
    oracle["_artifact_path"] = str(result_path)
    return oracle


async def create_board(gateway: WrightGateway, root: Path) -> dict:
    board = root / "controller-A.kicad_pcb"
    gerbers = root / "controller-A-gerbers"
    gerbers.mkdir()
    search = await gateway.call(
        "kicad-mcp-blwfish",
        "library",
        {
            "operation": "search",
            "query": "0603 resistor",
            "type": "footprint",
            "limit": 5,
        },
    )
    footprint = json_result(search)["results"][0]
    for arguments in (
        {"operation": "create", "pcb_path": str(board)},
        {
            "operation": "set_outline",
            "pcb_path": str(board),
            "x_mm": 0,
            "y_mm": 0,
            "width_mm": 50,
            "height_mm": 40,
        },
        {
            "operation": "place_footprint",
            "pcb_path": str(board),
            "library": footprint["library"],
            "footprint_name": footprint["name"],
            "reference": "R1",
            "value": "10k",
            "x_mm": 25,
            "y_mm": 20,
        },
    ):
        await gateway.call("kicad-mcp-blwfish", "pcb", arguments)
    await gateway.call(
        "kicad-mcp-blwfish",
        "audit",
        {"operation": "all", "pcb_path": str(board)},
    )
    await gateway.call(
        "kicad-mcp-blwfish",
        "export",
        {
            "operation": "gerbers",
            "pcb_path": str(board),
            "output_dir": str(gerbers),
            "create_zip": True,
        },
    )
    return {
        "board_path": board,
        "board": inspect_board(board, width_mm=50, height_mm=40),
        "fabrication": inspect_fabrication(gerbers, board.stem),
    }


async def read_rosbag(
    gateway: WrightGateway, bag: Path, topic: str, timestamp_ns: int, expected: dict
) -> dict:
    artifact = inspect_rosbag(bag, topic, timestamp_ns, expected)
    result = await gateway.call(
        "rosbag-mcp-pypi",
        "get_message_at_time",
        {
            "topic": topic,
            "timestamp": timestamp_ns / 1_000_000_000,
            "bag_path": str(bag),
            "tolerance": 0.01,
        },
    )
    payload = json_result(result)
    observed = json.loads(payload["data"]["data"])
    if observed != expected:
        raise AssertionError("ROSBag MCP returned different evidence")
    return {"artifact": artifact, "gateway_message": observed}


async def mechanical_chain(gateway: WrightGateway, root: Path) -> dict:
    root.mkdir()
    design = "MECH-BRACKET"
    revision = "A"
    dimensions = (100, 30, 8)
    holes = ((15, 15, 4), (85, 15, 4))
    geometry_dir = root / "geometry-A"
    geometry = await export_two_hole_bracket(
        gateway, geometry_dir, dimensions, holes
    )
    geometry_paths = [next(geometry_dir.glob("*.stl")), next(geometry_dir.glob("*.step"))]
    handoff_cad_fea = create_handoff(
        producer="brep-mcp",
        consumer="oasis-open-fem-agent",
        revision=f"{design}-{revision}",
        units={"geometry": "mm", "analysis": "m-N-Pa"},
        paths=geometry_paths,
        data={"dimensions_mm": dimensions, "material": "Al 6061-T6"},
    )
    accepted_cad_fea = accept_handoff(
        handoff_cad_fea,
        producer="brep-mcp",
        consumer="oasis-open-fem-agent",
        revision=f"{design}-{revision}",
    )
    simulation = await run_simulation(
        gateway,
        job_name="mechanical-bracket-A",
        script=structural_script(
            length_m=0.1,
            height_m=0.03,
            thickness_m=0.008,
            load_n=-250.0,
            young_pa=69e9,
            poisson=0.33,
        ),
        field="displacement_m",
        components=3,
    )
    if not 0 < max(abs(simulation["field_min"]), abs(simulation["field_max"])) < 0.01:
        raise AssertionError("Structural response is outside the engineering sanity range")
    simulation["input_geometry_sha256"] = geometry["step"]["sha256"]
    simulation["model_scope"] = (
        "2D equivalent solid-section screening model; mounting holes are excluded"
    )
    vtu = Path(simulation.pop("_artifact_path"))
    handoff_fea_drawing = create_handoff(
        producer="oasis-open-fem-agent",
        consumer="autocad-mcp-u-c4n",
        revision=f"{design}-{revision}",
        units={"drawing": "mm", "displacement": "m"},
        paths=[*geometry_paths, vtu],
        data={"load_N": -250.0, "result_sha256": simulation["sha256"]},
    )
    accepted_fea_drawing = accept_handoff(
        handoff_fea_drawing,
        producer="oasis-open-fem-agent",
        consumer="autocad-mcp-u-c4n",
        revision=f"{design}-{revision}",
    )
    drawing = await create_drawing(
        gateway,
        root / "mechanical-review-A.dxf",
        width=100.0,
        height=30.0,
        holes=((15.0, 15.0, 4.0), (85.0, 15.0, 4.0)),
        centerline=(50.0, 0.0, 50.0, 30.0),
    )
    return {
        "id": "mechanical-cad-fea-review",
        "status": "passed",
        "design_id": design,
        "revision": revision,
        "geometry": geometry,
        "simulation": simulation,
        "review_drawing": drawing,
        "handoffs": [accepted_cad_fea, accepted_fea_drawing],
    }


async def electronics_chain(gateway: WrightGateway, root: Path) -> dict:
    root.mkdir()
    design = "ELEC-CONTROLLER"
    revision = "A"
    board_result = await create_board(gateway, root)
    board = board_result["board_path"]
    enclosure_dir = root / "enclosure-envelope-A"
    board_to_enclosure = create_handoff(
        producer="kicad-mcp-blwfish",
        consumer="brep-mcp",
        revision=f"{design}-{revision}",
        units={"board": "mm", "enclosure": "mm"},
        paths=[board],
        data={"board_envelope_mm": [50, 40, 1.6], "clearance_mm": 5},
    )
    accepted_board_to_enclosure = accept_handoff(
        board_to_enclosure,
        producer="kicad-mcp-blwfish",
        consumer="brep-mcp",
        revision=f"{design}-{revision}",
    )
    enclosure = await export_box(gateway, enclosure_dir, (60, 50, 15))
    enclosure["input_board_sha256"] = board_result["board"]["sha256"]
    enclosure_paths = [
        next(enclosure_dir.glob("*.stl")),
        next(enclosure_dir.glob("*.step")),
    ]
    enclosure_to_thermal = create_handoff(
        producer="brep-mcp",
        consumer="oasis-open-fem-agent",
        revision=f"{design}-{revision}",
        units={"geometry": "mm", "thermal": "m-W-K"},
        paths=[board, *enclosure_paths],
        data={"board_m": [0.05, 0.04, 0.0016], "heat_flux_W_m2": 5000},
    )
    accepted_enclosure_to_thermal = accept_handoff(
        enclosure_to_thermal,
        producer="brep-mcp",
        consumer="oasis-open-fem-agent",
        revision=f"{design}-{revision}",
    )
    thermal = await run_simulation(
        gateway,
        job_name="electronics-controller-A-thermal",
        script=thermal_script(
            width_m=0.05,
            height_m=0.04,
            conductivity=20.0,
            thickness_m=0.0016,
            heat_flux=5000.0,
        ),
        field="temperature_K",
        components=1,
    )
    if not 298.14 <= thermal["field_min"] <= 298.16 or not 298.15 < thermal[
        "field_max"
    ] < 400:
        raise AssertionError("Thermal result is outside the engineering sanity range")
    thermal["input_board_sha256"] = board_result["board"]["sha256"]
    thermal["input_enclosure_step_sha256"] = enclosure["step"]["sha256"]
    thermal_vtu = Path(thermal.pop("_artifact_path"))
    trace = {
        "design_id": design,
        "revision": revision,
        "board_sha256": board_result["board"]["sha256"],
        "enclosure_step_sha256": enclosure["step"]["sha256"],
        "simulation_sha256": thermal["sha256"],
        "max_temperature_K": thermal["field_max"],
        "limit_temperature_K": 358.15,
        "status": "pass" if thermal["field_max"] <= 358.15 else "fail",
    }
    timestamp_ns = 1_710_000_000_000_000_000
    bag = await generate_rosbag(
        root / "thermal-validation", "/wright/thermal_validation", timestamp_ns, trace
    )
    thermal_to_test = create_handoff(
        producer="oasis-open-fem-agent",
        consumer="rosbag-mcp-pypi",
        revision=f"{design}-{revision}",
        units={"temperature": "K", "timestamp": "ns"},
        paths=[board, thermal_vtu],
        data=trace,
    )
    accepted_thermal_to_test = accept_handoff(
        thermal_to_test,
        producer="oasis-open-fem-agent",
        consumer="rosbag-mcp-pypi",
        revision=f"{design}-{revision}",
    )
    validation = await read_rosbag(
        gateway, bag, "/wright/thermal_validation", timestamp_ns, trace
    )
    return {
        "id": "electronics-ecad-enclosure-thermal-test",
        "status": "passed",
        "design_id": design,
        "revision": revision,
        "board": board_result["board"],
        "fabrication": board_result["fabrication"],
        "enclosure": enclosure,
        "thermal_simulation": thermal,
        "validation_trace": validation,
        "handoffs": [
            accepted_board_to_enclosure,
            accepted_enclosure_to_thermal,
            accepted_thermal_to_test,
        ],
    }


async def field_revision_chain(gateway: WrightGateway, root: Path) -> dict:
    root.mkdir()
    design = "FIELD-BRACKET"
    drawing_a_path = root / "field-bracket-A.dxf"
    drawing_a = await create_drawing(
        gateway,
        drawing_a_path,
        width=100.0,
        height=8.0,
        holes=((20.0, 4.0, 2.0), (80.0, 4.0, 2.0)),
        centerline=(50.0, 0.0, 50.0, 8.0),
    )
    measurement = {
        "design_id": design,
        "source_revision": "A",
        "source_drawing_sha256": drawing_a["sha256"],
        "measured_deflection_mm": 1.8,
        "allowable_deflection_mm": 1.0,
        "sample_id": "RIG-17-RUN-0042",
        "instrument": "LVDT-03",
    }
    timestamp_ns = 1_720_000_000_000_000_000
    bag = await generate_rosbag(
        root / "field-evidence", "/wright/field_deflection", timestamp_ns, measurement
    )
    field_to_review = create_handoff(
        producer="test-rig-RIG-17",
        consumer="rosbag-mcp-pypi",
        revision=f"{design}-A",
        units={"deflection": "mm", "timestamp": "ns"},
        paths=[drawing_a_path, next(bag.glob("*.db3")), bag / "metadata.yaml"],
        data=measurement,
    )
    accepted_field_to_review = accept_handoff(
        field_to_review,
        producer="test-rig-RIG-17",
        consumer="rosbag-mcp-pypi",
        revision=f"{design}-A",
    )
    field_evidence = await read_rosbag(
        gateway, bag, "/wright/field_deflection", timestamp_ns, measurement
    )
    if field_evidence["gateway_message"]["source_drawing_sha256"] != sha256_file(
        drawing_a_path
    ):
        raise AssertionError("Field evidence does not bind to revision A")
    if measurement["measured_deflection_mm"] <= measurement["allowable_deflection_mm"]:
        raise AssertionError("Revision trigger was not present")
    revised_thickness = 10.0
    evidence_to_revision = create_handoff(
        producer="rosbag-mcp-pypi",
        consumer="autocad-mcp-u-c4n",
        revision=f"{design}-B",
        units={"drawing": "mm", "deflection": "mm"},
        paths=[drawing_a_path, next(bag.glob("*.db3"))],
        data={
            "change": "increase section thickness",
            "from_mm": 8.0,
            "to_mm": revised_thickness,
            "source_evidence_sha256": field_evidence["artifact"]["database_sha256"],
        },
    )
    accepted_evidence_to_revision = accept_handoff(
        evidence_to_revision,
        producer="rosbag-mcp-pypi",
        consumer="autocad-mcp-u-c4n",
        revision=f"{design}-B",
    )
    drawing_b_path = root / "field-bracket-B.dxf"
    drawing_b = await create_drawing(
        gateway,
        drawing_b_path,
        width=100.0,
        height=revised_thickness,
        holes=((20.0, 5.0, 2.0), (80.0, 5.0, 2.0)),
        centerline=(50.0, 0.0, 50.0, 10.0),
    )
    if drawing_a["sha256"] == drawing_b["sha256"] or sha256_file(
        drawing_a_path
    ) != drawing_a["sha256"]:
        raise AssertionError("Controlled revision did not preserve A and create B")
    return {
        "id": "field-evidence-controlled-revision",
        "status": "passed",
        "design_id": design,
        "source_revision": {"id": "A", "drawing": drawing_a},
        "field_evidence": field_evidence,
        "released_revision": {
            "id": "B",
            "drawing": drawing_b,
            "change": "section thickness increased from 8 mm to 10 mm",
        },
        "handoffs": [accepted_field_to_review, accepted_evidence_to_revision],
    }


async def prepare_gateway(root: Path, report: dict):
    os.environ["DATABASE_PATH"] = str(root / "wright.db")
    os.environ["WRIGHT_SECRETS_PATH"] = str(root / "secrets.json")
    os.environ["BREP_WORKSPACE"] = str(root)
    os.environ["ALLOWED_PATHS"] = str(root)
    os.environ["PYVISTA_OFF_SCREEN"] = "true"
    if os.getenv("WRIGHT_TESTING") == "1":
        raise ValueError("Live process-chain qualification cannot use Wright's mock runner")

    from api.database.migrate import run_migrations
    from data_vault import install_default_secret_provider
    from data_vault.gateway_repository import GatewayRepository
    from data_vault.secret_provider import FileSecretProvider
    from data_vault.workspace_repository import WorkspaceRepository
    from tool_registry.canonical_catalog import load_canonical_entries
    from tool_registry.catalog_loader import catalog_entry_to_mcp_seed
    from tool_registry.curation_models import (
        evaluate_curation,
        qualification_configuration,
    )
    from tool_registry.db import insert_server, insert_tools
    from tool_registry.gateway_adapters import (
        DatabaseGatewayAudit,
        DatabaseGatewayCatalog,
        DatabaseGatewayWorkspace,
        EngineGatewayLifecycle,
    )
    from tool_registry.gateway_notifications import GatewayNotificationHub
    from tool_registry.gateway_service import GatewayService
    from tool_registry.manager import McpEngine
    from tool_registry.models import McpServer, McpTool
    from tool_registry.secrets import write_secrets

    install_default_secret_provider()
    entries_by_id = {entry.id: entry for entry in load_canonical_entries()}
    entries = [entries_by_id[server_id] for server_id in SERVER_IDS]
    configurations = {}
    for entry in entries:
        configuration = qualification_configuration(entry)
        view = evaluate_curation(
            entry.curation,
            today=date.today(),
            platform="linux_x64",
            distribution_mode="docker",
            configuration_sha256=configuration,
        )
        if view.effective_disposition != "curated":
            raise ValueError(f"Process chain requires a current curated scope: {entry.id}")
        configurations[entry.id] = configuration
    write_secrets("autocad-mcp-u-c4n", {"ALLOWED_PATHS": str(root)})

    discovered_by_id = {}
    for entry in entries:
        env = dict(entry.launch_env or {})
        if entry.id in {"oasis-open-fem-agent", "rosbag-mcp-pypi"}:
            env["PYTHONPATH"] = ""
        if entry.id == "autocad-mcp-u-c4n":
            env["ALLOWED_PATHS"] = str(root)
        cwd = str(root) if entry.id == "rosbag-mcp-pypi" else None
        async with client_session(entry.command, env, cwd) as client:
            await client.initialize()
            tools = await client.list_tools()
            discovered_by_id[entry.id] = tools.tools

    run_migrations()
    database = str(root / "wright.db")
    for entry in entries:
        seed = catalog_entry_to_mcp_seed(entry)
        seed.update(
            server_id=entry.id,
            command=entry.command,
            is_active=False,
            is_installed=True,
            status="inactive",
            created_at=1,
            updated_at=1,
        )
        insert_server(database, McpServer.model_validate(seed))
        insert_tools(
            database,
            [
                McpTool(
                    tool_id=f"{entry.id}:{tool.name}",
                    server_id=entry.id,
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.inputSchema,
                    output_schema=tool.outputSchema,
                    is_enabled=True,
                    created_at=1,
                )
                for tool in discovered_by_id[entry.id]
            ],
        )
    workspace = root / "workspace"
    workspace.mkdir()
    WorkspaceRepository(
        database, secrets=FileSecretProvider(root / "secrets.json")
    ).create(
        "process-chain-workspace",
        "process-chain-session",
        str(workspace),
        workspace_name="Disposable process-chain qualification",
    )
    with closing(sqlite3.connect(database)) as connection:
        connection.execute(
            "UPDATE engineering_workspaces SET enabled_tools=? WHERE workspace_id=?",
            (json.dumps(list(SERVER_IDS)), "process-chain-workspace"),
        )
        connection.commit()
    repository = GatewayRepository(database)
    engine = McpEngine(database, operation_timeout=120)
    service = GatewayService(
        workspaces=DatabaseGatewayWorkspace(repository),
        catalog=DatabaseGatewayCatalog(database),
        lifecycle=EngineGatewayLifecycle(engine),
        audit=DatabaseGatewayAudit(repository),
        notifier=GatewayNotificationHub(),
        operation_timeout=120,
    )
    service.open_session(
        session_id="process-chain-session",
        principal_id="curation-operator",
        workspace_id="process-chain-workspace",
        transport="stdio",
    )
    service.initialize_session(
        "process-chain-session",
        protocol_version="2025-11-25",
        client_name="wright-process-chain-qualification",
        client_version="1",
        client_capabilities={},
    )
    visible = {tool.name for tool in service.list_tools("process-chain-session")}
    for entry in entries:
        if not any(name.startswith(f"{entry.id}__") for name in visible):
            raise AssertionError(f"Wright did not expose enabled server {entry.id}")
    report["portfolio_inputs"] = {
        entry.id: {
            "configuration_sha256": configurations[entry.id],
            "source_url": entry.source_url,
            "tool_schema_sha256": digest(
                [tool.model_dump(mode="json") for tool in discovered_by_id[entry.id]]
            ),
            "tool_count": len(discovered_by_id[entry.id]),
        }
        for entry in entries
    }
    report["workspace_policy"] = {
        "workspace_id": "process-chain-workspace",
        "principal_id": "curation-operator",
        "enabled_server_ids": list(SERVER_IDS),
        "visible_tool_count": len(visible),
    }
    return service


async def run(args, root: Path, report: dict) -> None:
    report.update(
        {
            "observed_at": datetime.now(UTC).isoformat(),
            "wright_revision": args.wright_revision,
            "environment": args.environment,
            "platform": args.platform,
            "container_image": args.container_image,
            "status": "partial",
            "calls": [],
            "chains": [],
        }
    )
    service = await prepare_gateway(root, report)
    gateway = WrightGateway(service, "process-chain-session", report["calls"])
    try:
        workspace = root / "workspace"
        report["chains"].append(await mechanical_chain(gateway, workspace / "chain-1"))
        report["chains"].append(await electronics_chain(gateway, workspace / "chain-2"))
        report["chains"].append(await field_revision_chain(gateway, workspace / "chain-3"))
        if len(report["chains"]) != 3 or any(
            chain["status"] != "passed" for chain in report["chains"]
        ):
            raise AssertionError("All three process chains must pass")
        report["status"] = "passed"
    finally:
        await service.shutdown()


def exception_leaves(error) -> list[dict]:
    leaves = []
    stack = [error]
    while stack and len(leaves) < 10:
        item = stack.pop()
        if isinstance(item, BaseExceptionGroup):
            stack.extend(reversed(item.exceptions))
        else:
            leaves.append(
                {
                    "type": type(item).__name__,
                    "message": str(item)[:1000],
                    "traceback": "".join(traceback.format_exception(item))[-3000:],
                }
            )
    return leaves


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--wright-revision", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--platform", choices=["linux_x64"], required=True)
    parser.add_argument("--container-image", required=True)
    parser.add_argument("--installed-item", action="append", default=[])
    parser.add_argument("--prerequisite", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-parent", type=Path)
    args = parser.parse_args()
    if args.work_parent:
        args.work_parent = args.work_parent.resolve()
        args.work_parent.mkdir(parents=True, exist_ok=True)
    from core.redaction import redact_mapping

    report = {
        "installed_items": args.installed_item,
        "prerequisites": args.prerequisite,
    }
    temporary = tempfile.TemporaryDirectory(
        prefix="wright-process-chains-", dir=args.work_parent
    )
    original_cwd = Path.cwd()
    try:
        os.chdir(temporary.name)
        asyncio.run(asyncio.wait_for(run(args, Path(temporary.name), report), timeout=900))
    except Exception as error:
        report.update(
            status="failed",
            error=type(error).__name__,
            diagnostic=str(error)[:1000],
            errors=exception_leaves(error),
        )
    finally:
        os.chdir(original_cwd)
        try:
            temporary.cleanup()
            report["cleanup"] = "passed"
        except OSError:
            report.update(
                status="failed",
                cleanup="failed",
                cleanup_reason="Disposable chain files remain locked",
            )
    report["evidence_sha256"] = digest(
        {key: value for key, value in report.items() if key != "evidence_sha256"}
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(redact_mapping(report), indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"status": report.get("status"), "output": str(args.output)}))
    return 0 if report.get("status") == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
