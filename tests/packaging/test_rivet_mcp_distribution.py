from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_protocol_v2_runner_contracts_and_persistence_ship_in_wheel_and_sdist(
    tmp_path: Path,
) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheel = next(tmp_path.glob("*.whl"))
    sdist = next(tmp_path.glob("*.tar.gz"))
    wheel_required = {
        "workspace_service/_rivet/runner/manifest.json",
        "workspace_service/_rivet/runner/dist/wright-runner.mjs",
        "workspace_service/_rivet/runner/src/wright-runner.ts",
        "workspace_service/_rivet/contracts/capability-binding.schema.json",
        "workspace_service/_rivet/contracts/run-manifest.schema.json",
        "data_vault/migrations.py",
        "data_vault/rivet_mcp_repository.py",
    }
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        assert wheel_required <= names
        manifest = json.loads(
            archive.read("workspace_service/_rivet/runner/manifest.json")
        )
        assert manifest["protocol_version"] == 2
        assert manifest["runtime_network_policy"] == "wright-bridge-only"
        assert (
            len(archive.read("workspace_service/_rivet/runner/dist/wright-runner.mjs"))
            > 1_000_000
        )
        for contract in (
            "capability-binding.schema.json",
            "run-manifest.schema.json",
        ):
            document = json.loads(
                archive.read(f"workspace_service/_rivet/contracts/{contract}")
            )
            assert document["$schema"].startswith("https://json-schema.org/")

    with tarfile.open(sdist, "r:gz") as archive:
        names = {"/".join(name.split("/")[1:]) for name in archive.getnames()}
        assert {
            "integrations/rivet/runner/manifest.json",
            "integrations/rivet/runner/dist/wright-runner.mjs",
            "integrations/rivet/runner/src/wright-runner.ts",
            "packages/workspace_service/src/workspace_service/_rivet/contracts/capability-binding.schema.json",
            "packages/workspace_service/src/workspace_service/_rivet/contracts/run-manifest.schema.json",
            "packages/data_vault/src/data_vault/migrations.py",
            "packages/data_vault/src/data_vault/rivet_mcp_repository.py",
        } <= names


def test_public_rivet_contract_copies_match_specification() -> None:
    public_contracts = (
        ROOT
        / "packages"
        / "workspace_service"
        / "src"
        / "workspace_service"
        / "_rivet"
        / "contracts"
    )
    specification_contracts = ROOT / "specs" / "069-rivet-mcp-gateway" / "contracts"
    for contract in (
        "capability-binding.schema.json",
        "run-manifest.schema.json",
    ):
        assert (public_contracts / contract).read_bytes() == (
            specification_contracts / contract
        ).read_bytes()
