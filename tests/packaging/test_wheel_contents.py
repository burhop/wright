from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_workspace_surface_packages_and_assets_are_declared() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    wheel = project["tool"]["hatch"]["build"]["targets"]["wheel"]
    sdist = project["tool"]["hatch"]["build"]["targets"]["sdist"]

    assert "src/wright" in wheel["packages"]
    assert "packages/core/src/core" in wheel["packages"]
    assert "src/wright_engineering" in wheel["packages"]
    assert (
        ROOT / "packages/core/src/core/surfaces/schemas/contract-set.json"
    ).is_file()
    assert (ROOT / "src/wright_engineering/static/web/asset-manifest.json").is_file()
    assert project["project"]["scripts"]["wright-rivet-mcp"] == (
        "workspace_service.rivet_mcp:main"
    )
    runner_manifest_path = ROOT / "integrations/rivet/runner/manifest.json"
    runner_artifact = ROOT / "integrations/rivet/runner/dist/wright-runner.mjs"
    assert runner_manifest_path.is_file()
    assert runner_artifact.is_file()
    assert (ROOT / "integrations/rivet/runner/src/wright-runner.ts").is_file()
    runner_manifest = json.loads(runner_manifest_path.read_text(encoding="utf-8"))
    assert runner_manifest["entrypoint"] == "dist/wright-runner.mjs"
    assert runner_manifest["bytes"] == runner_artifact.stat().st_size
    assert (
        runner_manifest["sha256"]
        == hashlib.sha256(runner_artifact.read_bytes()).hexdigest()
    )
    assert {
        "/integrations/rivet/editor/dist",
        "/integrations/rivet/runner/dist",
    } <= set(sdist["artifacts"])


def test_built_wheel_contains_public_helper_contracts_and_renderer_assets(
    tmp_path: Path,
) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--no-isolation",
            "--outdir",
            str(tmp_path),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    wheels = list(tmp_path.glob("*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())
        editor_manifest = json.loads(
            archive.read("workspace_service/_rivet/editor/manifest.json")
        )

        runner_manifest = json.loads(
            archive.read("workspace_service/_rivet/runner/manifest.json")
        )
        runner_artifact = archive.read(
            "workspace_service/_rivet/runner/dist/wright-runner.mjs"
        )
        for category in ("patches", "wrapper"):
            for entry in editor_manifest[category]:
                content = archive.read(
                    f"workspace_service/_rivet/editor/{entry['path']}"
                )
                assert hashlib.sha256(content).hexdigest() == entry["sha256"]

        assert runner_manifest["bytes"] == len(runner_artifact)
        assert runner_manifest["sha256"] == hashlib.sha256(runner_artifact).hexdigest()
    required = {
        "wright/__init__.py",
        "core/surfaces/schemas/v1/display-envelope.schema.json",
        "core/surfaces/schemas/v1/live-app-manifest.schema.json",
        "core/surfaces/schemas/v1/surface-message.schema.json",
        "core/surfaces/schemas/v1/workspace-surfaces.openapi.yaml",
        "core/surfaces/schemas/contract-set.json",
        "wright_engineering/static/web/index.html",
        "wright_engineering/static/web/asset-manifest.json",
        "tool_registry/catalog/catalog-snapshot-envelope.schema.json",
        "tool_registry/catalog/engineering-catalog.yaml",
        "tool_registry/catalog/import-preview.schema.json",
        "tool_registry/catalog/install-plan.schema.json",
        "tool_registry/catalog/schema.json",
        "tool_registry/catalog/trust-root.json",
        "workspace_service/workflow_catalog/catalog.yaml",
        "workspace_service/workflow_catalog/NOTICE.md",
        "workspace_service/workflow_catalog/templates/basic-flow.rivet-project",
        "workspace_service/workflow_catalog/templates/ai-agent.rivet-project",
        "workspace_service/workflow_catalog/templates/mcp-agent.rivet-project",
        "workspace_service/workflow_catalog/examples/text-rpg.rivet-project",
        "workspace_service/engineering_scenario_catalog/catalog.yaml",
        "workspace_service/engineering_scenario_catalog/NOTICE.md",
        "workspace_service/engineering_scenario_catalog/contracts/scenario-manifest.schema.json",
        "workspace_service/engineering_scenario_catalog/contracts/artifact-envelope.schema.json",
        "workspace_service/engineering_scenario_catalog/contracts/assertion-result.schema.json",
        "workspace_service/engineering_scenario_catalog/scenarios/structural-bracket.yaml",
        "workspace_service/engineering_scenario_catalog/scenarios/electronics-enclosure-cooling.yaml",
        "workspace_service/engineering_scenario_catalog/scenarios/parametric-manufacturing.yaml",
        "workspace_service/engineering_scenario_catalog/workflows/structural-bracket.rivet-project",
        "workspace_service/engineering_scenario_catalog/workflows/electronics-enclosure-cooling.rivet-project",
        "workspace_service/engineering_scenario_catalog/workflows/parametric-manufacturing.rivet-project",
        "workspace_service/engineering_scenario_catalog/fixtures/structural-bracket.json",
        "workspace_service/engineering_scenario_catalog/fixtures/electronics-enclosure-cooling.json",
        "workspace_service/engineering_scenario_catalog/fixtures/parametric-manufacturing.json",
        "workspace_service/_rivet/editor/host.py",
        "workspace_service/_rivet/editor/manifest.json",
        "workspace_service/_rivet/editor/dist/index.html",
        "workspace_service/_rivet/editor/patches/rivet2-canvas-only.patch",
        "workspace_service/_rivet/editor/wrapper/WrightAiRuntime.ts",
        "workspace_service/_rivet/runner/manifest.json",
        "workspace_service/_rivet/runner/dist/wright-runner.mjs",
        "workspace_service/_rivet/runner/src/wright-runner.ts",
    }
    assert required <= names
