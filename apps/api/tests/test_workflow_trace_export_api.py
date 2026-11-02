import io
import json
import zipfile
from types import SimpleNamespace

import pytest
from api.routers import workspace as workspace_router
from api.schemas.workspace import RivetRunInspectionResponse
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def _features(monkeypatch):
    monkeypatch.setattr(workspace_router, "_runner_feature_enabled", lambda: None)
    monkeypatch.setattr(workspace_router, "_operations_feature_enabled", lambda: None)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "size,included", [(100, True), (2 * 1024 * 1024 + 1, False), (None, False)]
)
async def test_report_only_includes_size_bounded_svg_evidence(
    monkeypatch, size, included
):
    reads = []
    inspection = {"run": {"run_id": "run-1"}, "steps": [], "final_outputs": []}

    async def scoped_record(*_args):
        return SimpleNamespace(workspace_dir="/workspace"), {}, inspection

    async def read_reference(workspace_dir, path):
        reads.append((workspace_dir, path))
        return b'<svg xmlns="http://www.w3.org/2000/svg"/>'

    monkeypatch.setattr(workspace_router, "_canonical_trace_record", scoped_record)
    monkeypatch.setattr(
        workspace_router,
        "canonical_artifact_paths",
        lambda _: [
            {
                "artifact_id": "drawing",
                "label": "support-preview.svg",
                "media_type": "image/svg+xml",
                "bytes": size,
                "workspace_path": "outputs/support-preview.svg",
            }
        ],
    )
    response = await workspace_router.workflow_source_run_trace_export_endpoint(
        "session-1",
        "runs/run.json",
        "report_only",
        SimpleNamespace(files=SimpleNamespace(read_reference=read_reference)),
    )
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        entry = json.loads(archive.read("manifest.json"))["entries"][0]
        assert bool(entry["package_path"]) is included
    assert reads == (
        [("/workspace", "outputs/support-preview.svg")] if included else []
    )


@pytest.mark.asyncio
async def test_trace_export_is_scoped_and_returns_offline_zip() -> None:
    calls = []

    class Operations:
        def inspection(self, **kwargs):
            calls.append(("inspection", kwargs))
            return {
                "run": {
                    "run_id": "run-1",
                    "workflow_id": "workflow-1",
                    "state": "succeeded",
                },
                "final_outputs": [],
                "steps": [],
                "run_inputs": [],
            }

        def run_evidence(self, **kwargs):
            calls.append(("evidence", kwargs))
            return {"run_id": "run-1", "artifacts": []}

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {"workspace_id": "workspace-1"} if session == "session-1" else None
            )
        ),
        workflow_operations=Operations(),
    )
    response = await workspace_router.workflow_run_trace_export_endpoint(
        "run-1", "session-1", "report_only", SimpleNamespace(), service
    )
    assert response.media_type == "application/zip"
    assert response.headers["cache-control"] == "no-store"
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        assert "index.html" in archive.namelist()
        assert "manifest.json" in archive.namelist()
    assert calls == [
        (
            "inspection",
            {
                "workspace_id": "workspace-1",
                "session_id": "session-1",
                "run_id": "run-1",
            },
        ),
        (
            "evidence",
            {
                "workspace_id": "workspace-1",
                "session_id": "session-1",
                "run_id": "run-1",
            },
        ),
    ]

    with pytest.raises(HTTPException) as hidden:
        await workspace_router.workflow_run_trace_export_endpoint(
            "run-1", "other-session", "report_only", SimpleNamespace(), service
        )
    assert hidden.value.status_code == 404


@pytest.mark.asyncio
async def test_canonical_saved_run_trace_and_full_export_are_workspace_scoped() -> None:
    artifact = b"ISO-10303-21;\nEND-ISO-10303-21;\n"
    import hashlib

    digest = hashlib.sha256(artifact).hexdigest()
    record = {
        "workflow_path": "workflows/housing.workflow.wflow",
        "source_digest": "a" * 64,
        "status": "completed",
        "started_at": "2026-09-16T10:00:00Z",
        "completed_at": "2026-09-16T10:00:02Z",
        "trace_definition": {
            "graph_id": "canonical",
            "name": "Housing",
            "nodes": [],
            "connections": [],
        },
        "trace_inputs": {"requirements": "b" * 64},
        "result": {
            "run_id": "run-canonical",
            "steps": [],
            "results": [
                {
                    "id": "housing",
                    "kind": "cad_model",
                    "name": "Housing",
                    "representations": [
                        {
                            "kind": "workspace_file",
                            "location": "outputs/housing.step",
                            "format": "model/step",
                            "sha256": digest,
                            "size_bytes": len(artifact),
                        }
                    ],
                }
            ],
        },
        "events": [],
    }

    class Files:
        async def read_reference(self, workspace_dir, path):
            assert workspace_dir == "/workspace"
            if path == "runs/housing/run.json":
                return json.dumps(record).encode()
            if path == "outputs/housing.step":
                return artifact
            raise FileNotFoundError(path)

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda session: (
                {
                    "workspace_id": "workspace-1",
                    "local_path": "/workspace",
                }
                if session == "session-1"
                else None
            )
        ),
        ensure_workspace_path_safe=lambda path: path,
        files=Files(),
    )
    inspection = await workspace_router.workflow_source_run_trace_endpoint(
        "session-1", "runs/housing/run.json", service
    )
    assert inspection["run"]["state"] == "succeeded"
    assert inspection["final_outputs"][0]["name"] == "Housing"

    report_only = await workspace_router.workflow_source_run_trace_export_endpoint(
        "session-1", "runs/housing/run.json", "report_only", service
    )
    with zipfile.ZipFile(io.BytesIO(report_only.body)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["entries"][0]["availability"] == "omitted_from_export"
        assert manifest["entries"][0]["package_path"] is None

    response = await workspace_router.workflow_source_run_trace_export_endpoint(
        "session-1", "runs/housing/run.json", "full_data", service
    )
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        included = manifest["entries"][0]["package_path"]
        assert archive.read(included) == artifact

    with pytest.raises(HTTPException):
        await workspace_router.workflow_source_run_trace_endpoint(
            "other", "runs/housing/run.json", service
        )


@pytest.mark.asyncio
async def test_campaign_run_trace_exports_sibling_artifact_not_original_host_path() -> (
    None
):
    import hashlib

    artifact = b"solid retained campaign output"
    digest = hashlib.sha256(artifact).hexdigest()
    record = {
        "schema_version": 1,
        "scenario_id": "printed-replacement-part-01",
        "attempt_id": "attempt-003",
        "run_id": "campaign-run-1",
        "status": "completed",
        "started_at": "2026-09-14T20:00:00Z",
        "finished_at": "2026-09-14T20:00:02Z",
        "definition_digest": "a" * 64,
        "required_step_ids": ["create_mesh"],
        "completed_step_ids": ["create_mesh"],
        "terminal_step_reached": True,
        "all_required_steps_succeeded": True,
        "produced_files": [
            {
                "artifact_id": "campaign-mesh-1",
                "path": "models/part.stl",
                "workspace_path": "C:/old-host/campaign/artifacts/models/part.stl",
                "sha256": digest,
                "size_bytes": len(artifact),
                "task_id": "create_mesh",
                "artifact_role": "deliverable",
            }
        ],
        "step_events": [
            {
                "kind": "step_started",
                "at": "2026-09-14T20:00:00Z",
                "task_id": "create_mesh",
            },
            {
                "kind": "step_completed",
                "at": "2026-09-14T20:00:02Z",
                "task_id": "create_mesh",
            },
        ],
    }
    reads = []

    class Files:
        async def read_reference(self, workspace_dir, path):
            assert workspace_dir == "/workspace"
            reads.append(path)
            if path == "runs/campaign/attempt-003/run.json":
                return json.dumps(record).encode()
            if path == "runs/campaign/attempt-003/artifacts/models/part.stl":
                return artifact
            raise FileNotFoundError(path)

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda _session: {
                "workspace_id": "workspace-1",
                "local_path": "/workspace",
            }
        ),
        ensure_workspace_path_safe=lambda path: path,
        files=Files(),
    )

    inspection = await workspace_router.workflow_source_run_trace_endpoint(
        "session-1", "runs/campaign/attempt-003/run.json", service
    )
    RivetRunInspectionResponse.model_validate(inspection)
    assert inspection["run"]["state"] == "succeeded"
    assert inspection["final_outputs"][0]["artifact"]["workspace_path"] == (
        "runs/campaign/attempt-003/artifacts/models/part.stl"
    )

    response = await workspace_router.workflow_source_run_trace_export_endpoint(
        "session-1",
        "runs/campaign/attempt-003/run.json",
        "full_data",
        service,
    )
    with zipfile.ZipFile(io.BytesIO(response.body)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        included = manifest["entries"][0]["package_path"]
        assert archive.read(included) == artifact
    assert "C:/old-host/campaign/artifacts/models/part.stl" not in reads


@pytest.mark.asyncio
async def test_canonical_trace_serves_only_digest_verified_raster_previews() -> None:
    import hashlib

    preview = b"\x89PNG\r\n\x1a\nretained-preview"
    digest = hashlib.sha256(preview).hexdigest()
    record = {
        "schema_version": 1,
        "scenario_id": "printed-replacement-part-01",
        "attempt_id": "attempt-003",
        "run_id": "campaign-run-1",
        "status": "completed",
        "started_at": "2026-09-14T20:00:00Z",
        "finished_at": "2026-09-14T20:00:02Z",
        "required_step_ids": ["render_preview"],
        "produced_files": [
            {
                "artifact_id": "preview-1",
                "path": "preview.png",
                "sha256": digest,
                "size_bytes": len(preview),
                "task_id": "render_preview",
                "artifact_role": "deliverable",
            }
        ],
        "step_events": [],
    }

    class Files:
        async def read_reference(self, _workspace_dir, path):
            if path == "runs/campaign/attempt.json":
                return json.dumps(record).encode()
            if path == "runs/campaign/artifacts/preview.png":
                return preview
            raise FileNotFoundError(path)

    service = SimpleNamespace(
        lifecycle=SimpleNamespace(
            get_by_session=lambda _session: {
                "workspace_id": "workspace-1",
                "local_path": "/workspace",
            }
        ),
        ensure_workspace_path_safe=lambda path: path,
        files=Files(),
    )
    response = await workspace_router.workflow_source_run_trace_artifact_endpoint(
        "session-1",
        "runs/campaign/attempt.json",
        "preview-1",
        service,
    )
    assert response.body == preview
    assert response.media_type == "image/png"
    assert response.headers["cache-control"] == "no-store"

    record["produced_files"][0]["sha256"] = "0" * 64
    with pytest.raises(HTTPException) as mismatch:
        await workspace_router.workflow_source_run_trace_artifact_endpoint(
            "session-1",
            "runs/campaign/attempt.json",
            "preview-1",
            service,
        )
    assert mismatch.value.status_code == 409
