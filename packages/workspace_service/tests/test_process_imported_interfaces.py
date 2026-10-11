"""Inactive imported source discovery and confined local authoring, never execution."""

import json
from pathlib import Path

import pytest

from core.process_interfaces import InterfaceManifest, SourceEnvelope
from core.process_validation import canonical_digest, canonical_json
from core.workflow_bundle import ImportedInterfaceReference, PortableInterface
from workspace_service.process_interfaces.errors import ProcessInterfaceError
from workspace_service.process_interfaces.imported import ImportedInterfaceLibrary
from packages.workspace_service.tests.test_process_ui_authoring import (
    Engine,
    authorized,
    prepared,
    fake_build,
)
from workspace_service.process_interfaces import authoring as authoring_module


def candidate(
    root, source_path="workflows/example.workflow.wflow", *, title="Imported comparison"
):
    directory = (
        root
        / "imported-assets"
        / Path(source_path).name.removesuffix(".workflow.wflow")
    )
    (directory / "interfaces").mkdir(parents=True, exist_ok=True)
    source = SourceEnvelope(
        files={"App.tsx": "export default function App(){return <p>Imported view</p>}"}
    )
    manifest = InterfaceManifest(
        ui_id="foreign-ui",
        revision_id="foreign-revision",
        title=title,
        process={
            "workspace_id": "origin",
            "source_path": "workflows/original.workflow.wflow",
            "source_digest": "a" * 64,
        },
        client_version="1.0.0",
        kit_version="1.0.0",
        capabilities=("process.cancel",),
    )
    value = PortableInterface(
        manifest=manifest, source=source, source_digest=canonical_digest(source)
    )
    path = directory / "interfaces/foreign-ui.json"
    path.write_text(canonical_json(value), encoding="utf-8")
    receipt = {
        "authority": "definition-only-local-readiness-required",
        "destination_path": source_path,
        "interface_candidates": [manifest.ui_id],
        "requirements": [
            {
                "category": "ui",
                "identity": manifest.ui_id,
                "disposition": "embedded",
                "sha256": value.source_digest,
                "details": {"activation": "local-rebuild-and-review-required"},
            }
        ],
    }
    (directory / "manifest.json").write_text(json.dumps(receipt), encoding="utf-8")
    return path, value


def test_candidates_are_inactive_bounded_metadata_and_exact_source(tmp_path):
    library = ImportedInterfaceLibrary(tmp_path, "workflows/example.workflow.wflow")
    assert library.list() == {"candidates": [], "reasons": []}
    path, value = candidate(tmp_path)
    choice = library.list()["candidates"][0]
    assert set(choice) == {"ui_id", "sha256", "title", "client_version", "kit_version"}
    assert (
        library.read(
            ImportedInterfaceReference(ui_id=choice["ui_id"], sha256=choice["sha256"])
        )
        == value
    )
    assert not (tmp_path / "state.db").exists() and not (tmp_path / "runs").exists()
    assert path.exists()


@pytest.mark.parametrize(
    "failure",
    [
        "changed",
        "digest",
        "missing",
        "foreign",
        "inventory",
        "receipt",
        "injected_build",
        "traversal",
    ],
)
def test_invalid_candidates_never_become_local_interfaces(tmp_path, failure):
    path, value = candidate(tmp_path)
    library = ImportedInterfaceLibrary(tmp_path, "workflows/example.workflow.wflow")
    choice = library.list()["candidates"][0]
    selection = ImportedInterfaceReference(
        ui_id=choice["ui_id"], sha256=choice["sha256"]
    )
    if failure == "changed":
        path.write_text(
            canonical_json(
                value.model_copy(
                    update={
                        "manifest": value.manifest.model_copy(
                            update={"title": "Changed"}
                        )
                    }
                )
            ),
            encoding="utf-8",
        )
    elif failure == "digest":
        raw = json.loads(path.read_bytes())
        raw["source"]["files"]["App.tsx"] += " /* changed */"
        path.write_text(json.dumps(raw), encoding="utf-8")
    elif failure == "missing":
        path.unlink()
    elif failure == "foreign":
        selection = selection.model_copy(update={"ui_id": "other-ui"})
    elif failure == "injected_build":
        raw = json.loads(path.read_bytes())
        raw["build"] = {"state": "built"}
        path.write_text(json.dumps(raw), encoding="utf-8")
    else:
        receipt_path = path.parent.parent / "manifest.json"
        raw = json.loads(receipt_path.read_bytes())
        if failure == "inventory":
            raw["interface_candidates"] = ["undeclared-ui"]
        if failure == "receipt":
            raw["destination_path"] = "workflows/another.workflow.wflow"
        if failure == "traversal":
            raw["interface_candidates"] = ["../../other"]
        receipt_path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ProcessInterfaceError):
        library.read(selection)
    if failure not in {"changed", "foreign"}:
        assert library.list()["reasons"]


def test_legacy_receipt_still_discovers_preserved_candidate(tmp_path):
    path, _ = candidate(tmp_path)
    receipt = path.parent.parent / "manifest.json"
    raw = json.loads(receipt.read_bytes())
    del raw["destination_path"]
    receipt.write_text(json.dumps(raw), encoding="utf-8")
    assert (
        len(
            ImportedInterfaceLibrary(
                tmp_path, "workflows/example.workflow.wflow"
            ).list()["candidates"]
        )
        == 1
    )


@pytest.mark.asyncio
async def test_authoring_freezes_imported_source_with_local_identity_and_no_inherited_grants(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(authoring_module, "build_interface", fake_build)
    engine = Engine()
    service, process = prepared(tmp_path, engine)
    path, imported = candidate(tmp_path, process.source_path)
    choices = await service.imported_interfaces(authorized(), process)
    choice = choices["candidates"][0]
    selection = {key: choice[key] for key in ("ui_id", "sha256")}
    job = await service.submit(
        authorized(),
        process,
        "rebuild-one",
        "Reuse this layout",
        imported_interface=selection,
    )
    result = await service.wait(authorized(), process, job.job_id)
    assert result.state == "preview_ready"
    record = service.repository.get_authoring_record(
        process.workspace_id, job.job_id, "request"
    )
    prompt = json.loads(engine.calls[0].message)
    assert record["imported_reference"] == imported.model_dump(mode="json")
    assert prompt["imported_reference"] == record["imported_reference"]
    assert record["manifest"]["process"] == process.model_dump(mode="json")
    assert record["manifest"]["ui_id"] != imported.manifest.ui_id
    assert record["manifest"]["parent_revision"] is None and job.base_revision is None
    assert "process.cancel" not in record["manifest"]["capabilities"]
    assert not service.repository.get_ui(
        process.workspace_id, record["manifest"]["ui_id"]
    ).active_revision
    path.unlink()
    repeat = await service.submit(
        authorized(),
        process,
        "rebuild-one",
        "Reuse this layout",
        imported_interface=selection,
    )
    assert repeat.job_id == job.job_id and len(engine.calls) == 1
    with pytest.raises(ProcessInterfaceError):
        await service.submit(
            authorized(),
            process,
            "rebuild-one",
            "Reuse this layout",
            imported_interface={**selection, "sha256": "e" * 64},
        )
    with pytest.raises(ProcessInterfaceError):
        await service.submit(
            authorized(),
            process,
            "new-request",
            "Reuse this layout",
            imported_interface=selection,
        )
    assert len(engine.calls) == 1
    await service.close()


@pytest.mark.asyncio
async def test_cannot_mix_imported_reference_with_saved_update_or_cross_scope(tmp_path):
    service, process = prepared(tmp_path)
    candidate(tmp_path, process.source_path)
    selection = {"ui_id": "foreign-ui", "sha256": "a" * 64}
    with pytest.raises(ProcessInterfaceError):
        await service.submit(
            authorized(),
            process,
            "mixed",
            "Reuse",
            ui_id="local-ui",
            base_revision="local-revision",
            imported_interface=selection,
        )
    with pytest.raises(ProcessInterfaceError):
        await service.imported_interfaces(
            authorized(), process.model_copy(update={"workspace_id": "another"})
        )
    assert service.engine.probes == 0
    await service.close()
