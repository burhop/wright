"""Real selected KiCad prerequisite probe; never campaign completion evidence."""
import asyncio
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    root = Path(sys.argv[1]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    report = {"kind": "selected_prerequisite_probe", "started_at": datetime.now(UTC).isoformat(), "calls": [], "campaign_run": False}
    board, schematic = root / "probe.kicad_pcb", root / "probe.kicad_sch"
    with (root / "server-stderr.log").open("w") as errors:
        params = StdioServerParameters(command="/opt/kicad-mcp/.venv/bin/python", args=["/opt/wright-kicad/server.py" if "--baked" in sys.argv else "/probe/server.py"]) if "--selected" in sys.argv else StdioServerParameters(command="/opt/kicad-mcp/.venv/bin/kicad-mcp")
        async with stdio_client(params, errlog=errors) as (read, write):
            async with ClientSession(read, write) as client:
                initial = await client.initialize()
                report["initialize"] = initial.model_dump(mode="json")
                tools = await client.list_tools()
                (root / "tools.json").write_text(tools.model_dump_json(indent=2))
                async def call(name, arguments):
                    result = await client.call_tool(name, arguments)
                    payload = result.structuredContent
                    if payload is None:
                        raw = next(c.text for c in result.content if c.type == "text")
                        try:
                            payload = json.loads(raw)
                        except ValueError:
                            payload = {"error": raw}
                    report["calls"].append({"tool": name, "operation": arguments.get("operation"), "result": payload, "isError": result.isError})
                    (root / "probe.json").write_text(json.dumps(report, indent=2))
                    if result.isError or payload.get("error"):
                        raise ValueError(f"{name}/{arguments.get('operation')} failed: {payload}")
                    return payload
                found = await call("library", {"operation": "search", "type": "footprint", "query": "0603 resistor", "limit": 5})
                footprint = found["results"][0]
                await call("pcb", {"operation": "create", "pcb_path": str(board)})
                await call("pcb", {"operation": "set_outline", "pcb_path": str(board), "x_mm": 0, "y_mm": 0, "width_mm": 40, "height_mm": 30})
                for ref, x in [("R1", 10), ("R2", 25)]:
                    await call("pcb", {"operation": "place_footprint", "pcb_path": str(board), "library": footprint["library"], "footprint_name": footprint["name"], "reference": ref, "value": "10k", "x_mm": x, "y_mm": 15})
                for name in ["A", "B"]:
                    await call("pcb", {"operation": "add_net", "pcb_path": str(board), "net_name": name})
                await call("pcb", {"operation": "bulk_assign_pad_nets", "pcb_path": str(board), "assignments": [{"reference": ref, "pad": pad, "net": net} for ref in ["R1", "R2"] for pad, net in [("1", "A"), ("2", "B")]]})
                first = await call("drc", {"operation": "run", "project_path": str(board)})
                assert first["success"] and first["unconnected_count"] > 0, "Deliberately unrouted board must not be called clean"
                await call("drc", {"operation": "run", "project_path": str(board)})
                await call("drc", {"operation": "history", "project_path": str(board)})
                assert len((await client.list_tools()).tools) == len(tools.tools)
                await call("schematic", {"operation": "create", "name": "real-erc-negative-probe"})
                found = await call("library", {"operation": "search", "type": "symbol", "query": "Device:R", "limit": 5})
                symbol = next(item for item in found["results"] if item["name"] == "R")
                await call("schematic", {"operation": "add_component", "lib_id": symbol["library"] + ":" + symbol["name"], "reference": "R1", "value": "10k", "position": [50.8, 50.8], "footprint": footprint["library"] + ":" + footprint["name"]})
                await call("schematic", {"operation": "save", "schematic_path": str(schematic)})
                bom = await call("export", {"operation": "bom_csv", "project_path": str(schematic)})
                assert bom["success"] and (root / "probe_bom.csv").is_file()
                if "--selected" in sys.argv:
                    native_erc = await call("native_rule_check", {"kind": "erc", "source_path": str(schematic), "report_path": str(root / "selected-erc.json")})
                    assert native_erc["error_count"] > 0
                    native_drc = await call("native_rule_check", {"kind": "drc", "source_path": str(board), "report_path": str(root / "selected-drc-before.json")})
                    assert native_drc["error_count"] > 0
                if "--route" in sys.argv:
                    await call("autoroute", {"operation": "run", "pcb_path": str(board), "freerouter_jar": "/opt/freerouting-2.2.4.jar", "passes": 1})
                    routed = await call("drc", {"operation": "run", "project_path": str(board)})
                    assert routed["success"] and routed["unconnected_count"] == 0
                await call("export", {"operation": "gerbers", "pcb_path": str(board), "output_dir": str(root / "gerbers"), "create_zip": True})
    for domain, operation, file in [("sch", "erc", schematic), ("pcb", "drc", board)]:
        output = root / f"native-{operation}.json"
        completed = subprocess.run(["kicad-cli", domain, operation, "--format", "json", "--output", str(output), str(file)], capture_output=True, text=True, timeout=60)
        report[f"native_{operation}"] = {"exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}
        assert completed.returncode == 0 and output.is_file()
        data = json.loads(output.read_text())
        if operation == "erc":
            assert sum(len(sheet["violations"]) for sheet in data["sheets"]) > 0, "Unconnected resistor must cause actual ERC issues"
    report["files"] = [{"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in root.rglob("*") if path.is_file() and path.name != "probe.json"]
    report["finished_at"] = datetime.now(UTC).isoformat()
    report["status"] = "passed"
    (root / "probe.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"status": report["status"], "file_count": len(report["files"])}))


asyncio.run(main())
