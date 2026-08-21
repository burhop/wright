from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sqlite3

import pytest
from data_vault import ModelArtifactStore, ModelRepository, upgrade_database
from model_registry import ModelCatalog
from model_registry.offline_source import inspect_offline_package
from model_registry.policy import HostObservation
from workspace_service import EngineeringModelService


pytestmark = pytest.mark.external_model


def _source_root() -> Path:
    raw = os.environ.get("WRIGHT_EXTERNAL_MODEL_ROOT")
    if not raw:
        pytest.skip("Set WRIGHT_EXTERNAL_MODEL_ROOT for the opt-in NeuralFoil probe")
    root = Path(raw).resolve()
    if root.parent == root or ".local-run" not in root.parts or not root.is_dir():
        pytest.fail("External model root must be a real directory beneath .local-run")
    return root


@pytest.mark.asyncio
async def test_exact_neuralfoil_model_completes_bounded_offline_lifecycle(
    tmp_path,
) -> None:
    pytest.importorskip("numpy")
    root = _source_root()
    catalog = ModelCatalog.load_bundled()
    package = catalog.get("neuralfoil-medium").package
    assert package is not None
    variant = package.variants[0]
    observed = {
        item.path: (
            (root / Path(*item.path.split("/"))).stat().st_size,
            hashlib.sha256(
                (root / Path(*item.path.split("/"))).read_bytes()
            ).hexdigest(),
        )
        for item in variant.artifacts
    }
    assert observed == {
        item.path: (item.size, item.sha256) for item in variant.artifacts
    }

    from model_registry.runtime import built_in_runtime_registry

    runtime_versions = built_in_runtime_registry().versions()
    assert runtime_versions["wright-neuralfoil-numpy"] == "1.0.0"
    host = HostObservation(
        platform="windows",
        architecture="x86_64",
        available_disk_bytes=1_000_000_000,
        available_ram_bytes=1_000_000_000,
        accelerators=frozenset({"cpu"}),
        runtime_adapters=runtime_versions,
    )
    view = catalog.get_view(package.model_id, host=host)
    assert view["readiness"] == "approved"
    assert view["compatibility"]["state"] == "compatible"

    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = ModelRepository(str(database))
    store = ModelArtifactStore(tmp_path / "model-data")
    service = EngineeringModelService(
        catalog=catalog,
        host_observer=lambda: host,
        repository=repository,
        artifact_store=store,
    )
    with sqlite3.connect(database) as connection:
        connection.execute(
            """INSERT INTO engineering_workspaces
            (workspace_id, session_id, local_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)""",
            ("workspace-neuralfoil", "session-neuralfoil", str(tmp_path), 1, 1),
        )

    install_plan = service.create_plan(
        operation_kind="install",
        model_id=package.model_id,
        variant_id=variant.variant_id,
        principal_id="engineer-neuralfoil",
    )
    assert install_plan["state"] == "confirmable"
    assert install_plan["requirements"]["network"] == "required"
    installed = service.confirm_plan(
        install_plan["plan_id"],
        principal_id="engineer-neuralfoil",
        plan_digest=install_plan["plan_digest"],
        trace_id="trace-neuralfoil-install",
    )
    assert installed["state"] == "succeeded", installed
    installation_id = installed["result"]["installation_id"]
    cached_plan = service.create_plan(
        operation_kind="install",
        model_id=package.model_id,
        variant_id=variant.variant_id,
        principal_id="engineer-neuralfoil",
    )
    assert cached_plan["requirements"]["network"] == "none"
    assert not any(item["kind"] == "network" for item in cached_plan["effects"])
    cached = service.confirm_plan(
        cached_plan["plan_id"],
        principal_id="engineer-neuralfoil",
        plan_digest=cached_plan["plan_digest"],
        trace_id="trace-neuralfoil-cache-reuse",
    )
    assert cached["state"] == "succeeded"
    tested = await service.run_standard_test(
        installation_id,
        principal_id="engineer-neuralfoil",
        trace_id="trace-neuralfoil-test",
    )
    assert tested["installation_state"] == "ready"
    assert tested["evidence"][0]["state"] == "passed"

    binding = service.create_workspace_binding(
        installation_id,
        task_id="airfoil_aerodynamics",
        workspace_id="workspace-neuralfoil",
        principal_id="engineer-neuralfoil",
    )
    output = await service.invoke_model_capability(
        principal_id="engineer-neuralfoil",
        workspace_id="workspace-neuralfoil",
        session_id="session-neuralfoil",
        request_id="request-neuralfoil",
        trace_id="trace-neuralfoil-infer",
        tool_name=binding["tool_name"],
        binding_digest=binding["binding_digest"],
        arguments=variant.test_vectors[0].input,
        approval_context={},
        progress_callback=None,
    )
    assert output["structuredContent"]["cl"] == pytest.approx(1.10332809679, rel=1e-6)

    export_plan = service.create_plan(
        operation_kind="export",
        installation_id=installation_id,
        principal_id="engineer-neuralfoil",
    )
    exported_operation = service.confirm_plan(
        export_plan["plan_id"],
        principal_id="engineer-neuralfoil",
        plan_digest=export_plan["plan_digest"],
        trace_id="trace-neuralfoil-export",
    )
    exported = exported_operation["result"]
    payload = service.read_offline_export(
        exported["artifact_id"], principal_id="engineer-neuralfoil"
    )
    selected = tmp_path / "neuralfoil.wright-model.zip"
    selected.write_bytes(payload)
    assert inspect_offline_package(selected).package.digest == package.digest

    service.set_workspace_binding_state(
        binding["binding_id"],
        state="disabled",
        workspace_id="workspace-neuralfoil",
        principal_id="engineer-neuralfoil",
    )
    for kind in ("disable", "uninstall"):
        plan = service.create_plan(
            operation_kind=kind,
            installation_id=installation_id,
            principal_id="engineer-neuralfoil",
        )
        operation = service.confirm_plan(
            plan["plan_id"],
            principal_id="engineer-neuralfoil",
            plan_digest=plan["plan_digest"],
            trace_id=f"trace-neuralfoil-{kind}",
        )
        assert operation["state"] == "succeeded"
    service.set_model_reference_state(
        f"reference-{exported['artifact_id']}",
        state="archived",
        principal_id="engineer-neuralfoil",
    )
    purge_plan = service.create_plan(
        operation_kind="purge",
        installation_id=installation_id,
        principal_id="engineer-neuralfoil",
    )
    purged = service.confirm_plan(
        purge_plan["plan_id"],
        principal_id="engineer-neuralfoil",
        plan_digest=purge_plan["plan_digest"],
        trace_id="trace-neuralfoil-purge",
    )
    assert purged["state"] == "succeeded"
    assert purged["result"]["reclaimed_bytes"] == 112237
    assert not tuple(store.objects_root.glob("sha256/*/*"))
    assert not tuple((store.root / "runtime-scratch").glob("runtime-*"))
