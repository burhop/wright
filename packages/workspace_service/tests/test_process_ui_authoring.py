"""Durable presentation jobs with controlled model/build responses; no engineering effects."""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from unittest.mock import AsyncMock

import pytest

from agent_adapters.base import AgentInvocationCapabilities, AgentStreamEvent
from core.process_interfaces import (
    AuthoringJob,
    BuildReport,
    CodingRole,
    RoleResolution,
)
from core.process_validation import canonical_digest, canonical_json
from data_vault.process_ui_artifacts import ImmutableFileSet
from workspace_service.process_interfaces import authoring as module
from workspace_service.process_interfaces.authoring import (
    NativeAuthoringScope,
    ProcessInterfaceAuthoring,
)
from workspace_service.process_interfaces.build import BuildToolchain, BuiltInterface
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.resources import load_authoring_resources
from packages.workspace_service.tests.test_process_preparation_service import (
    owner,
    scope,
)
from packages.workspace_service.tests.test_process_input_readiness import (
    source,
    process,
)


class Engine:
    def __init__(
        self, replies=None, *, entered=None, release=None, tool=False, wrong_role=False
    ):
        self.calls, self.probes = [], 0
        self.replies = replies or []
        self.entered, self.release = entered, release
        self.tool, self.wrong_role = tool, wrong_role

    async def get_invocation_capabilities(self):
        self.probes += 1
        return AgentInvocationCapabilities(
            adapter="controlled-adapter",
            available=True,
            effective_instructions_every_turn=True,
            no_tools=True,
            inherited_default_model=True,
            model_reference="configured-default",
            configuration_digest="a" * 64,
        )

    async def stream_chat(self, request):
        self.calls.append(request)
        if self.entered:
            self.entered.set()
        if self.release:
            await self.release.wait()
        if self.tool:
            yield AgentStreamEvent("tool", {"name": "forbidden"})
            return
        role = request.invocation_context
        yield AgentStreamEvent(
            "progress",
            {
                "effective_instructions_digest": "b" * 64
                if self.wrong_role
                else role.instructions_digest,
                "resolution": {
                    "model_reference": role.expected_model_reference,
                    "configuration_digest": role.expected_configuration_digest,
                },
            },
        )
        prompt = json.loads(request.message)
        output = {
            "manifest": prompt["manifest"],
            "source": {"files": {"App.tsx": prompt["reference_template"]}},
        }
        index = len(self.calls) - 1
        reply = self.replies[index] if index < len(self.replies) else output
        if callable(reply):
            reply = reply(output)
        yield AgentStreamEvent(
            "token",
            {"text": reply if isinstance(reply, str) else canonical_json(reply)},
        )
        yield AgentStreamEvent("stream_end", {})


class Compiler:
    def describe(self):
        return {"controlled": True}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code,expected",
    [
        ("SCOPED_MODEL_TIMEOUT", "UI_MODEL_TIMEOUT"),
        ("SCOPED_MODEL_AUTH_REQUIRED", "UI_MODEL_AUTH_REQUIRED"),
        ("SCOPED_MODEL_RATE_LIMITED", "UI_MODEL_RATE_LIMITED"),
    ],
)
async def test_safe_provider_failure_is_actionable_and_not_replayed(
    tmp_path, code, expected
):
    class FailingEngine(Engine):
        async def stream_chat(self, request):
            self.calls.append(request)
            yield AgentStreamEvent(
                "error", {"code": code, "message": "SECRET SDK token"}
            )

    engine = FailingEngine()
    service, reference = prepared(tmp_path, engine)
    job = await service.submit(
        authorized(), reference, "provider-failure", "Show results"
    )
    final = await service.wait(authorized(), reference, job.job_id)
    assert final.state == "failed" and final.repair_attempt == 0
    assert final.diagnostics[0].code == expected
    assert "SECRET" not in final.model_dump_json()
    retained = await service.submit(
        authorized(), reference, "provider-failure", "Show results"
    )
    assert retained.job_id == job.job_id and len(engine.calls) == 1
    await service.close()


async def fake_build(**values):
    root = values["builds_root"] / "controlled-build"
    # Each invocation is assigned a distinct draft, as the actual builder does.
    root = root.with_name(
        root.name
        + "-"
        + str(
            len(list(values["builds_root"].glob("*")))
            if values["builds_root"].exists()
            else 0
        )
    )
    dist = root / "dist"
    dist.mkdir(parents=True)
    raw = b"export function mount() {}"
    (dist / "app.js").write_bytes(raw)
    report = BuildReport(
        build_id="controlled-build",
        source_digest=canonical_digest(values["source"]),
        manifest_digest=canonical_digest(values["manifest"]),
        toolchain_digest="c" * 64,
        bundle_digest=canonical_digest({"app.js": hashlib.sha256(raw).hexdigest()}),
        state="built",
        created_at=datetime.now(timezone.utc).isoformat(),
        bundled_bytes=len(raw),
    )
    return BuiltInterface(report, root, dist)


def prepared(tmp_path, engine=None):
    text = source(
        default="Private engineering requirements omitted from authoring", later=True
    )
    application = owner(tmp_path, text)
    return ProcessInterfaceAuthoring(
        application, engine or Engine(), Compiler()
    ), process(text)


def authorized(*capabilities):
    return NativeAuthoringScope(
        scope(
            *(
                capabilities
                or (
                    "process.read",
                    "process.inputs",
                    "process.start",
                    "process.results",
                    "process.navigate",
                )
            )
        ),
        True,
    )


@pytest.fixture(autouse=True)
def controlled_compiler(monkeypatch):
    monkeypatch.setattr(module, "build_interface", fake_build)


@pytest.mark.asyncio
async def test_model_cannot_request_capabilities_outside_native_authoring_scope(
    tmp_path,
):
    def widen(output):
        output["manifest"]["capabilities"].append("process.cancel")
        return output

    service, reference = prepared(tmp_path, Engine(replies=[widen, widen, widen]))
    job = await service.submit(
        authorized(), reference, "widen-scope", "Show process progress"
    )
    final = await service.wait(authorized(), reference, job.job_id)
    assert final.state == "failed" and final.repair_attempt == 2
    assert len(service.engine.calls) == 3
    assert "available_process_capabilities" in json.loads(
        service.engine.calls[0].message
    )
    assert not list((tmp_path / ".wright/process-uis").rglob("inventory.json"))


@pytest.mark.asyncio
async def test_generation_retains_scope_build_provenance_and_survives_reopen(tmp_path):
    service, reference = prepared(tmp_path)
    job = await service.submit(
        authorized(), reference, "create-one", "Compare these outputs"
    )
    assert job.state == "queued"
    completed = await service.wait(authorized(), reference, job.job_id)
    assert completed.state == "preview_ready" and completed.repair_attempt == 0
    retained = service.repository.get_authoring_record(
        "workspace", job.job_id, "request"
    )
    attempt = service.repository.get_authoring_record(
        "workspace", job.job_id, "attempt-0"
    )
    assert "Private engineering requirements" not in attempt["prompt"]
    assert retained["catalog"] == [
        {
            "kind": "input",
            "selector": "brief",
            "block_id": "brief",
            "port_id": "brief_out",
            "expected_schema": {"type": "string", "minLength": 1},
        },
        {
            "kind": "output",
            "selector": "first.first_out",
            "block_id": "first",
            "port_id": "first_out",
            "expected_schema": None,
        },
        {
            "kind": "output",
            "selector": "later.later_out",
            "block_id": "later",
            "port_id": "later_out",
            "expected_schema": None,
        },
    ]
    built = service.repository.get_authoring_record("workspace", job.job_id, "built")
    manifest = built["manifest"]
    location = (
        tmp_path
        / f".wright/process-uis/{manifest['ui_id']}/revisions/{manifest['revision_id']}"
    )
    files = ImmutableFileSet(location).read(built["inventory_digest"])
    assert set(files) == {
        "source.json",
        "binding.json",
        "build-report.json",
        "dist/app.js",
    }
    assert json.loads(files["build-report.json"])["state"] == "built"
    reopened, _ = prepared(tmp_path)
    assert await reopened.status(authorized(), reference, job.job_id) == completed
    assert (
        await reopened.submit(
            authorized(), reference, "create-one", "Compare these outputs"
        )
        == completed
    )
    assert reopened.engine.probes == 0 and not reopened.engine.calls
    assert len(service.engine.calls) == 1
    assert service.engine.calls[0].trace_id == retained["trace_id"]
    assert not (tmp_path / "first.txt").exists()
    assert "runs" not in service.application.__dict__


@pytest.mark.asyncio
async def test_actual_fixed_compiler_builds_controlled_model_output(
    tmp_path, monkeypatch
):
    from workspace_service.process_interfaces.build import build_interface

    monkeypatch.setattr(module, "build_interface", build_interface)
    service, reference = prepared(tmp_path)
    root = Path(__file__).resolve().parents[3]
    node = shutil.which("node")
    assert node, "Explicit compiler qualification requires installed Node"
    service.toolchain = BuildToolchain(
        Path(node), root, root / "packages/process_client", root / "packages/ui_kit"
    )
    job = await service.submit(
        authorized(), reference, "actual-build", "Show inputs and outputs"
    )
    assert (
        await service.wait(authorized(), reference, job.job_id)
    ).state == "preview_ready"
    assert (
        service.repository.get_authoring_record("workspace", job.job_id, "built")[
            "build"
        ]["bundled_bytes"]
        > 100_000
    )


@pytest.mark.asyncio
async def test_concurrent_duplicate_requests_do_not_probe_or_generate_twice(tmp_path):
    service, reference = prepared(tmp_path)
    jobs = await asyncio.gather(
        *(
            service.submit(authorized(), reference, "same-request", "Show outputs")
            for _ in range(2)
        )
    )
    assert jobs[0].job_id == jobs[1].job_id
    await service.wait(authorized(), reference, jobs[0].job_id)
    assert service.engine.probes == 1 and len(service.engine.calls) == 1
    with pytest.raises(ProcessInterfaceError) as caught:
        await service.submit(
            authorized(), reference, "same-request", "Different request"
        )
    assert caught.value.reason.code == "REQUEST_CONFLICT"


@pytest.mark.asyncio
async def test_optional_binding_repair_explains_fallback_without_private_input(
    tmp_path,
):
    def missing_fallback(output):
        output["manifest"]["bindings"] = [
            {
                "binding_id": "optional-result",
                "kind": "output",
                "selector": "SECRET-PRIVATE-SELECTOR",
                "required": False,
            }
        ]
        return output

    engine = Engine([missing_fallback])
    service, reference = prepared(tmp_path, engine)
    job = await service.submit(
        authorized(), reference, "optional-binding", "Show results"
    )
    complete = await service.wait(authorized(), reference, job.job_id)
    assert complete.state == "preview_ready" and complete.repair_attempt == 1
    correction = json.loads(engine.calls[1].message)["correction"][0]
    assert "required=false" in correction["correction"]
    assert "fallback" in correction["correction"]
    assert "SECRET-PRIVATE-SELECTOR" not in canonical_json(correction)
    await service.close()


@pytest.mark.asyncio
async def test_two_exact_diagnostic_repairs_preserve_role_and_default_model(tmp_path):
    def wrong_identity(output):
        output["manifest"]["process"]["source_digest"] = "f" * 64
        return output

    engine = Engine(["not-json", wrong_identity])
    service, reference = prepared(tmp_path, engine)
    job = await service.submit(authorized(), reference, "repair", "Show results")
    complete = await service.wait(authorized(), reference, job.job_id)
    assert complete.state == "preview_ready" and complete.repair_attempt == 2
    assert len(engine.calls) == 3
    assert len({call.invocation_context for call in engine.calls}) == 1
    assert all(call.session_id == job.job_id for call in engine.calls)
    corrections = [json.loads(call.message)["correction"] for call in engine.calls]
    assert corrections[0] is None
    assert "json_invalid" in corrections[1][0]["message"]
    assert "assigned identities" in corrections[2][0]["message"]
    assert all(
        call.invocation_context.expected_model_reference == "configured-default"
        for call in engine.calls
    )


@pytest.mark.asyncio
async def test_exhausted_repairs_are_durable_and_not_replayed(tmp_path):
    service, reference = prepared(tmp_path, Engine(["bad"] * 3))
    job = await service.submit(authorized(), reference, "bad-source", "Show results")
    final = await service.wait(authorized(), reference, job.job_id)
    assert final.state == "failed" and final.repair_attempt == 2
    assert len(service.engine.calls) == 3
    assert (
        await service.submit(authorized(), reference, "bad-source", "Show results")
        == final
    )
    assert len(service.engine.calls) == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("options", [{"tool": True}, {"wrong_role": True}])
async def test_tool_or_unattested_model_response_fails_closed(tmp_path, options):
    service, reference = prepared(tmp_path, Engine(**options))
    job = await service.submit(authorized(), reference, "bad-role", "Show results")
    final = await service.wait(authorized(), reference, job.job_id)
    assert final.state == "failed" and final.repair_attempt == 0
    assert len(service.engine.calls) == 1
    with pytest.raises(KeyError):
        service.repository.get_authoring_record("workspace", job.job_id, "built")


@pytest.mark.asyncio
async def test_observer_disconnect_does_not_cancel_owned_generation(tmp_path):
    entered, release = asyncio.Event(), asyncio.Event()
    service, reference = prepared(tmp_path, Engine(entered=entered, release=release))
    job = await service.submit(authorized(), reference, "detach", "Show results")
    await entered.wait()
    observer = asyncio.create_task(service.wait(authorized(), reference, job.job_id))
    await asyncio.sleep(0)
    observer.cancel()
    with pytest.raises(asyncio.CancelledError):
        await observer
    other, _ = prepared(tmp_path)
    assert (
        await other.status(authorized(), reference, job.job_id)
    ).state == "generating"
    assert not other.engine.calls
    release.set()
    assert (
        await service.wait(authorized(), reference, job.job_id)
    ).state == "preview_ready"


@pytest.mark.asyncio
async def test_explicit_cancel_and_shutdown_stop_owned_model_work(tmp_path):
    for shutdown in (False, True):
        path = tmp_path / str(shutdown)
        path.mkdir()
        entered, release = asyncio.Event(), asyncio.Event()
        service, reference = prepared(path, Engine(entered=entered, release=release))
        job = await service.submit(authorized(), reference, "cancel", "Show results")
        await entered.wait()
        if shutdown:
            await service.close()
        else:
            assert (
                await service.cancel(authorized(), reference, job.job_id)
            ).state == "cancelled"
        assert (
            await service.status(authorized(), reference, job.job_id)
        ).state == "cancelled"
        assert not service._tasks
        assert len(service.engine.calls) == 1
        assert not (
            await service.submit(authorized(), reference, "cancel", "Show results")
        ).revision_id


@pytest.mark.asyncio
async def test_permission_source_and_capacity_fail_before_generation(tmp_path):
    entered, release = asyncio.Event(), asyncio.Event()
    service, reference = prepared(tmp_path, Engine(entered=entered, release=release))
    denied = NativeAuthoringScope(scope(), False)
    with pytest.raises(ProcessInterfaceError) as caught:
        await service.submit(denied, reference, "deny", "Show results")
    assert caught.value.reason.code == "SCOPE_DENIED" and service.engine.probes == 0
    stale = reference.model_copy(update={"source_digest": "f" * 64})
    with pytest.raises(ProcessInterfaceError) as caught:
        await service.submit(authorized(), stale, "stale", "Show results")
    assert caught.value.reason.code == "SOURCE_CHANGED" and service.engine.probes == 0
    service.maximum_active = 1
    job = await service.submit(authorized(), reference, "capacity-one", "Show results")
    await entered.wait()
    with pytest.raises(ProcessInterfaceError) as caught:
        await service.submit(authorized(), reference, "capacity-two", "Show results")
    assert caught.value.reason.code == "CAPABILITY_UNAVAILABLE"
    with pytest.raises(ProcessInterfaceError):
        await service.status(authorized(), stale, job.job_id)
    with pytest.raises(ProcessInterfaceError):
        await service.cancel(denied, reference, job.job_id)
    await service.close()


@pytest.mark.asyncio
async def test_missing_model_and_compiler_are_explicit_without_job_allocation(tmp_path):
    service, reference = prepared(tmp_path)
    unavailable = AgentInvocationCapabilities(
        adapter="unqualified", reason="Restricted role unavailable"
    )
    service.engine.get_invocation_capabilities = AsyncMock(return_value=unavailable)
    assert not (await service.capabilities())["available"]
    with pytest.raises(ProcessInterfaceError) as caught:
        await service.submit(authorized(), reference, "missing", "Show results")
    assert caught.value.reason.code == "CAPABILITY_UNAVAILABLE"
    assert (
        service.repository.job_for_request(
            "workspace", reference.source_path, "missing"
        )
        is None
    )
    assert not service.engine.calls


@pytest.mark.asyncio
async def test_dead_owner_job_becomes_interrupted_without_generation_replay(tmp_path):
    service, reference = prepared(tmp_path)
    resources = load_authoring_resources()
    role = RoleResolution(
        profile=CodingRole(
            instructions_version=resources.version,
            instructions_digest=resources.instructions_digest,
        ),
        adapter="controlled",
        model_reference="configured-default",
        configuration_digest="a" * 64,
        effective_instructions_digest=resources.instructions_digest,
    )
    job = AuthoringJob(
        job_id="job-" + "a" * 32,
        request_id="interrupted",
        request_digest="b" * 64,
        process=reference,
        role_resolution=role,
        state="queued",
        created_at="2026-09-30T12:00:00Z",
        updated_at="2026-09-30T12:00:00Z",
    )
    service.repository.create_job(job)
    service.repository.retain_authoring_record(
        "workspace", job.job_id, "request", {"retained": True}
    )
    final = await service.status(authorized(), reference, job.job_id)
    assert (
        final.state == "failed"
        and final.diagnostics[0].code == "UI_AUTHORING_INTERRUPTED"
    )
    assert not service.engine.calls and service.engine.probes == 0


@pytest.mark.asyncio
async def test_changed_bundle_is_not_published(tmp_path, monkeypatch):
    async def changed(**values):
        result = await fake_build(**values)
        (result.dist / "app.js").write_bytes(b"changed")
        return result

    monkeypatch.setattr(module, "build_interface", changed)
    service, reference = prepared(tmp_path)
    job = await service.submit(authorized(), reference, "changed", "Show results")
    assert (await service.wait(authorized(), reference, job.job_id)).state == "failed"
    with pytest.raises(KeyError):
        service.repository.get_authoring_record("workspace", job.job_id, "built")


def test_authoring_records_are_immutable_bounded_and_scoped(tmp_path):
    service, reference = prepared(tmp_path)
    with pytest.raises(Exception):
        service.repository.retain_authoring_record("workspace", "absent", "request", {})
    with pytest.raises(KeyError):
        service.repository.get_authoring_record("other-workspace", "job", "request")
    with pytest.raises(ValueError):
        service.repository.retain_authoring_record("workspace", "job", "shell", {})


def test_immutable_files_survive_reopen_and_reject_corruption_or_overwrite(tmp_path):
    vault = ImmutableFileSet(tmp_path / "files")
    identity = vault.publish({"App.tsx": b"source", "dist/app.js": b"bundle"})
    assert ImmutableFileSet(vault.root).read(identity) == {
        "App.tsx": b"source",
        "dist/app.js": b"bundle",
    }
    with pytest.raises(FileExistsError):
        vault.publish({"App.tsx": b"changed"})
    with pytest.raises(ValueError):
        vault.read("a" * 64)
    inventory = json.loads((vault.root / "inventory.json").read_bytes())
    (vault.root / inventory["dist/app.js"]["storage_key"]).write_bytes(b"change")
    with pytest.raises(ValueError):
        vault.read(identity)


@pytest.mark.parametrize(
    "content", [{"../outside": b"bad"}, {"App.tsx": "not bytes"}, {}]
)
def test_immutable_files_reject_invalid_envelopes(tmp_path, content):
    with pytest.raises(ValueError):
        ImmutableFileSet(tmp_path / "files").publish(content)
    assert not (tmp_path / "files").exists()


def working_scope():
    return authorized(
        "process.read",
        "process.inputs",
        "process.start",
        "process.results",
        "process.navigate",
    )


async def preview_and_save(service, reference, job, *, expected_active=None):
    from workspace_service.process_interfaces.artifacts import (
        ProcessUIPreviewObservation,
    )

    native = working_scope()
    revisions = service.application.ui_revisions
    _, manifest, report, _, _ = revisions.preview_bundle(
        native.process_scope, reference, job.job_id
    )
    # Synthetic presenter observation tests the owner boundary. This is not
    # evidence of a live managed browser preview or human acceptance.
    revisions.observe_preview(
        native.process_scope,
        reference,
        job.job_id,
        ProcessUIPreviewObservation(
            "synthetic-presentation",
            manifest.ui_id,
            manifest.revision_id,
            report.bundle_digest,
        ),
    )
    return await revisions.save(
        native,
        reference,
        job.job_id,
        expected_source_digest=report.source_digest,
        expected_manifest_digest=report.manifest_digest,
        expected_bundle_digest=report.bundle_digest,
        expected_active_revision=expected_active,
    )


@pytest.mark.asyncio
async def test_save_update_rollback_and_saved_source_reuse_without_model_or_compile(
    tmp_path,
):
    def with_controls(output):
        output["manifest"]["capabilities"] += ["process.inputs", "process.start"]
        output["manifest"]["viewers"] = ["text"]
        return output

    service, reference = prepared(tmp_path, Engine(replies=[with_controls]))
    first = await service.submit(working_scope(), reference, "create", "Show outputs")
    await service.wait(working_scope(), reference, first.job_id)
    revision_one = await preview_and_save(service, reference, first)
    assert (
        await service.status(working_scope(), reference, first.job_id)
    ).state == "saved"
    # Lost save acknowledgement is idempotent for identical content.
    assert await preview_and_save(service, reference, first) == revision_one
    second = await service.submit(
        working_scope(),
        reference,
        "update",
        "Add a comparison heading",
        ui_id=revision_one.manifest.ui_id,
        base_revision=revision_one.manifest.revision_id,
    )
    assert (
        await service.wait(working_scope(), reference, second.job_id)
    ).state == "preview_ready"
    update_prompt = json.loads(service.engine.calls[-1].message)
    assert update_prompt["previous_manifest"] == revision_one.manifest.model_dump(
        mode="json"
    )
    assert update_prompt["manifest"]["capabilities"] == list(
        revision_one.manifest.capabilities
    )
    assert update_prompt["manifest"]["viewers"] == list(revision_one.manifest.viewers)
    assert (
        update_prompt["previous_source"]["files"]["App.tsx"]
        == load_authoring_resources().template
    )
    revision_two = await preview_and_save(
        service, reference, second, expected_active=revision_one.manifest.revision_id
    )
    assert revision_two.manifest.parent_revision == revision_one.manifest.revision_id
    assert revision_two.manifest.capabilities == revision_one.manifest.capabilities
    assert revision_two.manifest.viewers == revision_one.manifest.viewers
    original_calls = len(service.engine.calls)
    original_probes = service.engine.probes
    ui = await service.application.ui_revisions.activate(
        working_scope(),
        reference,
        revision_one.manifest.ui_id,
        revision_one.manifest.revision_id,
        expected_active_revision=revision_two.manifest.revision_id,
    )
    assert ui.active_revision == revision_one.manifest.revision_id
    saved = service.application.ui_revisions.saved_source(
        working_scope().process_scope, reference, revision_one
    )
    assert saved["files"]["App.tsx"] == load_authoring_resources().template
    assert (
        len(service.engine.calls) == original_calls == 2
        and service.engine.probes == original_probes
    )
    assert not (tmp_path / "first.txt").exists()


@pytest.mark.asyncio
async def test_save_requires_exact_preview_hashes_permissions_and_current_source(
    tmp_path,
):
    from workspace_service.process_interfaces.artifacts import (
        ProcessUIPreviewObservation,
    )

    service, reference = prepared(tmp_path)
    job = await service.submit(working_scope(), reference, "create", "Show outputs")
    await service.wait(working_scope(), reference, job.job_id)
    revisions = service.application.ui_revisions
    _, manifest, report, _, _ = revisions.preview_bundle(
        working_scope().process_scope, reference, job.job_id
    )
    hashes = {
        "expected_source_digest": report.source_digest,
        "expected_manifest_digest": report.manifest_digest,
        "expected_bundle_digest": report.bundle_digest,
        "expected_active_revision": None,
    }
    with pytest.raises(ProcessInterfaceError) as caught:
        await revisions.save(working_scope(), reference, job.job_id, **hashes)
    assert caught.value.reason.code == "ACTION_NOT_PERMITTED"
    bad = ProcessUIPreviewObservation(
        "preview", "other-ui", manifest.revision_id, report.bundle_digest
    )
    with pytest.raises(ProcessInterfaceError) as caught:
        revisions.observe_preview(
            working_scope().process_scope, reference, job.job_id, bad
        )
    assert caught.value.reason.code == "SCOPE_DENIED"
    revisions.observe_preview(
        working_scope().process_scope,
        reference,
        job.job_id,
        ProcessUIPreviewObservation(
            "preview", manifest.ui_id, manifest.revision_id, report.bundle_digest
        ),
    )
    with pytest.raises(ProcessInterfaceError) as caught:
        await revisions.save(
            working_scope(),
            reference,
            job.job_id,
            **(hashes | {"expected_source_digest": "f" * 64}),
        )
    assert caught.value.reason.code == "SUBJECT_STALE"
    with pytest.raises(ProcessInterfaceError):
        await revisions.save(
            NativeAuthoringScope(scope(), False), reference, job.job_id, **hashes
        )
    with pytest.raises(ProcessInterfaceError) as caught:
        await revisions.save(
            authorized("process.read"), reference, job.job_id, **hashes
        )
    assert caught.value.reason.code == "UI_INCOMPATIBLE"
    revision = await revisions.save(working_scope(), reference, job.job_id, **hashes)
    changed = reference.model_copy(update={"source_digest": "f" * 64})
    with pytest.raises(ProcessInterfaceError):
        await revisions.activate(
            working_scope(),
            changed,
            manifest.ui_id,
            manifest.revision_id,
            expected_active_revision=manifest.revision_id,
        )
    assert revision.previewed_at


@pytest.mark.asyncio
async def test_corrupt_saved_bundle_falls_back_without_regeneration_or_recompilation(
    tmp_path,
):
    service, reference = prepared(tmp_path)
    job = await service.submit(working_scope(), reference, "create", "Show outputs")
    await service.wait(working_scope(), reference, job.job_id)
    revision = await preview_and_save(service, reference, job)
    manifest = revision.manifest
    root = (
        tmp_path
        / f".wright/process-uis/{manifest.ui_id}/revisions/{manifest.revision_id}"
    )
    inventory = json.loads((root / "inventory.json").read_bytes())
    (root / inventory["dist/app.js"]["storage_key"]).write_bytes(b"damaged")
    with pytest.raises(ProcessInterfaceError) as caught:
        service.application.ui_revisions.saved_source(
            working_scope().process_scope, reference, revision
        )
    assert caught.value.reason.code == "UI_INCOMPATIBLE"
    assert len(service.engine.calls) == 1
