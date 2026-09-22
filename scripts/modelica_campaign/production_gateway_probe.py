"""Exact native production stdio command through ordinary Wright GatewayService."""
import asyncio
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import time

from core.redaction import redact_mapping
from tool_registry import McpServer
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.runners.stdio import StdioRunner


def verify_export_files(installation, value, dataset, attempt):
    """Compare provider digests with the files visible to the downstream workspace."""
    target = f"/exports/{dataset}/{attempt}"
    mount = next(row for row in installation["mounts"] if row["container"] == target)
    root = Path(mount["host"]).resolve(strict=True)
    prefix = f"campaign/{dataset}/{attempt}/artifacts/"
    files = value["produced_files"]
    expected = {"request.json", "resolved-parameters.json", "WrightWaterHeater.mo", "scenario.json", "parameter-schema.json", "run.mos", "omc.log", "result.csv", "evidence.json", "run.json"}
    if len(files) != len(expected) or {Path(row["output_path"]).name for row in files} != expected:
        raise ValueError("Export did not produce the complete native artifact set")
    for row in files:
        relative = row["output_path"]
        if not relative.startswith(prefix):
            raise ValueError("Export path belongs to another attempt")
        path = (root / relative[len(prefix):]).resolve(strict=True)
        if not path.is_relative_to(root):
            raise ValueError("Export escaped its exact attempt root")
        data = path.read_bytes()
        if len(data) != row["output_bytes"] or hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError("Exported file differs from sealed native evidence")
    return files


async def main(args):
    root = args.root.resolve(strict=True)
    evidence_path = root / "production-stdio-gateway.json"
    if evidence_path.exists():
        raise ValueError("Preserve the existing qualification receipt; inspect it before retrying")
    installation = json.loads((root / "installation.json").read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("native_probe_helpers", "scripts/qualify_stdio_mcp.py")
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    runner = StdioRunner(installation["production_command"], cwd=str(Path.cwd()), operation_timeout=120)
    report = {"campaign_run": False, "native_simulation_dispatched": False, "command": installation["production_command"], "image": installation["image"], "container_id": installation["container_id"]}
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
        if args.exercise_export:
            dataset = "water-heater-sizing-01"
            attempt = args.attempt
            request_id = f"{dataset}-{attempt}-native-export-proof"
            baseline = manifests["wright-300-baseline"]
            quantities = {
                "initial_water_temperature": (20.0, "degC"), "ambient_temperature": (20.0, "degC"),
                "water_mass": (0.35, "kg"), "boiler_heat_capacity": (90.0, "J/K"),
                "heat_loss_conductance": (0.6, "W/K"), "heater_efficiency": (0.92, "1"),
                "setpoint_temperature": (90.0, "degC"), "hysteresis": (2.0, "K"), "electrical_power": (350.0, "W"),
            }
            arguments = {**identity, "scenario_id": "wright-300-baseline", "request_id": request_id,
                "manifest_sha256": baseline["manifest_sha256"], "parameters": {key: {"value": value, "unit": unit} for key, (value, unit) in quantities.items()}, "timeout_ms": 120000}
            report["native_simulation_dispatched"] = True
            simulated = await gateway.call_tool("qualification", "simulate-export-proof", "selected-modelica-native__modelica_simulation_submit", arguments)
            assert not simulated.is_error, simulated.content
            report["simulation"] = simulated.structured_content
            deadline = time.monotonic() + 150
            while simulated.structured_content["request"]["status"] in {"accepted", "queued", "running"}:
                if time.monotonic() > deadline:
                    raise TimeoutError("Native simulation remains in progress; inspect the retained request")
                await asyncio.sleep(1)
                simulated = await gateway.call_tool("qualification", f"poll-{time.monotonic_ns()}", "selected-modelica-native__modelica_simulation_request_get", {"request_id": request_id})
                assert not simulated.is_error, simulated.content
            report["simulation"] = simulated.structured_content
            export_args = {"dataset_id": dataset, "attempt_id": attempt, "request_id": request_id, "expected_manifest_sha256": baseline["manifest_sha256"]}
            exported = await gateway.call_tool("qualification", "export-proof", "selected-modelica-native__modelica_export_recorded_result", export_args)
            assert not exported.is_error, exported.content
            report["exported_files"] = verify_export_files(installation, exported.structured_content, dataset, attempt)
            repeated = await gateway.call_tool("qualification", "export-idempotence", "selected-modelica-native__modelica_export_recorded_result", export_args)
            assert not repeated.is_error, repeated.content
            assert verify_export_files(installation, repeated.structured_content, dataset, attempt) == report["exported_files"]
            report.update(export_verified=True, export_idempotence_verified=True)
        report.update(status="passed", tool_count=len(tools), gateway_audit=audit.events, backend_touch="Actual OMC/MSL manifest plus native simulation and sealed export/readback/idempotence" if args.exercise_export else "Actual OMC/MSL engine probe and immutable manifest; request template only")
        print(json.dumps({"status": "passed", "tools": len(tools), "export_verified": report.get("export_verified", False)}))
    except BaseException as error:
        report.update(status="failed", error_type=type(error).__name__, error=str(error))
        raise
    finally:
        evidence_path.write_text(json.dumps(redact_mapping(report), indent=2) + "\n", encoding="utf-8")
        await runner.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(".local-run/feature-081-live/modelica-prerequisite"))
    parser.add_argument("--exercise-export", action="store_true")
    parser.add_argument("--attempt", default="attempt-export-qualification")
    asyncio.run(main(parser.parse_args()))
