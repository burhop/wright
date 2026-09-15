"""Opt-in real fixed compiler -> native Foam-Agent run -> confined field collection."""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path
import shutil
import sys


async def run(args):
    operations = Path(__file__).resolve().parent
    spec = importlib.util.spec_from_file_location("selected_mcp_probe", operations/"qualify-robot-campaign.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    root = Path(args.root).resolve()
    attempt = root/args.attempt
    inputs = attempt/"inputs"
    inputs.mkdir(parents=True)
    output = attempt/"artifacts"
    output.mkdir()
    for source in (operations/"pi_cfd_operations.py", operations/"pi_cfd_mcp.py", operations/"pi_foam_boundary/wrightPrghFanPressure.C"):
        shutil.copyfile(source, inputs/source.name)
    contracts = []
    for ordinal, original_case in enumerate(("probe-002", "probe-fan-001")):
        document = json.loads((root/original_case/"contract.json").read_text())
        for region in document["regions"]:
            path = root/region["step"]
            target = output/f"prerequisite-{'ab'[ordinal]}-{region['name']}.step"
            shutil.copyfile(path, target)
            region["step"] = target.relative_to(root).as_posix()
        destination = output/f"thermal-contract-{'ab'[ordinal]}.json"
        destination.write_text(json.dumps(document, indent=2))
        contracts.append(destination.relative_to(root).as_posix())
    arguments = {"operation_source_document": args.attempt+"/inputs/pi_cfd_operations.py", "output_directory": args.attempt+"/artifacts"}
    environment = {"WRIGHT_PI_CFD_WORKSPACE": str(root), "WRIGHT_PI_CFD_FOAM_ROOT": str(root), "PYTHONPATH": ""}
    prepared = await helper.session_call(sys.executable, [str(operations/"pi_cfd_mcp.py")], [("prepare_pi_cfd_comparison", {**arguments, "contract_documents": contracts})], environment)
    (attempt/"prepare-mcp.json").write_text(json.dumps(prepared, indent=2))
    receipt = json.loads((output/"cfd-preparation.json").read_text())
    solver = await helper.session_call(sys.executable, ["-m", "src.mcp.cli", "--transport", "stdio"], [("run", {"request": {"case_dir": receipt["foam_case_dir"], "timeout": 180}})], {"PYTHONPATH": "/home/openfoam/Foam-Agent", "WM_PROJECT_DIR": "/opt/openfoam10", "OPENAI_API_KEY": "qualification-unused-no-model-request", "FOAMAGENT_MODEL_PROVIDER": "openai", "FOAMAGENT_MODEL_VERSION": "unused-run-only", "FOAMAGENT_EMBEDDING_PROVIDER": "openai", "FOAMAGENT_EMBEDDING_MODEL": "unused-run-only"})
    (attempt/"native-foam-mcp.json").write_text(json.dumps(solver, indent=2))
    collected = await helper.session_call(sys.executable, [str(operations/"pi_cfd_mcp.py")], [("collect_pi_cfd_comparison", arguments)], environment)
    (attempt/"collect-mcp.json").write_text(json.dumps(collected, indent=2))
    comparison = json.loads((output/"cfd-comparison.json").read_text())
    assert len(comparison["variants"]) == 2 and all(len(item["actual_regions"]) == 3 for item in comparison["variants"])
    (attempt/"evidence.json").write_text(json.dumps({"status": "actual_selected_comparison_pipeline_passed", "scope": "Independent OCC prerequisite geometry; passive and fan runtime contracts, not the Pi dataset alternatives", "campaign_credit": 0, "native_foam_tool": "run", "compiler_source_sha256": comparison["variants"][0]["compiler_sha256"], "field_archive_sha256": comparison["field_archive_sha256"]}, indent=2)+"\n")
    print(json.dumps({"status": "passed_actual_pipeline", "evidence": str(attempt/"evidence.json")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--attempt", required=True)
    asyncio.run(run(parser.parse_args()))
