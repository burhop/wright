"""Native selected Modelica MCP qualification, never canonical campaign evidence."""
import argparse
import asyncio
import csv
from datetime import UTC, datetime
from datetime import timedelta
import hashlib
import io
import json
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(args):
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    runs = root / "runs"
    runs.mkdir(exist_ok=True)
    exports = root / "exports"
    for index in range(1, 4):
        (exports / f"water-heater-sizing-{index:02d}" / "attempt-qualification").mkdir(parents=True, exist_ok=True)
    report = {"kind": "selected_prerequisite_probe", "campaign_run": False, "started_at": datetime.now(UTC).isoformat(), "calls": [], "simulations": []}

    def persist():
        (root / "probe.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    command = ["run", "--rm", "-i", "--network", "none", "--cpus", "2", "--memory", "3g", "--mount", f"type=bind,source={runs},target=/runs", "--mount", f"type=bind,source={exports},target=/exports", "--entrypoint", "deno", args.image,
               "run", "--cached-only", "--allow-read=/app,/runs,/exports", "--allow-write=/runs,/exports", "--allow-run=omc,perl", "--allow-env=MODELICA_RUN_DIR,OPENMODELICALIBRARY", "/app/server.ts", "--stdio"]
    try:
        with (root / "stderr.log").open("w", encoding="utf-8") as errors:
            async with stdio_client(StdioServerParameters(command="docker", args=command), errlog=errors) as (read, write):
                async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=150)) as client:
                    report["initialize"] = (await client.initialize()).model_dump(mode="json")
                    (root / "tools.json").write_text((await client.list_tools()).model_dump_json(indent=2), encoding="utf-8")
                    persist()

                    async def call(name, arguments, expect_error=False):
                        result = await client.call_tool(name, arguments)
                        payload = result.structuredContent
                        if payload is None:
                            payload = json.loads(next(block.text for block in result.content if block.type == "text"))
                        report["calls"].append({"tool": name, "arguments": arguments, "result": payload, "is_error": result.isError})
                        persist()
                        if not expect_error and result.isError:
                            raise ValueError(f"Native MCP call failed: {name}: {payload}")
                        if expect_error and not result.isError:
                            raise ValueError("Invalid selected input was accepted")
                        return payload

                    if args.discover_only:
                        report["status"] = "discovered"
                        return
                    for case, horizon, mass, capacity, loss, efficiency, power in [
                        ("01", 300, .35, 90, .60, .92, 350),
                        ("02", 600, .60, 180, .85, .93, 800),
                        ("03", 700, 1.5, 480, 2.88, .94, 1800),
                    ]:
                        for numerical in ["baseline", "refined"]:
                            identity = {"model_id": "wright-water-heater-v1", "model_version": "0.1.0", "scenario_id": f"wright-{horizon}-{numerical}"}
                            manifest = (await call("modelica_simulation_manifest_get", identity))["manifest"]
                            assert manifest["lowering"]["id"] == "wright-modelica-numerical-lowering"
                            controls = manifest["scenario"]["public"]["numerical_controls"]
                            request_id = f"water-heater-sizing-{case}-attempt-qualification-{numerical}" if args.export else f"qualification-{case}-{numerical}"
                            template = await call("modelica_simulation_request_template_get", {**identity, "manifest_sha256": manifest["manifest_sha256"], "request_id": request_id, "timeout_ms": 120000})
                            submit = template["submit"]
                            for key, value in {"water_mass": mass, "boiler_heat_capacity": capacity, "heat_loss_conductance": loss, "heater_efficiency": efficiency, "electrical_power": power}.items():
                                submit["parameters"][key]["value"] = value
                            result = await call("modelica_simulation_submit", submit)
                            request = result["request"]
                            assert request["status"] == "completed", result
                            # Read-only recovery must find the same exact immutable result.
                            reread = await call("modelica_simulation_request_get", {"request_id": submit["request_id"]})
                            assert reread["request"]["status"] == "completed", reread
                            if args.export:
                                export_input = {"dataset_id": f"water-heater-sizing-{case}", "attempt_id": "attempt-qualification", "request_id": request_id, "expected_manifest_sha256": manifest["manifest_sha256"]}
                                await call("modelica_export_recorded_result", {**export_input, "expected_manifest_sha256": "0" * 64}, expect_error=True)
                                exported_result = await call("modelica_export_recorded_result", export_input)
                                assert len(exported_result["produced_files"]) == 10
                                assert (await call("modelica_export_recorded_result", export_input)) == exported_result
                            report["simulations"].append({"case": case, "numerical": numerical, "controls": controls, "request": request})
                            persist()
                            print(json.dumps({"completed": case + "/" + numerical}), flush=True)

                    # The original kit's existing lower power bound remains enforced.
                    if args.summary:
                        for case, power, loss, limit in [("01", 350, .6, 180), ("02", 800, .85, 360), ("03", 1800, 2.88, 400)]:
                            entries = [row for row in report["simulations"] if row["case"] == case]
                            summary_input = {"dataset_id": f"water-heater-sizing-{case}", "attempt_id": "attempt-qualification", "requests": [{"request_id": row["request"]["request_id"], "expected_manifest_sha256": row["request"]["manifest_sha256"]} for row in entries], "time_limit_s": limit, "candidate_powers_w": [power], "loss_conductances_w_per_k": [loss]}
                            await call("modelica_summarize_recorded_study", {**summary_input, "candidate_powers_w": [power, 1200 if power != 1200 else 1500]}, expect_error=True)
                            summarized = await call("modelica_summarize_recorded_study", summary_input)
                            assert len(summarized["produced_files"]) == 6
                            assert (await call("modelica_summarize_recorded_study", summary_input)) == summarized
                    await call("modelica_simulate_recorded", {"model_id": "coffee-machine-v1", "scenario_id": "heat-up-nominal", "parameter_overrides": {"heater_power": {"value": 350, "unit": "W"}}}, expect_error=True)
                    resources = await client.list_resources()
                    report["resources"] = resources.model_dump(mode="json")
                    exported = root / "retrieved"
                    exported.mkdir(exist_ok=True)
                    for resource in resources.resources:
                        if "/runs/" not in str(resource.uri) and "/requests/" not in str(resource.uri):
                            continue
                        result = await client.read_resource(resource.uri)
                        for content in result.contents:
                            if not hasattr(content, "text"):
                                raise ValueError("Expected exact UTF-8 native resource")
                            name = hashlib.sha256(str(resource.uri).encode()).hexdigest()[:16] + "-" + str(resource.uri).rsplit("/", 1)[-1]
                            (exported / name).write_bytes(content.text.encode("utf-8"))
                    native = list(runs.rglob("result.csv"))
                    assert len(native) == 6, f"Expected six real OMC CSVs, found {len(native)}"
                    for path in native:
                        rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"))))
                        assert rows and "electricalEnergyJ" in rows[0]
                        electrical = float(rows[-1]["electricalEnergyJ"])
                        thermal = float(rows[-1]["heaterEnergyJ"])
                        assert electrical > 0 and 0.919999 < thermal / electrical < 0.940001
                        assert any(p.read_bytes() == path.read_bytes() for p in exported.glob("*")), "Native CSV must be retrievable byte for byte via MCP resources"
                        if args.export:
                            assert any(p.read_bytes() == path.read_bytes() for p in exports.rglob("result.csv")), "Exported CSV must equal exact native source bytes"
                    report["status"] = "passed"
    except BaseException as error:
        report["status"] = "failed"
        report["error_type"] = type(error).__name__
        report["error"] = str(error)
        raise
    finally:
        report["finished_at"] = datetime.now(UTC).isoformat()
        report["files"] = [{"path": str(p.relative_to(root)), "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in root.rglob("*") if p.is_file() and p.name != "probe.json"]
        persist()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default="wright:modelica-campaign-selected-20260912")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--export", action="store_true")
    parser.add_argument("--summary", action="store_true")
    asyncio.run(main(parser.parse_args()))
