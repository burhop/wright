"""Exact process references compose canonical records and bounded file ownership."""

from contextlib import asynccontextmanager
from dataclasses import replace
import hashlib
import json
import threading
from types import SimpleNamespace

import pytest

from core.process_interactions import ArtifactRef, FileBinding
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.executor import BoundedExecutor
from workspace_service.errors import WorkspaceTimeoutError
from workspace_service.use_cases.files import WorkspaceFileUseCases
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from packages.workspace_service.tests.test_process_preparation_service import (
    owner,
    scope,
)
from packages.workspace_service.tests.test_process_input_readiness import (
    source,
    process,
)
from packages.workspace_service.tests.test_process_run_supervisor import start


CAPABILITIES = ("process.read", "process.inputs", "process.results", "process.start")


@asynccontextmanager
async def case(root, *, text=None):
    text = text or source(file="original.txt")
    reference = process(text)
    path = root / reference.source_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    app = owner(root, text)
    executor = BoundedExecutor()
    app.workspace.executor = executor
    app.workspace.files = WorkspaceFileUseCases(
        app.db_path, executor, LocalWorkspaceFiles
    )
    try:
        yield SimpleNamespace(app=app, process=reference, root=root, text=text)
    finally:
        await app.close()
        await executor.close()


@pytest.mark.asyncio
async def test_omitted_canonical_result_is_reported_as_unavailable_not_unrelated(
    tmp_path, monkeypatch
):
    async with case(tmp_path) as c:
        from workspace_service.workflow_run_record import WorkflowRunReadError

        def unavailable_inventory(*args, **kwargs):
            assert kwargs["complete_results"] is True
            raise WorkflowRunReadError(
                "result_inventory_limit",
                "Recorded inventory exceeds its supported bound",
            )

        monkeypatch.setattr(
            "workspace_service.process_interfaces.artifacts.read_workflow_run",
            unavailable_inventory,
        )
        with pytest.raises(ProcessInterfaceError) as failure:
            await c.app.artifacts.read(
                scope(*CAPABILITIES),
                c.process,
                ArtifactRef(
                    artifact_ref="result.txt", sha256="a" * 64, result_id="omitted"
                ),
                run_id="recorded-run",
            )
        assert failure.value.reason.code == "CAPABILITY_UNAVAILABLE"


@pytest.mark.asyncio
@pytest.mark.parametrize("long_path", [False, True])
async def test_prior_attempt_file_requires_exact_history_identity_and_unchanged_bytes(
    tmp_path, monkeypatch, long_path
):
    from .test_workflow_revision_history import revision_events
    from workspace_service.workflow_run_record import _previous_result_rows

    async with case(tmp_path) as c:
        _, events = revision_events()
        history = _previous_result_rows({"run_id": "run-1", "events": events})
        row = history[0]["result"]
        rep = row["representations"][0]
        if long_path:
            rep["location"] = (
                "thermal/" + "/".join(["temperature-comparison" * 3] * 3) + "/field.csv"
            )
        path = tmp_path / rep["location"]
        path.parent.mkdir(parents=True)
        path.write_bytes(b"failed geometry")
        monkeypatch.setattr(
            "workspace_service.process_interfaces.artifacts.read_workflow_run",
            lambda *a, **kw: {
                "source_digest": c.process.source_digest,
                "results": [],
                "previous_results": history,
            },
        )
        reference = ArtifactRef(
            artifact_ref=rep["location"], sha256=rep["sha256"], result_id=row["id"]
        )
        observed = await c.app.artifacts.read(
            scope(*CAPABILITIES), c.process, reference, run_id="run-1"
        )
        assert observed.content == b"failed geometry"
        for foreign_scope, foreign_process, foreign_run in (
            (scope(*CAPABILITIES), c.process, "foreign-run"),
            (
                scope(*CAPABILITIES),
                c.process.model_copy(update={"source_digest": "c" * 64}),
                "run-1",
            ),
            (replace(scope(*CAPABILITIES), workspace_id="foreign"), c.process, "run-1"),
        ):
            with pytest.raises(ProcessInterfaceError) as denied:
                await c.app.artifacts.read(
                    foreign_scope, foreign_process, reference, run_id=foreign_run
                )
            assert denied.value.reason.code == "SCOPE_DENIED"
        for candidate in (
            reference.model_copy(
                update={"result_id": history[0]["original_result_id"]}
            ),
            reference.model_copy(update={"sha256": "b" * 64}),
            reference.model_copy(update={"artifact_ref": "another-attempt.csv"}),
        ):
            with pytest.raises(ProcessInterfaceError) as denied:
                await c.app.artifacts.read(
                    scope(*CAPABILITIES), c.process, candidate, run_id="run-1"
                )
            assert denied.value.reason.code == "SCOPE_DENIED"
        path.write_bytes(b"changed geometry")
        with pytest.raises(ProcessInterfaceError) as stale:
            await c.app.artifacts.read(
                scope(*CAPABILITIES), c.process, reference, run_id="run-1"
            )
        assert stale.value.reason.code == "SUBJECT_STALE"


@pytest.mark.asyncio
async def test_upload_is_scoped_immutable_and_does_not_prepare_or_execute(tmp_path):
    async with case(tmp_path) as c:
        content = b"Exact engineering requirement"
        uploaded = await c.app.artifacts.upload(
            scope(*CAPABILITIES), c.process, "brief", "requirements.txt", content
        )
        assert uploaded.artifact_ref.startswith(
            f".wright/process-inputs/{c.process.source_digest}/"
        )
        assert uploaded.sha256 == hashlib.sha256(content).hexdigest()
        assert (tmp_path / uploaded.artifact_ref).read_bytes() == content
        assert (tmp_path / c.process.source_path).read_text(encoding="utf-8") == c.text
        assert not (tmp_path / "runs").exists()
        assert not (tmp_path / "state.db").exists()
        second = await c.app.artifacts.upload(
            scope(*CAPABILITIES),
            c.process,
            "brief",
            "requirements.txt",
            b"Changed requirements",
        )
        assert second.artifact_ref != uploaded.artifact_ref
        assert (tmp_path / uploaded.artifact_ref).read_bytes() == content


@pytest.mark.asyncio
async def test_more_than_four_mib_can_be_uploaded_prepared_and_read(tmp_path):
    async with case(tmp_path) as c:
        content = b"A" * (5 * 1024 * 1024)
        uploaded = await c.app.artifacts.upload(
            scope(*CAPABILITIES), c.process, "brief", "requirements.txt", content
        )
        prepared = await c.app.set_inputs(
            scope(*CAPABILITIES),
            c.process,
            bindings=(FileBinding(input_id="brief", reference=uploaded),),
        )
        artifact = await c.app.artifacts.read(
            scope(*CAPABILITIES),
            c.process,
            uploaded,
            input_snapshot_id=prepared.snapshot.snapshot_id,
        )
        assert artifact.content == content
        assert artifact.media_type == "text/plain"
        assert len(prepared.values["brief"].text) == len(content)
        assert not (tmp_path / "runs").exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "name,content",
    [
        ("../outside.txt", b"data"),
        ("one.txt", b""),
        (".hidden", b"data"),
        ("bad\nname.txt", b"data"),
        ("one.abcdefghijklmnop", b"data"),
        ("binary.txt", b"\x00\xff"),
    ],
)
async def test_invalid_uploads_never_publish(tmp_path, name, content):
    async with case(tmp_path) as c:
        with pytest.raises(ProcessInterfaceError):
            await c.app.artifacts.upload(
                scope(*CAPABILITIES), c.process, "brief", name, content
            )
        assert not (tmp_path / ".wright/process-inputs").exists()


@pytest.mark.asyncio
async def test_configured_upload_bound_is_enforced_before_write(tmp_path):
    async with case(tmp_path) as c:
        c.app.limits = replace(c.app.limits, maximum_upload_bytes=4)
        with pytest.raises(ProcessInterfaceError) as error:
            await c.app.artifacts.upload(
                scope(*CAPABILITIES), c.process, "brief", "one.txt", b"12345"
            )
        assert error.value.reason.code == "RESPONSE_INVALID"
        assert not (tmp_path / ".wright/process-inputs").exists()


@pytest.mark.asyncio
async def test_upload_capability_and_declared_file_input_are_required(tmp_path):
    async with case(tmp_path, text=source(default="A text input")) as c:
        with pytest.raises(ProcessInterfaceError) as denied:
            await c.app.artifacts.upload(
                scope("process.read"), c.process, "brief", "one.txt", b"data"
            )
        assert denied.value.reason.code == "SCOPE_DENIED"
        for input_id in ("brief", "undeclared"):
            with pytest.raises(ProcessInterfaceError) as error:
                await c.app.artifacts.upload(
                    scope(*CAPABILITIES), c.process, input_id, "one.txt", b"data"
                )
            assert error.value.reason.code == "SCOPE_DENIED"
        assert not (tmp_path / ".wright/process-inputs").exists()


@pytest.mark.asyncio
async def test_changed_source_rejects_upload_before_file_publication(tmp_path):
    async with case(tmp_path) as c:
        changed = c.process.model_copy(update={"source_digest": "b" * 64})
        with pytest.raises(ProcessInterfaceError) as error:
            await c.app.artifacts.upload(
                scope(*CAPABILITIES), changed, "brief", "one.txt", b"data"
            )
        assert error.value.reason.code == "SOURCE_CHANGED"
        assert not (tmp_path / ".wright/process-inputs").exists()


@pytest.mark.asyncio
async def test_unprepared_or_unrelated_files_do_not_gain_read_authority(tmp_path):
    async with case(tmp_path) as c:
        uploaded = await c.app.artifacts.upload(
            scope(*CAPABILITIES), c.process, "brief", "one.txt", b"owned data"
        )
        prepared = await c.app.set_inputs(
            scope(*CAPABILITIES),
            c.process,
            bindings=(FileBinding(input_id="brief", reference=uploaded),),
        )
        (tmp_path / "private.txt").write_bytes(b"not an input")
        forged = ArtifactRef(
            artifact_ref="private.txt",
            sha256=hashlib.sha256(b"not an input").hexdigest(),
        )
        for candidate in (
            forged,
            uploaded.model_copy(update={"sha256": "0" * 64}),
            uploaded.model_copy(update={"result_id": "pretend-result"}),
        ):
            with pytest.raises(ProcessInterfaceError) as error:
                await c.app.artifacts.read(
                    scope(*CAPABILITIES),
                    c.process,
                    candidate,
                    input_snapshot_id=prepared.snapshot.snapshot_id,
                )
            assert error.value.reason.code == "SCOPE_DENIED"
        with pytest.raises(ProcessInterfaceError) as missing:
            await c.app.artifacts.read(scope(*CAPABILITIES), c.process, uploaded)
        assert missing.value.reason.code == "RESPONSE_INVALID"


@pytest.mark.asyncio
async def test_changed_input_bytes_are_reported_as_stale(tmp_path):
    async with case(tmp_path) as c:
        uploaded = await c.app.artifacts.upload(
            scope(*CAPABILITIES), c.process, "brief", "one.txt", b"old data"
        )
        prepared = await c.app.set_inputs(
            scope(*CAPABILITIES),
            c.process,
            bindings=(FileBinding(input_id="brief", reference=uploaded),),
        )
        (tmp_path / uploaded.artifact_ref).write_bytes(b"changed data")
        with pytest.raises(ProcessInterfaceError) as error:
            await c.app.artifacts.read(
                scope(*CAPABILITIES),
                c.process,
                uploaded,
                input_snapshot_id=prepared.snapshot.snapshot_id,
            )
        assert error.value.reason.code == "SUBJECT_STALE"


@pytest.mark.asyncio
async def test_read_requires_results_capability_and_host_workspace_scope(tmp_path):
    async with case(tmp_path) as c:
        reference = ArtifactRef(artifact_ref="private.txt", sha256="a" * 64)
        for candidate_scope, candidate_process in (
            (scope("process.read"), c.process),
            (
                scope(*CAPABILITIES),
                c.process.model_copy(update={"workspace_id": "other"}),
            ),
        ):
            with pytest.raises(ProcessInterfaceError) as error:
                await c.app.artifacts.read(
                    candidate_scope,
                    candidate_process,
                    reference,
                    input_snapshot_id="input-one",
                )
            assert error.value.reason.code == "SCOPE_DENIED"


@pytest.mark.asyncio
async def test_actual_recorded_result_read_does_not_execute_again(tmp_path):
    async with case(tmp_path, text=source(default="Exact requirements")) as c:
        prepared = await c.app.set_inputs(scope(*CAPABILITIES), c.process)
        calls = []

        async def generate(prompt, fmt):
            calls.append(prompt)
            return "Actual controlled output"

        receipt = await start(c.app, c.process, prepared.snapshot, generate)
        await c.app.runs.wait(scope(*CAPABILITIES), c.process, receipt.run_id)
        snapshot = await c.app.get_snapshot(
            scope(*CAPABILITIES), c.process, run_id=receipt.run_id
        )
        reference = snapshot.outputs[0].representations[0]
        artifact = await c.app.artifacts.read(
            scope(*CAPABILITIES), c.process, reference, run_id=receipt.run_id
        )
        assert artifact.content == b"Actual controlled output"
        assert len(calls) == 1
        assert artifact.reference.result_id == snapshot.outputs[0].result_id
        for changed in (
            reference.model_copy(update={"result_id": "another-result"}),
            reference.model_copy(update={"sha256": "0" * 64}),
            reference.model_copy(update={"representation_id": "made-up"}),
        ):
            with pytest.raises(ProcessInterfaceError) as denied:
                await c.app.artifacts.read(
                    scope(*CAPABILITIES), c.process, changed, run_id=receipt.run_id
                )
            assert denied.value.reason.code == "SCOPE_DENIED"
        (tmp_path / reference.artifact_ref).write_bytes(b"Changed output")
        with pytest.raises(ProcessInterfaceError) as stale:
            await c.app.artifacts.read(
                scope(*CAPABILITIES), c.process, reference, run_id=receipt.run_id
            )
        assert stale.value.reason.code == "SUBJECT_STALE"


@pytest.mark.asyncio
async def test_file_read_bound_and_traversal_are_enforced_by_the_file_owner(tmp_path):
    async with case(tmp_path) as c:
        (tmp_path / "one.txt").write_bytes(b"12345")
        for path, maximum in (
            ("one.txt", 4),
            ("../outside.txt", 32),
            ("one.txt", 0),
            ("one.txt", 101 * 1024 * 1024),
        ):
            with pytest.raises(ValueError):
                await c.app.workspace.files.read_bytes(
                    str(tmp_path), path, maximum_bytes=maximum
                )
        assert (
            await c.app.workspace.files.read_bytes(
                str(tmp_path), "one.txt", maximum_bytes=5
            )
            == b"12345"
        )


@pytest.mark.asyncio
async def test_passive_preview_uses_exact_recorded_result_and_never_replays_work(
    tmp_path,
):
    text = source(default="Prepared view fixture")
    async with case(tmp_path, text=text) as c:
        prepared = await c.app.set_inputs(scope(*CAPABILITIES), c.process)
        calls = []
        content = "G90\nM83\nG1 X0 Y0 Z0.2\n;CHANGE_LAYER\n;Z_HEIGHT:0.2\n;FEATURE:Support\nG1 X10 E1"

        async def generate(prompt, fmt):
            calls.append(prompt)
            return content

        receipt = await start(c.app, c.process, prepared.snapshot, generate)
        await c.app.runs.wait(scope(*CAPABILITIES), c.process, receipt.run_id)
        snapshot = await c.app.get_snapshot(
            scope(*CAPABILITIES), c.process, run_id=receipt.run_id
        )
        reference = snapshot.outputs[0].representations[0]
        derived = await c.app.artifacts.preview(
            scope(*CAPABILITIES), c.process, reference, run_id=receipt.run_id
        )
        assert derived.media_type == "application/vnd.wright.toolpaths+json"
        data = json.loads(derived.content)
        assert data["package_sha256"] == reference.sha256
        assert data["layers"][0]["support"] == [[0, 0, 10, 0]]
        assert (tmp_path / reference.artifact_ref).read_text() == content
        raw = await c.app.artifacts.read(
            scope(*CAPABILITIES), c.process, reference, run_id=receipt.run_id
        )
        assert raw.content == content.encode()
        assert len(calls) == 1
        for changed in (
            reference.model_copy(update={"sha256": "0" * 64}),
            reference.model_copy(update={"result_id": "foreign"}),
        ):
            with pytest.raises(ProcessInterfaceError) as denied:
                await c.app.artifacts.preview(
                    scope(*CAPABILITIES), c.process, changed, run_id=receipt.run_id
                )
            assert denied.value.reason.code == "SCOPE_DENIED"
        (tmp_path / reference.artifact_ref).write_bytes(b"changed")
        with pytest.raises(ProcessInterfaceError) as stale:
            await c.app.artifacts.preview(
                scope(*CAPABILITIES), c.process, reference, run_id=receipt.run_id
            )
        assert stale.value.reason.code == "SUBJECT_STALE"


@pytest.mark.asyncio
async def test_passive_parse_and_serialization_use_the_owned_bounded_worker(
    tmp_path, monkeypatch
):
    from workspace_service.process_interfaces import representations

    async with case(tmp_path) as c:
        content = b"G90\nM83\nG1 X0 Y0 Z0.2\n;CHANGE_LAYER\nG1 X10 E1"
        reference = await c.app.artifacts.upload(
            scope(*CAPABILITIES), c.process, "brief", "paths.txt", content
        )
        prepared = await c.app.set_inputs(
            scope(*CAPABILITIES),
            c.process,
            bindings=(FileBinding(input_id="brief", reference=reference),),
        )
        main_thread = threading.get_ident()
        threads = []
        read = representations.read_gcode_toolpaths

        def observed(*args, **kwargs):
            threads.append(threading.get_ident())
            return read(*args, **kwargs)

        monkeypatch.setattr(representations, "read_gcode_toolpaths", observed)
        derived = await c.app.artifacts.preview(
            scope(*CAPABILITIES),
            c.process,
            reference,
            input_snapshot_id=prepared.snapshot.snapshot_id,
        )
        assert threads and threads[0] != main_thread
        assert (
            json.loads(derived.content)["provenance"]["engineering_acceptance"] is False
        )
        assert (tmp_path / reference.artifact_ref).read_bytes() == content


@pytest.mark.asyncio
async def test_passive_deadline_failure_preserves_exact_download(tmp_path, monkeypatch):
    async with case(tmp_path) as c:
        content = b"Recorded engineering file"
        reference = await c.app.artifacts.upload(
            scope(*CAPABILITIES), c.process, "brief", "paths.txt", content
        )
        prepared = await c.app.set_inputs(
            scope(*CAPABILITIES),
            c.process,
            bindings=(FileBinding(input_id="brief", reference=reference),),
        )
        bounded = c.app.workspace.executor.run

        async def timed_out(operation, work, *, timeout_seconds):
            if operation == "process.representation.preview":
                assert timeout_seconds == c.app.limits.representation_timeout_seconds
                raise WorkspaceTimeoutError(
                    "Controlled passive deadline", operation=operation
                )
            return await bounded(operation, work, timeout_seconds=timeout_seconds)

        monkeypatch.setattr(c.app.workspace.executor, "run", timed_out)
        with pytest.raises(ProcessInterfaceError) as failure:
            await c.app.artifacts.preview(
                scope(*CAPABILITIES),
                c.process,
                reference,
                input_snapshot_id=prepared.snapshot.snapshot_id,
            )
        assert failure.value.reason.code == "CAPABILITY_UNAVAILABLE"
        raw = await c.app.artifacts.read(
            scope(*CAPABILITIES),
            c.process,
            reference,
            input_snapshot_id=prepared.snapshot.snapshot_id,
        )
        assert raw.content == content
