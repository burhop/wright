"""Read-only saved-binding discovery uses the real confined source store."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from api.desktop.connection_workflow_usage import connection_workflow_usage
from workspace_service.executor import BoundedExecutor
from workspace_service.workflow_sources import (
    WorkspaceWorkflowSourceStore,
    WorkspaceWorkflowSourceUseCases,
)


def source(title, server, extra=""):
    return f'''workflow test
  name: "{title}"
end

task inspect
  name: "Inspect exact engineering output"
  settings: {{"mcp_server":"{server}","mcp_tool":"inspect"}}
  tool: null
  reusable_step: null
{extra}end
'''


@pytest.mark.asyncio
async def test_actual_store_lists_exact_provider_without_mutating_sources(tmp_path):
    store = WorkspaceWorkflowSourceStore(tmp_path)
    first = store.create(
        "workflows/geometry.workflow.wflow", source("Geometry check", "cad")
    )
    second = store.create(
        "workflows/measurements.workflow.wflow",
        source("Recorded measurement diagnosis", "metrics"),
    )
    executor = BoundedExecutor()
    try:
        owner = WorkspaceWorkflowSourceUseCases(executor)
        result = await connection_workflow_usage(owner, str(tmp_path), "metrics")
        assert result["scan_complete"]
        assert result["examined"] == 2
        assert result["matches"] == [
            {
                "path": second.path,
                "title": "Recorded measurement diagnosis",
                "source_digest": second.storage_digest,
                "steps": [
                    {"id": "inspect", "title": "Inspect exact engineering output"}
                ],
            }
        ]
        assert store.read(first.path) == first
        assert store.read(second.path) == second
        assert not (tmp_path / "runs").exists()
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_bad_or_unresolved_sources_are_not_reported_as_unaffected(tmp_path):
    store = WorkspaceWorkflowSourceStore(tmp_path)
    store.create("workflows/broken.workflow.wflow", "not valid source")
    store.create("workflows/dynamic.workflow.wflow", source("Dynamic", ""))
    good = store.create("workflows/known.workflow.wflow", source("Known", "cad"))
    (tmp_path / good.path).write_text("externally replaced source")
    executor = BoundedExecutor()
    try:
        result = await connection_workflow_usage(
            WorkspaceWorkflowSourceUseCases(executor), str(tmp_path), "cad"
        )
        assert not result["scan_complete"]
        assert result["matches"] == []
        assert set(result["unchecked_paths"]) == {
            "workflows/broken.workflow.wflow",
            "workflows/dynamic.workflow.wflow",
            good.path,
        }
    finally:
        await executor.close()


@pytest.mark.asyncio
async def test_listing_failure_is_incomplete_without_raw_error_disclosure():
    owner = SimpleNamespace(
        list_input_files=AsyncMock(side_effect=ValueError("PRIVATE"))
    )
    result = await connection_workflow_usage(owner, "/scope", "cad")
    assert not result["scan_complete"]
    assert result["matches"] == []
    assert "PRIVATE" not in str(result)


@pytest.mark.asyncio
async def test_scan_limit_is_visible_and_reads_are_bounded():
    paths = [{"path": f"workflows/item-{i:03}.workflow.wflow"} for i in range(65)]
    owner = SimpleNamespace(
        list_input_files=AsyncMock(return_value=paths),
        read=AsyncMock(
            return_value=SimpleNamespace(
                source=source("Unrelated", "other"),
                size_bytes=200,
            )
        ),
    )
    result = await connection_workflow_usage(owner, "/scope", "cad")
    assert not result["scan_complete"]
    assert result["examined"] == 64
    assert owner.read.await_count == 64


@pytest.mark.asyncio
async def test_existing_handle_and_robot_sources_remain_inspectable_but_unbound(
    tmp_path,
):
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    fixtures = {
        "handle": root
        / "prototypes/desktop-harness/engineering-experience/handle/replacement-handle-draft.workflow.wflow",
        "robot": root
        / "packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/robot-tracking-diagnosis.workflow.wflow",
    }
    store = WorkspaceWorkflowSourceStore(tmp_path)
    documents = []
    for name, fixture in fixtures.items():
        # Instantiate the existing template token; retain all engineering content.
        text = fixture.read_text().replace("__instance__", "usage_proof")
        documents.append(store.create(f"workflows/{name}.workflow.wflow", text))
    executor = BoundedExecutor()
    try:
        result = await connection_workflow_usage(
            WorkspaceWorkflowSourceUseCases(executor),
            str(tmp_path),
            "unrelated-provider",
        )
        assert result["examined"] == 2
        assert result["matches"] == []
        assert "workflows/robot.workflow.wflow" in result["unchecked_paths"]
        assert not result["scan_complete"]
        for document in documents:
            assert store.read(document.path) == document
    finally:
        await executor.close()
