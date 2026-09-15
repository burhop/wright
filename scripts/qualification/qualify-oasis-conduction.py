"""Explicit live OASiS container probe through Wright stdio and gateway layers."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from core.redaction import redact_mapping
from tool_registry import McpServer
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.runners.stdio import StdioRunner

ROOT = Path(__file__).resolve().parents[2]
COMMAND = ["docker", "exec", "-i", "-e", "PYTHONPATH=", "-e", "PYVISTA_OFF_SCREEN=true",
           "wright-oasis-campaign", "uv", "run", "--isolated", "--python", "3.12", "--with",
           "git+https://github.com/Hereon-InstituteMS/OASiS.git@7c184d5b7ca5cda6086f3912d1c7923c58307780",
           "--with", "mcp[cli]==1.28.1", "--with", "scikit-fem==12.0.2", "python", "-m", "server"]


def payload(value):
    if not isinstance(value, dict):
        value = {"content": list(value.content), "is_error": value.is_error}
    if value.get("isError") or value.get("is_error"):
        raise ValueError("MCP reported tool error")
    content = value.get("content") or []
    for item in content:
        if not isinstance(item, dict):
            item = item.model_dump()
        if item.get("type") == "text":
            result = json.loads(item["text"])
            if result.get("status") != "completed":
                raise ValueError("Solver did not complete: " + str(result))
            return result
    raise ValueError("Missing actual solver result")


async def run(args):
    spec = importlib.util.spec_from_file_location("qualification_helpers", ROOT / "scripts/qualify_stdio_mcp.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    source = (ROOT / "scripts/engineering/heat_conduction_skfem.py").read_text()
    root = ROOT / ".local-run/feature-081-live/oasis-workspace/qualification" / args.attempt
    if root.exists():
        raise ValueError("Qualification attempt already exists")
    root.mkdir(parents=True)
    runner = StdioRunner(COMMAND, cwd=str(ROOT), operation_timeout=180)
    results = []
    try:
        await runner.start()
        tools = await runner.list_tools()
        (root / "tools.json").write_text(json.dumps(tools, indent=2))
        now = int(time.time())
        server = McpServer(server_id="oasis-container-probe", name="OASiS container probe", type="stdio",
                           command=COMMAND, is_active=True, is_installed=True, status="active",
                           created_at=now, updated_at=now, risk_level="high")
        gateway = GatewayService(workspaces=helpers._Workspaces(root, server.server_id),
                                 catalog=helpers._Catalog(server, tools), lifecycle=helpers._Lifecycle(runner),
                                 audit=helpers._Audit(), notifier=GatewayNotificationHub(), operation_timeout=180)
        gateway.open_session(session_id="qualification", principal_id="wright-validator",
                             workspace_id="qualification-workspace", transport="stdio")
        gateway.initialize_session("qualification", protocol_version=SUPPORTED_PROTOCOL_VERSION,
                                   client_name="conduction-probe", client_version="1", client_capabilities={})
        listed = [t.name for t in gateway.list_tools("qualification")]
        if "oasis-container-probe__run_simulation" not in listed:
            raise ValueError("Gateway did not list real solver tool")
        for route in ("direct", "gateway"):
            output = "/workspace/qualification/" + args.attempt + "/" + route
            config = {"output_root": output, "cases": [
                {"case_id": "qualification_link", "length_mm": 50, "width_mm": 30,
                 "thickness_mm": 2, "conductivity_w_mk": 150, "density_kg_m3": 2700,
                 "heat_input_w": 1, "rail_temperature_c": 20,
                 "total_contact_resistance_k_per_w": .10, "limit_c": 30},
                {"case_id": "qualification_fixed", "length_mm": 50, "width_mm": 30,
                 "thickness_mm": 2, "conductivity_w_mk": 150, "density_kg_m3": 2700,
                 "heat_input_w": 1, "cold_face_temperature_c": 20, "limit_c": 30}]}
            execution_source = "HEAT_CONFIG = " + repr(config) + "\nexec(compile(" + repr(source) + ", 'heat_conduction_skfem.py', 'exec'))\n"
            arguments = {"solver": "skfem", "input_content": execution_source,
                         "job_name": output, "critic_approved": False}
            if route == "direct":
                response = await runner.call_tool("run_simulation", arguments)
            else:
                response = await gateway.call_tool("qualification", "conduction", "oasis-container-probe__run_simulation", arguments)
            result = payload(response)
            expected = ["qualification_link-fine-temperature.vtu", "qualification_link-fine-temperature.csv",
                        "qualification_fixed-fine-temperature.vtu", "qualification_fixed-fine-temperature.csv",
                        "heat-balance.json", "mesh-comparison.json", "sizing-decision.json"]
            files = []
            for name in expected:
                path = root / route / name
                if not path.is_file() or not path.stat().st_size:
                    raise ValueError("Missing actual probe output: " + str(path))
                files.append({"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
                              "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
            results.append({"route": route, "result": result, "files": files})
        return {"status": "passed", "scope": "clean selected-container 3D conduction backend and native Wright GatewayService",
                "container": "wright-oasis-campaign", "base_image": "sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73",
                "command": COMMAND, "tool_count": len(tools), "results": results,
                "critic_approved": False, "campaign_runs": 0, "public_qualification_changed": False,
                "limitations": ["Probe checks actual file presence only; numerical correctness remains unqualified.",
                                "Hermes-facing gateway MCP proxy is a separate outstanding qualification scope."]}
    finally:
        await runner.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True)
    args = parser.parse_args()
    result = asyncio.run(run(args))
    path = ROOT / ".local-run/feature-081-live/oasis-workspace/qualification" / args.attempt / "evidence.json"
    path.write_text(json.dumps(redact_mapping(result), indent=2) + "\n")
    print(json.dumps({"status": result["status"], "tool_count": result["tool_count"], "evidence": str(path)}))


if __name__ == "__main__":
    main()
