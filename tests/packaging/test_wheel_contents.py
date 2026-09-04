from __future__ import annotations

import hashlib
import json
import os
import runpy
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
    installed = tmp_path / "installed"
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
        process_definition_member = (
            "wright_engineering/static/process-definitions/product-definition-v1.json"
        )
        process_schema_member = (
            "wright_engineering/static/process-definitions/"
            "process-definition.schema.json"
        )
        process_definition_bytes = archive.read(process_definition_member)
        process_schema_bytes = archive.read(process_schema_member)
        assert (
            process_definition_bytes
            == (
                ROOT / "src/wright_engineering/static/process-definitions/"
                "product-definition-v1.json"
            ).read_bytes()
        )
        assert (
            process_schema_bytes
            == (
                ROOT / "src/wright_engineering/static/process-definitions/"
                "process-definition.schema.json"
            ).read_bytes()
        )
        assert hashlib.sha256(process_definition_bytes).hexdigest() == (
            "6a02f71e35f9c3d9a3184509ddeab2df251cff454b6d6ce66d7244d015eefdef"
        )
        archive.extractall(installed)
    required = {
        "wright/__init__.py",
        "core/surfaces/schemas/v1/display-envelope.schema.json",
        "core/surfaces/schemas/v1/live-app-manifest.schema.json",
        "core/surfaces/schemas/v1/surface-message.schema.json",
        "core/surfaces/schemas/v1/workspace-surfaces.openapi.yaml",
        "core/surfaces/schemas/contract-set.json",
        "wright_engineering/static/web/index.html",
        "wright_engineering/static/web/asset-manifest.json",
        "wright_engineering/static/program-status/current.json",
        "wright_engineering/static/program-status/dashboard.schema.json",
        "wright_engineering/static/program-status/program-status-bundle.schema.json",
        "wright_engineering/static/program-status/program-status-source-catalog.json",
        "wright_engineering/static/program-status/program-status-source-catalog.schema.json",
        "wright_engineering/static/program-status/work-registry.schema.json",
        "wright_engineering/static/program-status/use-case-registry.schema.json",
        "wright_engineering/static/program-status/test-run-ledger.schema.json",
        "wright_engineering/static/process-definitions/product-definition-v1.json",
        "wright_engineering/static/process-definitions/process-definition.schema.json",
        "tool_registry/process_definition.py",
        "api/routers/process_definition.py",
        "api/schemas/process_definition.py",
        "core/native_process.py",
        "core/native_process_contract/definition.schema.json",
        "core/native_tracing.py",
        "data_vault/native_process_repository.py",
        "data_vault/native_process_runs.py",
        "data_vault/native_process_artifacts.py",
        "workspace_service/native_process_service.py",
        "workspace_service/native_process_runtime.py",
        "workspace_service/native_process_mcp.py",
        "workspace_service/native_process_cli.py",
        "api/routers/native_process.py",
        "api/schemas/native_process.py",
        "wright_engineering/static/native-processes/concept-brief.json",
        "wright_engineering/static/native-processes/mass-check.json",
        "wright_engineering/static/native-processes/package-review.json",
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

    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    probe = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            (
                "import pathlib, socket, sys; "
                f"target=pathlib.Path({str(installed)!r}).resolve(); "
                "sys.path.insert(0, str(target)); "
                "socket.create_connection=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError('network')); "
                "socket.socket.connect=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError('network')); "
                "import api.routers.process_definition as router_module; "
                "import api.schemas.process_definition as schema_module; "
                "import tool_registry.process_definition as process_module; "
                "from importlib.resources import files; "
                "from tool_registry.process_definition import PROCESS_ID, ProcessDefinitionReader; "
                "packaged=pathlib.Path(str(files('wright_engineering').joinpath('static/process-definitions'))); "
                "document=ProcessDefinitionReader(target/'absent', packaged).read(PROCESS_ID); "
                "assert document.source_kind == 'packaged_fallback'; "
                "assert document.source_sha256 == '6a02f71e35f9c3d9a3184509ddeab2df251cff454b6d6ce66d7244d015eefdef'; "
                "assert all(pathlib.Path(module.__file__).resolve().is_relative_to(target) for module in (router_module, schema_module, process_module))"
            ),
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert probe.returncode == 0, probe.stdout + probe.stderr

    native = runpy.run_path(
        str(ROOT / "tests/native_runtime/test_native_process_lifecycle.py")
    )
    native["verify_installed_native_lifecycle"](
        installed, tmp_path / "native-process-lifecycle"
    )
