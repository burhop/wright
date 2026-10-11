"""Keep retired operational code out of the shared process entry points.

Historical data and inactive archives remain readable. These guards cover the
retired prototype dependency set, not qualification of every external provider.
"""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RETIRED = (
    "packages/workspace_service/src/workspace_service/print_part_demo.py",
    "packages/workspace_service/src/workspace_service/print_part_demo_printer.py",
    "apps/web/src/components/pages/PrintPartDemoPage.tsx",
    "apps/web/src/components/pages/PrintPartDemoPage.css",
    "scripts/configure_print_demo_offline.py",
    "scripts/configure_print_demo_studio.py",
    "scripts/print_demo_p1s_mcp.py",
    "scripts/print_demo_p1s_session.py",
    "scripts/print_demo_p1s_transfer.py",
    "scripts/print_demo_studio.py",
    "scripts/windows/inspect-bambu-studio.ps1",
    "scripts/windows/studio-desktop.ps1",
    "scripts/engineering_dataset_slice.py",
    "scripts/engineering_dataset_slice_mcp.py",
    "scripts/engineering_jig_slice_mcp.py",
    "scripts/engineering_dataset_mesh_repair.py",
    "scripts/engineering_dataset_mesh_repair_mcp.py",
    "scripts/run_printed_validator_campaign.py",
    "tests/test_print_demo_dispatch.py",
    "tests/test_engineering_jig_slice_mcp.py",
    "tests/test_printed_validator_campaign_wrapper.py",
)
RETIRED_MODULES = {Path(name).stem for name in RETIRED if name.endswith(".py")}


@pytest.mark.parametrize("relative", RETIRED)
def test_retired_prototype_source_does_not_return(relative):
    assert not (ROOT / relative).exists()


def test_application_and_script_imports_do_not_reach_retired_implementations():
    count = 0
    roots = [ROOT / "scripts", ROOT / "apps/api/src"]
    roots.extend((ROOT / "packages").glob("*/src"))
    for root in roots:
        for path in root.rglob("*.py"):
            if {"node_modules", "__pycache__", "static"}.intersection(path.parts):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or "", *[alias.name for alias in node.names]]
                else:
                    continue
                for name in names:
                    assert not RETIRED_MODULES.intersection(name.split(".")), (
                        path,
                        name,
                    )
            count += 1
    assert count > 0


def test_workspace_entry_and_client_use_shared_work_and_read_only_history():
    entry = (ROOT / "apps/web/src/components/pages/WorkflowRecoveryPage.tsx").read_text(
        encoding="utf-8"
    )
    client = (ROOT / "apps/web/src/services/workspace-service.ts").read_text(
        encoding="utf-8"
    )
    assert "PrintPartDemoPage" not in entry
    assert "HistoricalResultView" in entry and "Open working view" in entry
    assert 'historicalWorkflow === visiblePath' in entry
    assert "/print-demo/" not in client
    assert "uploadWorkflowImage" in client
    assert "preparePrintPartDemo" not in client


def test_legacy_reader_delegates_to_recorder_without_execution_imports():
    path = (
        ROOT
        / "packages/workspace_service/src/workspace_service/process_interfaces/legacy_results.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert modules == {"pathlib", "workspace_path", "workflow_run_record"}
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "read_workflow_run" in calls
    assert not calls.intersection({"start_run", "execute_workflow", "call_tool"})
