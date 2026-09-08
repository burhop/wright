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
    else:
        rosbag_path = None
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
    direct_env = {"PYTHONPATH": ""} if args.server in isolated_python else None
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
            else:
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
            else:
                report["outcome"] = {
                    "artifact": rosbag_artifact_oracle(rosbag_path),
                    "server": rosbag_result_oracle(result),
                }
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
        approvals = {
            gate
            for tool in gateway.list_tools("qualification-session")
            if tool.name == name
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
        else:
            report["gateway_outcome"] = {
                "artifact": rosbag_artifact_oracle(workspace_bag),
                "server": rosbag_result_oracle(result),
            }
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
        else:
            report["gateway_mcp_outcome"] = {
                "artifact": rosbag_artifact_oracle(workspace_bag),
                "server": rosbag_result_oracle(result),
            }
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
