"""Opt-in selected WireViz MCP qualification with actual supplied harness data."""
import argparse
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys


async def run(root, output):
    spec=importlib.util.spec_from_file_location("mcp_probe_helpers",root/"scripts/qualify-robot-campaign.py")
    helper=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    output.mkdir(parents=True,exist_ok=False)
    binding=json.loads((root/"tests/datasets/engineering-workflows/bindings/sensor-fan-harness.json").read_text())
    report={"scope":"Direct selected MCP real retrieval, native WireViz generation and independent engineering observation; not canonical campaign completion","cases":[]}
    for directory in sorted((root/"tests/datasets/engineering-workflows/scenarios/sensor-fan-harness").iterdir()):
        identity=json.loads((directory/"scenario.json").read_text())["scenario_id"]
        case=output/identity
        shutil.copytree(directory,case/"inputs")
        for name in ("harness_engineering_operations.py","harness_component_sources.json"):
            shutil.copyfile(root/"scripts"/name,case/"inputs"/name)
        (case/"inputs/design.json").write_text(json.dumps(binding["scenarios"][identity]))
        common={"operation_source_document":identity+"/inputs/harness_engineering_operations.py"}
        calls=[("retrieve_harness_component_records",dict(**common,source_specification=identity+"/inputs/harness_component_sources.json",output_directory=identity+"/artifacts/research")),
               ("generate_harness_package",dict(**common,input_directory=identity+"/inputs",design_document=identity+"/inputs/design.json",research_directory=identity+"/artifacts/research",output_directory=identity+"/artifacts/generated")),
               ("verify_harness_package",dict(**common,input_directory=identity+"/inputs",research_directory=identity+"/artifacts/research",generated_directory=identity+"/artifacts/generated",output_directory=identity+"/artifacts/verified"))]
        result=await helper.session_call(sys.executable,[str(root/"scripts/harness_engineering_mcp.py")],calls,dict(os.environ,WRIGHT_HARNESS_WORKSPACE=str(output)))
        report["cases"].append({"scenario_id":identity,**result})
        (output/"evidence.json").write_text(json.dumps(report,indent=2))
    report["status"]="passed_actual_execution_not_electrical_release"
    (output/"evidence.json").write_text(json.dumps(report,indent=2))
    print(json.dumps({"status":report["status"],"cases":len(report["cases"])}))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute",action="store_true",required=True)
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    asyncio.run(run(args.root,args.output))
