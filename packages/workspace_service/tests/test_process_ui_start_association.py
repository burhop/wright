"""Controlled view-to-start association checks; no browser or engineering proof."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.surface_bridge import (
    AuthorizedProcessPresentation,
    ProcessSurfaceBridge,
)
from packages.workspace_service.tests.test_process_ui_presentations import (
    native_case,
    build,
    save,
    retained_grants,
)


async def preparation(root, monkeypatch):
    case = native_case(root, monkeypatch)
    job = await build(case)
    preview = await case.owner.open(
        case.scope, case.process, case.actor, job.job_id, "preview", read_only=True
    )
    await save(case, job, preview)
    view = await case.owner.open(
        case.scope, case.process, case.actor, job.job_id, "preparation", read_only=False
    )
    frozen = (await case.application.set_inputs(case.scope, case.process)).snapshot
    context = AuthorizedProcessPresentation(
        view["binding"],
        case.scope,
        job.job_id,
        case.actor.session_id,
        view["descriptor"].source.source_version,
        view["launch"].instance_id,
    )
    request = SimpleNamespace(
        request_id="start-one",
        input_snapshot_id=frozen.snapshot_id,
        expected_input_digest=frozen.digest,
        integration_policy_digest=None,
    )
    return case, view, context, request, frozen


async def read_receipt(case, view, request_id=None):
    return await case.owner.start_receipt(
        case.scope,
        case.process,
        case.actor,
        view["descriptor"].surface_id,
        view["launch"].presentation_id,
        request_id=request_id,
    )


@pytest.mark.asyncio
async def test_exact_association_reads_existing_receipt_without_replaying_work(
    tmp_path, monkeypatch
):
    case, view, context, request, frozen = await preparation(tmp_path, monkeypatch)
    assert await read_receipt(case, view) is None
    ProcessSurfaceBridge.retain_start(case.application, context, request)
    with pytest.raises(ProcessInterfaceError, match="no confirmed start receipt"):
        await read_receipt(case, view, request.request_id)
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        return "Controlled source response, not engineering acceptance"

    try:
        receipt = await case.application.runs.start(
            case.scope,
            case.process,
            frozen.snapshot_id,
            request.request_id,
            expected_input_digest=frozen.digest,
            response_generator=generate,
        )
        assert await read_receipt(case, view, request.request_id) == receipt
        assert await read_receipt(case, view) == receipt
        ProcessSurfaceBridge.retain_start(case.application, context, request)
        assert await read_receipt(case, view) == receipt
        await case.application.runs.wait(case.scope, case.process, receipt.run_id)
        assert len(calls) == 2
        case.application.runs.cancel.assert_not_called()
    finally:
        await case.application.runs.close()


@pytest.mark.asyncio
async def test_unknown_request_cannot_be_replaced_and_foreign_signal_cannot_attach(
    tmp_path, monkeypatch
):
    case, view, context, request, _ = await preparation(tmp_path, monkeypatch)
    ProcessSurfaceBridge.retain_start(case.application, context, request)
    for change in ({"request_id": "new-start"}, {"expected_input_digest": "f" * 64}):
        with pytest.raises(ProcessInterfaceError, match="different start request"):
            ProcessSurfaceBridge.retain_start(
                case.application, context, SimpleNamespace(**(vars(request) | change))
            )
    with pytest.raises(ProcessInterfaceError, match="does not belong to this view"):
        await read_receipt(case, view, "foreign-start")
    assert not case.application.runs._owned


@pytest.mark.asyncio
async def test_preview_run_bound_closed_and_revoked_views_cannot_adopt_a_start(
    tmp_path, monkeypatch
):
    case, view, context, request, _ = await preparation(tmp_path, monkeypatch)
    for binding in (
        context.binding.model_copy(update={"read_only": True}),
        context.binding.model_copy(update={"run_id": "other-run"}),
    ):
        with pytest.raises(ProcessInterfaceError):
            ProcessSurfaceBridge.retain_start(
                case.application, replace(context, binding=binding), request
            )
    read = next(
        grant
        for grant in retained_grants(case)
        if grant.capability == "process.read"
        and grant.constraints["presentation_id"] == view["launch"].presentation_id
    )
    case.surfaces.grant_service.revoke(actor=case.actor, grant_id=read.grant_id)
    with pytest.raises(ProcessInterfaceError, match="grant is unavailable"):
        await read_receipt(case, view)
    await case.owner.close(
        case.scope,
        case.actor,
        view["descriptor"].surface_id,
        view["launch"].presentation_id,
    )
    with pytest.raises(ProcessInterfaceError, match="no longer current"):
        await read_receipt(case, view)
