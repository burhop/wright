"""Opt-in real MCP qualification. Run in a disposable Wright environment.

Only reviewed, credential-free scenarios are allowed. Host prerequisites must
be installed in the selected disposable container, never the base image. This
runner produces evidence; it never promotes a catalog entry.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import struct
import sys
import tempfile
import traceback
import xml.etree.ElementTree as ET

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client

_blender_process_groups: set[int] = set()


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()


@asynccontextmanager
async def client_session(command, env_overrides=None, cwd=None):
    if isinstance(command, str):
        async with httpx.AsyncClient(
            timeout=60, trust_env=False, follow_redirects=False
        ) as http:
            async with streamable_http_client(command, http_client=http) as (
                read,
                write,
                _,
            ):
                async with ClientSession(read, write) as client:
                    yield client
    else:
        child_env = dict(os.environ)
        child_env.update(env_overrides or {})
        async with stdio_client(
            StdioServerParameters(
                command=command[0], args=command[1:], env=child_env, cwd=cwd
            )
        ) as (read, write):
            async with ClientSession(read, write) as client:
                yield client


def cube_oracle(path, expected_dimensions=(10, 8, 6), expected_volume=480):
    raw = path.read_bytes()
    assert 0 < len(raw) < 1024 * 1024, "Missing or oversized STL"
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
    assert len(points) >= 36 and len(points) % 3 == 0, "STL has no usable triangle mesh"
    bounds = [
        max(point[i] for point in points) - min(point[i] for point in points)
        for i in range(3)
    ]
    assert all(
        abs(actual - expected) < 0.001
        for actual, expected in zip(bounds, expected_dimensions)
    ), "Incorrect cube dimensions"
    volume = 0.0
    for offset in range(0, len(points), 3):
        a, b, c = points[offset : offset + 3]
        volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6
    assert abs(abs(volume) - expected_volume) < 0.01, "Incorrect mesh volume"
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "dimensions_mm": bounds,
        "volume_mm3": abs(volume),
    }


def autocad_dxf_oracle(path):
    """Inspect the fixed drafting scenario without trusting the MCP response."""
    raw = path.read_bytes()
    assert 500 < len(raw) < 5 * 1024 * 1024, "Missing or oversized DXF"
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    assert len(lines) % 2 == 0, "DXF group-code stream is incomplete"
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

    by_type = {}
    for entity in entities:
        by_type.setdefault(entity["type"], []).append(entity["pairs"])
    assert {key: len(value) for key, value in by_type.items()} == {
        "LWPOLYLINE": 1,
        "CIRCLE": 2,
        "LINE": 1,
    }, "DXF entity inventory changed"

    rectangle = by_type["LWPOLYLINE"][0]
    xs = [float(value) for code, value in rectangle if code == 10]
    ys = [float(value) for code, value in rectangle if code == 20]
    vertices = {(round(x, 6), round(y, 6)) for x, y in zip(xs, ys)}
    assert vertices == {(0.0, 0.0), (100.0, 0.0), (100.0, 60.0), (0.0, 60.0)}
    flags = [int(value) for code, value in rectangle if code == 70]
    assert flags and flags[-1] & 1, "DXF rectangle is not closed"

    circles = set()
    for values in by_type["CIRCLE"]:
        grouped = {code: value for code, value in values if code in {10, 20, 40}}
        circles.add(tuple(round(float(grouped[code]), 6) for code in (10, 20, 40)))
    assert circles == {(20.0, 30.0, 5.0), (80.0, 30.0, 5.0)}

    line = {code: value for code, value in by_type["LINE"][0] if code in {10, 20, 11, 21}}
    assert tuple(round(float(line[code]), 6) for code in (10, 20, 11, 21)) == (
        50.0,
        0.0,
        50.0,
        60.0,
    )
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "entity_counts": {key: len(value) for key, value in by_type.items()},
        "rectangle": sorted([list(point) for point in vertices]),
        "circles": sorted([list(circle) for circle in circles]),
        "centerline": [50.0, 0.0, 50.0, 60.0],
    }


def rhino_artifact_oracle(model_path, mesh_path):
    """Check the 3DM container and independently integrate the exported mesh."""
    raw = model_path.read_bytes()
    assert 500 < len(raw) < 10 * 1024 * 1024, "Missing or oversized 3DM"
    assert raw.startswith(b"3D Geometry File Format"), "Invalid 3DM header"
    return {
        "model": {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "header": raw[:32].decode("ascii", errors="replace").rstrip("\x00"),
        },
        "mesh": cube_oracle(mesh_path),
    }


def blender_probe(output, object_name):
    rendered_path = json.dumps(str(output))
    return (
        "execute_blender_code",
        {
            "code": (
                "import bpy\n"
                "bpy.ops.object.select_all(action='SELECT')\n"
                "bpy.ops.object.delete(use_global=False)\n"
                "bpy.context.scene.unit_settings.system = 'METRIC'\n"
                "bpy.context.scene.unit_settings.length_unit = 'MILLIMETERS'\n"
                "bpy.context.scene.unit_settings.scale_length = 0.001\n"
                "bpy.ops.mesh.primitive_cube_add(size=2, location=(0, 0, 0))\n"
                "obj = bpy.context.active_object\n"
                f"obj.name = {json.dumps(object_name)}\n"
                "obj.dimensions = (10, 8, 6)\n"
                "bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)\n"
                "bpy.ops.object.select_all(action='DESELECT')\n"
                "obj.select_set(True)\n"
                "bpy.context.view_layer.objects.active = obj\n"
                f"bpy.ops.wm.stl_export(filepath={rendered_path}, "
                "export_selected_objects=True, global_scale=1.0)\n"
                "print({'name': obj.name, 'dimensions_mm': list(obj.dimensions)})\n"
            )
        },
    )


def blender_object_oracle(result, expected_name):
    payload = _json_result(result)
    assert payload["name"] == expected_name, "Blender returned another object"
    assert payload["type"] == "MESH", "Blender object is not a mesh"
    assert payload["mesh"] == {"vertices": 8, "edges": 12, "polygons": 6}, (
        "Blender box topology changed"
    )
    assert payload["world_bounding_box"] == [
        [-5.0, -4.0, -3.0],
        [5.0, 4.0, 3.0],
    ], "Blender box bounds are incorrect"
    return {
        "name": payload["name"],
        "type": payload["type"],
        "mesh": payload["mesh"],
        "world_bounding_box": payload["world_bounding_box"],
    }


async def start_blender_bridge(root, addon_path, label):
    bootstrap = root / f"start-blender-{label}.py"
    bootstrap.write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "debian_packages = Path('/usr/lib/python3/dist-packages')\n"
        "if debian_packages.is_dir():\n"
        "    sys.path.insert(0, str(debian_packages))\n"
        f"sys.path.insert(0, {json.dumps(str(addon_path.parent))})\n"
        "import addon\n"
        "addon.register()\n"
        "print('WRIGHT_BLENDER_BRIDGE_READY', flush=True)\n",
        encoding="utf-8",
    )
    log_path = root / f"blender-{label}.log"
    blender_env = dict(os.environ)
    # Blender embeds its own interpreter. Wright's source path belongs only to
    # the qualification process and can hide Blender's normal site packages.
    blender_env["PYTHONPATH"] = ""
    with log_path.open("wb") as log:
        process = await asyncio.create_subprocess_exec(
            "xvfb-run",
            "-a",
            "blender",
            "--factory-startup",
            "--python",
            str(bootstrap),
            stdout=log,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
            env=blender_env,
        )
    _blender_process_groups.add(process.pid)
    deadline = asyncio.get_running_loop().time() + 60
    while asyncio.get_running_loop().time() < deadline:
        if process.returncode is not None:
            diagnostic = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
            raise RuntimeError(f"Blender bridge exited before startup: {diagnostic}")
        try:
            _reader, writer = await asyncio.open_connection("127.0.0.1", 9876)
            writer.close()
            await writer.wait_closed()
            return process, log_path
        except OSError:
            await asyncio.sleep(0.25)
    await stop_blender_bridge(process)
    diagnostic = log_path.read_text(encoding="utf-8", errors="replace")[-2000:]
    raise TimeoutError(f"Blender bridge did not listen on port 9876: {diagnostic}")


async def stop_blender_bridge(process):
    if process is None:
        return
    process_group = process.pid
    if process.returncode is not None:
        _blender_process_groups.discard(process_group)
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    except ProcessLookupError:
        _blender_process_groups.discard(process_group)
        return
    try:
        await asyncio.wait_for(process.wait(), timeout=15)
    except TimeoutError:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        await process.wait()
    finally:
        _blender_process_groups.discard(process_group)


def brep_oracle(path):
    stl_files = list(path.glob("*.stl"))
    step_files = list(path.glob("*.step")) + list(path.glob("*.stp"))
    assert len(stl_files) == 1, "BREP export did not produce exactly one STL"
    assert len(step_files) == 1, "BREP export did not produce exactly one STEP file"
    result = cube_oracle(
        stl_files[0], expected_dimensions=(40, 20, 10), expected_volume=8000
    )
    step = step_files[0].read_bytes()
    assert 500 < len(step) < 10 * 1024 * 1024, "Missing or oversized STEP artifact"
    assert step.startswith(b"ISO-10303-21;"), "Invalid STEP exchange-file header"
    assert b"END-ISO-10303-21;" in step, "Incomplete STEP exchange file"
    result.update(
        {
            "step_bytes": len(step),
            "step_sha256": hashlib.sha256(step).hexdigest(),
        }
    )
    return result


def freecad_probe(output, document_name):
    rendered_path = json.dumps(str(output))
    return (
        "execute_code",
        {
            "code": (
                "import FreeCAD, Mesh\n"
                f'doc = FreeCAD.newDocument("{document_name}")\n'
                'obj = doc.addObject("Part::Box", "WrightBox")\n'
                "obj.Length = 10\n"
                "obj.Width = 8\n"
                "obj.Height = 6\n"
                "doc.recompute()\n"
                f"Mesh.export([obj], {rendered_path})\n"
                'print({"name": obj.Name, "volume_mm3": obj.Shape.Volume})\n'
            )
        },
    )


def oasis_probe(job_name, *, slow=False):
    if slow:
        script = (
            "import time\n"
            "from skfem import MeshTri\n"
            "time.sleep(30)\n"
            'open("result.vtu", "w").write("late artifact")\n'
        )
    else:
        script = '''from skfem import MeshTri, Basis, ElementTriP1, asm, solve, condense
from skfem.models.poisson import laplace, unit_load
import meshio
import numpy as np

m = MeshTri.init_symmetric().refined(5)
basis = Basis(m, ElementTriP1())
A = asm(laplace, basis)
b = asm(unit_load, basis)
phi = solve(*condense(A, b, D=basis.get_dofs()))
points = np.column_stack([m.p.T, np.zeros(m.p.shape[1])])
meshio.write(
    "result.vtu",
    meshio.Mesh(points, [("triangle", m.t.T)], point_data={"phi": phi}),
    binary=False,
)
print({"max_phi": float(phi.max()), "min_phi": float(phi.min()), "nodes": len(phi)})
'''
    return (
        "run_simulation",
        {
            "solver": "skfem",
            "input_content": script,
            "job_name": job_name,
            # The fixed scenario and its independent mesh/field oracle below are
            # the qualification critic for this one deterministic solve.
            "critic_approved": not slow,
        },
    )


def _result_text(result):
    values = []
    for item in result.content:
        value = item.get("text") if isinstance(item, dict) else getattr(item, "text", None)
        if value is not None:
            values.append(value)
    return "\n".join(values)


def _json_result(result):
    payload = json.loads(_result_text(result))
    if isinstance(payload, str):
        payload = json.loads(payload)
    assert isinstance(payload, dict), "Tool did not return a JSON object"
    return payload


def oasis_oracle(result, expected_job_name):
    payload = _json_result(result)
    assert payload["status"] == "completed", "OASiS simulation did not complete"
    assert payload["output_files"] == ["result.vtu"], (
        "OASiS did not return the expected result artifact"
    )
    assert payload["trustworthy_result"] is True, (
        "OASiS verification did not bind the result to run evidence"
    )
    assert payload["verification"].startswith("VERIFIED"), (
        "OASiS did not attest its automated checks"
    )
    work_dir = Path(payload["work_dir"])
    assert work_dir.name == expected_job_name, "OASiS returned another job's output"
    result_path = work_dir / "result.vtu"
    raw = result_path.read_bytes()
    assert 1000 < len(raw) < 10 * 1024 * 1024, "Missing or oversized VTU result"

    tree = ET.fromstring(raw)
    point_data = next(
        node
        for node in tree.findall(".//{*}PointData/{*}DataArray")
        if node.attrib.get("Name") == "phi"
    )
    phi = [float(value) for value in (point_data.text or "").split()]
    points_node = tree.find(".//{*}Points/{*}DataArray")
    assert points_node is not None, "VTU has no mesh points"
    coordinates = [float(value) for value in (points_node.text or "").split()]
    assert len(coordinates) == len(phi) * 3 and len(phi) > 500, (
        "VTU mesh or solution field is incomplete"
    )
    assert all(math.isfinite(value) for value in phi + coordinates), (
        "VTU contains non-finite values"
    )
    axes = [coordinates[index::3] for index in range(3)]
    bounds = [[min(axis), max(axis)] for axis in axes]
    assert all(abs(bounds[index][0]) < 1e-12 for index in range(3)), (
        "Unexpected VTU lower bounds"
    )
    assert abs(bounds[0][1] - 1) < 1e-12 and abs(bounds[1][1] - 1) < 1e-12, (
        "Unexpected unit-square mesh bounds"
    )
    assert abs(bounds[2][1]) < 1e-12, "2D solution has a non-zero Z extent"
    assert abs(min(phi)) < 1e-12 and 0.07 < max(phi) < 0.08, (
        "Poisson result is outside the independently expected range"
    )
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "nodes": len(phi),
        "bounds": bounds,
        "min_phi": min(phi),
        "max_phi": max(phi),
        "verification": payload["verification"],
    }


async def generate_rosbag_fixture(root):
    bag_path = root / "wright_chatter"
    script = '''from pathlib import Path
from rosbags.rosbag2 import Writer
from rosbags.typesys import Stores, get_typestore

bag = Path(__import__("sys").argv[1])
typestore = get_typestore(Stores.ROS2_HUMBLE)
String = typestore.types["std_msgs/msg/String"]
with Writer(bag, version=9) as writer:
    connection = writer.add_connection(
        "/chatter", String.__msgtype__, typestore=typestore
    )
    for timestamp, value in [
        (1700000000000000000, "hello"),
        (1700000001000000000, "world"),
    ]:
        message = String(data=value)
        writer.write(
            connection,
            timestamp,
            typestore.serialize_cdr(message, String.__msgtype__),
        )
'''
    fixture_env = dict(os.environ)
    fixture_env["PYTHONPATH"] = ""
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
        script,
        str(bag_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=fixture_env,
    )
    stdout, stderr = await process.communicate()
    assert process.returncode == 0, (
        "ROSBag fixture generation failed: "
        + (stderr or stdout).decode(errors="replace")[-500:]
    )
    return bag_path


def rosbag_artifact_oracle(bag_path):
    metadata = bag_path / "metadata.yaml"
    databases = list(bag_path.glob("*.db3"))
    assert metadata.is_file() and len(databases) == 1, "Incomplete ROS 2 bag"
    database = databases[0]
    with sqlite3.connect(database) as connection:
        topics = connection.execute(
            "SELECT id, name, type, serialization_format FROM topics ORDER BY id"
        ).fetchall()
        messages = connection.execute(
            "SELECT topic_id, timestamp, data FROM messages ORDER BY timestamp"
        ).fetchall()
    assert topics == [(1, "/chatter", "std_msgs/msg/String", "cdr")], (
        "Unexpected ROS 2 topic schema"
    )
    assert [row[1] for row in messages] == [
        1700000000000000000,
        1700000001000000000,
    ], "Unexpected ROS 2 timestamps"
    decoded = []
    for _, _, data in messages:
        raw = bytes(data)
        assert raw[:4] == b"\x00\x01\x00\x00", "Unexpected CDR encoding"
        length = struct.unpack_from("<I", raw, 4)[0]
        assert length > 1 and raw[8 + length - 1] == 0, "Invalid CDR string"
        decoded.append(raw[8 : 8 + length - 1].decode("utf-8"))
    assert decoded == ["hello", "world"], "Unexpected ROS 2 message content"
    return {
        "database_bytes": database.stat().st_size,
        "database_sha256": hashlib.sha256(database.read_bytes()).hexdigest(),
        "metadata_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
        "topic": topics[0][1],
        "message_type": topics[0][2],
        "timestamps_ns": [row[1] for row in messages],
        "messages": decoded,
    }


def rosbag_result_oracle(result):
    payload = _json_result(result)
    assert payload["topic"] == "/chatter", "ROSBag MCP returned another topic"
    assert abs(payload["timestamp"] - 1700000000.0) < 1e-9, (
        "ROSBag MCP returned another timestamp"
    )
    assert payload["msg_type"] == "std_msgs/msg/String", (
        "ROSBag MCP returned another message type"
    )
    message = payload["data"]
    assert message.get("data") == "hello", "ROSBag MCP returned another message"
    return {
        "topic": payload["topic"],
        "timestamp": payload["timestamp"],
        "message_type": payload["msg_type"],
        "message": message,
    }


def exception_leaves(error):
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


async def run(args, root, report):
    # Import the actual application schema, registry, manager, and gateway.
    os.environ["DATABASE_PATH"] = str(root / "wright.db")
    os.environ["WRIGHT_SECRETS_PATH"] = str(root / "secrets.json")
    if os.getenv("WRIGHT_TESTING") == "1":
        raise ValueError("Live qualification cannot use Wright's mock runner")
    from api.database.migrate import run_migrations
    from tool_registry.canonical_catalog import load_canonical_entries
    from tool_registry.catalog_loader import catalog_entry_to_mcp_seed
    from tool_registry.db import insert_server, insert_tools
    from tool_registry.models import McpServer, McpTool
    from tool_registry.manager import McpEngine
    from tool_registry.runners.stdio import StdioRunner
    from tool_registry.gateway_adapters import (
        DatabaseGatewayWorkspace,
        DatabaseGatewayAudit,
        DatabaseGatewayCatalog,
        EngineGatewayLifecycle,
    )
    from tool_registry.gateway_service import GatewayService
    from tool_registry.gateway_notifications import GatewayNotificationHub
    from data_vault.gateway_repository import GatewayRepository
    from data_vault.workspace_repository import WorkspaceRepository
    from data_vault.secret_provider import FileSecretProvider
    from data_vault import install_default_secret_provider
    install_default_secret_provider()
    entry = next(entry for entry in load_canonical_entries() if entry.id == args.server)
    from tool_registry.curation_models import qualification_configuration

    command = entry.command
    rosbag_path = None
    blender_process = None
    blender_log = None
    if args.server == "openscad-mcp":
        if not isinstance(command, list) or not any(
            re.fullmatch(
                r"git\+https://github.com/quellant/openscad-mcp\.git@[a-f0-9]{40}", part
            )
            for part in command
        ):
            raise ValueError("Catalog must pin the reviewed OpenSCAD repository commit")
        os.environ["OPENSCAD_WORKSPACE"] = str(root)
    elif args.server == "brep-mcp":
        if command != ["brep-mcp-wrapped"]:
            raise ValueError("Catalog must use the reviewed BREP compatibility launcher")
        os.environ["BREP_WORKSPACE"] = str(root)
    elif args.server == "freecad-mcp-nekanat":
        expected = [
            "uv",
            "tool",
            "run",
            "--with",
            "mcp[cli]==1.28.1",
            "--from",
            "git+https://github.com/neka-nat/freecad-mcp.git@63acb305573194a011641ab13ccfb391fe95769f",
            "freecad-mcp",
            "--only-text-feedback",
        ]
        if command != expected:
            raise ValueError("Catalog must pin the reviewed FreeCAD MCP commit")
        os.environ["FREECAD_MCP_WORK_DIR"] = str(root / "freecad-work")
    elif args.server == "oasis-open-fem-agent":
        expected = [
            "uv",
            "run",
            "--isolated",
            "--python",
            "3.12",
            "--with",
            "git+https://github.com/Hereon-InstituteMS/OASiS.git@7c184d5b7ca5cda6086f3912d1c7923c58307780",
            "--with",
            "mcp[cli]==1.28.1",
            "--with",
            "scikit-fem==12.0.2",
            "python",
            "-m",
            "server",
        ]
        if command != expected:
            raise ValueError("Catalog must pin the reviewed OASiS MCP commit")
        os.environ["PYVISTA_OFF_SCREEN"] = "true"
    elif args.server == "rosbag-mcp-pypi":
        expected = [
            "uv",
            "run",
            "--isolated",
            "--python",
            "3.12",
            "--with",
            "rosbag-mcp==0.2.0",
            "--with",
            "mcp==1.28.1",
            "--with",
            "rosbags==0.11.5",
            "--with",
            "numpy==2.5.3",
            "--with",
            "matplotlib==3.11.1",
            "--with",
            "pillow==12.3.0",
            "rosbag-mcp",
        ]
        if command != expected:
            raise ValueError("Catalog must pin the reviewed ROSBag MCP package")
        rosbag_path = await generate_rosbag_fixture(root)
    elif args.server == "blender-mcp":
        expected = [
            "uv",
            "tool",
            "run",
            "--python",
            "3.11",
            "--from",
            "git+https://github.com/ahujasid/blender-mcp.git@5f8ddaf6e987c4aa0c3467fcc548838b28f64477",
            "blender-mcp",
        ]
        if command != expected:
            raise ValueError("Catalog must pin the reviewed Blender MCP commit")
        addon_path_value = os.getenv("BLENDER_MCP_ADDON_PATH")
        if not addon_path_value:
            raise ValueError("BLENDER_MCP_ADDON_PATH is required for Blender qualification")
        addon_path = Path(addon_path_value).resolve()
        if not addon_path.is_file():
            raise ValueError("Reviewed Blender MCP addon source is unavailable")
        blender_process, blender_log = await start_blender_bridge(
            root, addon_path, "initial"
        )
    elif args.server == "autocad-mcp-u-c4n":
        expected = [
            "uv",
            "tool",
            "run",
            "--python",
            "3.11",
            "--from",
            "git+https://github.com/U-C4N/Autocad-MCP.git@abc2a82e7128358b9e228a7d9442b37019aa3fe5",
            "autocad-mcp",
        ]
        if command != expected:
            raise ValueError("Catalog must pin the reviewed AutoCAD MCP commit")
        os.environ["ALLOWED_PATHS"] = str(root)
        # Structured required environment variables are intentionally loaded
        # through Wright's credential store rather than inherited ambient env.
        # This is non-secret configuration, but recording it exercises the same
        # production path users use for required per-installation values.
        from tool_registry.secrets import write_secrets

        write_secrets(entry.id, {"ALLOWED_PATHS": str(root)})
    elif args.server == "rhino-mcp-easehee":
        expected = [
            "uv",
            "tool",
            "run",
            "--python",
            "3.11",
            "--from",
            "git+https://github.com/EaseHee/rhino-mcp.git@3e10efb9963be36ee1209f8f9ebd2cc6efcfcc46",
            "rhino3dm-mcp",
        ]
        if command != expected:
            raise ValueError("Catalog must pin the reviewed Rhino MCP commit")
    report.update(
        {
            "server_id": entry.id,
            "observed_at": datetime.now(UTC).isoformat(),
            "wright_revision": args.wright_revision,
            "environment": args.environment,
            "platform": args.platform,
            "container_image": args.container_image,
            "source_url": entry.source_url,
            "status": "partial",
            "steps": [],
            "adoption": "unknown",
            "scope": {
                "autodesk-product-help-mcp": "Autodesk help product discovery",
                "openscad-mcp": "OpenSCAD cube STL export",
                "brep-mcp": "BREP box STEP and STL export",
                "freecad-mcp-nekanat": "FreeCAD box creation and STL export",
                "oasis-open-fem-agent": "OASiS scikit-fem Poisson solve",
                "rosbag-mcp-pypi": "ROS 2 known-message retrieval",
                "blender-mcp": "Blender dimensioned box STL export",
                "autocad-mcp-u-c4n": "AutoCAD headless mechanical DXF authoring",
                "rhino-mcp-easehee": "Rhino standalone 3DM and mesh authoring",
            }[args.server],
            "configuration_sha256": qualification_configuration(entry),
            "installed_items": args.installed_item,
            "source_references": args.source_reference,
            "prerequisites": args.prerequisite,
        }
    )
    discovered = None
    probe = None
    isolated_python = {"oasis-open-fem-agent", "rosbag-mcp-pypi"}
    direct_env = dict(entry.launch_env or {})
    if args.server in isolated_python:
        direct_env["PYTHONPATH"] = ""
    if args.server == "autocad-mcp-u-c4n":
        direct_env["ALLOWED_PATHS"] = str(root)
    direct_env = direct_env or None
    direct_cwd = str(root) if args.server == "rosbag-mcp-pypi" else None
    for attempt in range(3):
        async with client_session(command, direct_env, direct_cwd) as client:
            info = await client.initialize()
            tools = await client.list_tools()
            selected = {tool.name: tool for tool in tools.tools}
            report["server_info"] = info.serverInfo.model_dump(mode="json")
            report["tool_schema_sha256"] = digest(
                [tool.model_dump(mode="json") for tool in tools.tools]
            )
            report["tool_count"] = len(tools.tools)
            discovered = tools.tools
            if args.server == "autodesk-product-help-mcp":
                probe = ("get_available_products", {})
            elif args.server == "openscad-mcp":
                report["export_schema"] = selected["export_model"].inputSchema
                output = root / f"direct-{attempt}.stl"
                properties = selected["export_model"].inputSchema.get("properties", {})
                # Only known parameter shapes for this deterministic export.
                values = {"scad_content": "cube([10,8,6]);"}
                if "export_format" in properties:
                    values["export_format"] = "stl"
                elif "format" in properties:
                    values["format"] = "stl"
                elif "output_format" in properties:
                    values["output_format"] = "stl"
                else:
                    raise ValueError(
                        "Export format parameter changed; recipe review required"
                    )
                if "output_path" in properties:
                    values["output_path"] = str(output)
                elif "output_file" in properties:
                    values["output_file"] = str(output)
                else:
                    raise ValueError(
                        "Export output parameter changed; recipe review required"
                    )
                probe = ("export_model", values)
            elif args.server == "brep-mcp":
                report["export_schema"] = selected["export_part"].inputSchema
                output = root / f"direct-{attempt}"
                output.mkdir()
                probe = (
                    "export_part",
                    {
                        "code": (
                            'import { box } from "brepjs";\n'
                            "export const expected = { volume: 8000, tolerancePct: 0.1 };\n"
                            "export default () => box(40, 20, 10);\n"
                        ),
                        "outDir": str(output),
                        "formats": {"step": True, "stl": True},
                    },
                )
            elif args.server == "freecad-mcp-nekanat":
                required = {
                    "create_document",
                    "create_object",
                    "get_objects",
                    "execute_code",
                }
                assert required <= selected.keys(), "FreeCAD tool surface is incomplete"
                report["execute_schema"] = selected["execute_code"].inputSchema
                output = root / f"direct-{attempt}.stl"
                probe = freecad_probe(output, f"WrightDirect{attempt}")
            elif args.server == "oasis-open-fem-agent":
                required = {"discover", "prepare_simulation", "run_simulation"}
                assert required <= selected.keys(), "OASiS tool surface is incomplete"
                report["run_schema"] = selected["run_simulation"].inputSchema
                probe = oasis_probe(f"wright-direct-{attempt}")
            elif args.server == "rosbag-mcp-pypi":
                required = {"list_bags", "bag_info", "get_message_at_time"}
                assert required <= selected.keys(), "ROSBag MCP tool surface is incomplete"
                report["message_schema"] = selected["get_message_at_time"].inputSchema
                info = await client.call_tool("bag_info", {"bag_path": str(rosbag_path)})
                info_payload = _json_result(info)
                assert info_payload["message_count"] == 2, (
                    "ROSBag MCP returned the wrong message count"
                )
                probe = (
                    "get_message_at_time",
                    {
                        "topic": "/chatter",
                        "timestamp": 1700000000.0,
                        "bag_path": str(rosbag_path),
                        "tolerance": 0.01,
                    },
                )
            elif args.server == "blender-mcp":
                required = {
                    "get_scene_info",
                    "get_object_info",
                    "execute_blender_code",
                }
                assert required <= selected.keys(), "Blender MCP tool surface is incomplete"
                report["execute_schema"] = selected["execute_blender_code"].inputSchema
                scene_result = await client.call_tool(
                    "get_scene_info", {"user_prompt": ""}
                )
                assert not scene_result.isError and "scene" in _result_text(
                    scene_result
                ).lower(), "Blender scene inspection failed"
                output = root / f"direct-{attempt}.stl"
                probe = blender_probe(output, f"WrightDirect{attempt}")
            elif args.server == "autocad-mcp-u-c4n":
                required = {
                    "drawing_new",
                    "drawing_open",
                    "drawing_info",
                    "drawing_save_as",
                    "entity_create_rectangle",
                    "entity_create_circle",
                    "entity_create_line",
                }
                assert required <= selected.keys(), "AutoCAD lean tool surface is incomplete"
                assert len(tools.tools) == 47, "AutoCAD lean profile changed"
                report["save_schema"] = selected["drawing_save_as"].inputSchema
                if attempt:
                    previous = root / f"direct-{attempt - 1}.dxf"
                    reopened = await client.call_tool(
                        "drawing_open", {"path": str(previous)}
                    )
                    assert not reopened.isError, "AutoCAD could not reopen its prior DXF"
                    prior_info = await client.call_tool("drawing_info", {})
                    assert not prior_info.isError and "4" in _result_text(prior_info), (
                        "AutoCAD reopened a different entity inventory"
                    )
                created = await client.call_tool(
                    "drawing_new", {"template": None, "bootstrap": False}
                )
                assert not created.isError, "AutoCAD could not create a drawing"
                for tool_name, values in (
                    (
                        "entity_create_rectangle",
                        {"x1": 0, "y1": 0, "x2": 100, "y2": 60},
                    ),
                    (
                        "entity_create_circle",
                        {"cx": 20, "cy": 30, "radius": 5},
                    ),
                    (
                        "entity_create_circle",
                        {"cx": 80, "cy": 30, "radius": 5},
                    ),
                    (
                        "entity_create_line",
                        {"x1": 50, "y1": 0, "x2": 50, "y2": 60},
                    ),
                ):
                    created = await client.call_tool(tool_name, values)
                    assert not created.isError, f"AutoCAD failed at {tool_name}"
                output = root / f"direct-{attempt}.dxf"
                probe = ("drawing_save_as", {"path": str(output), "format": "dxf"})
            elif args.server == "rhino-mcp-easehee":
                required = {
                    "rhino_open",
                    "rhino_save",
                    "rhino_export_stl",
                    "rhino_document_units_set",
                    "rhino_document_summary",
                    "rhino_mesh_box",
                    "rhino_object_info",
                }
                assert required <= selected.keys(), "Rhino tool surface is incomplete"
                report["save_schema"] = selected["rhino_save"].inputSchema
                if attempt:
                    previous = root / f"direct-{attempt - 1}.3dm"
                    reopened = await client.call_tool(
                        "rhino_open",
                        {"path": str(previous), "doc_id": f"reopen-{attempt}"},
                    )
                    assert not reopened.isError, "Rhino could not reopen its prior 3DM"
                    prior_summary = await client.call_tool(
                        "rhino_document_summary", {"args": {"doc_id": f"reopen-{attempt}"}}
                    )
                    assert not prior_summary.isError and "mesh" in _result_text(prior_summary).lower(), (
                        "Rhino reopened a different object inventory"
                    )
                units = await client.call_tool(
                    "rhino_document_units_set",
                    {"args": {"doc_id": "active", "units": "mm", "scale_existing": False}},
                )
                assert not units.isError, "Rhino could not set millimetre units"
                created = await client.call_tool(
                    "rhino_mesh_box",
                    {
                        "args": {
                            "doc_id": "active",
                            "corner": {"x": 0, "y": 0, "z": 0},
                            "size_x": 10,
                            "size_y": 8,
                            "size_z": 6,
                            "name": f"WrightDirect{attempt}",
                        }
                    },
                )
                assert not created.isError, "Rhino could not create the mesh box"
                created_payload = _json_result(created)
                object_id = created_payload["summary"]["object_id"]
                object_info = await client.call_tool(
                    "rhino_object_info",
                    {"args": {"doc_id": "active", "object_id": object_id}},
                )
                object_text = _result_text(object_info).lower()
                assert not object_info.isError and all(
                    marker in object_text for marker in ("mesh", "vertex_count", "face_count")
                ), "Rhino object inspection is incomplete"
                model_output = root / f"direct-{attempt}.3dm"
                saved = await client.call_tool(
                    "rhino_save",
                    {"args": {"doc_id": "active", "path": str(model_output), "version": 8}},
                )
                assert not saved.isError, "Rhino could not save the 3DM"
                output = root / f"direct-{attempt}.stl"
                probe = (
                    "rhino_export_stl",
                    {"args": {"doc_id": "active", "path": str(output)}},
                )
            else:
                raise ValueError("Qualification recipe is incomplete")
            result = await client.call_tool(*probe)
            assert not result.isError, "Backend reported an error"
            if args.server == "autodesk-product-help-mcp":
                serialized = result.model_dump_json()
                assert "fusion" in serialized.lower() and len(serialized) > 100, (
                    "Expected Autodesk product evidence missing"
                )
                report["outcome"] = {
                    "result_sha256": hashlib.sha256(serialized.encode()).hexdigest(),
                    "contains_fusion": True,
                }
            elif args.server == "openscad-mcp":
                report["outcome"] = cube_oracle(output)
            elif args.server == "brep-mcp":
                report["outcome"] = brep_oracle(output)
            elif args.server == "freecad-mcp-nekanat":
                serialized = result.model_dump_json()
                assert "wrightbox" in serialized.lower() and "480" in serialized, (
                    "FreeCAD result did not report the created box"
                )
                report["outcome"] = cube_oracle(output)
            elif args.server == "oasis-open-fem-agent":
                report["outcome"] = oasis_oracle(result, f"wright-direct-{attempt}")
            elif args.server == "rosbag-mcp-pypi":
                report["outcome"] = {
                    "artifact": rosbag_artifact_oracle(rosbag_path),
                    "server": rosbag_result_oracle(result),
                }
            elif args.server == "blender-mcp":
                assert "executed successfully" in _result_text(result).lower(), (
                    "Blender did not report successful code execution"
                )
                object_result = await client.call_tool(
                    "get_object_info", {"object_name": f"WrightDirect{attempt}"}
                )
                assert not object_result.isError, "Blender object inspection failed"
                report["outcome"] = {
                    "artifact": cube_oracle(output),
                    "object": blender_object_oracle(
                        object_result, f"WrightDirect{attempt}"
                    ),
                }
            elif args.server == "autocad-mcp-u-c4n":
                info_result = await client.call_tool("drawing_info", {})
                assert not info_result.isError and "ezdxf" in _result_text(info_result).lower(), (
                    "AutoCAD did not report the reviewed headless backend"
                )
                report["outcome"] = autocad_dxf_oracle(output)
            elif args.server == "rhino-mcp-easehee":
                report["outcome"] = rhino_artifact_oracle(model_output, output)
            report["steps"].append(
                {
                    "stage": "direct_protocol_backend_outcome",
                    "attempt": attempt + 1,
                    "status": "passed",
                }
            )
            if args.server == "brep-mcp" and attempt == 0:
                invalid_output = root / "controlled-error"
                invalid_output.mkdir()
                invalid = await client.call_tool(
                    "export_part",
                    {
                        "code": "export default () => null;\n",
                        "outDir": str(invalid_output),
                        "formats": {"step": True},
                    },
                )
                assert invalid.isError, "Invalid BREP program was reported as successful"
                assert not list(invalid_output.iterdir()), (
                    "Invalid BREP program left an export artifact"
                )
                report["steps"].append(
                    {"stage": "controlled_error_behavior", "status": "passed"}
                )
                timeout = await client.call_tool(
                    "run_program",
                    {
                        "code": (
                            "export default () => { while (true) {} };\n"
                        ),
                        "timeoutMs": 250,
                    },
                )
                timeout_text = timeout.model_dump_json().lower()
                assert timeout.isError and "timeout" in timeout_text, (
                    "BREP sandbox did not report its bounded timeout"
                )
                report["steps"].append(
                    {"stage": "bounded_timeout_cancellation", "status": "passed"}
                )
            if args.server == "freecad-mcp-nekanat" and attempt == 0:
                invalid = await client.call_tool(
                    "execute_code", {"code": 'raise RuntimeError("wright-controlled-error")'}
                )
                invalid_text = invalid.model_dump_json().lower()
                assert "wright-controlled-error" in invalid_text, (
                    "FreeCAD MCP did not return the controlled backend error"
                )
                report["steps"].append(
                    {
                        "stage": "controlled_error_reported_in_content",
                        "status": "passed",
                    }
                )
            if args.server == "oasis-open-fem-agent" and attempt == 0:
                invalid = await client.call_tool(
                    "run_simulation",
                    {
                        "solver": "skfem",
                        "input_content": "from skfem import MeshTri\nthis is invalid python\n",
                        "job_name": "wright-controlled-error",
                    },
                )
                invalid_payload = _json_result(invalid)
                assert invalid_payload["status"] == "failed", (
                    "OASiS did not report the controlled solver failure"
                )
                assert invalid_payload["trustworthy_result"] is False, (
                    "OASiS treated a failed solve as verified"
                )
                assert not (Path(invalid_payload["work_dir"]) / "result.vtu").exists(), (
                    "Failed OASiS solve left a result artifact"
                )
                report["steps"].append(
                    {"stage": "controlled_solver_error", "status": "passed"}
                )
            if args.server == "rosbag-mcp-pypi" and attempt == 0:
                missing = await client.call_tool(
                    "bag_info", {"bag_path": str(root / "missing-bag")}
                )
                missing_text = missing.model_dump_json().lower()
                assert (
                    missing.isError
                    or "not found" in missing_text
                    or "exist" in missing_text
                    or "no such file" in missing_text
                ), (
                    "ROSBag MCP did not report a missing bag"
                )
                report["steps"].append(
                    {
                        "stage": "controlled_missing_bag_error_in_content",
                        "status": "passed",
                    }
                )
            if args.server == "blender-mcp" and attempt == 0:
                invalid = await client.call_tool(
                    "execute_blender_code",
                    {"code": 'raise RuntimeError("wright-controlled-error")'},
                )
                assert "wright-controlled-error" in invalid.model_dump_json().lower(), (
                    "Blender MCP did not report the controlled backend error"
                )
                report["steps"].append(
                    {
                        "stage": "controlled_error_reported_in_content",
                        "status": "passed",
                    }
                )
                await stop_blender_bridge(blender_process)
                disconnected = await client.call_tool(
                    "get_scene_info", {"user_prompt": ""}
                )
                disconnect_text = disconnected.model_dump_json().lower()
                report["disconnect_diagnostic"] = disconnect_text[:500]
                assert disconnected.isError or any(
                    marker in disconnect_text
                    for marker in (
                        "could not connect",
                        "connection",
                        "broken pipe",
                        "reset by peer",
                        "refused",
                    )
                ), (
                    "Blender MCP did not report the disconnected add-on"
                )
                blender_process, blender_log = await start_blender_bridge(
                    root, addon_path, "recovered"
                )
                recovered = await client.call_tool(
                    "get_scene_info", {"user_prompt": ""}
                )
                assert "cube" in _result_text(recovered).lower(), (
                    "Blender MCP did not reconnect to the restarted add-on"
                )
                report["steps"].append(
                    {
                        "stage": "addon_disconnect_and_recovery",
                        "status": "passed",
                    }
                )
            if args.server == "autocad-mcp-u-c4n" and attempt == 0:
                outside = root.parent / f"{root.name}-outside.dxf"
                outside.unlink(missing_ok=True)
                invalid = await client.call_tool(
                    "drawing_save_as", {"path": str(outside), "format": "dxf"}
                )
                assert invalid.isError and not outside.exists(), (
                    "AutoCAD path boundary did not reject an out-of-workspace write"
                )
                report["steps"].append(
                    {"stage": "controlled_path_boundary_error", "status": "passed"}
                )
            if args.server == "rhino-mcp-easehee" and attempt == 0:
                invalid = await client.call_tool(
                    "rhino_mesh_box",
                    {
                        "args": {
                            "doc_id": "active",
                            "corner": {"x": 0, "y": 0, "z": 0},
                            "size_x": -1,
                            "size_y": 8,
                            "size_z": 6,
                        }
                    },
                )
                assert invalid.isError, "Rhino accepted an invalid negative dimension"
                report["steps"].append(
                    {"stage": "controlled_schema_error", "status": "passed"}
                )

    run_migrations()
    db = str(root / "wright.db")
    seed = catalog_entry_to_mcp_seed(entry)
    seed.update(
        server_id=entry.id,
        command=command,
        is_active=False,
        is_installed=True,
        status="inactive",
        created_at=1,
        updated_at=1,
    )
    server = McpServer.model_validate(seed)
    insert_server(db, server)
    insert_tools(
        db,
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
            for tool in discovered
        ],
    )
    workspace = root / "workspace"
    workspace.mkdir()
    if args.server == "rosbag-mcp-pypi":
        workspace_bag = workspace / "wright_chatter"
        shutil.copytree(rosbag_path, workspace_bag)
    WorkspaceRepository(db, secrets=FileSecretProvider(root / "secrets.json")).create(
        "qualification-workspace",
        "qualification-session",
        str(workspace),
        workspace_name="Disposable qualification",
    )
    from contextlib import closing

    with closing(sqlite3.connect(db)) as connection:
        connection.execute(
            "UPDATE engineering_workspaces SET enabled_tools=? WHERE workspace_id=?",
            (json.dumps([entry.id]), "qualification-workspace"),
        )
        connection.commit()
    repository = GatewayRepository(db)
    engine = McpEngine(db, operation_timeout=90)
    gateway = GatewayService(
        workspaces=DatabaseGatewayWorkspace(repository),
        catalog=DatabaseGatewayCatalog(db),
        lifecycle=EngineGatewayLifecycle(engine),
        audit=DatabaseGatewayAudit(repository),
        notifier=GatewayNotificationHub(),
        operation_timeout=90,
    )
    try:
        gateway.open_session(
            session_id="qualification-session",
            principal_id="qualification-operator",
            workspace_id="qualification-workspace",
            transport="stdio",
        )
        gateway.initialize_session(
            "qualification-session",
            protocol_version="2025-11-25",
            client_name="wright-curation-qualification",
            client_version="1",
            client_capabilities={},
        )
        name = f"{entry.id}__{probe[0]}"
        assert name in {
            tool.name for tool in gateway.list_tools("qualification-session")
        }
        # Only the fixed disposable scenario is approved by this opt-in operator run.
        scenario_tool_names = {name}
        if args.server == "autocad-mcp-u-c4n":
            scenario_tool_names.update(
                f"{entry.id}__{tool_name}"
                for tool_name in (
                    "drawing_new",
                    "entity_create_rectangle",
                    "entity_create_circle",
                    "entity_create_line",
                )
            )
        elif args.server == "rhino-mcp-easehee":
            scenario_tool_names.update(
                f"{entry.id}__{tool_name}"
                for tool_name in (
                    "rhino_document_units_set",
                    "rhino_mesh_box",
                    "rhino_save",
                )
            )
        approvals = {
            gate
            for tool in gateway.list_tools("qualification-session")
            if tool.name in scenario_tool_names
            for gate in tool.required_approvals
        }
        if args.server == "openscad-mcp":
            for field in ("output_path", "output_file"):
                if field in probe[1]:
                    probe[1][field] = str(workspace / "gateway.stl")
        elif args.server == "brep-mcp":
            gateway_output = workspace / "gateway-brep"
            gateway_output.mkdir()
            probe[1]["outDir"] = str(gateway_output)
        elif args.server == "freecad-mcp-nekanat":
            probe = freecad_probe(workspace / "gateway.stl", "WrightGateway")
        elif args.server == "oasis-open-fem-agent":
            probe = oasis_probe("wright-gateway")
        elif args.server == "rosbag-mcp-pypi":
            probe = (
                "get_message_at_time",
                {
                    "topic": "/chatter",
                    "timestamp": 1700000000.0,
                    "bag_path": str(workspace_bag),
                    "tolerance": 0.01,
                },
            )
        elif args.server == "blender-mcp":
            probe = blender_probe(workspace / "gateway.stl", "WrightGateway")
        elif args.server == "autocad-mcp-u-c4n":
            gateway_output = workspace / "gateway.dxf"
            for step, (tool_name, values) in enumerate(
                (
                    ("drawing_new", {"template": None, "bootstrap": False}),
                    (
                        "entity_create_rectangle",
                        {"x1": 0, "y1": 0, "x2": 100, "y2": 60},
                    ),
                    (
                        "entity_create_circle",
                        {"cx": 20, "cy": 30, "radius": 5},
                    ),
                    (
                        "entity_create_circle",
                        {"cx": 80, "cy": 30, "radius": 5},
                    ),
                    (
                        "entity_create_line",
                        {"x1": 50, "y1": 0, "x2": 50, "y2": 60},
                    ),
                )
            ):
                setup_result = await gateway.call_tool(
                    "qualification-session",
                    f"qualification-setup-{step}",
                    f"{entry.id}__{tool_name}",
                    values,
                    workspace_approvals=approvals,
                )
                assert not setup_result.is_error, f"Gateway failed at {tool_name}"
            probe = (
                "drawing_save_as",
                {"path": str(gateway_output), "format": "dxf"},
            )
        elif args.server == "rhino-mcp-easehee":
            gateway_model_output = workspace / "gateway.3dm"
            gateway_mesh_output = workspace / "gateway.stl"
            for step, (tool_name, values) in enumerate(
                (
                    (
                        "rhino_document_units_set",
                        {"args": {"doc_id": "active", "units": "mm", "scale_existing": False}},
                    ),
                    (
                        "rhino_mesh_box",
                        {
                            "args": {
                                "doc_id": "active",
                                "corner": {"x": 0, "y": 0, "z": 0},
                                "size_x": 10,
                                "size_y": 8,
                                "size_z": 6,
                                "name": "WrightGateway",
                            }
                        },
                    ),
                    (
                        "rhino_save",
                        {
                            "args": {
                                "doc_id": "active",
                                "path": str(gateway_model_output),
                                "version": 8,
                            }
                        },
                    ),
                )
            ):
                setup_result = await gateway.call_tool(
                    "qualification-session",
                    f"qualification-setup-{step}",
                    f"{entry.id}__{tool_name}",
                    values,
                    workspace_approvals=approvals,
                )
                assert not setup_result.is_error, f"Gateway failed at {tool_name}"
            probe = (
                "rhino_export_stl",
                {"args": {"doc_id": "active", "path": str(gateway_mesh_output)}},
            )
        result = await gateway.call_tool(
            "qualification-session",
            "qualification-call",
            name,
            probe[1],
            workspace_approvals=approvals,
        )
        assert not result.is_error, f"Gateway failed: {result.error_code}"
        if args.server == "openscad-mcp":
            report["gateway_outcome"] = cube_oracle(workspace / "gateway.stl")
        elif args.server == "autodesk-product-help-mcp":
            assert (
                "fusion"
                in json.dumps(
                    {
                        "content": result.content,
                        "structured": result.structured_content,
                    },
                    default=str,
                ).lower()
            ), "Gateway result lost the expected product"
        elif args.server == "brep-mcp":
            report["gateway_outcome"] = brep_oracle(gateway_output)
        elif args.server == "freecad-mcp-nekanat":
            report["gateway_outcome"] = cube_oracle(workspace / "gateway.stl")
        elif args.server == "oasis-open-fem-agent":
            report["gateway_outcome"] = oasis_oracle(result, "wright-gateway")
        elif args.server == "rosbag-mcp-pypi":
            report["gateway_outcome"] = {
                "artifact": rosbag_artifact_oracle(workspace_bag),
                "server": rosbag_result_oracle(result),
            }
        elif args.server == "blender-mcp":
            assert "executed successfully" in json.dumps(
                {"content": result.content, "structured": result.structured_content},
                default=str,
            ).lower(), "Blender gateway did not report successful execution"
            report["gateway_outcome"] = cube_oracle(workspace / "gateway.stl")
        elif args.server == "autocad-mcp-u-c4n":
            report["gateway_outcome"] = autocad_dxf_oracle(gateway_output)
        elif args.server == "rhino-mcp-easehee":
            report["gateway_outcome"] = rhino_artifact_oracle(
                gateway_model_output, gateway_mesh_output
            )
        report["steps"].append(
            {"stage": "wright_gateway_backend_outcome", "status": "passed"}
        )
        report["status"] = "passed"
    finally:
        from tool_registry.db import get_server

        child = get_server(db, entry.id)
        report["gateway_child"] = {
            "status": child.status,
            "diagnostic": child.error_message,
        }
        await gateway.shutdown()
    # Exercise the actual Hermes-facing MCP transport and production composition.
    insert_tools(
        db,
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
            for tool in discovered
        ],
    )
    async with client_session(
        [
            sys.executable,
            "-m",
            "api.gateway_stdio",
            "--session-id",
            "qualification-session",
            "--workspace-id",
            "qualification-workspace",
            "--principal-id",
            "qualification-operator",
        ]
    ) as client:
        await client.initialize()
        listed = await client.list_tools()
        assert name in {tool.name for tool in listed.tools}, (
            "Prefixed tool missing from gateway MCP"
        )
        if args.server == "brep-mcp":
            gateway_mcp_output = workspace / "gateway-mcp-brep"
            gateway_mcp_output.mkdir()
            probe[1]["outDir"] = str(gateway_mcp_output)
        elif args.server == "freecad-mcp-nekanat":
            probe = freecad_probe(
                workspace / "gateway-mcp.stl", "WrightGatewayMcp"
            )
        elif args.server == "oasis-open-fem-agent":
            probe = oasis_probe("wright-gateway-mcp")
        elif args.server == "blender-mcp":
            probe = blender_probe(
                workspace / "gateway-mcp.stl", "WrightGatewayMcp"
            )
        elif args.server == "autocad-mcp-u-c4n":
            gateway_mcp_output = workspace / "gateway-mcp.dxf"
            for tool_name, values in (
                ("drawing_new", {"template": None, "bootstrap": False}),
                (
                    "entity_create_rectangle",
                    {"x1": 0, "y1": 0, "x2": 100, "y2": 60},
                ),
                (
                    "entity_create_circle",
                    {"cx": 20, "cy": 30, "radius": 5},
                ),
                (
                    "entity_create_circle",
                    {"cx": 80, "cy": 30, "radius": 5},
                ),
                (
                    "entity_create_line",
                    {"x1": 50, "y1": 0, "x2": 50, "y2": 60},
                ),
            ):
                setup_result = await client.call_tool(
                    f"{entry.id}__{tool_name}", values
                )
                assert not setup_result.isError, f"Gateway MCP failed at {tool_name}"
            probe = (
                "drawing_save_as",
                {"path": str(gateway_mcp_output), "format": "dxf"},
            )
        elif args.server == "rhino-mcp-easehee":
            gateway_mcp_model_output = workspace / "gateway-mcp.3dm"
            gateway_mcp_mesh_output = workspace / "gateway-mcp.stl"
            for tool_name, values in (
                (
                    "rhino_document_units_set",
                    {"args": {"doc_id": "active", "units": "mm", "scale_existing": False}},
                ),
                (
                    "rhino_mesh_box",
                    {
                        "args": {
                            "doc_id": "active",
                            "corner": {"x": 0, "y": 0, "z": 0},
                            "size_x": 10,
                            "size_y": 8,
                            "size_z": 6,
                            "name": "WrightGatewayMcp",
                        }
                    },
                ),
                (
                    "rhino_save",
                    {
                        "args": {
                            "doc_id": "active",
                            "path": str(gateway_mcp_model_output),
                            "version": 8,
                        }
                    },
                ),
            ):
                setup_result = await client.call_tool(
                    f"{entry.id}__{tool_name}", values
                )
                assert not setup_result.isError, f"Gateway MCP failed at {tool_name}"
            probe = (
                "rhino_export_stl",
                {"args": {"doc_id": "active", "path": str(gateway_mcp_mesh_output)}},
            )
        result = await client.call_tool(name, probe[1])
        assert not result.isError, (
            f"Gateway MCP rejected the scenario: {result.model_dump_json()[:300]}"
        )
        if args.server == "openscad-mcp":
            report["gateway_mcp_outcome"] = cube_oracle(workspace / "gateway.stl")
        elif args.server == "autodesk-product-help-mcp":
            assert "fusion" in result.model_dump_json().lower(), (
                "Gateway MCP lost the expected product"
            )
        elif args.server == "brep-mcp":
            report["gateway_mcp_outcome"] = brep_oracle(gateway_mcp_output)
        elif args.server == "freecad-mcp-nekanat":
            report["gateway_mcp_outcome"] = cube_oracle(
                workspace / "gateway-mcp.stl"
            )
        elif args.server == "oasis-open-fem-agent":
            report["gateway_mcp_outcome"] = oasis_oracle(
                result, "wright-gateway-mcp"
            )
        elif args.server == "rosbag-mcp-pypi":
            report["gateway_mcp_outcome"] = {
                "artifact": rosbag_artifact_oracle(workspace_bag),
                "server": rosbag_result_oracle(result),
            }
        elif args.server == "blender-mcp":
            assert "executed successfully" in result.model_dump_json().lower(), (
                "Blender gateway MCP did not report successful execution"
            )
            report["gateway_mcp_outcome"] = cube_oracle(
                workspace / "gateway-mcp.stl"
            )
        elif args.server == "autocad-mcp-u-c4n":
            report["gateway_mcp_outcome"] = autocad_dxf_oracle(gateway_mcp_output)
        elif args.server == "rhino-mcp-easehee":
            report["gateway_mcp_outcome"] = rhino_artifact_oracle(
                gateway_mcp_model_output, gateway_mcp_mesh_output
            )
        report["steps"].append(
            {"stage": "hermes_facing_gateway_mcp_backend_outcome", "status": "passed"}
        )
    if args.server == "oasis-open-fem-agent" and os.name != "nt":
        timeout_runner = StdioRunner(
            command, env={"PYTHONPATH": ""}, operation_timeout=1
        )
        await timeout_runner.start()
        try:
            try:
                await timeout_runner.call_tool(*oasis_probe("wright-timeout", slow=True))
            except TimeoutError:
                pass
            else:
                raise AssertionError("OASiS slow solve exceeded Wright's deadline")
            assert not timeout_runner.is_running(), (
                "Wright kept the timed-out OASiS transport running"
            )
            await asyncio.sleep(0.25)
            remaining = []
            for cmdline_path in Path("/proc").glob("[0-9]*/cmdline"):
                try:
                    cmdline = cmdline_path.read_bytes().replace(b"\0", b" ")
                except (FileNotFoundError, PermissionError, ProcessLookupError):
                    continue
                if b"simulation_outputs/wright-timeout/solve.py" in cmdline:
                    remaining.append(cmdline_path.parent.name)
            assert not remaining, (
                f"Timed-out OASiS solver processes remain: {remaining}"
            )
            report["steps"].append(
                {"stage": "wright_timeout_process_tree_cleanup", "status": "passed"}
            )
        finally:
            await timeout_runner.stop()
    if args.server == "blender-mcp":
        await stop_blender_bridge(blender_process)
        await asyncio.sleep(0.25)
        try:
            _reader, writer = await asyncio.open_connection("127.0.0.1", 9876)
        except OSError:
            pass
        else:
            writer.close()
            await writer.wait_closed()
            raise AssertionError("Blender add-on port remained open after cleanup")
        report["blender_log_sha256"] = hashlib.sha256(
            blender_log.read_bytes()
        ).hexdigest()
        report["steps"].append(
            {"stage": "blender_process_group_cleanup", "status": "passed"}
        )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument(
        "--server",
        choices=[
            "openscad-mcp",
            "autodesk-product-help-mcp",
            "brep-mcp",
            "freecad-mcp-nekanat",
            "oasis-open-fem-agent",
            "rosbag-mcp-pypi",
            "blender-mcp",
            "autocad-mcp-u-c4n",
            "rhino-mcp-easehee",
        ],
        required=True,
    )
    parser.add_argument("--wright-revision", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--container-image")
    parser.add_argument("--installed-item", action="append", default=[])
    parser.add_argument("--source-reference", action="append", default=[])
    parser.add_argument("--prerequisite", action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-parent", type=Path)
    args = parser.parse_args()
    if args.work_parent:
        args.work_parent = args.work_parent.resolve()
        args.work_parent.mkdir(parents=True, exist_ok=True)
    from core.redaction import redact_mapping

    report = {}
    temporary = tempfile.TemporaryDirectory(
        prefix="wright-qualification-", dir=args.work_parent
    )
    try:
        asyncio.run(
            asyncio.wait_for(run(args, Path(temporary.name), report), timeout=360)
        )
    except Exception as error:
        report.update(
            server_id=args.server,
            status="failed",
            error=type(error).__name__,
            diagnostic=str(error)[:500],
        )
        causes = []
        cause = error.__cause__
        while cause is not None and len(causes) < 5:
            causes.append({"type": type(cause).__name__, "message": str(cause)[:500]})
            cause = cause.__cause__
        report["causes"] = causes
        if isinstance(error, BaseExceptionGroup):
            report["sub_errors"] = exception_leaves(error)
    finally:
        import gc

        if os.name != "nt":
            for process_group in tuple(_blender_process_groups):
                try:
                    os.killpg(process_group, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                finally:
                    _blender_process_groups.discard(process_group)
        gc.collect()
        try:
            temporary.cleanup()
            report["cleanup"] = "passed"
        except OSError:
            report.update(
                status="failed",
                cleanup="failed",
                cleanup_reason="Disposable files remain locked",
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(redact_mapping(report), indent=2, default=str) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {
                "server_id": args.server,
                "status": report.get("status"),
                "output": str(args.output),
            }
        )
    )
    return 0 if report.get("status") == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
