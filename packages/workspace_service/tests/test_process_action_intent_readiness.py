"""Action-contract incompatibility requires correction, not a provider retry."""

from unittest.mock import AsyncMock

import pytest

from packages.workspace_service.tests.test_process_preparation_service import scope
from packages.workspace_service.tests.test_process_run_supervisor import prepared_case
from workspace_service.process_interfaces import readiness, runs
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.workflow_source_execution import WorkflowSourceExecutionError


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source_code",
    [
        "WORKFLOW_ACTION_INTENT_UPGRADE_REQUIRED",
        "WORKFLOW_ACTION_INTENT_SCHEMA_UNSUPPORTED",
        "WORKFLOW_ACTION_INTENT_INVALID",
    ],
)
async def test_contract_defects_are_unsupported_in_readiness_and_public_start(
    tmp_path,
    monkeypatch,
    source_code,
):
    app, process, frozen = await prepared_case(tmp_path)
    correction = "Review and explicitly save the supported action-intent contract."
    error = WorkflowSourceExecutionError(
        source_code, "Saved action contract requires correction.", correction
    )
    qualify = AsyncMock(side_effect=error)
    allocate = AsyncMock(side_effect=error)
    monkeypatch.setattr(readiness, "prepare_authorized_workflow_run", qualify)
    monkeypatch.setattr(runs, "prepare_authorized_workflow_run", allocate)

    async def must_not_generate(*args, **kwargs):
        pytest.fail("Readiness rejection must occur before model submission")

    try:
        view = await app.check_readiness(scope(), process, frozen.snapshot_id)
        assert view.state == "unsupported"
        assert view.input_digest == frozen.digest
        assert view.reasons[0].code == "READINESS_UNSUPPORTED"
        assert view.reasons[0].correction == correction
        with pytest.raises(ProcessInterfaceError) as caught:
            await app.runs.start(
                scope(),
                process,
                frozen.snapshot_id,
                "action-contract-rejected",
                expected_input_digest=frozen.digest,
                response_generator=must_not_generate,
            )
        assert caught.value.reason.code == "READINESS_UNSUPPORTED"
        assert caught.value.reason.correction == correction
        assert caught.value.diagnostic["source_code"] == source_code
        assert app.runs._owned == {}
        with pytest.raises(KeyError):
            app.inputs.start_receipt("user", process, "action-contract-rejected")
        assert not (tmp_path / "runs").exists()
        assert not (tmp_path / "first.txt").exists()
        qualify.assert_awaited_once()
        allocate.assert_awaited_once()
    finally:
        await app.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "source_code,expected_state,expected_reason",
    [
        ("WORKFLOW_MODEL_UNAVAILABLE", "blocked", "CAPABILITY_UNAVAILABLE"),
        ("WORKFLOW_SOURCE_CONFLICT", "blocked", "SOURCE_CHANGED"),
    ],
)
async def test_other_failures_keep_existing_classification(
    tmp_path,
    monkeypatch,
    source_code,
    expected_state,
    expected_reason,
):
    app, process, frozen = await prepared_case(tmp_path)
    error = WorkflowSourceExecutionError(
        source_code, "Changed external state.", "Reconcile the exact dependency."
    )
    monkeypatch.setattr(
        readiness, "prepare_authorized_workflow_run", AsyncMock(side_effect=error)
    )
    monkeypatch.setattr(
        runs, "prepare_authorized_workflow_run", AsyncMock(side_effect=error)
    )
    try:
        view = await app.check_readiness(scope(), process, frozen.snapshot_id)
        assert view.state == expected_state
        assert view.reasons[0].code == expected_reason
        with pytest.raises(ProcessInterfaceError) as caught:
            await app.runs.start(
                scope(),
                process,
                frozen.snapshot_id,
                "existing-classification",
                expected_input_digest=frozen.digest,
                response_generator=None,
            )
        assert caught.value.reason.code == expected_reason
        assert app.runs._owned == {}
        assert not (tmp_path / "runs").exists()
    finally:
        await app.close()
