"""Exact native production stdio command through ordinary Wright GatewayService."""
import asyncio
import importlib.util
import json
from pathlib import Path
import time

from core.redaction import redact_mapping
from tool_registry import McpServer
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.runners.stdio import StdioRunner


async def main():
    root = Path(".local-run/feature-081-live/modelica-prerequisite").resolve()
    installation = json.loads((root / "installation.json").read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("native_probe_helpers", "scripts/qualify_stdio_mcp.py")
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    runner = StdioRunner(installation["production_command"], cwd=str(Path.cwd()), operation_timeout=120)
    report = {"campaign_run": False, "native_simulation_dispatched": False, "command": installation["production_command"], "image": installation["image"]}
    try:
        await runner.start()
        tools = await runner.list_tools()
        now = int(time.time())
        server = McpServer(server_id="selected-modelica-native", name="Selected Modelica native gateway qualification", type="stdio", command=installation["production_command"], is_active=True, is_installed=True, status="active", created_at=now, updated_at=now)
        audit = h._Audit()
        gateway = GatewayService(workspaces=h._Workspaces(root, server.server_id), catalog=h._Catalog(server, tools), lifecycle=h._Lifecycle(runner), audit=audit, notifier=GatewayNotificationHub(), operation_timeout=120)
        gateway.open_session(session_id="qualification", principal_id="wright-validator", workspace_id="qualification-workspace", transport="stdio")
        gateway.initialize_session("qualification", protocol_version=SUPPORTED_PROTOCOL_VERSION, client_name="modelica-native-probe", client_version="1", client_capabilities={})
        assert len(gateway.list_tools("qualification")) == 15
        identity = {"model_id": "wright-water-heater-v1", "model_version": "0.1.0", "scenario_id": "wright-300-refined"}
        result = await gateway.call_tool("qualification", "native-manifest", "selected-modelica-native__modelica_simulation_manifest_get", identity)
        assert not result.is_error, result.content
        manifest = result.structured_content["manifest"]
        assert manifest["engine"] == {"name": "OpenModelica", "version": "1.27.0", "msl_version": "4.1.0"}
        report["native_manifest"] = manifest
        manifests = {identity["scenario_id"]: manifest}
        for horizon in [300, 600, 700]:
            for mode in ["baseline", "refined"]:
                scenario = f"wright-{horizon}-{mode}"
                if scenario in manifests:
                    continue
                result = await gateway.call_tool("qualification", "native-manifest-" + scenario, "selected-modelica-native__modelica_simulation_manifest_get", {**identity, "scenario_id": scenario})
                assert not result.is_error, result.content
                manifests[scenario] = result.structured_content["manifest"]
        (root / "manifest-catalog.json").write_text(json.dumps(manifests, indent=2) + "\n", encoding="utf-8")
        template = await gateway.call_tool("qualification", "native-template", "selected-modelica-native__modelica_simulation_request_template_get", {**identity, "manifest_sha256": manifest["manifest_sha256"], "request_id": "water-heater-sizing-01-attempt-001-native-gateway-no-dispatch"})
        assert not template.is_error, template.content
        report.update(status="passed", tool_count=len(tools), gateway_audit=audit.events, backend_touch="Actual OMC/MSL engine probe and compiler-agreed immutable manifest; request template only, production store remains empty.")
        print(json.dumps({"status": "passed", "tools": len(tools), "production_runs_created": 0}))
    except BaseException as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        (root / "production-stdio-gateway.json").write_text(json.dumps(redact_mapping(report), indent=2) + "\n", encoding="utf-8")
        await runner.stop()


asyncio.run(main())
