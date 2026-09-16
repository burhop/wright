"""Opt-in actual selected-container robot CSV/bag MCP probe; no campaign run claim."""
import argparse
import asyncio
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def session_call(command, arguments, calls, environment):
    async with stdio_client(StdioServerParameters(command=command, args=arguments, env=environment)) as (read, write):
        async with ClientSession(read, write) as client:
            initialized = await client.initialize()
            listed = await client.list_tools()
            results = []
            for name, args in calls:
                if name not in {tool.name for tool in listed.tools}:
                    raise ValueError("Tool not actually advertised: " + name)
                result = await client.call_tool(name, args)
                if result.isError:
                    raise ValueError(str(result))
                results.append({"tool": name, "arguments": args, "result": result.model_dump(mode="json")})
            return {"server": initialized.model_dump(mode="json"), "tools": [tool.model_dump(mode="json") for tool in listed.tools], "calls": results}


async def run(root, output):
    output.mkdir(parents=True, exist_ok=False)
    binding = json.loads((root / "tests/datasets/engineering-workflows/bindings/robot-tracking-diagnosis.json").read_text())
    environment = dict(os.environ, WRIGHT_ROBOT_WORKSPACE=str(output))
    report = {"observed_at": datetime.now(UTC).isoformat(), "scope": "direct selected offline MCP conversion, actual five-topic bag inspection/extraction and alignment metrics; not a canonical campaign run", "cases": []}
    for directory in sorted((root / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis").iterdir()):
        manifest = json.loads((directory / "scenario.json").read_text())
        identity = manifest["scenario_id"]
        case = output / identity
        shutil.copytree(directory, case / "inputs")
        shutil.copyfile(root / "scripts/robot_tracking_operations.py", case / "inputs/robot_tracking_operations.py")
        (case / "inputs/alignment.json").write_text(json.dumps(binding["scenarios"][identity]))
        companion = await session_call(sys.executable, [str(root / "scripts/robot_tracking_mcp.py")],
            [("normalize_csv_to_ros2", {"input_directory": identity + "/inputs", "output_directory": identity + "/artifacts/converted", "operation_source_document": identity + "/inputs/robot_tracking_operations.py"})], environment)
        bag = str(case / "artifacts/converted/recording")
        calls = [("bag_info", {"bag_path": bag}), ("get_topic_schema", {"bag_path": bag, "topic": "/wright_test/external_pose"})]
        for topic in ["planned_pose", "external_pose", "odom", "cmd_vel", "operator_event"]:
            calls.append(("get_messages_in_range", {"bag_path": bag, "topic": "/wright_test/" + topic, "start_time": 1767225600.0, "end_time": 1767225630.01, "max_messages": 100}))
        native = await session_call(str(Path(sys.executable).with_name("rosbag-mcp")), [], calls, environment)
        expected_external = 56 if identity.endswith("03") else 61
        for call in native["calls"][2:]:
            messages = json.loads(call["result"]["content"][0]["text"])
            expected = 1 if call["arguments"]["topic"].endswith("operator_event") else expected_external if call["arguments"]["topic"].endswith("external_pose") else 61
            if len(messages) != expected:
                raise ValueError("Actual native MCP extraction differs from expected original row count")
        analysis = await session_call(sys.executable, [str(root / "scripts/robot_tracking_mcp.py")],
            [("calculate_tracking_metrics", {"bag_directory": identity + "/artifacts/converted/recording", "alignment_document": identity + "/inputs/alignment.json", "output_directory": identity + "/artifacts/analysis", "operation_source_document": identity + "/inputs/robot_tracking_operations.py"})], environment)
        report["cases"].append({"scenario_id": identity, "conversion": companion, "native_inspection": native, "analysis": analysis,
                                "outputs": [{"path": str(p.relative_to(output)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in sorted(case.rglob("*")) if p.is_file() and "inputs" not in p.parts]})
        (output / "evidence.json").write_text(json.dumps(report, indent=2, allow_nan=True))
    report["status"] = "passed"
    report["finished_at"] = datetime.now(UTC).isoformat()
    (output / "evidence.json").write_text(json.dumps(report, indent=2, allow_nan=True))
    print(json.dumps({"status": "passed", "cases": len(report["cases"]), "evidence": str(output / "evidence.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.root, args.output))
