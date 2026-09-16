"""Confined fixed Pi CHT preparation and collection, with separate Foam scratch.

Only actual declared STEP regions and JSON physical data enter the compiler.
The existing Foam-Agent run tool executes the generated fixed parent Allrun.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import shutil
import zipfile

import pi_cfd_operations as operation


def scope(workspace, source_document, output_directory):
    workspace = Path(workspace).resolve()
    source = operation.path_under(workspace, source_document)
    output = operation.path_under(workspace, output_directory)
    if source.parent.name != "inputs" or source.read_bytes() != Path(operation.__file__).read_bytes():
        raise ValueError("Exact compiler must be an explicit same-attempt input")
    for filename in ("pi_cfd_mcp.py", "wrightPrghFanPressure.C"):
        actual = Path(__file__) if filename.endswith(".py") else Path(__file__).parent/"pi_foam_boundary"/filename
        if (source.parent/filename).read_bytes() != actual.read_bytes():
            raise ValueError("Staged wrapper or fixed boundary adapter source changed")
    if output != source.parent.parent/"artifacts":
        raise ValueError("Only this exact attempt's artifact directory is writable")
    return workspace, source.parent.parent, output


def prepare_variant(workspace, foam_root, operation_source_document, output_directory,
                    contract_document, variant):
    """Prepare one exact CAD alternative within one canonical task budget."""
    workspace, attempt, output = scope(
        workspace, operation_source_document, output_directory
    )
    foam_root = Path(foam_root).resolve()
    if variant not in {"a", "b"}:
        raise ValueError("Variant must be exactly a or b")
    original = operation.path_under(workspace, contract_document)
    if not original.is_relative_to(output):
        raise ValueError("Thermal contract must be a same-run CAD artifact")
    contract = json.loads(original.read_text())
    operation.validate(contract, workspace)
    for region in contract["regions"]:
        if not operation.path_under(workspace, region["step"]).is_relative_to(output):
            raise ValueError("CAD regions must come from this exact attempt")

    relative_attempt = attempt.relative_to(workspace)
    staging = foam_root / relative_attempt / "pi-cfd" / ("variant-" + variant)
    receipt_path = output / f"cfd-preparation-{variant}.json"
    if staging.exists() or receipt_path.exists():
        raise ValueError("Variant preparation exists; inspect prior state rather than replaying")
    cad = staging / "cad"
    cad.mkdir(parents=True)
    source = Path(operation.__file__)
    shutil.copyfile(source, staging / "fixed-compiler.py")
    for region in contract["regions"]:
        source_path = operation.path_under(workspace, region["step"])
        destination = cad / (region["name"] + ".step")
        shutil.copyfile(source_path, destination)
        if operation.sha(destination) != region["sha256"]:
            raise ValueError("CAD transfer hash mismatch")
        region["step"] = destination.relative_to(foam_root).as_posix()
    staged_contract = cad / "contract.json"
    operation.write(staged_contract, json.dumps(contract, indent=2))
    case = staging / "case"
    case_relative = case.relative_to(foam_root).as_posix()
    result = operation.prepare(
        foam_root, staged_contract.relative_to(foam_root).as_posix(), case_relative
    )
    solver_source = "/workspace/" + (staging / "fixed-compiler.py").relative_to(foam_root).as_posix()
    command = [
        "/opt/conda/envs/FoamAgent/bin/python", solver_source, "solve",
        "--root", "/workspace", "--case", case_relative,
    ]
    allrun = staging / "Allrun"
    operation.write(
        allrun,
        "#!/bin/bash\nset -eu\n"
        + 'trap \'echo "ERROR: fixed Pi CFD variant failed; preserve dispatch evidence" >&2\' ERR\n'
        + 'cd "$(dirname "$0")"\n'
        + " ".join(shlex.quote(value) for value in command)
        + "\n",
    )
    allrun.chmod(0o755)
    receipt = {
        "operation": "prepare_pi_cfd_variant",
        "variant": "variant-" + variant,
        "compiler_sha256": operation.sha(source),
        "wrapper_sha256": operation.sha(__file__),
        "original_contract": original.relative_to(workspace).as_posix(),
        "original_contract_sha256": operation.sha(original),
        "case_relative_to_foam_root": case_relative,
        "preparation_sha256": operation.sha(case / "preparation.json"),
        "foam_case_dir": "/workspace/" + staging.relative_to(foam_root).as_posix(),
        "staging_relative_to_foam_root": staging.relative_to(foam_root).as_posix(),
        "allrun_sha256": operation.sha(allrun),
        "result": result,
        "solver_executed": False,
    }
    operation.write(receipt_path, json.dumps(receipt, indent=2))
    return receipt


def prepare_comparison(workspace, foam_root, operation_source_document, output_directory, contract_documents):
    workspace, attempt, output = scope(workspace, operation_source_document, output_directory)
    foam_root = Path(foam_root).resolve()
    if not isinstance(contract_documents, list) or len(contract_documents) != 2 or len(set(contract_documents)) != 2:
        raise ValueError("Two distinct actual CAD-derived alternative contracts are required")
    relative_attempt = attempt.relative_to(workspace)
    staging = foam_root/relative_attempt/"pi-cfd"
    if staging.exists() or (output/"cfd-preparation.json").exists():
        raise ValueError("Comparison attempt exists; inspect prior state rather than replaying")
    # Validate both full contracts and same-attempt geometry before any writes.
    checked = []
    for document in contract_documents:
        path = operation.path_under(workspace, document)
        if not path.is_relative_to(output):
            raise ValueError("Thermal contract must be a same-run CAD artifact")
        contract = json.loads(path.read_text())
        operation.validate(contract, workspace)
        for region in contract["regions"]:
            if not operation.path_under(workspace, region["step"]).is_relative_to(output):
                raise ValueError("CAD regions must come from this exact attempt")
        checked.append((path, contract))
    staging.mkdir(parents=True)
    source = Path(operation.__file__)
    shutil.copyfile(source, staging/"fixed-compiler.py")
    observations = []
    for ordinal, (original, contract) in enumerate(checked):
        variant = "variant-"+"ab"[ordinal]
        cad = staging/variant/"cad"
        cad.mkdir(parents=True)
        for region in contract["regions"]:
            source_path = operation.path_under(workspace, region["step"])
            destination = cad/(region["name"]+".step")
            shutil.copyfile(source_path, destination)
            if operation.sha(destination) != region["sha256"]:
                raise ValueError("CAD transfer hash mismatch")
            region["step"] = destination.relative_to(foam_root).as_posix()
        staged_contract = cad/"contract.json"
        operation.write(staged_contract, json.dumps(contract, indent=2))
        case_relative = (staging/variant/"case").relative_to(foam_root).as_posix()
        result = operation.prepare(foam_root, staged_contract.relative_to(foam_root).as_posix(), case_relative)
        observations.append({"variant": variant, "original_contract": original.relative_to(workspace).as_posix(),
                             "original_contract_sha256": operation.sha(original), "case_relative_to_foam_root": case_relative,
                             "preparation_sha256": operation.sha(foam_root/case_relative/"preparation.json"), "result": result})
    # The command and executing source are fixed; no user script or Allrun text is accepted.
    lines = ["#!/bin/bash", "set -eu", 'trap \'echo "ERROR: fixed Pi CFD pipeline failed; preserve dispatch evidence" >&2\' ERR', 'cd "$(dirname "$0")"']
    for observation in observations:
        solver_source = "/workspace/"+(staging/"fixed-compiler.py").relative_to(foam_root).as_posix()
        lines.append(" ".join(shlex.quote(value) for value in ["/opt/conda/envs/FoamAgent/bin/python", solver_source, "solve", "--root", "/workspace", "--case", observation["case_relative_to_foam_root"]]))
    operation.write(staging/"Allrun", "\n".join(lines)+"\n")
    (staging/"Allrun").chmod(0o755)
    receipt = {"operation": "prepare_pi_cfd_comparison", "compiler_sha256": operation.sha(source),
               "wrapper_sha256": operation.sha(__file__), "foam_case_dir": "/workspace/"+staging.relative_to(foam_root).as_posix(),
               "staging_relative_to_foam_root": staging.relative_to(foam_root).as_posix(),
               "allrun_sha256": operation.sha(staging/"Allrun"), "variants": observations, "solver_executed": False}
    operation.write(output/"cfd-preparation.json", json.dumps(receipt, indent=2))
    return receipt


def collect_comparison(workspace, foam_root, operation_source_document, output_directory):
    workspace, _, output = scope(workspace, operation_source_document, output_directory)
    foam_root = Path(foam_root).resolve()
    legacy_path = output / "cfd-preparation.json"
    if legacy_path.exists():
        receipt = json.loads(legacy_path.read_text())
        rows = receipt["variants"]
        common_compiler = receipt["compiler_sha256"]
        common_wrapper = receipt["wrapper_sha256"]
        staging = operation.path_under(foam_root, receipt["staging_relative_to_foam_root"])
        if operation.sha(staging/"Allrun") != receipt["allrun_sha256"]:
            raise ValueError("Fixed solver orchestration changed")
    else:
        rows = [json.loads((output/f"cfd-preparation-{variant}.json").read_text())
                for variant in ("a", "b")]
        common_compiler = operation.sha(operation.__file__)
        common_wrapper = operation.sha(__file__)
        if [row.get("variant") for row in rows] != ["variant-a", "variant-b"]:
            raise ValueError("Both exact prepared alternatives are required")
        for row in rows:
            staging = operation.path_under(foam_root, row["staging_relative_to_foam_root"])
            if operation.sha(staging/"Allrun") != row["allrun_sha256"]:
                raise ValueError("Fixed solver orchestration changed")
    if common_compiler != operation.sha(operation.__file__) or common_wrapper != operation.sha(__file__):
        raise ValueError("Prepared comparison source changed")
    if (output/"cfd-comparison.json").exists() or (output/"cfd-fields.zip").exists():
        raise ValueError("Collected results exist; preserve them")
    variants = []
    files = []
    for row in rows:
        original = operation.path_under(workspace, row["original_contract"])
        if operation.sha(original) != row["original_contract_sha256"]:
            raise ValueError("Original CAD thermal contract changed")
        case = operation.path_under(foam_root, row["case_relative_to_foam_root"])
        if operation.sha(case/"preparation.json") != row["preparation_sha256"]:
            raise ValueError("Actual meshing provenance changed")
        result = json.loads((case/"results/computed-fields.json").read_text())
        dispatch = json.loads((case/"solver-dispatch.json").read_text())
        if dispatch.get("status") != "completed" or dispatch.get("result_sha256") != operation.sha(case/"results/computed-fields.json"):
            raise ValueError("Native solver dispatch lacks a completed matching result")
        if result["compiler_sha256"] != common_compiler or result["contract_sha256"] != operation.sha(case/"contract.json"):
            raise ValueError("Solver fields lack matching compiler/contract lineage")
        if "\nEnd\n" not in (case/"log.chtMultiRegionFoam").read_text():
            raise ValueError("Actual solver completion is absent")
        for region in result["actual_regions"]:
            field = operation.path_under(case/"results", region["field"])
            if region["cells"] <= 0 or field.stat().st_size == 0 or operation.sha(field) != region["sha256"]:
                raise ValueError("Computed field is absent or changed")
            files.append((field, row["variant"]+"/"+field.name))
        for boundary in result.get("actual_boundaries", []):
            field = operation.path_under(case/"results", boundary["field"])
            if operation.sha(field) != boundary["sha256"]:
                raise ValueError("Actual pressure/flow boundary field changed")
            files.append((field, row["variant"]+"/"+field.name))
        files.append((case/"results/computed-fields.json", row["variant"]+"/computed-fields.json"))
        files.append((case/"log.chtMultiRegionFoam", row["variant"]+"/solver.log"))
        variants.append({"variant": row["variant"], "original_contract_sha256": row["original_contract_sha256"], **result})
    with zipfile.ZipFile(output/"cfd-fields.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, relative in files:
            archive.write(path, relative)
    comparison = {"variants": variants, "field_archive_sha256": operation.sha(output/"cfd-fields.zip"),
                  "engineering_validation_complete": False, "scope": "Actual numerical fields; convergence and engineering targets must be assessed separately"}
    operation.write(output/"cfd-comparison.json", json.dumps(comparison, indent=2))
    return comparison


def main():
    from mcp.server.fastmcp import FastMCP
    workspace = os.environ["WRIGHT_PI_CFD_WORKSPACE"]
    foam_root = os.environ["WRIGHT_PI_CFD_FOAM_ROOT"]
    app = FastMCP("wright-pi-cad-cfd")

    @app.tool()
    def prepare_pi_cfd_variant(operation_source_document: str, output_directory: str,
                               contract_document: str, variant: str) -> dict:
        """Prepare one exact CAD-derived alternative with its own receipt and deadline."""
        return prepare_variant(
            workspace, foam_root, operation_source_document, output_directory,
            contract_document, variant,
        )

    @app.tool()
    def prepare_pi_cfd_comparison(operation_source_document: str, output_directory: str, contract_documents: list[str]) -> dict:
        """Compile two explicit same-run CAD thermal region contracts into real meshes and fixed Allrun."""
        return prepare_comparison(workspace, foam_root, operation_source_document, output_directory, contract_documents)

    @app.tool()
    def collect_pi_cfd_comparison(operation_source_document: str, output_directory: str) -> dict:
        """Collect only actual matching native fields after the existing Foam-Agent run completes."""
        return collect_comparison(workspace, foam_root, operation_source_document, output_directory)

    app.run(transport="stdio")


if __name__ == "__main__":
    main()
