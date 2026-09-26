"""Configure local print-demo MCP tools in one isolated Wright workspace.

Run after the API has initialized its database and before activating the three
servers. This changes only the selected local database and workspace binding.
It never contacts a printer or changes the engineering generation campaign.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tool_registry.db import get_server, update_server
from tool_registry.models import McpServerCreate
from tool_registry.services import register_server
from workspace_service.adapters.runtime import (
    get_workspace_by_id,
    update_workspace_enabled_tools_by_workspace,
)


ROOT = Path(__file__).resolve().parents[1]
BLENDER_SOURCE = ROOT / ".local-run/feature-081-live/sources/blender-mcp/src"
SLICER = ROOT / ".local-run/feature-081-live/tools/bambu-studio-2.8.2.61/bambu-studio.exe"
PROFILES = ROOT / ".local-run/feature-081-live/tools/bambu-studio-2.8.2.61/resources/profiles/BBL"
PRINTER_SOURCE = ROOT / ".local-run/feature-081-live/sources/bambu-p1s-mcp"


def configure(
    database: Path, workspace_id: str, workspace: Path, port: int,
    include_printer: bool = False,
) -> None:
    python = ROOT / ".venv/Scripts/python.exe"
    for path in (python, BLENDER_SOURCE / "blender_mcp/server.py", SLICER, PROFILES):
        if not path.exists():
            raise FileNotFoundError(f"Print-demo prerequisite is missing: {path}")
    if not workspace.is_dir():
        raise ValueError(f"The isolated print-demo workspace is missing: {workspace}")
    record = get_workspace_by_id(str(database), workspace_id)
    if record is None or Path(record["local_path"]).resolve() != workspace:
        raise ValueError("The workspace ID and local directory do not match this database.")
    blender_id = "blender-mcp-ahujasid"
    if get_server(str(database), blender_id) is None:
        raise ValueError("Reconcile the catalogued Blender MCP server before configuring it.")
    update_server(str(database), blender_id, {
        "command": [str(python), "-m", "blender_mcp.server"],
        "launch_env": {
            "PYTHONPATH": str(BLENDER_SOURCE),
            "BLENDER_HOST": "127.0.0.1",
            "BLENDER_PORT": str(port),
            "BLENDER_MCP_SAFE_MODE": "true",
            "BLENDER_MCP_DISABLE_TELEMETRY": "true",
        },
        "is_installed": True,
    })
    shared_path = str(ROOT / "scripts") + ";" + str(BLENDER_SOURCE)
    fixed = (
        ("wright-printed-part-mesh-repair", "engineering_dataset_mesh_repair_mcp.py", {
            "WRIGHT_PRINT_WORKSPACE": str(workspace), "BLENDER_HOST": "127.0.0.1",
            "BLENDER_PORT": str(port), "PYTHONPATH": shared_path,
        }),
        ("wright-printed-part-slicer", "engineering_dataset_slice_mcp.py", {
            "WRIGHT_PRINT_WORKSPACE": str(workspace), "PYTHONPATH": shared_path,
        }),
    )
    for server_id, filename, launch_env in fixed:
        command = [str(python), str(ROOT / "scripts" / filename)]
        if get_server(str(database), server_id) is None:
            register_server(
                str(database),
                McpServerCreate(
                    name=server_id, type="stdio", command=command,
                    category="manufacturing", description="Fixed local print-demo operation",
                    launch_env=launch_env, risk_level="medium", default_enabled=False,
                ),
                server_id=server_id,
            )
        update_server(str(database), server_id, {
            "command": command, "launch_env": launch_env, "is_installed": True,
        })
    enabled = [blender_id, *(item[0] for item in fixed)]
    if include_printer:
        printer_id = "bambu-p1s-mcp-marctheshark3"
        source_dir = PRINTER_SOURCE / "src"
        packages_dir = PRINTER_SOURCE / ".venv/Lib/site-packages"
        if not (source_dir / "bambu_p1s_mcp/__main__.py").is_file() or not (
            packages_dir / "paho/mqtt/client.py"
        ).is_file():
            raise FileNotFoundError("The pinned local P1S MCP source and dependencies are missing.")
        if get_server(str(database), printer_id) is None:
            raise ValueError("Reconcile the catalogued P1S MCP server before configuring it.")
        update_server(str(database), printer_id, {
            "command": [str(python), str(ROOT / "scripts/print_demo_p1s_mcp.py")],
            "launch_env": {
                "PYTHONPATH": ";".join((
                    str(ROOT / ".venv/Lib/site-packages"),
                    str(source_dir), str(packages_dir),
                )),
                "BAMBU_MCP_SKIP_DOTENV": "1",
            },
            "is_installed": True,
        })
        enabled.append(printer_id)
    update_workspace_enabled_tools_by_workspace(str(database), workspace_id, enabled)
    print(f"Configured {len(enabled)} local MCP servers for the isolated print-demo workspace.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--blender-port", type=int, default=9876)
    parser.add_argument("--include-printer", action="store_true", help="Bind the pinned local P1S MCP server; does not contact the printer")
    args = parser.parse_args()
    configure(
        args.database.resolve(), args.workspace_id, args.workspace.resolve(),
        args.blender_port, args.include_printer,
    )
