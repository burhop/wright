"""Run inside an unchanged clean Wright image against one isolated Modelica sidecar."""
import asyncio
import importlib.util
import json
from pathlib import Path
import time

from core.redaction import redact_mapping
from tool_registry import McpServer
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.gateway_notifications import GatewayNotificationHub


async def main():
    spec = importlib.util.spec_from_file_location("qualification_helpers", "/helpers/qualify_stdio_mcp.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    root = Path("/evidence")
    transport_spec = importlib.util.spec_from_file_location("current_http_qualification", "/helpers/qualify-calculix-recorded.py")
    transport = importlib.util.module_from_spec(transport_spec)
    transport_spec.loader.exec_module(transport)
    endpoint = "http://wright-081-modelica-qualification:3016/mcp"
    runner = transport.CurrentHttpRunner(endpoint)
    report = {"campaign_run": False, "calls": [], "transport": "Qualification-only explicit stateless2026 HTTP adapter; production uses verified standard stdio2025-11-25. Ordinary HTTP SseRunner initialization is not claimed compatible."}
    try:
        await runner.start()
        tools = await runner.list_tools()
        (root / "gateway-tools.json").write_text(json.dumps(tools, indent=2))
        now = int(time.time())
        server = McpServer(server_id="selected-modelica", name="Selected Modelica qualification", type="sse", command=endpoint,
                           is_active=True, is_installed=True, status="active", created_at=now, updated_at=now)
        audit = helper._Audit()
        gateway = GatewayService(workspaces=helper._Workspaces(root, server.server_id), catalog=helper._Catalog(server, tools),
                                 lifecycle=helper._Lifecycle(runner), audit=audit, notifier=GatewayNotificationHub(), operation_timeout=150)
        gateway.open_session(session_id="qualification", principal_id="wright-validator", workspace_id="qualification-workspace", transport="stdio")
        gateway.initialize_session("qualification", protocol_version=SUPPORTED_PROTOCOL_VERSION, client_name="modelica-probe", client_version="1", client_capabilities={})
        assert "selected-modelica__modelica_export_recorded_result" in [tool.name for tool in gateway.list_tools("qualification")]

        async def call(tool, arguments):
            response = await gateway.call_tool("qualification", f"call-{len(report['calls'])}", f"selected-modelica__{tool}", arguments)
            result = response.structured_content
            report["calls"].append({"tool": tool, "arguments": arguments, "result": result, "is_error": response.is_error})
            (root / "gateway-probe.json").write_text(json.dumps(redact_mapping(report), indent=2))
            if response.is_error:
                raise ValueError(str(response.content))
            assert result is not None
            return result

        identity = {"model_id": "wright-water-heater-v1", "model_version": "0.1.0", "scenario_id": "wright-300-refined"}
        manifest = (await call("modelica_simulation_manifest_get", identity))["manifest"]
        request_id = "water-heater-sizing-01-attempt-qualification-gateway"
        template = await call("modelica_simulation_request_template_get", {**identity, "request_id": request_id, "manifest_sha256": manifest["manifest_sha256"], "timeout_ms": 120000})
        submit = template["submit"]
        for key, value in {"electrical_power": 700, "water_mass": .35, "boiler_heat_capacity": 90, "heater_efficiency": .92, "heat_loss_conductance": .6}.items():
            submit["parameters"][key]["value"] = value
        native = await call("modelica_simulation_submit", submit)
        assert native["request"]["status"] == "completed" and native["request"]["run"]["status"] == "succeeded"
        exported = await call("modelica_export_recorded_result", {"dataset_id": "water-heater-sizing-01", "attempt_id": "attempt-qualification", "request_id": request_id, "expected_manifest_sha256": manifest["manifest_sha256"]})
        assert len(exported["produced_files"]) == 10
        report.update(status="passed", tool_count=len(tools), gateway_audit=audit.events, backend_native_run_id=exported["native_run_id"])
        print(json.dumps({"status": "passed", "tools": len(tools), "exported_files": 10}))
    except BaseException as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        (root / "gateway-probe.json").write_text(json.dumps(redact_mapping(report), indent=2))
        await runner.stop()


asyncio.run(main())
