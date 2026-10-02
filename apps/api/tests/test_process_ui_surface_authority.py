"""Real immutable UI/grant/process owners behind an isolated-route authority.

Model/compiler and pinned listener are controlled. This is API boundary proof,
not a browser/managed-process/live-model or engineering acceptance claim.
"""

import asyncio
import json
import sqlite3
from datetime import timedelta
from dataclasses import replace
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routers.surface_preview import router
from api.routers.process_surface import get_process_surface_grants
from api.routers.workspace import get_workspace_service
from api.surface_route_authority import (
    AuthorizedSurfaceRoute,
    SurfaceRouteAuthorizationError,
)
from core.process_interfaces import InterfaceManifest
from data_vault import upgrade_database
from workspace_service.process_interfaces import authoring as authoring_module
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.service import ProcessScope
from workspace_service.process_interfaces.surface_bridge import ProcessSurfaceBridge
from workspace_service.surfaces.grants import (
    CapabilityGrantService,
    CapabilityRequest,
    ProcessPresentationBinding,
)
from workspace_service.surfaces.process_ui_manifest import process_ui_manifest
from workspace_service.surfaces.service import ActorRole, SurfaceActor
from packages.workspace_service.tests.test_process_ui_authoring import (
    prepared,
    authorized,
    fake_build,
    Engine,
)

ORIGIN = "https://s-owned.preview.example.test"
PREFIX = "/__wright/process"


@pytest.fixture
def case(tmp_path, monkeypatch, request):
    upgrade_database(tmp_path / "state.db")
    with sqlite3.connect(tmp_path / "state.db") as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES ('workspace', 'owned-session', ?, 1, 1)""",
            (str(tmp_path),),
        )
    monkeypatch.setattr(authoring_module, "build_interface", fake_build)
    readonly = getattr(request, "param", True)

    def working(output):
        output["manifest"]["capabilities"] += ["process.inputs", "process.start"]
        return output

    author, reference = prepared(
        tmp_path, Engine(replies=None if readonly else [working])
    )

    async def built():
        job = await author.submit(
            authorized(), reference, "author-one", "Show this process"
        )
        return await author.wait(authorized(), reference, job.job_id)

    job = asyncio.run(built())
    assert job.state == "preview_ready"
    retained = author.repository.get_authoring_record("workspace", job.job_id, "built")
    manifest = InterfaceManifest.model_validate(retained["manifest"])
    _, declaration = process_ui_manifest(
        tmp_path, manifest, retained["inventory_digest"]
    )
    state = {"authority": True, "target": True, "activity": 0}
    route = AuthorizedSurfaceRoute(
        presentation_id="presentation-one",
        presentation_origin=ORIGIN,
        principal_id="user",
        workspace_id="workspace",
        session_id="owned-session",
        surface_id="surface-one",
        source_id=declaration.manifest_id,
        source_version=declaration.canonical_hash,
        instance_id="instance-one",
        generation=1,
        pin=SimpleNamespace(),
        http_declared=True,
        websocket_declared=False,
        sse_declared=False,
        limits=SimpleNamespace(),
        authority_valid=lambda: state["authority"],
        target_valid=lambda: state["target"],
        activity=lambda: state.update(activity=state["activity"] + 1),
    )

    class Authority:
        current = route

        def authorize(self, *, host, cookie):
            if host != ORIGIN.split("//")[1] or cookie != "owned-cookie":
                raise SurfaceRouteAuthorizationError(
                    "SURFACE_PREVIEW_UNAUTHORIZED", "Denied", status_code=401
                )
            return self.current

    grants = CapabilityGrantService(tmp_path / "state.db")
    actor = SurfaceActor(
        user_id="user",
        workspace_id="workspace",
        session_id="owned-session",
        role=ActorRole.ENGINEER,
    )
    binding = ProcessPresentationBinding(
        process=reference,
        ui_id=manifest.ui_id,
        revision_id=manifest.revision_id,
        run_id=None,
        read_only=readonly,
        presentation_id=route.presentation_id,
        generation=1,
    )
    records = []
    for capability in manifest.capabilities:
        read = capability in {"process.read", "process.results", "process.navigate"}
        if readonly and not read:
            continue
        records.append(
            grants.decide(
                actor=actor,
                request=CapabilityRequest(
                    source_id=route.source_id,
                    source_version=route.source_version,
                    instance_id=route.instance_id,
                    capability=capability,
                    operation=capability,
                    constraints=binding.model_dump(mode="json"),
                    risk_tier="low" if read else "mutating",
                    persistence="instance",
                    duration_seconds=600,
                    declared=True,
                    decision="allow",
                    reason="Exact test presentation",
                ),
            )
        )
    app = FastAPI()
    app.include_router(router)
    author.application.workspace.process_interfaces = author.application
    app.dependency_overrides[get_workspace_service] = lambda: (
        author.application.workspace
    )
    app.dependency_overrides[get_process_surface_grants] = lambda: grants
    authority = Authority()
    app.state.surface_route_authority = authority
    with TestClient(
        app, base_url=ORIGIN, cookies={"wright_surface": "owned-cookie"}
    ) as client:
        yield SimpleNamespace(
            client=client,
            owner=author.application,
            root=tmp_path,
            job=job,
            manifest=manifest,
            binding=binding,
            authority=authority,
            route=route,
            grants=grants,
            actor=actor,
            records=records,
            state=state,
            reference=reference,
            query={
                "session_id": "owned-session",
                "path": reference.source_path,
                "expected_storage_digest": reference.source_digest,
            },
        )


def test_context_and_snapshot_use_exact_owner_without_native_token(case):
    context = case.client.get(PREFIX + "/context")
    assert context.status_code == 200
    assert context.json()["read_only"] is True
    assert context.json()["process"] == case.reference.model_dump(mode="json")
    assert context.json()["capabilities"] == [
        "process.navigate",
        "process.read",
        "process.results",
    ]
    assert "token" not in context.json()
    snapshot = case.client.get(PREFIX + "/interaction", params=case.query)
    assert snapshot.status_code == 200
    assert snapshot.headers["cache-control"] == "no-store"
    assert snapshot.json()["context"]["process"] == context.json()["process"]
    assert not (case.root / "first.txt").exists()


def test_preview_loaded_record_is_derived_from_exact_route_and_verified_bundle(case):
    with pytest.raises(KeyError):
        case.owner.interfaces.get_authoring_record(
            "workspace", case.job.job_id, "preview"
        )
    body = {"schema_version": "wright.process-presentation-loaded/1"}
    assert (
        case.client.post(
            PREFIX + "/loaded", json=body, headers={"Origin": ORIGIN}
        ).status_code
        == 200
    )
    first = case.owner.interfaces.get_authoring_record(
        "workspace", case.job.job_id, "preview"
    )
    assert first["presentation_id"] == case.route.presentation_id
    assert first["revision_id"] == case.manifest.revision_id
    assert (
        case.client.post(
            PREFIX + "/loaded", json=body, headers={"Origin": ORIGIN}
        ).status_code
        == 200
    )
    assert (
        case.owner.interfaces.get_authoring_record(
            "workspace", case.job.job_id, "preview"
        )
        == first
    )
    assert (
        case.client.post(
            PREFIX + "/loaded",
            json=body | {"bundle_digest": "f" * 64},
            headers={"Origin": ORIGIN},
        ).status_code
        == 403
    )


@pytest.mark.parametrize("case", [False], indirect=True)
def test_malformed_duplicate_large_or_extra_json_does_not_reach_input_owner(case):
    body = json.dumps(case.query | {"bindings": []})
    for malformed in [
        body[:-1] + ',"session_id":"owned-session"}',
        body[:-1] + ',"extra":"private"}',
        '{"value":NaN}',
    ]:
        response = case.client.post(
            PREFIX + "/inputs",
            content=malformed,
            headers={"Origin": ORIGIN, "content-type": "application/json"},
        )
        assert response.status_code == 422
        assert "private" not in response.text
    too_large = case.client.post(
        PREFIX + "/inputs",
        content=" " * 1_200_001,
        headers={"Origin": ORIGIN, "content-type": "application/json"},
    )
    assert too_large.status_code == 413


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_id", "vendor.server.resource"),
        ("source_version", "f" * 64),
        ("presentation_id", "other-presentation"),
        ("generation", 2),
        ("instance_id", "other-instance"),
        ("principal_id", "other-user"),
        ("workspace_id", "other-workspace"),
        ("http_declared", False),
    ],
)
def test_presentation_identity_drift_denies_context(case, field, value):
    case.authority.current = replace(case.route, **{field: value})
    assert case.client.get(PREFIX + "/context").status_code == 403


@pytest.mark.parametrize("key", ["authority", "target"])
def test_stopped_revoked_or_replaced_presentation_denies_reads(case, key):
    case.state[key] = False
    response = case.client.get(PREFIX + "/interaction", params=case.query)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PRESENTATION_EXPIRED"


def test_revoked_process_read_grant_denies_context(case):
    for record in case.records:
        if record.capability == "process.read":
            case.grants.revoke(actor=case.actor, grant_id=record.grant_id)
    assert case.client.get(PREFIX + "/context").status_code == 403


def test_passive_toolpath_preview_keeps_exact_managed_results_grant(case, monkeypatch):
    from workspace_service.process_interfaces.artifacts import ProcessArtifactBytes

    calls = []

    async def passive(scope, process, reference, **options):
        calls.append((scope, process, reference, options))
        return ProcessArtifactBytes(
            reference,
            b'{"format":"wright.gcode.toolpaths.v1"}',
            "application/vnd.wright.toolpaths+json",
        )

    monkeypatch.setattr(case.owner.artifacts, "preview", passive)
    body = case.query | {
        "reference": {"artifact_ref": "outputs/slice.3mf", "sha256": "a" * 64},
        "input_snapshot_id": "input-one",
        "preview": "toolpaths",
        "archive_entry": "Metadata/plate_1.gcode",
    }
    response = case.client.post(
        PREFIX + "/representations/read", json=body, headers={"Origin": ORIGIN}
    )
    assert response.status_code == 200
    assert response.headers["x-wright-artifact-sha256"] == "a" * 64
    assert response.headers["x-wright-view-format"] == "wright.gcode.toolpaths.v1"
    assert len(calls) == 1
    scope, process, reference, options = calls[0]
    assert scope.run_bound is True and scope.run_id is None
    assert process == case.reference
    assert reference.artifact_ref == "outputs/slice.3mf"
    assert options == {
        "run_id": None,
        "input_snapshot_id": "input-one",
        "archive_entry": "Metadata/plate_1.gcode",
    }
    foreign = body | {"run_id": "other-run", "input_snapshot_id": None}
    assert (
        case.client.post(
            PREFIX + "/representations/read", json=foreign, headers={"Origin": ORIGIN}
        ).status_code
        == 403
    )
    for record in case.records:
        if record.capability == "process.results":
            case.grants.revoke(actor=case.actor, grant_id=record.grant_id)
    assert (
        case.client.post(
            PREFIX + "/representations/read", json=body, headers={"Origin": ORIGIN}
        ).status_code
        == 403
    )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "path,body",
    [
        ("inputs", {"bindings": []}),
        (
            "runs",
            {
                "input_snapshot_id": "input-one",
                "request_id": "request-one",
                "expected_input_digest": "a" * 64,
            },
        ),
        ("runs/other-run/cancel", {"request_id": "request-one"}),
        (
            "actions/continue-other",
            {"request_id": "request-one", "subject_digest": "a" * 64},
        ),
        (
            "interactions/other/response",
            {
                "request_id": "request-one",
                "subject_digest": "a" * 64,
                "value": "answer",
            },
        ),
        (
            "interactions/other/decision",
            {
                "request_id": "request-one",
                "subject_digest": "a" * 64,
                "decision": "approved",
            },
        ),
    ],
)
def test_readonly_preview_rejects_every_mutation_before_owner(case, path, body):
    response = case.client.post(
        PREFIX + "/" + path, json=case.query | body, headers={"Origin": ORIGIN}
    )
    assert response.status_code == 403
    assert "runs" not in case.owner.__dict__ or not case.owner.runs._owned


@pytest.mark.parametrize("case", [False], indirect=True)
def test_working_presentation_uses_native_input_owner_and_exact_selectors(case):
    response = case.client.post(
        PREFIX + "/inputs",
        json=case.query
        | {
            "bindings": [
                {"kind": "value", "input_id": "brief", "value": "Exact run input"}
            ]
        },
        headers={"Origin": ORIGIN},
    )
    assert response.status_code == 200
    frozen = response.json()
    assert (
        case.owner.inputs.get_snapshot("workspace", frozen["snapshot_id"]).digest
        == frozen["digest"]
    )
    readiness = case.client.post(
        PREFIX + "/readiness",
        json=case.query | {"input_snapshot_id": frozen["snapshot_id"]},
        headers={"Origin": ORIGIN},
    )
    assert readiness.status_code == 200
    assert readiness.json()["state"] == "ready"
    changed = case.client.post(
        PREFIX + "/inputs",
        json=case.query | {"path": "other.workflow.wflow", "bindings": []},
        headers={"Origin": ORIGIN},
    )
    assert changed.status_code == 403
    assert not (case.root / "first.txt").exists()


@pytest.mark.parametrize("case", [False], indirect=True)
@pytest.mark.parametrize("origin", [None, "https://wright.example.test", "null"])
def test_post_requires_exact_origin_even_with_cookie(case, origin):
    response = case.client.post(
        PREFIX + "/inputs",
        json=case.query | {"bindings": []},
        headers={} if origin is None else {"Origin": origin},
    )
    assert response.status_code == 403


def test_foreign_run_and_ambiguous_selectors_are_rejected(case):
    for suffix, query in [
        ("interaction", case.query | {"run_id": "other-run"}),
        ("runs/other-run", case.query),
        ("runs/other-run/events", case.query),
        ("interaction", list(case.query.items()) + [("session_id", "other-session")]),
        ("interaction", case.query | {"actor": "administrator"}),
    ]:
        assert case.client.get(PREFIX + "/" + suffix, params=query).status_code == 403


def test_no_generic_tool_or_authoring_authority_or_native_cookie_equivalence(case):
    assert (
        case.client.post(
            PREFIX + "/invokeTool", json={}, headers={"Origin": ORIGIN}
        ).status_code
        == 403
    )
    assert (
        case.client.post(
            PREFIX + "/authoring-jobs", json={}, headers={"Origin": ORIGIN}
        ).status_code
        == 403
    )
    case.client.cookies.clear()
    assert (
        case.client.get(
            PREFIX + "/context", headers={"Authorization": "Bearer native-token"}
        ).status_code
        == 401
    )


def test_run_binding_is_enforced_by_common_receipt_snapshot_and_artifact_owners(case):
    bound = ProcessScope(
        "user",
        "workspace",
        frozenset({"process.read", "process.results"}),
        run_bound=True,
        run_id="run-one",
    )
    with pytest.raises(ProcessInterfaceError, match="different run"):
        case.owner.runs._receipt(bound, case.reference, "run-two")
    with pytest.raises(ProcessInterfaceError, match="different run"):
        asyncio.run(case.owner.get_snapshot(bound, case.reference, run_id="run-two"))
    with pytest.raises(ProcessInterfaceError, match="different run"):
        asyncio.run(
            case.owner.artifacts.read(bound, case.reference, None, run_id="run-two")
        )


def test_live_stream_grants_are_revalidated_without_rereading_static_bundle(
    case, monkeypatch
):
    bridge = ProcessSurfaceBridge(case.owner, case.grants)
    context = bridge.authorize(case.route)

    def unexpected(*args):
        raise AssertionError(
            "The verified UI bundle must not be reread for every chunk"
        )

    monkeypatch.setattr(case.owner.ui_revisions, "preview_bundle", unexpected)
    for _ in range(20):
        bridge.revalidate(case.route, context)
    for record in case.records:
        if record.capability == "process.read":
            case.grants.revoke(actor=case.actor, grant_id=record.grant_id)
    with pytest.raises(ProcessInterfaceError, match="cannot access"):
        bridge.revalidate(case.route, context)


def test_expired_and_changed_stream_context_are_rejected(case):
    bridge = ProcessSurfaceBridge(case.owner, case.grants)
    context = bridge.authorize(case.route)
    with pytest.raises(ProcessInterfaceError, match="cannot access"):
        bridge.revalidate(replace(case.route, source_version="f" * 64), context)
    now = case.grants.clock()
    case.grants.clock = lambda: now + timedelta(seconds=601)
    with pytest.raises(ProcessInterfaceError, match="cannot access"):
        bridge.revalidate(case.route, context)


def test_bound_receipt_must_match_exact_source_digest(case, monkeypatch):
    bound = ProcessScope(
        "user",
        "workspace",
        frozenset({"process.read"}),
        run_bound=True,
        run_id="run-one",
    )
    monkeypatch.setattr(
        case.owner.inputs,
        "receipt_for_run",
        lambda *args: SimpleNamespace(
            process=case.reference.model_copy(update={"source_digest": "f" * 64})
        ),
    )
    with pytest.raises(ProcessInterfaceError, match="does not belong"):
        case.owner.runs._receipt(bound, case.reference, "run-one")


def test_corrupted_built_asset_never_receives_bridge_authority(case):
    built = case.owner.interfaces.get_authoring_record(
        "workspace", case.job.job_id, "built"
    )
    vault = (
        case.root
        / f".wright/process-uis/{case.manifest.ui_id}/revisions/{case.manifest.revision_id}"
    )
    from data_vault.process_ui_artifacts import ImmutableFileSet

    files = ImmutableFileSet(vault)
    assert files.read(built["inventory_digest"])
    # Physical vault files have opaque names. Corrupt a stored asset without
    # changing the exact signed inventory/source identity.
    index = json.loads((vault / "inventory.json").read_text())
    target = index["dist/app.js"]["storage_key"]
    from data_vault.file_vault import FileVault

    FileVault(vault).resolve(target).write_bytes(b"tampered")
    response = case.client.get(PREFIX + "/context")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "UI_INCOMPATIBLE"


@pytest.mark.parametrize(
    "target",
    [
        {"kind": "process"},
        {"kind": "block", "block_id": "make-output", "result_id": "result-one"},
        {"kind": "result", "result_id": "result-one"},
        {
            "kind": "assessment",
            "assessment_id": "assessment-one",
            "result_id": "result-one",
        },
        {
            "kind": "evidence",
            "artifact_ref": "results/fine.csv",
            "result_id": "result-one",
        },
    ],
)
@pytest.mark.parametrize("bound_run", [None, "run-one"])
def test_presentation_navigation_supplies_only_its_authorized_run(
    case, monkeypatch, target, bound_run
):
    from api.routers import process_interfaces as native
    from api.routers.process_surface import _dispatch
    from starlette.requests import Request
    from starlette.responses import Response

    calls = []

    async def resolve(**kwargs):
        calls.append(kwargs["body"].target.model_dump(exclude_none=True))
        return calls[-1]

    monkeypatch.setattr(native, "resolve_process_navigation", resolve)
    context = SimpleNamespace(
        binding=case.binding.model_copy(update={"run_id": bound_run}),
        scope=ProcessScope(
            "user",
            "workspace",
            frozenset({"process.navigate"}),
            run_bound=True,
            run_id=bound_run,
        ),
        session_id="owned-session",
    )

    def dispatch(requested):
        raw = json.dumps(case.query | {"target": requested}).encode()

        async def receive():
            return {"type": "http.request", "body": raw, "more_body": False}

        request = Request(
            {
                "type": "http",
                "method": "POST",
                "path": PREFIX + "/navigation",
                "query_string": b"",
                "headers": [(b"content-type", b"application/json")],
            },
            receive,
        )
        return asyncio.run(
            _dispatch(
                "navigation",
                request,
                Response(),
                case.owner.workspace,
                case.route,
                context,
            )
        )

    expected = target | ({"run_id": bound_run} if bound_run else {})
    assert dispatch(target) == expected
    assert calls == [expected]
    assert target.get("run_id") is None  # Caller data was not mutated.
    if bound_run:
        assert dispatch(target | {"run_id": bound_run}) == expected
    with pytest.raises(ProcessInterfaceError, match="different run"):
        dispatch(target | {"run_id": "other-run"})
    assert all(call.get("run_id") == bound_run for call in calls)
