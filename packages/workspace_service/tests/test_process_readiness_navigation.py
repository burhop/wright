"""Readiness corrections retain exact block identity without executing work."""

from unittest.mock import AsyncMock

import pytest

from core.process_interactions import NavigationTarget
from packages.workspace_service.tests.test_process_preparation_service import (
    tool_source,
    scope,
)
from packages.workspace_service.tests.test_process_run_supervisor import prepared_case
from workspace_service.process_interfaces import inputs, readiness
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError


def test_missing_tool_configuration_retains_compiler_block_not_display_title():
    source = tool_source().replace('"mcp_tool":', '"unused_tool":')
    with pytest.raises(ProcessInterfaceError) as caught:
        inputs._sections(source)
    assert caught.value.reason.navigation == NavigationTarget(
        kind="block", block_id="first"
    )
    assert caught.value.reason.code == "READINESS_UNSUPPORTED"


@pytest.mark.asyncio
async def test_readiness_target_preserves_frozen_inputs_and_does_not_start(
    tmp_path, monkeypatch
):
    app, process, frozen = await prepared_case(tmp_path)
    monkeypatch.setattr(
        readiness,
        "prepare_authorized_workflow_run",
        AsyncMock(
            side_effect=WorkflowSourceExecutionError(
                "WORKFLOW_NOT_READY",
                "Configure the selected tool.",
                "Open this step's settings.",
                block_id="first",
            )
        ),
    )
    try:
        view = await app.check_readiness(scope(), process, frozen.snapshot_id)
        assert view.state == "blocked"
        assert view.input_digest == frozen.digest
        assert view.reasons[0].navigation == NavigationTarget(
            kind="block", block_id="first"
        )
        destination = await app.navigation.resolve(
            scope("process.read", "process.navigate"),
            process,
            view.reasons[0].navigation,
        )
        assert destination.process == process
        assert destination.target.block_id == "first"
        assert app.runs._owned == {}
        assert not (tmp_path / "runs").exists()
        assert not (tmp_path / "first.txt").exists()
    finally:
        await app.close()


@pytest.mark.asyncio
async def test_start_rejection_links_step_but_changed_source_rejects_old_target(
    tmp_path, monkeypatch
):
    from types import SimpleNamespace
    from workspace_service.process_interfaces import runs

    app, process, frozen = await prepared_case(tmp_path)
    monkeypatch.setattr(
        runs,
        "prepare_authorized_workflow_run",
        AsyncMock(
            side_effect=WorkflowSourceExecutionError(
                "WORKFLOW_NOT_READY",
                "The tool configuration changed.",
                "Review this step.",
                block_id="first",
            )
        ),
    )

    async def must_not_generate(*args, **kwargs):
        pytest.fail("Rejected readiness cannot submit model work")

    try:
        with pytest.raises(ProcessInterfaceError) as caught:
            await app.runs.start(
                scope(),
                process,
                frozen.snapshot_id,
                "rejected-step-navigation",
                expected_input_digest=frozen.digest,
                response_generator=must_not_generate,
            )
        target = caught.value.reason.navigation
        assert target == NavigationTarget(kind="block", block_id="first")
        monkeypatch.setattr(
            app.workspace.workflow_sources,
            "read",
            AsyncMock(
                return_value=SimpleNamespace(
                    source="workflow changed\nend\n", storage_digest="f" * 64
                )
            ),
        )
        with pytest.raises(ProcessInterfaceError) as stale:
            await app.navigation.resolve(
                scope("process.read", "process.navigate"), process, target
            )
        assert stale.value.reason.code == "SOURCE_CHANGED"
        assert app.runs._owned == {}
        assert not (tmp_path / "runs").exists()
    finally:
        await app.close()
