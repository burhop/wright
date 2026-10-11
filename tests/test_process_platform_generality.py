"""The process interface foundation has no selected-provider execution policy."""

import ast
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PROVIDER_WORDS = re.compile(
    r"\b(?:bambu|p1s|mqtt|ftps|agentcad|oasis|blender|blender_mcp|bpy|bmesh)\b", re.I
)
PROVIDER_IMPORTS = {
    "bambu",
    "bambulabs_api",
    "bambu_lab_cloud_api",
    "blender_mcp",
    "bpy",
    "bmesh",
    "paho",
    "ftplib",
}
SHARED_PYTHON = (
    "packages/core/src/core/process_interactions.py",
    "packages/core/src/core/process_interfaces.py",
    "packages/data_vault/src/data_vault/process_input_repository.py",
    "packages/data_vault/src/data_vault/process_interface_repository.py",
    "packages/agent_adapters/src/agent_adapters/base.py",
    "packages/agent_adapters/src/agent_adapters/hermes.py",
    "packages/workspace_service/src/workspace_service/workflow_source_execution.py",
    "packages/workspace_service/src/workspace_service/workflow_mcp_execution.py",
    "packages/workspace_service/src/workspace_service/workflow_external_actions.py",
    "packages/workspace_service/src/workspace_service/workflow_async_operations.py",
    "packages/workspace_service/src/workspace_service/workflow_run_preparation.py",
    "packages/workspace_service/src/workspace_service/process_validation/readers/printing.py",
    "apps/api/src/api/routers/process_interfaces.py",
)


def shared_python_paths():
    paths = [ROOT / name for name in SHARED_PYTHON]
    paths.extend(
        (
            ROOT
            / "packages/workspace_service/src/workspace_service/process_interfaces"
        ).rglob("*.py")
    )
    return sorted(set(paths))


def test_shared_foundation_has_no_selected_vendor_literals_or_native_imports():
    for path in shared_python_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                assert not PROVIDER_WORDS.search(node.value), (path, node.lineno)
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or "", *[alias.name for alias in node.names]]
            else:
                continue
            assert all(
                not PROVIDER_IMPORTS.intersection(name.split(".")) for name in names
            ), path


def test_public_client_kit_and_process_views_have_no_provider_branch():
    roots = [
        ROOT / "packages/process_client/src",
        ROOT / "packages/ui_kit/src",
        ROOT / "apps/web/src/components/process-interfaces",
    ]
    count = 0
    for root in roots:
        for path in root.rglob("*"):
            if path.suffix not in {".ts", ".tsx"} or ".spec." in path.name:
                continue
            assert not PROVIDER_WORDS.search(path.read_text(encoding="utf-8")), path
            count += 1
    assert count > 0


def test_original_slice_profiles_already_declare_their_operation():
    root = (
        ROOT
        / "packages/workspace_service/src/workspace_service/process_validation/profiles"
    )
    profiles = [
        root / f"{prefix}-{index:02}.json"
        for prefix in ("printed-replacement-part", "parametric-drill-jig")
        for index in range(1, 4)
    ]
    declared = 0
    for path in profiles:
        profile = json.loads(path.read_bytes())
        checks = [
            check
            for check in profile["checks"]
            if check.get("parameters", {}).get("operation") == "slice_binding"
        ]
        declared += len(checks)
        assert all(
            isinstance(check["parameters"].get("expected_operation"), str)
            and check["parameters"]["expected_operation"].strip()
            for check in checks
        ), path
    assert declared > 0
