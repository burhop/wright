"""Qualify the selected harness KiCad runtime with an actual native save.

This is an isolated provider check against one already-staged harness attempt. It
does not dispatch, resume, validate, or award credit to a canonical campaign run.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


CONNECTOR_CALLS = (
    {
        "operation": "add_component",
        "lib_id": "Connector_Generic:Conn_01x06",
        "position": [80, 80],
        "reference": "J0",
        "value": "Controller 6-pin",
    },
    {
        "operation": "add_component",
        "lib_id": "Connector_Generic:Conn_01x04",
        "position": [140, 70],
        "reference": "JF",
        "value": "Fan 4-pin",
    },
    {
        "operation": "add_component",
        "lib_id": "Connector_Generic:Conn_01x03",
        "position": [140, 100],
        "reference": "JS",
        "value": "Temperature transmitter 3-pin",
    },
)

NET_CALLS = (
    ("J0", "1", "JF", "1", "24V"),
    ("JF", "1", "JS", "1", "24V"),
    ("J0", "2", "JF", "2", "FAN_GND"),
    ("J0", "3", "JF", "3", "PWM"),
    ("JF", "4", "J0", "4", "TACH"),
    ("JS", "3", "J0", "5", "TEMP_SIGNAL"),
    ("J0", "6", "JS", "2", "SIGNAL_RETURN"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def qualify(args: argparse.Namespace) -> dict:
    workspace = args.workspace_root.resolve(strict=True)
    relative = Path("campaign") / args.scenario / args.attempt
    attempt = (workspace / relative).resolve(strict=True)
    if not attempt.is_relative_to(workspace):
        raise ValueError("Attempt escaped the workspace")
    sources = {
        "pin_schedule": attempt / "artifacts/generated/pin-schedule.csv",
        "independent_netlist": attempt / "artifacts/verified/independent-netlist.csv",
    }
    for path in sources.values():
        if not path.is_file() or not path.read_bytes():
            raise ValueError(f"Required actual harness evidence is unavailable: {path.name}")

    output_directory = attempt / "artifacts/interconnect-qualification"
    if output_directory.exists():
        raise ValueError("Preserve prior qualification output; use a fresh attempt")
    output_directory.mkdir(parents=True, exist_ok=False)
    container_output = (
        f"/work/{relative.as_posix()}/artifacts/interconnect-qualification/"
        "harness.kicad_sch"
    )
    command = [
        "docker",
        "exec",
        "-i",
        "-e",
        "PYTHONPATH=",
        args.container,
        "/opt/kicad-mcp/.venv/bin/python",
        "/opt/wright-kicad/server.py",
    ]
    results = []
    async with stdio_client(
        StdioServerParameters(command=command[0], args=command[1:], env={})
    ) as (read, write):
        async with ClientSession(read, write) as client:
            initialized = await client.initialize()
            listed = await client.list_tools()
            advertised = sorted(tool.name for tool in listed.tools)
            if "schematic" not in advertised:
                raise ValueError("Selected runtime did not advertise schematic")

            calls = [{"operation": "create", "name": container_output}]
            calls.extend(CONNECTOR_CALLS)
            calls.extend(
                {
                    "operation": "connect_pins_with_labels",
                    "comp1_ref": left,
                    "pin1": left_pin,
                    "comp2_ref": right,
                    "pin2": right_pin,
                    "net_name": net,
                }
                for left, left_pin, right, right_pin, net in NET_CALLS
            )
            calls.extend(
                (
                    {"operation": "check_pin_collisions"},
                    {"operation": "validate"},
                    {"operation": "save", "schematic_path": container_output},
                )
            )
            for arguments in calls:
                result = await client.call_tool("schematic", arguments)
                row = {
                    "operation": arguments["operation"],
                    "is_error": bool(result.isError),
                }
                results.append(row)
                if result.isError:
                    raise ValueError(
                        f"KiCad schematic operation failed: {arguments['operation']}"
                    )

            server = initialized.model_dump(mode="json")

    output = output_directory / "harness.kicad_sch"
    if not output.is_file() or output.stat().st_size == 0:
        raise ValueError("KiCad reported success without a saved native schematic")
    evidence = {
        "schema_version": 1,
        "status": "passed_actual_native_save",
        "observed_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Isolated selected-provider initialize/list/create/connect/validate/save "
            "using actual harness attempt evidence; no canonical campaign credit"
        ),
        "container": args.container,
        "scenario_id": args.scenario,
        "attempt_id": args.attempt,
        "server": server,
        "advertised_tools": advertised,
        "calls": results,
        "inputs": {
            role: {
                "path": path.relative_to(workspace).as_posix(),
                "sha256": sha256(path),
            }
            for role, path in sources.items()
        },
        "output": {
            "path": output.relative_to(workspace).as_posix(),
            "sha256": sha256(output),
            "bytes": output.stat().st_size,
        },
        "campaign_runs": 0,
    }
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--scenario", default="sensor-fan-harness-01")
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--container", default="wright-082-harness-kicad-runtime")
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    evidence = asyncio.run(qualify(args))
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "calls": len(evidence["calls"]),
                "output": str(args.evidence),
            }
        )
    )


if __name__ == "__main__":
    main()
