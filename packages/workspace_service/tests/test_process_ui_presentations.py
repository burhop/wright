"""Existing surface owners with controlled runtime/model/compiler ports.

These checks do not claim a managed browser launch, live model or engineering
acceptance. They verify native opening/closing and exact presentation grants.
"""

import sqlite3
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from core.surfaces.live_app_manifest import parse_live_app_manifest
from core.surfaces.models import SurfaceLifecycle
from data_vault import SurfaceRepository, upgrade_database
from workspace_service.config import SurfacePreviewSettings
from workspace_service.process_interfaces import authoring as authoring_module
from workspace_service.process_interfaces.artifacts import ProcessUIPreviewObservation
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.presentation import (
    ProcessInterfacePresentations,
)
from workspace_service.surfaces.grants import CapabilityGrantService, CapabilityPolicy
from workspace_service.surfaces.live_app_service import (
    LiveAppControlService,
    LiveAppControlError,
)
from workspace_service.surfaces.presentation_service import PresentationService
from workspace_service.surfaces.service import SurfaceActor, SurfaceService
from packages.workspace_service.tests.surfaces.test_live_app_service import _instance
from packages.workspace_service.tests.test_process_ui_authoring import (
    prepared,
    authorized,
    fake_build,
)


class ControlledManager:
    def __init__(self, root):
        self.root, self.instances, self.calls = root, {}, []

    async def start(self, request):
        import json

        path = self.root / f".wright/apps/{request.manifest_id}.surface.json"
        declaration = parse_live_app_manifest(json.loads(path.read_bytes()))
        self.calls.append(("start", request))
        instance = replace(
            _instance(instance_id="instance-" + str(request.surface_id)),
            workspace_id="workspace",
            surface_id=request.surface_id,
            manifest_id=request.manifest_id,
            manifest_hash=declaration.canonical_hash,
            sharing="isolated",
            lifetime_policy="presentation",
        )
        self.instances[instance.instance_id] = instance
        return instance

    def get(self, instance_id):
        return self.instances[instance_id]

    def presentation_projection(self, instance_id):
        return (
            {"kind": "panel", "eligible": True},
            {"kind": "browser", "eligible": False},
        )

    async def stop(self, instance_id, *, idempotency_key):
        self.calls.append(("stop", instance_id))
        instance = replace(self.get(instance_id), state="stopped")
        self.instances[instance_id] = instance
        return instance


def native_case(root, monkeypatch, *, policy=None):
    database = root / "state.db"
    upgrade_database(database)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO engineering_workspaces "
            "(workspace_id,session_id,local_path,created_at,updated_at) VALUES (?,?,?,1,1)",
            ("workspace", "owned-session", str(root)),
        )
    monkeypatch.setattr(authoring_module, "build_interface", fake_build)
    author, process = prepared(root)
    service = SurfaceService(repository=SurfaceRepository(database))
    manager = ControlledManager(root)
    surfaces = SimpleNamespace(
        accepting_commands=True,
        service=service,
        live_apps=LiveAppControlService(
            surfaces=service, manager_for_workspace=lambda _: manager
        ),
        presentation_service=PresentationService(
            database, preview=SurfacePreviewSettings()
        ),
        grant_service=CapabilityGrantService(database, policy=policy),
    )
    actor = SurfaceActor(
        user_id="user",
        workspace_id="workspace",
        session_id="owned-session",
        role="engineer",
    )
    owner = ProcessInterfacePresentations(author.application, surfaces)
    author.application.runs.cancel = AsyncMock(
        side_effect=AssertionError("View cleanup cannot cancel a process")
    )
    return SimpleNamespace(
        author=author,
        application=author.application,
        process=process,
        surfaces=surfaces,
        manager=manager,
        actor=actor,
        owner=owner,
        scope=authorized().process_scope,
        root=root,
    )


async def build(case):
    accepted = await case.application.workspace.workflow_sources.read(
        case.root, case.process.source_path
    )
    path = case.root / case.process.source_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(accepted.source, encoding="utf-8")
    job = await case.author.submit(
        authorized(), case.process, "create-one", "Show these results"
    )
    job = await case.author.wait(authorized(), case.process, job.job_id)
    assert job.state == "preview_ready"
    return job


@pytest.mark.anyio
async def test_open_reports_capacity_without_private_runtime_details(
    tmp_path, monkeypatch
):
    case = native_case(tmp_path, monkeypatch)
    case.owner._open = AsyncMock(
        side_effect=LiveAppControlError(
            "SURFACE_LIMIT_OWNED_APPS", "private host path", retryable=False
        )
    )
    with pytest.raises(ProcessInterfaceError) as raised:
        await case.owner.open(
            case.scope, case.process, case.actor, "job", "open-capacity", read_only=True
        )
    assert "open interface limit" in raised.value.reason.message
    assert "Close an unused interface tab" in raised.value.reason.correction
    assert raised.value.diagnostic == {
        "runtime_code": "SURFACE_LIMIT_OWNED_APPS",
        "retryable": False,
    }
    assert "private host" not in str(raised.value)


def retained_grants(case):
    sources = {
        (descriptor.source.source_id, descriptor.source.source_version)
        for descriptor in case.surfaces.service.repository.list(
            user_id=case.actor.user_id,
            workspace_id=case.actor.workspace_id,
            session_id=case.actor.session_id,
        )
    }
    return [
        grant
        for source_id, source_version in sources
        for grant in case.surfaces.grant_service.repository.list(
            user_id=case.actor.user_id,
            workspace_id=case.actor.workspace_id,
            source_id=source_id,
            source_version=source_version,
        )
    ]


async def save(case, job, opened):
    _, manifest, report, _, _ = case.application.ui_revisions.preview_bundle(
        case.scope, case.process, job.job_id
    )
    # Explicitly synthetic owner observation. Actual browser proof is separate.
    case.application.ui_revisions.observe_preview(
        case.scope,
        case.process,
        job.job_id,
        ProcessUIPreviewObservation(
            opened["launch"].presentation_id,
            manifest.ui_id,
            manifest.revision_id,
            report.bundle_digest,
        ),
    )
    return await case.application.ui_revisions.save(
        authorized(),
        case.process,
        job.job_id,
        expected_source_digest=report.source_digest,
        expected_manifest_digest=report.manifest_digest,
        expected_bundle_digest=report.bundle_digest,
        expected_active_revision=None,
    )


@pytest.mark.asyncio
async def test_preview_uses_fixed_existing_owner_and_exact_read_only_grants(
    tmp_path, monkeypatch
):
    case = native_case(tmp_path, monkeypatch)
    job = await build(case)
    opened = await case.owner.open(
        case.scope, case.process, case.actor, job.job_id, "preview-one", read_only=True
    )
    descriptor, launch = opened["descriptor"], opened["launch"]
    assert descriptor.lifecycle is SurfaceLifecycle.READY
    assert descriptor.source.source_id.startswith("process.ui-")
    assert launch.kind == "panel" and opened["binding"].read_only
    assert opened["binding"].run_id is None
    grants = retained_grants(case)
    assert {grant.capability for grant in grants} == {
        "process.read",
        "process.results",
        "process.navigate",
    }
    assert all(
        grant.constraints == opened["binding"].model_dump(mode="json")
        for grant in grants
    )
    again = await case.owner.open(
        case.scope, case.process, case.actor, job.job_id, "preview-one", read_only=True
    )
    assert again["launch"].presentation_id == launch.presentation_id
    assert len(case.manager.calls) == 1
    assert len(retained_grants(case)) == 3
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_saved_reuse_requires_no_model_or_compiler_and_close_does_not_cancel(
    tmp_path, monkeypatch
):
    case = native_case(tmp_path, monkeypatch)
    job = await build(case)
    preview = await case.owner.open(
        case.scope, case.process, case.actor, job.job_id, "preview-one", read_only=True
    )
    await save(case, job, preview)
    calls = len(case.author.engine.calls)
    monkeypatch.setattr(
        authoring_module,
        "build_interface",
        AsyncMock(side_effect=AssertionError("No fresh build")),
    )
    case.author.engine.stream_chat = AsyncMock(
        side_effect=AssertionError("No fresh model invocation")
    )
    view = await case.owner.open(
        case.scope, case.process, case.actor, job.job_id, "saved-one", read_only=False
    )
    assert not view["binding"].read_only
    await case.owner.close(
        case.scope,
        case.actor,
        view["descriptor"].surface_id,
        view["launch"].presentation_id,
    )
    await case.owner.close(
        case.scope,
        case.actor,
        view["descriptor"].surface_id,
        view["launch"].presentation_id,
    )
    record = case.surfaces.presentation_service.get_record(
        actor=case.actor, presentation_id=view["launch"].presentation_id
    )
    assert record.state == "closed"
    grants = retained_grants(case)
    own = [
        grant
        for grant in grants
        if grant.constraints["presentation_id"] == record.presentation_id
    ]
    assert own and all(grant.revoked_at is not None for grant in own)
    assert len([call for call in case.manager.calls if call[0] == "stop"]) == 1
    assert len(case.author.engine.calls) == calls
    case.application.runs.cancel.assert_not_called()
    assert (
        case.surfaces.presentation_service.get_record(
            actor=case.actor, presentation_id=preview["launch"].presentation_id
        ).state
        == "issued"
    )


@pytest.mark.asyncio
async def test_unsaved_working_mode_and_foreign_context_are_denied(
    tmp_path, monkeypatch
):
    case = native_case(tmp_path, monkeypatch)
    job = await build(case)
    with pytest.raises(KeyError):
        await case.owner.open(
            case.scope, case.process, case.actor, job.job_id, "unsaved", read_only=False
        )
    actor = SurfaceActor(
        user_id="another-user",
        workspace_id="workspace",
        session_id="owned-session",
        role="admin",
    )
    with pytest.raises(ProcessInterfaceError, match="native workspace context"):
        await case.owner.open(
            case.scope, case.process, actor, job.job_id, "foreign", read_only=True
        )
    assert case.manager.calls == []


@pytest.mark.asyncio
async def test_native_open_cannot_renew_revoked_grants_or_rebind_preview_mode(
    tmp_path, monkeypatch
):
    case = native_case(tmp_path, monkeypatch)
    job = await build(case)
    view = await case.owner.open(
        case.scope,
        case.process,
        case.actor,
        job.job_id,
        "exact-request",
        read_only=True,
    )
    await save(case, job, view)
    with pytest.raises(ProcessInterfaceError, match="different process/run binding"):
        await case.owner.open(
            case.scope,
            case.process,
            case.actor,
            job.job_id,
            "exact-request",
            read_only=False,
        )
    grant = retained_grants(case)[0]
    case.surfaces.grant_service.revoke(actor=case.actor, grant_id=grant.grant_id)
    with pytest.raises(ProcessInterfaceError, match="capability policy"):
        await case.owner.open(
            case.scope,
            case.process,
            case.actor,
            job.job_id,
            "exact-request",
            read_only=True,
        )
    assert (
        case.surfaces.presentation_service.get_record(
            actor=case.actor, presentation_id=view["launch"].presentation_id
        ).state
        == "closed"
    )


@pytest.mark.asyncio
async def test_policy_denial_contains_view_and_corrupt_manifest_cannot_launch(
    tmp_path, monkeypatch
):
    case = native_case(
        tmp_path,
        monkeypatch,
        policy=CapabilityPolicy(denied_capabilities=frozenset({"process.results"})),
    )
    job = await build(case)
    with pytest.raises(ProcessInterfaceError, match="capability policy"):
        await case.owner.open(
            case.scope, case.process, case.actor, job.job_id, "denied", read_only=True
        )
    assert case.manager.calls[-1][0] == "stop"
    assert all(grant.revoked_at is not None for grant in retained_grants(case))
    path = next((tmp_path / ".wright/apps").glob("*.surface.json"))
    path.write_text("{}", encoding="utf-8")
    count = len(case.manager.calls)
    with pytest.raises(ProcessInterfaceError, match="runtime declaration"):
        await case.owner.open(
            case.scope, case.process, case.actor, job.job_id, "changed", read_only=True
        )
    assert len(case.manager.calls) == count


@pytest.mark.asyncio
async def test_bound_saved_views_reuse_two_durable_runs_and_close_leaves_work_running(
    tmp_path, monkeypatch
):
    import asyncio

    case = native_case(tmp_path, monkeypatch)
    job = await build(case)
    preview = await case.owner.open(
        case.scope, case.process, case.actor, job.job_id, "preview-one", read_only=True
    )
    await save(case, job, preview)
    frozen = (await case.application.set_inputs(case.scope, case.process)).snapshot
    entered, release = asyncio.Event(), asyncio.Event()
    calls = []

    async def generate(prompt, fmt):
        calls.append(prompt)
        entered.set()
        await release.wait()
        return "Controlled result, not engineering acceptance"

    try:
        receipt = await case.application.runs.start(
            case.scope,
            case.process,
            frozen.snapshot_id,
            "run-one",
            expected_input_digest=frozen.digest,
            response_generator=generate,
        )
        await asyncio.wait_for(entered.wait(), 3)
        view = await case.owner.open(
            case.scope,
            case.process,
            case.actor,
            job.job_id,
            "run-one-view",
            read_only=False,
            run_id=receipt.run_id,
        )
        assert view["binding"].run_id == receipt.run_id
        await case.owner.close(
            case.scope,
            case.actor,
            view["descriptor"].surface_id,
            view["launch"].presentation_id,
        )
        case.application.runs.cancel.assert_not_called()
        assert not release.is_set()
        observed = await case.application.get_snapshot(
            case.scope, case.process, run_id=receipt.run_id
        )
        assert observed.state == "running"
        release.set()
        assert (
            await case.application.runs.wait(case.scope, case.process, receipt.run_id)
        )["status"] == "completed"
        second = await case.application.runs.start(
            case.scope,
            case.process,
            frozen.snapshot_id,
            "run-two",
            expected_input_digest=frozen.digest,
            response_generator=generate,
        )
        assert (
            await case.application.runs.wait(case.scope, case.process, second.run_id)
        )["status"] == "completed"
        reuse = await case.owner.open(
            case.scope,
            case.process,
            case.actor,
            job.job_id,
            "run-two-view",
            read_only=False,
            run_id=second.run_id,
        )
        assert reuse["binding"].ui_id == view["binding"].ui_id
        assert reuse["binding"].revision_id == view["binding"].revision_id
        assert reuse["binding"].run_id == second.run_id != receipt.run_id
        assert len(case.author.engine.calls) == 1
        assert len(calls) == 4  # Two existing source tasks in each run.
        with pytest.raises(ProcessInterfaceError):
            await case.owner.open(
                case.scope,
                case.process,
                case.actor,
                job.job_id,
                "foreign-run-view",
                read_only=False,
                run_id="foreign-run",
            )
        await case.owner.close(
            case.scope,
            case.actor,
            reuse["descriptor"].surface_id,
            reuse["launch"].presentation_id,
        )
    finally:
        release.set()
        await case.application.close()
