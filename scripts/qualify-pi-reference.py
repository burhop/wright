"""Opt-in direct MCP primary Pi PDF retrieval in the isolated selected runtime."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import shutil
import sys


async def run(args):
    source = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("mcp_probe", source/"qualify-robot-campaign.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    root = Path(args.root)
    inputs = root/args.attempt/"inputs"
    inputs.mkdir(parents=True)
    shutil.copyfile(source/"pi_reference_mcp.py", inputs/"pi_reference_mcp.py")
    arguments = {"operation_source_document": args.attempt+"/inputs/pi_reference_mcp.py", "output_directory": args.attempt+"/artifacts/research"}
    result = await helper.session_call(sys.executable, [str(source/"pi_reference_mcp.py")], [("retrieve_pi_manufacturer_references", arguments)], {"WRIGHT_PI_REFERENCE_WORKSPACE": str(root), "PYTHONPATH": ""})
    result["scope"] = "Actual direct MCP primary references; no design, CAD, CFD or campaign credit"
    (root/args.attempt/"evidence.json").write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({"status": "actual_reference_tool_passed", "tools": len(result["tools"])}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--attempt", required=True)
    asyncio.run(run(parser.parse_args()))
