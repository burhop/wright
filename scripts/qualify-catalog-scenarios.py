"""Opt-in real MCP qualification. Run in a disposable Wright environment.

Only two reviewed, credential-free scenarios are allowed. Host prerequisites
must be installed in the selected disposable container, never the base image.
This runner produces evidence; it never promotes a catalog entry.
"""

from __future__ import annotations

import argparse
import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, default=str).encode()
    ).hexdigest()


@asynccontextmanager
async def client_session(command):
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
        async with stdio_client(
            StdioServerParameters(
                command=command[0], args=command[1:], env=dict(os.environ)
            )
        ) as (read, write):
            async with ClientSession(read, write) as client:
                yield client


def cube_oracle(path):
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
        abs(actual - expected) < 0.001 for actual, expected in zip(bounds, (10, 8, 6))
    ), "Incorrect cube dimensions"
    volume = 0.0
    for offset in range(0, len(points), 3):
        a, b, c = points[offset : offset + 3]
        volume += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            + a[1] * (b[2] * c[0] - b[0] * c[2])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        ) / 6
    assert abs(abs(volume) - 480) < 0.01, "Incorrect mesh volume"
    return {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "dimensions_mm": bounds,
        "volume_mm3": abs(volume),
    }


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
    import sqlite3

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
            "scope": "Autodesk help product discovery"
            if args.server == "autodesk-product-help-mcp"
            else "OpenSCAD cube STL export",
            "configuration_sha256": qualification_configuration(entry),
        }
    )
    discovered = None
    probe = None
    for attempt in range(3):
        async with client_session(command) as client:
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
            else:
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
            else:
                report["outcome"] = cube_oracle(output)
            report["steps"].append(
                {
                    "stage": "direct_protocol_backend_outcome",
                    "attempt": attempt + 1,
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
        else:
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
        result = await client.call_tool(name, probe[1])
        assert not result.isError, (
            f"Gateway MCP rejected the scenario: {result.model_dump_json()[:300]}"
        )
        if args.server == "openscad-mcp":
            report["gateway_mcp_outcome"] = cube_oracle(workspace / "gateway.stl")
        else:
            assert "fusion" in result.model_dump_json().lower(), (
                "Gateway MCP lost the expected product"
            )
        report["steps"].append(
            {"stage": "hermes_facing_gateway_mcp_backend_outcome", "status": "passed"}
        )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument(
        "--server", choices=["openscad-mcp", "autodesk-product-help-mcp"], required=True
    )
    parser.add_argument("--wright-revision", required=True)
    parser.add_argument("--environment", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--container-image")
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
            report["sub_errors"] = [
                {"type": type(item).__name__, "message": str(item)[:500]}
                for item in error.exceptions[:5]
            ]
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
