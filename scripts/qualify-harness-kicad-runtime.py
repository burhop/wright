"""Qualify the selected harness KiCad runtime with an actual native save.

This is an isolated provider check against one already-staged harness attempt. It
does not dispatch, resume, validate, or award credit to a canonical campaign run.
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter, defaultdict
import csv
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def schematic_calls(pin_schedule: Path, contract: dict, output_path: str) -> list[dict]:
    """Plan actual native operations from the produced schedule and fixed map.

    Named splice terminal numbers are schematic representation only. Numeric
    connector pin numbers and unconnected reserves remain exactly as declared.
    This plan is not a native export, ERC result or correspondence measurement.
    """
    with pin_schedule.open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream, strict=True))
    if not rows or len(rows) > 1000:
        raise ValueError("A bounded nonempty physical pin schedule is required")
    mapping = contract["native_pin_map"]
    required = contract["expected_connections"]
    reserved = set(contract["reserved_endpoints"])

    def edge(left, right, net):
        if left == right or not isinstance(net, str) or not net.strip():
            raise ValueError("Invalid physical connection")
        return (*sorted((left, right)), net)

    observed = Counter(
        edge(
            f"{r['from_connector']}:{r['from_pin']}",
            f"{r['to_connector']}:{r['to_pin']}",
            r["net"],
        )
        for r in rows
    )
    expected = Counter(edge(r["from"], r["to"], r["net"]) for r in required)
    connected = {endpoint for left, right, _ in observed for endpoint in (left, right)}
    if (
        observed != expected
        or any(count != 1 for count in observed.values())
        or connected & reserved
        or set(mapping) != connected | reserved
        or len(set(mapping.values())) != len(mapping)
    ):
        raise ValueError(
            "Physical schedule or native pin map differs from the fixed interconnect contract"
        )
    components = defaultdict(set)
    for original, native in mapping.items():
        reference, pin = original.split(":")
        native_reference, number = native.split(":")
        if (
            reference != native_reference
            or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", reference)
            or not number.isdigit()
            or (pin.isdigit() and pin != number)
        ):
            raise ValueError(
                "Native mapping must preserve connector references and physical pin numbers"
            )
        components[reference].add(int(number))
    calls = [{"operation": "create", "name": output_path}]
    for index, (reference, pins) in enumerate(sorted(components.items())):
        count = len(pins)
        if not 1 <= count <= 40 or pins != set(range(1, count + 1)):
            raise ValueError(
                "Native connector symbol requires contiguous declared pins"
            )
        calls.append(
            {
                "operation": "add_component",
                "lib_id": f"Connector_Generic:Conn_01x{count:02d}",
                "position": [60 + 65 * (index % 3), 50 + 70 * (index // 3)],
                "reference": reference,
                "value": reference + " interconnect representation",
            }
        )
    for row in rows:
        left, left_pin = mapping[f"{row['from_connector']}:{row['from_pin']}"].split(
            ":"
        )
        right, right_pin = mapping[f"{row['to_connector']}:{row['to_pin']}"].split(":")
        calls.append(
            {
                "operation": "connect_pins_with_labels",
                "comp1_ref": left,
                "pin1": left_pin,
                "comp2_ref": right,
                "pin2": right_pin,
                "net_name": row["net"],
            }
        )
    calls.extend(
        (
            {"operation": "check_pin_collisions"},
            {"operation": "validate"},
            {"operation": "save", "schematic_path": output_path},
        )
    )
    return calls


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
            raise ValueError(
                f"Required actual harness evidence is unavailable: {path.name}"
            )

    from workspace_service.process_validation.profiles import load_profile

    profile = load_profile(args.scenario)
    check = next(item for item in profile.checks if item.id == "kicad-correspondence")

    output_directory = attempt / "artifacts/interconnect-qualification"
    if output_directory.exists():
        raise ValueError("Preserve prior qualification output; use a fresh attempt")
    output_directory.mkdir(parents=True, exist_ok=False)
    container_output = (
        f"/work/{relative.as_posix()}/artifacts/interconnect-qualification/"
        "harness.kicad_sch"
    )
    calls = schematic_calls(sources["pin_schedule"], check.parameters, container_output)
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
        "profile_ref": profile.reference().model_dump(mode="json"),
        "native_pin_map": check.parameters["native_pin_map"],
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
