from __future__ import annotations

from datetime import UTC, datetime
import io
import sqlite3
import zipfile

import pytest
from data_vault import ModelArtifactStore, ModelRepository, upgrade_database
from model_registry import ModelCatalog, canonical_json
from model_registry.generated import affine_artifacts
from model_registry.policy import HostObservation
from workspace_service.engineering_model_service import EngineeringModelService


def test_model_catalog_service_is_offline_and_composes_host_compatibility(
    monkeypatch,
) -> None:
    def network_must_not_run(*args, **kwargs):
        raise AssertionError("read-only model catalog contacted the network")

    monkeypatch.setattr("urllib.request.urlopen", network_must_not_run)
    service = EngineeringModelService(
        catalog=ModelCatalog.load_bundled(),
        host_observer=HostObservation.reference,
    )

    page = service.list_catalog(task="predict", limit=10)
    detail = service.get_catalog_model("wright-affine-test")

    assert page["total"] == 1
    assert page["models"][0]["model_id"] == "wright-affine-test"
    assert detail["compatibility"]["state"] == "compatible"
    assert detail["snapshot"]["offline"] is True


def test_service_installs_generated_package_only_after_exact_confirmation(
    tmp_path,
) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = ModelRepository(str(database))
    store = ModelArtifactStore(tmp_path / "data")
    service = EngineeringModelService(
        host_observer=HostObservation.reference,
        repository=repository,
        artifact_store=store,
        clock=lambda: datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
    )

    plan = service.create_plan(
        operation_kind="install",
        model_id="wright-affine-test",
        variant_id="json-cpu-f64",
        principal_id="engineer-1",
    )
    assert plan["state"] == "confirmable"
    assert list(store.installations_root.glob("*.json")) == []

    operation = service.confirm_plan(
        plan["plan_id"],
        principal_id="engineer-1",
        plan_digest=plan["plan_digest"],
        trace_id="trace-service-install",
    )
    assert operation["state"] == "succeeded"
    assert operation["result"]["readiness"] == "installed_unverified"
    assert len(list(store.installations_root.glob("*.json"))) == 1


def test_service_uploads_inspects_and_imports_without_exposing_a_host_path(
    tmp_path,
) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = ModelRepository(str(database))
    store = ModelArtifactStore(tmp_path / "data")
    service = EngineeringModelService(
        host_observer=HostObservation.reference,
        repository=repository,
        artifact_store=store,
        clock=lambda: datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
    )
    package = ModelCatalog.load_bundled().get("wright-affine-test").package
    assert package is not None
    entries = {
        **affine_artifacts(package),
        "engineering-model-package.json": canonical_json(
            package.model_dump(mode="json", exclude_none=True)
        ).encode("utf-8"),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, content in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)

    plan = service.create_import_plan(
        archive=buffer.getvalue(), principal_id="engineer-1"
    )
    assert plan["operation_kind"] == "import"
    assert "host_path" not in canonical_json(plan)
    operation = service.confirm_plan(
        plan["plan_id"],
        principal_id="engineer-1",
        plan_digest=plan["plan_digest"],
        trace_id="trace-service-import",
    )
    assert operation["state"] == "succeeded"
    assert list((store.root / "imports").glob("*.zip")) == []


@pytest.mark.asyncio
async def test_standard_test_binding_and_runtime_call_use_exact_reviewed_identity(
    tmp_path,
) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = ModelRepository(str(database))
    store = ModelArtifactStore(tmp_path / "data")
    service = EngineeringModelService(
        repository=repository,
        artifact_store=store,
        clock=lambda: datetime(2026, 8, 13, 12, 0, tzinfo=UTC),
    )
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)""",
            ("workspace-one", "session-one", str(tmp_path), 1, 1),
        )
    plan = service.create_plan(
        operation_kind="install",
        model_id="wright-affine-test",
        variant_id="json-cpu-f64",
        principal_id="engineer-one",
    )
    installed = service.confirm_plan(
        plan["plan_id"],
        principal_id="engineer-one",
        plan_digest=plan["plan_digest"],
        trace_id="trace-install",
    )
    installation_id = installed["result"]["installation_id"]

    tested = await service.run_standard_test(
        installation_id,
        principal_id="engineer-one",
        trace_id="trace-test",
    )
    binding = service.create_workspace_binding(
        installation_id,
        task_id="predict",
        workspace_id="workspace-one",
        principal_id="engineer-one",
    )
    discovered = service.discover_model_capabilities(
        principal_id="engineer-one",
        workspace_id="workspace-one",
        session_id="session-one",
    )
    result = await service.invoke_model_capability(
        principal_id="engineer-one",
        workspace_id="workspace-one",
        session_id="session-one",
        request_id="request-one",
        trace_id="trace-infer",
        tool_name=binding["tool_name"],
        binding_digest=binding["binding_digest"],
        arguments={"x": 3.0},
        approval_context={},
        progress_callback=None,
    )

    assert tested["installation_state"] == "ready"
    assert tested["adapter_version"] == "1.0.0"
    assert len(tested["evidence"]) == 1
    assert discovered[0]["binding_digest"] == binding["binding_digest"]
    assert result["structuredContent"] == {"y": 7.0}
    assert "runtime_endpoint" not in canonical_json(result)
    assert not tuple((store.root / "runtime-scratch").glob("runtime-*"))

    disabled = service.set_workspace_binding_state(
        binding["binding_id"],
        state="disabled",
        workspace_id="workspace-one",
        principal_id="engineer-one",
    )
    assert disabled["state"] == "disabled"
    assert (
        service.discover_model_capabilities(
            principal_id="engineer-one",
            workspace_id="workspace-one",
            session_id="session-one",
        )[0]["binding_state"]
        == "disabled"
    )
    reenabled = service.create_workspace_binding(
        installation_id,
        task_id="predict",
        workspace_id="workspace-one",
        principal_id="engineer-one",
    )
    assert reenabled["binding_id"] == binding["binding_id"]
    assert repository.get_binding(binding["binding_id"])["state"] == "enabled"
