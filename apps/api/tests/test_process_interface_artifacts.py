"""Authenticated transport composes real bounded file and preparation owners."""

import asyncio
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from api.main import app
from api.routers.workspace import get_workspace_service
from api.security import SecuritySettings
from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.executor import BoundedExecutor
from workspace_service.use_cases.files import WorkspaceFileUseCases
from packages.workspace_service.tests.test_process_preparation_service import owner
from packages.workspace_service.tests.test_process_input_readiness import (
    source,
    process,
)


PREFIX = "/api/workspace/process-interfaces"
REPOSITORY = Path(__file__).resolve().parents[3]
THERMAL_SOURCE = (
    REPOSITORY
    / "tests/datasets/process-validation/processes/heat-validation.workflow.wflow"
).read_text(encoding="utf-8")


def test_pdf_preview_uses_exact_recorded_result_without_execution(
    sync_client, artifact_case
):
    from packages.workspace_service.tests.test_process_pdf_preview import pdf_bytes
    from workspace_service.workflow_results import Provenance, file_result
    from pathlib import PurePosixPath

    c = artifact_case
    data = pdf_bytes()
    (c.root / "drawing.pdf").write_bytes(data)
    result = file_result(
        {
            "output_path": "drawing.pdf",
            "output_format": "pdf",
            "output_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        },
        Provenance("pdf-run", "drawing", "pdf"),
    ).to_dict()
    result["representations"][0]["sha256"] = hashlib.sha256(data).hexdigest()
    source_path = c.query["path"]
    slug = PurePosixPath(source_path).name.removesuffix(".workflow.wflow")
    record = {
        "workflow_path": source_path,
        "source_digest": c.query["expected_storage_digest"],
        "run_id": "pdf-run",
        "status": "completed",
        "events": [],
        "result": {"run_id": "pdf-run", "results": [result]},
    }
    path = c.root / "runs" / slug / "pdf-run.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record))
    before = path.read_bytes()
    reference = {
        "artifact_ref": "drawing.pdf",
        "sha256": hashlib.sha256(data).hexdigest(),
        "result_id": result["id"],
    }
    response = read(
        sync_client, c, reference, None, run_id="pdf-run", preview="pdf-page", page=2
    )
    assert response.status_code == 200, response.text
    assert response.headers["x-wright-view-format"] == "wright.pdf.page.v1"
    assert response.headers["x-wright-artifact-sha256"] == reference["sha256"]
    assert response.json()["page"] == 2 and response.json()["page_count"] == 2
    raw = read(sync_client, c, reference, None, run_id="pdf-run")
    assert raw.headers["content-type"] == "application/pdf" and raw.content == data
    for extra in [
        {"run_id": "foreign-run"},
        {"run_id": "pdf-run", "reference": {**reference, "sha256": "0" * 64}},
    ]:
        selected = extra.pop("reference", reference)
        assert (
            read(
                sync_client, c, selected, None, preview="pdf-page", **extra
            ).status_code
            != 200
        )
    assert (
        read(sync_client, c, reference, None, run_id="pdf-run", page=1).status_code
        == 422
    )
    assert (
        read(
            sync_client,
            c,
            reference,
            None,
            run_id="pdf-run",
            preview="pdf-page",
            page=201,
        ).status_code
        == 422
    )
    (c.root / "drawing.pdf").write_bytes(b"%PDF-changed")
    assert (
        read(
            sync_client, c, reference, None, run_id="pdf-run", preview="pdf-page"
        ).status_code
        == 409
    )
    assert path.read_bytes() == before


@pytest.fixture
def artifact_case(tmp_path, request):
    text = getattr(request, "param", source(file="original.txt"))
    source_path = tmp_path / process(text).source_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(text, encoding="utf-8")
    application = owner(tmp_path, text)
    workspace = application.workspace
    executor = BoundedExecutor()
    workspace.executor = executor
    workspace.files = WorkspaceFileUseCases(
        application.db_path, executor, LocalWorkspaceFiles
    )
    workspace.ensure_workspace_path_safe = lambda path: path
    workspace.lifecycle = SimpleNamespace(
        get_by_session=lambda key: (
            {"workspace_id": "workspace", "local_path": str(tmp_path)}
            if key == "owned-session"
            else None
        )
    )
    workspace.process_interfaces = application
    app.dependency_overrides[get_workspace_service] = lambda: workspace
    try:
        yield SimpleNamespace(
            owner=application,
            root=tmp_path,
            query={
                "session_id": "owned-session",
                "path": process(text).source_path,
                "expected_storage_digest": process(text).source_digest,
            },
        )
    finally:
        app.dependency_overrides.pop(get_workspace_service, None)
        asyncio.run(application.close())
        asyncio.run(executor.close())


def upload(
    client, case, *, content=b"Engineering requirement", name="brief.txt", **extra
):
    return client.post(
        f"{PREFIX}/inputs/upload",
        data={**case.query, "input_id": "brief", **extra},
        files={"file": (name, content, "text/html")},
    )


def prepare(client, case, reference):
    response = client.post(
        f"{PREFIX}/inputs",
        json={
            **case.query,
            "bindings": [{"kind": "file", "input_id": "brief", "reference": reference}],
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["snapshot_id"]


def read(client, case, reference, snapshot_id, **extra):
    return client.post(
        f"{PREFIX}/representations/read",
        json={
            **case.query,
            "reference": reference,
            "input_snapshot_id": snapshot_id,
            **extra,
        },
    )


def record_thermal_assessment(
    case, *, duplicate=False, encoding="original", changed_field=None
):
    """Controlled recorder proof, with real thermal validation and no tool/model run."""
    from core.process_validation import (
        ProducerIdentity,
        SubjectBinding,
        ValidationRequest,
        canonical_digest,
    )
    from workspace_service.process_validation.application import ValidationApplication
    from workspace_service.process_validation.profiles import load_profile
    from workspace_service.workflow_results import (
        EngineeringResult,
        Provenance,
        Representation,
        file_result,
    )
    from workspace_service.workflow_run_record import record_workflow_run

    run_id = "thermal-assessment-run"
    profile = load_profile("heat-spreader-sizing-01")
    validation = ValidationApplication(case.owner.db_path, "workspace", str(case.root))
    files = {
        "baseline_coarse": "baseline-coarse.csv",
        "baseline_fine": "baseline-fine.csv",
        "revision_coarse": "revision-coarse.csv",
        "revision_fine": "revision-fine.csv",
        "decision": "decision.json",
    }
    subjects, declared = [], []
    for role, name in files.items():
        content = (
            REPOSITORY / "tests/datasets/process-validation/thermal" / name
        ).read_bytes()
        relative = f"thermal/fields/{name}"
        target = case.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        digest = hashlib.sha256(content).hexdigest()
        result = file_result(
            {
                "output_path": relative,
                "output_format": target.suffix[1:],
                "output_bytes": len(content),
                "sha256": digest,
            },
            Provenance(run_id, "produce", role),
        )
        subject = SubjectBinding(
            id=role.replace("_", "-"),
            role=role,
            result_id=result.id,
            producer=ProducerIdentity(
                run_id=run_id, step_id="produce", attempt=1, output_port=role
            ),
            kind="file",
            locator=relative,
            format=target.suffix[1:],
            encoding="raw-bytes",
            sha256=digest,
        )
        validation.repository.register_output("workspace", subject)
        subjects.append(subject)
        declared.append(result.to_dict())
    outcome = validation.service.evaluate(
        ValidationRequest(
            trace_id="thermal-artifact-transport",
            workspace_id="workspace",
            invocation_id="thermal-validation",
            run_id=run_id,
            check_step_id="inspect",
            subjects=tuple(subjects),
            profile_ref=profile.reference(),
            baseline_ref=profile.baseline.reference(),
            idempotency_key="thermal-validation",
        ),
        profile,
    )
    assert outcome.release_eligible
    assert len(outcome.assessment.measurements) == 15
    assert outcome.assessment.summary.counts["pass"] == 15
    ledger_content = outcome.assessment.model_dump_json(indent=2).encode("utf-8")
    payload = json.loads(ledger_content)
    if changed_field == "summary":
        payload["summary"]["requirements_compliant"] = False
    elif changed_field == "count":
        payload["summary"]["counts"]["pass"] += 1
    elif changed_field == "id":
        payload["id"] = "assessment-unowned-thermal"
    content = (
        ledger_content
        if changed_field is None
        else json.dumps(payload, indent=2).encode("utf-8")
    )
    if encoding == "compact":
        content = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    elif encoding == "reordered":
        content = reordered_assessment_json(content)
    assert (json.loads(content) == json.loads(ledger_content)) == (
        changed_field is None
    )
    if encoding != "original":
        assert content != ledger_content
    digest = hashlib.sha256(content).hexdigest()
    # The declared value card is intentionally distinct from its saved report.
    card = EngineeringResult(
        f"{run_id}:inspect:assessment",
        "structured",
        "Thermal validation disposition",
        (
            Representation(
                "value",
                "steps/inspect/assessment",
                "json",
                sha256=canonical_digest({"assessment_id": outcome.assessment.id}),
            ),
        ),
        Provenance(run_id, "inspect", "assessment"),
    ).to_dict()
    declared.append(card)
    diagnostics = []
    for index in range(2 if duplicate else 1):
        # No guessed assessment filename or directory is part of the read contract.
        relative = (
            f"unrelated/retained-evidence/check-{index}/numerical-observations.json"
        )
        target = case.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        recorded_content = (
            reordered_assessment_json(content)
            if index == 1 and duplicate == "reordered"
            else content
        )
        target.write_bytes(recorded_content)
        diagnostics.append(
            file_result(
                {
                    "output_path": relative,
                    "output_format": "json",
                    "output_bytes": len(recorded_content),
                    "sha256": hashlib.sha256(recorded_content).hexdigest(),
                    "artifact_role": "verification",
                },
                Provenance(run_id, "inspect", f"diagnostic:{relative}"),
            ).to_dict()
        )

    declared = json.loads(json.dumps(declared))
    diagnostics = json.loads(json.dumps(diagnostics))

    async def execute(emit):
        for row in declared + diagnostics:
            await emit(
                {
                    "kind": "result_ready",
                    "task_id": row["provenance"]["task_id"],
                    "task_title": "Thermal evidence",
                    "engineering_result": row,
                }
            )
        return {"run_id": run_id, "results": declared, "outputs": [], "steps": []}

    recorded = asyncio.run(
        record_workflow_run(
            service=case.owner.workspace,
            workspace_dir=str(case.root),
            workspace_id="workspace",
            source_path=case.query["path"],
            source_digest=case.query["expected_storage_digest"],
            run_id=run_id,
            execute=execute,
        )
    )
    record_path = case.root / recorded["run_log_path"]
    record = json.loads(record_path.read_bytes())
    assert record["status"] == "completed"
    assert record["result"]["results"] == declared
    assert all(row["id"] in record["partial_results"] for row in diagnostics)
    return SimpleNamespace(
        run_id=run_id,
        assessment=outcome.assessment,
        content=content,
        digest=digest,
        record_path=record_path,
        declared=declared,
        diagnostics=diagnostics,
        card=card,
    )


def reordered_assessment_json(content):
    # Change every object key order and whitespace, preserving all JSON values.
    value = json.loads(content, object_pairs_hook=lambda pairs: dict(reversed(pairs)))
    return json.dumps(value, indent=1).encode("utf-8")


def thermal_snapshot(client, case, run):
    response = client.get(
        f"{PREFIX}/interaction", params={**case.query, "run_id": run.run_id}
    )
    assert response.status_code == 200, response.text
    snapshot = response.json()
    assert snapshot["state"] == "completed"
    assert not snapshot["interactions"]
    assert not any(action["enabled"] for action in snapshot["actions"])
    targets = [
        target for target in snapshot["navigation"] if target["kind"] == "assessment"
    ]
    assert len(targets) == 5
    assert {target["assessment_id"] for target in targets} == {run.assessment.id}
    assert {
        (item["assessment_id"], item["outcome"], item["currentness"])
        for output in snapshot["outputs"]
        for item in output["assessments"]
    } == {(run.assessment.id, "pass", "current")}
    return snapshot, targets


@pytest.mark.parametrize("artifact_case", [THERMAL_SOURCE], indirect=True)
@pytest.mark.parametrize("encoding", ["original", "compact", "reordered"])
def test_completed_thermal_subject_links_read_actual_partial_only_assessment(
    sync_client,
    artifact_case,
    encoding,
):
    c = artifact_case
    run = record_thermal_assessment(c, encoding=encoding)
    before = run.record_path.read_bytes()
    snapshot, targets = thermal_snapshot(sync_client, c, run)
    assert {row["result_id"] for row in snapshot["outputs"]} == {
        row["id"] for row in run.declared + run.diagnostics
    }
    card = next(
        row for row in snapshot["outputs"] if row["result_id"] == run.card["id"]
    )
    assert card["port_id"] == "assessment" and not card["representations"]
    for target in targets:
        response = sync_client.post(
            f"{PREFIX}/navigation", json={**c.query, "target": target}
        )
        assert response.status_code == 200, response.text
        reference = response.json()["representation"]
        assert reference["result_id"] == run.diagnostics[0]["id"]
        assert (
            reference["artifact_ref"]
            == run.diagnostics[0]["representations"][0]["location"]
        )
        assert reference["sha256"] == run.digest
        raw = read(sync_client, c, reference, None, run_id=run.run_id)
        assert raw.status_code == 200, raw.text
        assert (
            raw.content == run.content
            and raw.headers["content-type"] == "application/json"
        )
        assert raw.headers["x-wright-artifact-sha256"] == run.digest
    preview = read(
        sync_client, c, reference, None, run_id=run.run_id, preview="validation-report"
    )
    assert preview.status_code == 200, preview.text
    assert run.assessment.id in preview.text and "HEAT-SELECTION" in preview.text
    assert run.record_path.read_bytes() == before
    assert (c.root / reference["artifact_ref"]).read_bytes() == run.content


@pytest.mark.parametrize("artifact_case", [THERMAL_SOURCE], indirect=True)
@pytest.mark.parametrize("changed_field", ["summary", "count", "id"])
def test_recorded_thermal_json_cannot_replace_authoritative_assessment(
    sync_client, artifact_case, changed_field
):
    c = artifact_case
    run = record_thermal_assessment(c, changed_field=changed_field)
    before = run.record_path.read_bytes()
    _, targets = thermal_snapshot(sync_client, c, run)
    row = run.diagnostics[0]
    reference = {
        "artifact_ref": row["representations"][0]["location"],
        "sha256": run.digest,
        "result_id": row["id"],
    }
    # Exact file membership permits a raw download, not a different assessment.
    raw = read(sync_client, c, reference, None, run_id=run.run_id)
    assert raw.status_code == 200 and raw.content == run.content
    assert hashlib.sha256(raw.content).hexdigest() == reference["sha256"]
    navigation = sync_client.post(
        f"{PREFIX}/navigation", json={**c.query, "target": targets[0]}
    )
    preview = read(
        sync_client, c, reference, None, run_id=run.run_id, preview="validation-report"
    )
    for response in (navigation, preview):
        assert response.status_code == 503, response.text
        assert response.json()["error_code"] == "CAPABILITY_UNAVAILABLE"
    assert run.record_path.read_bytes() == before
    assert (c.root / reference["artifact_ref"]).read_bytes() == run.content


@pytest.mark.parametrize("artifact_case", [THERMAL_SOURCE], indirect=True)
def test_semantically_equal_thermal_assessment_files_are_still_ambiguous(
    sync_client, artifact_case
):
    c = artifact_case
    run = record_thermal_assessment(c, duplicate="reordered")
    before = run.record_path.read_bytes()
    _, targets = thermal_snapshot(sync_client, c, run)
    refs = [row["representations"][0] for row in run.diagnostics]
    assert refs[0]["sha256"] != refs[1]["sha256"]
    contents = [(c.root / ref["location"]).read_bytes() for ref in refs]
    assert json.loads(contents[0]) == json.loads(contents[1])
    response = sync_client.post(
        f"{PREFIX}/navigation", json={**c.query, "target": targets[0]}
    )
    assert response.status_code == 503, response.text
    assert response.json()["error_code"] == "CAPABILITY_UNAVAILABLE"
    assert run.record_path.read_bytes() == before
    assert [(c.root / ref["location"]).read_bytes() for ref in refs] == contents


@pytest.mark.parametrize("artifact_case", [THERMAL_SOURCE], indirect=True)
@pytest.mark.parametrize(
    "change", ["ambiguous", "missing", "tampered", "removed", "foreign"]
)
def test_completed_thermal_assessment_links_fail_closed(
    sync_client,
    artifact_case,
    change,
):
    c = artifact_case
    run = record_thermal_assessment(c, duplicate=change == "ambiguous")
    _, targets = thermal_snapshot(sync_client, c, run)
    row = run.diagnostics[0]
    reference = {
        "artifact_ref": row["representations"][0]["location"],
        "sha256": run.digest,
        "result_id": row["id"],
    }
    path = c.root / reference["artifact_ref"]
    if change == "missing":
        path.unlink()
    elif change == "tampered":
        path.write_bytes(run.content + b"\n")
    elif change == "removed":
        record = json.loads(run.record_path.read_bytes())
        del record["partial_results"][row["id"]]
        run.record_path.write_text(json.dumps(record), encoding="utf-8")
    before = run.record_path.read_bytes()
    if change in {"ambiguous", "removed"}:
        response = sync_client.post(
            f"{PREFIX}/navigation", json={**c.query, "target": targets[0]}
        )
        assert response.status_code == 503, response.text
        assert response.json()["error_code"] == "CAPABILITY_UNAVAILABLE"
        if change == "removed":
            assert (
                read(sync_client, c, reference, None, run_id=run.run_id).status_code
                == 403
            )
            assert (
                path.read_bytes() == run.content
            )  # Disk existence grants no membership.
    elif change == "foreign":
        for extra, status in (
            ({"session_id": "foreign"}, 404),
            ({"run_id": "foreign-run"}, 503),
            ({"expected_storage_digest": "0" * 64}, 403),
        ):
            response = read(
                sync_client, c, reference, None, **{"run_id": run.run_id, **extra}
            )
            assert response.status_code == status, response.text
    else:
        response = read(sync_client, c, reference, None, run_id=run.run_id)
        assert response.status_code == (503 if change == "missing" else 409), (
            response.text
        )
        assert response.json()["error_code"] == (
            "CAPABILITY_UNAVAILABLE" if change == "missing" else "SUBJECT_STALE"
        )
    assert run.record_path.read_bytes() == before


def test_upload_prepare_and_read_exact_bytes_without_execution(
    sync_client, artifact_case
):
    c = artifact_case
    content = b"Exact input" * 10_000
    response = upload(sync_client, c, content=content)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    reference = response.json()
    assert reference["media_type"] == "text/plain"
    assert reference["sha256"] == hashlib.sha256(content).hexdigest()
    assert not (c.root / "state.db").exists()
    snapshot_id = prepare(sync_client, c, reference)
    downloaded = read(sync_client, c, reference, snapshot_id)
    assert downloaded.status_code == 200, downloaded.text
    assert downloaded.content == content
    assert downloaded.headers["content-type"].startswith("text/plain")
    assert downloaded.headers["content-disposition"].startswith("attachment;")
    assert downloaded.headers["content-length"] == str(len(content))
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert downloaded.headers["cache-control"] == "no-store"
    assert downloaded.headers["x-wright-artifact-sha256"] == reference["sha256"]
    assert not (c.root / "first.txt").exists()
    assert not (c.root / "runs").exists()


@pytest.mark.parametrize(
    "artifact_case", [source(default="Prepared passive view")], indirect=True
)
def test_passive_preview_keeps_original_download_and_exact_run_authority(
    sync_client, artifact_case
):
    from packages.workspace_service.tests.test_process_preparation_service import scope
    from packages.workspace_service.tests.test_process_run_supervisor import start

    c = artifact_case
    capabilities = (
        "process.read",
        "process.inputs",
        "process.results",
        "process.start",
    )
    content = "G90\nM83\nG1 X0 Y0 Z0.2\n;CHANGE_LAYER\n;Z_HEIGHT:0.2\n;FEATURE:Support\nG1 X10 E1"

    async def record():
        # Fixture source and stored digest are the same accepted process reference.
        text = source(default="Prepared passive view")
        selected = process(text)
        prepared = await c.owner.set_inputs(scope(*capabilities), selected)

        async def generate(prompt, fmt):
            return content

        receipt = await start(c.owner, selected, prepared.snapshot, generate)
        await c.owner.runs.wait(scope(*capabilities), selected, receipt.run_id)
        snapshot = await c.owner.get_snapshot(
            scope(*capabilities), selected, run_id=receipt.run_id
        )
        return receipt.run_id, snapshot.outputs[0].representations[0].model_dump(
            mode="json"
        )

    run_id, reference = asyncio.run(record())
    response = read(sync_client, c, reference, None, run_id=run_id, preview="toolpaths")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/vnd.wright.toolpaths+json"
    assert response.headers["x-wright-view-format"] == "wright.gcode.toolpaths.v1"
    assert response.headers["x-wright-artifact-sha256"] == reference["sha256"]
    assert response.json()["layers"][0]["support"] == [[0, 0, 10, 0]]
    raw = read(sync_client, c, reference, None, run_id=run_id)
    assert raw.content == content.encode()
    assert "x-wright-view-format" not in raw.headers
    assert (
        read(
            sync_client,
            c,
            {**reference, "sha256": "0" * 64},
            None,
            run_id=run_id,
            preview="toolpaths",
        ).status_code
        == 403
    )
    assert (
        read(
            sync_client, c, reference, None, run_id=run_id, preview="shell"
        ).status_code
        == 422
    )
    assert (
        read(
            sync_client, c, reference, None, run_id=run_id, archive_entry="plate.gcode"
        ).status_code
        == 422
    )


def test_uploaded_html_is_inert_download_even_with_caller_mime(
    sync_client, artifact_case
):
    response = upload(
        sync_client, artifact_case, name="brief.html", content=b"<script>1</script>"
    )
    assert response.status_code == 200
    reference = response.json()
    assert reference["media_type"] == "application/octet-stream"
    snapshot_id = prepare(sync_client, artifact_case, reference)
    downloaded = read(sync_client, artifact_case, reference, snapshot_id)
    assert downloaded.headers["content-type"] == "application/octet-stream"
    assert downloaded.headers["content-disposition"].startswith("attachment;")


@pytest.mark.parametrize("field", ["workspace_id", "principal_id", "capabilities"])
def test_upload_rejects_caller_authority_without_echo_or_publication(
    sync_client, artifact_case, field
):
    response = upload(sync_client, artifact_case, **{field: "private-must-not-echo"})
    assert response.status_code == 422
    assert "private-must-not-echo" not in response.text
    assert not (artifact_case.root / ".wright" / "process-inputs").exists()


def test_duplicate_input_field_rejects_before_publication(sync_client, artifact_case):
    body = [(key, (None, value)) for key, value in artifact_case.query.items()]
    body += [("input_id", (None, "brief")), ("input_id", (None, "other"))]
    body += [("file", ("brief.txt", b"data", "text/plain"))]
    response = sync_client.post(f"{PREFIX}/inputs/upload", files=body)
    assert response.status_code == 422
    assert not (artifact_case.root / ".wright" / "process-inputs").exists()


def test_upload_scope_and_size_are_checked_before_saving(sync_client, artifact_case):
    c = artifact_case
    assert upload(sync_client, c, session_id="foreign").status_code == 404
    assert upload(sync_client, c, expected_storage_digest="0" * 64).status_code == 409
    assert upload(sync_client, c, input_id="unknown").status_code == 403
    c.owner.limits = replace(c.owner.limits, maximum_upload_bytes=4)
    assert upload(sync_client, c, content=b"12345").status_code == 422
    assert not (c.root / ".wright" / "process-inputs").exists()


def test_representation_needs_exact_preparation_and_immutable_bytes(
    sync_client, artifact_case
):
    c = artifact_case
    reference = upload(sync_client, c).json()
    snapshot_id = prepare(sync_client, c, reference)
    for changed in (
        {**reference, "artifact_ref": "private.txt"},
        {**reference, "sha256": "0" * 64},
        {**reference, "result_id": "foreign"},
    ):
        assert read(sync_client, c, changed, snapshot_id).status_code == 403
    assert (
        read(sync_client, c, reference, snapshot_id, session_id="foreign").status_code
        == 404
    )
    assert (
        read(sync_client, c, reference, snapshot_id, run_id="other").status_code == 422
    )
    assert read(sync_client, c, reference, None).status_code == 422
    assert (
        read(
            sync_client, c, reference, snapshot_id, principal_id="private-must-not-echo"
        ).status_code
        == 422
    )
    (c.root / reference["artifact_ref"]).write_bytes(b"Changed input")
    stale = read(sync_client, c, reference, snapshot_id)
    assert stale.status_code == 409
    assert stale.json()["error_code"] == "SUBJECT_STALE"
    assert stale.headers["cache-control"] == "no-store"


def test_auth_and_origin_cover_upload_and_download(
    sync_client, artifact_case, monkeypatch
):
    monkeypatch.setattr(
        app.state,
        "security_settings",
        SecuritySettings(
            "enforced", "test-only-token", ("http://allowed.local",), "127.0.0.1"
        ),
    )
    for route in ("inputs/upload", "representations/read"):
        denied = sync_client.post(f"{PREFIX}/{route}")
        assert denied.status_code == 401
        origin = sync_client.post(
            f"{PREFIX}/{route}",
            headers={
                "Authorization": "Bearer test-only-token",
                "Origin": "http://other.local",
            },
        )
        assert origin.status_code == 403
    allowed = sync_client.post(
        f"{PREFIX}/inputs/upload",
        data={**artifact_case.query, "input_id": "brief"},
        files={"file": ("brief.txt", b"data", "text/plain")},
        headers={
            "Authorization": "Bearer test-only-token",
            "Origin": "http://allowed.local",
        },
    )
    assert allowed.status_code == 200


def test_artifact_routes_deny_viewer_before_resolving_workspace():
    from api.routers.process_interfaces import router

    probe = FastAPI()
    probe.state.security_settings = SimpleNamespace(enforced=True)

    @probe.middleware("http")
    async def identity(request: Request, call_next):
        request.state.principal_role = "viewer"
        return await call_next(request)

    def must_not_resolve():
        raise AssertionError("Denied callers cannot resolve a workspace")

    probe.dependency_overrides[get_workspace_service] = must_not_resolve
    probe.include_router(router, prefix=PREFIX)
    with TestClient(probe) as client:
        for route in ("inputs/upload", "representations/read"):
            response = client.post(f"{PREFIX}/{route}")
            assert response.status_code == 403


@pytest.mark.asyncio
async def test_bounded_request_replay_retains_the_actual_connection_lifetime():
    from api.main import ProcessInterfaceBodyLimitMiddleware

    disconnected = asyncio.Event()
    body_received = False

    async def receive():
        nonlocal body_received
        if not body_received:
            body_received = True
            return {"type": "http.request", "body": b"{}", "more_body": False}
        await disconnected.wait()
        return {"type": "http.disconnect"}

    async def downstream(scope, replay, send):
        assert await replay() == {
            "type": "http.request",
            "body": b"{}",
            "more_body": False,
        }
        waiting = asyncio.create_task(replay())
        await asyncio.sleep(0)
        assert not waiting.done(), (
            "Request-body completion must not invent a disconnect"
        )
        disconnected.set()
        assert await waiting == {"type": "http.disconnect"}

    async def send(message):
        raise AssertionError("This bounded request must not be rejected")

    await ProcessInterfaceBodyLimitMiddleware(downstream, max_body_bytes=4)(
        {"type": "http", "path": f"{PREFIX}/representations/read", "method": "POST"},
        receive,
        send,
    )


def test_native_navigation_resolves_source_and_rejects_foreign_intents(
    sync_client, artifact_case
):
    c = artifact_case
    for target in ({"kind": "process"}, {"kind": "block", "block_id": "brief"}):
        response = sync_client.post(
            f"{PREFIX}/navigation", json={**c.query, "target": target}
        )
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"] == "no-store"
        assert response.json()["target"]["kind"] == target["kind"]
        assert response.json()["process"]["workspace_id"] == "workspace"
    for target in (
        {"kind": "block", "block_id": "foreign"},
        {"kind": "result", "result_id": "foreign"},
        {"kind": "process", "artifact_ref": "private.txt"},
    ):
        response = sync_client.post(
            f"{PREFIX}/navigation", json={**c.query, "target": target}
        )
        assert response.status_code == 403
    for extra in (
        {"principal_id": "private-must-not-echo"},
        {"target": {"kind": "block"}},
        {"target": {"kind": "process", "url": "private-must-not-echo"}},
    ):
        response = sync_client.post(
            f"{PREFIX}/navigation",
            json={**c.query, "target": {"kind": "process"}, **extra},
        )
        assert response.status_code == 422
        assert "private-must-not-echo" not in response.text
    assert (
        sync_client.post(
            f"{PREFIX}/navigation",
            json={**c.query, "session_id": "foreign", "target": {"kind": "process"}},
        ).status_code
        == 404
    )
    assert (
        sync_client.post(
            f"{PREFIX}/navigation",
            json={
                **c.query,
                "expected_storage_digest": "0" * 64,
                "target": {"kind": "process"},
            },
        ).status_code
        == 409
    )
    assert not (c.root / "state.db").exists()
    assert not (c.root / "runs").exists()


@pytest.mark.parametrize(
    "artifact_case",
    [
        source(file="capture.png").replace(
            '"kind": "engineering_document"', '"kind": "reference_images"', 2
        )
    ],
    indirect=True,
)
def test_native_image_port_reads_real_prepared_artifact_and_rejects_changed_bytes(
    sync_client, artifact_case, monkeypatch
):
    """Actual artifact/upload owners plus native tool; HTTP transport is in-process."""
    import base64
    from pathlib import Path
    from unittest.mock import AsyncMock
    import httpx
    from mcp.server.fastmcp import FastMCP

    root = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root / "prototypes/desktop-harness"))
    from native_process_tools import register_native_process_tools

    content = (
        root
        / "artifacts/stevecad-demonstrations/qualification/native/06-inspect-coupon-1.png"
    ).read_bytes()
    c = artifact_case
    uploaded = upload(sync_client, c, content=content, name="capture.png")
    assert uploaded.status_code == 200, uploaded.text
    reference = uploaded.json()
    assert reference["media_type"] == "image/png"
    prepared = prepare(sync_client, c, reference)
    requests = []

    def owner_transport(request):
        assert request.method == "POST"
        assert request.url.path == PREFIX + "/representations/read"
        body = json.loads(request.content)
        requests.append(body)
        response = sync_client.post(request.url.path, json=body)
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            content=response.content,
            request=request,
        )

    async def exercise():
        async with httpx.AsyncClient(
            base_url="http://owner", transport=httpx.MockTransport(owner_transport)
        ) as http:
            client = SimpleNamespace(scope=AsyncMock(), http=http)
            server = FastMCP("native-image-owner-test")
            register_native_process_tools(server, client)
            request = {
                **c.query,
                "workspace_id": "workspace",
                "operation": "representation",
                "input_snapshot_id": prepared,
                "reference": reference,
            }
            _, result = await server.call_tool(
                "wright_process_ui_read", {"request": request}
            )
            assert result["ok"] is True
            assert result["document"]["media_type"] == "image/png"
            assert base64.b64decode(result["document"]["bytes_base64"]) == content
            assert result["document"]["sha256"] == hashlib.sha256(content).hexdigest()
            client.scope.assert_awaited_once_with("workspace", "owned-session")
            # Change only the isolated uploaded copy, preserving the historical source.
            (c.root / reference["artifact_ref"]).write_bytes(b"changed")
            _, denied = await server.call_tool(
                "wright_process_ui_read", {"request": request}
            )
            assert denied["ok"] is False
            assert denied["reason"]["code"] == "SUBJECT_STALE"

    asyncio.run(exercise())
    assert len(requests) == 2
    assert all(item["input_snapshot_id"] == prepared for item in requests)
    assert not (c.root / "runs").exists()
