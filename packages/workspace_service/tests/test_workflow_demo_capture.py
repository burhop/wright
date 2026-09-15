from __future__ import annotations

import asyncio
import hashlib
import json
import zipfile
from types import SimpleNamespace

import pytest

from workspace_service.adapters.filesystem import LocalWorkspaceFiles
from workspace_service.workflow_demo_capture import (
    WorkflowDemoCaptureError,
    WorkflowDemoCaptureService,
)


def files(root):
    adapter = LocalWorkspaceFiles(str(root))

    async def read_reference(workspace_dir, path):
        return (await asyncio.to_thread(adapter.read, path))[1]

    async def write_generated_bytes(workspace_dir, path, content, policy):
        return await asyncio.to_thread(adapter.write_generated, path, content, policy)

    return SimpleNamespace(
        read_reference=read_reference, write_generated_bytes=write_generated_bytes
    )


def write_run(root, *, verified=True, content=b"<svg>verified mesh</svg>"):
    artifact = root / "outputs" / "preview.svg"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    record = {
        "workflow_path": "workflows/printed-part.workflow.wflow",
        "source_digest": "a" * 64,
        "status": "completed",
        "result": {
            "run_id": "run-verified-1",
            "evidence_class": "live",
            "verification": {
                "status": "verified" if verified else "unverified",
                "assertions": [{"id": "mesh-scale", "status": "passed"}],
            },
            "capture_rights": {
                "capture_allowed": True,
                "attribution": "Wright project generated fixture",
            },
            "results": [
                {
                    "schema_version": 1,
                    "id": "run-verified-1:mesh:preview",
                    "kind": "image",
                    "name": "Mesh preview",
                    "artifact_role": "verification",
                    "representations": [
                        {
                            "kind": "workspace_file",
                            "location": "outputs/preview.svg",
                            "format": "svg",
                            "durability": "persistent",
                            "sha256": digest,
                            "size_bytes": len(content),
                        }
                    ],
                    "provenance": {
                        "run_id": "run-verified-1",
                        "task_id": "mesh",
                        "output_port": "preview",
                    },
                    "exports": [],
                }
            ],
        },
    }
    path = root / "runs" / "printed-part" / "run.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record), encoding="utf-8")
    return "runs/printed-part/run.json", digest


def test_verified_run_creates_local_lineage_package_without_publishing(tmp_path):
    run_path, artifact_digest = write_run(tmp_path)
    capture = asyncio.run(
        WorkflowDemoCaptureService(files(tmp_path)).create(
            workspace_dir=str(tmp_path),
            run_log_path=run_path,
            expected_run_id="run-verified-1",
            artifact_ids=["run-verified-1:mesh:preview"],
            caption="Measured mesh and independent scale check.",
        )
    )
    assert capture["published"] is False
    assert capture["artifact_count"] == 1
    with zipfile.ZipFile(tmp_path / capture["path"]) as bundle:
        assert set(bundle.namelist()) == {
            "manifest.json",
            "caption.md",
            "artifacts/01-preview.svg",
        }
        manifest = json.loads(bundle.read("manifest.json"))
    assert manifest["source"]["run_id"] == "run-verified-1"
    assert manifest["artifacts"][0]["sha256"] == artifact_digest
    assert manifest["disclosures"]["physical_completion_claimed"] is False
    assert manifest["disclosures"]["published"] is False


def test_capture_rejects_unverified_changed_and_sensitive_evidence(tmp_path):
    run_path, _ = write_run(tmp_path, verified=False)
    service = WorkflowDemoCaptureService(files(tmp_path))
    with pytest.raises(WorkflowDemoCaptureError) as unverified:
        asyncio.run(
            service.create(
                workspace_dir=str(tmp_path),
                run_log_path=run_path,
                expected_run_id="run-verified-1",
                artifact_ids=["run-verified-1:mesh:preview"],
                caption="Draft",
            )
        )
    assert unverified.value.code == "capture_run_unverified"

    run_path, _ = write_run(tmp_path)
    (tmp_path / "outputs" / "preview.svg").write_text("changed")
    with pytest.raises(WorkflowDemoCaptureError) as changed:
        asyncio.run(
            service.create(
                workspace_dir=str(tmp_path),
                run_log_path=run_path,
                expected_run_id="run-verified-1",
                artifact_ids=["run-verified-1:mesh:preview"],
                caption="Draft",
            )
        )
    assert changed.value.code == "capture_artifact_changed"

    write_run(
        tmp_path, content=b"<svg>api_token=sk-not-for-capture-123456789012345</svg>"
    )
    with pytest.raises(WorkflowDemoCaptureError) as sensitive:
        asyncio.run(
            service.create(
                workspace_dir=str(tmp_path),
                run_log_path=run_path,
                expected_run_id="run-verified-1",
                artifact_ids=["run-verified-1:mesh:preview"],
                caption="Draft",
            )
        )
    assert sensitive.value.code == "capture_sensitive_content"
