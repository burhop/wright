from __future__ import annotations

import contextlib
import hashlib
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from api.routers.engineering_models import router as engineering_models_router
from api.security import ControlPlaneSecurityMiddleware, SecuritySettings
from fastapi import FastAPI
from fastapi.testclient import TestClient

from data_vault import ModelRepository, upgrade_database
from data_vault.model_artifact_store import ModelArtifactStore
from model_registry.catalog import ModelCatalog
from model_registry.generated import affine_artifacts
from model_registry.http_source import (
    HttpArtifactSource,
    HttpSourceError,
    SourceRequest,
    SourceResponse,
)
from model_registry.models import ModelPackage, ModelRegistryError
from model_registry.observability import MODEL_BOUNDARY_EVENTS, ModelBoundaryObserver
from model_registry.offline_source import OfflinePackageError, inspect_offline_package
from model_registry.policy import HostObservation, ModelPolicy
from model_registry.runtime import (
    RuntimeFailure,
    RuntimeSupervisor,
    built_in_runtime_registry,
    current_runtime_platform,
)
from workspace_service import EngineeringModelService


@dataclass(slots=True)
class RecordingLogger:
    events: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def info(self, event: str, **attributes: Any) -> None:
        self.events.append((event, attributes))


@dataclass(slots=True)
class RecordingTracer:
    spans: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    @contextlib.contextmanager
    def start_as_current_span(self, name: str, *, attributes: dict[str, Any]):
        self.spans.append((name, attributes))
        yield object()


def test_model_boundary_event_contract_covers_every_lifecycle_boundary() -> None:
    assert MODEL_BOUNDARY_EVENTS == frozenset(
        {
            "model.adapter.infer",
            "model.adapter.verify",
            "model.cleanup",
            "model.database.operation",
            "model.database.plan",
            "model.evidence.record",
            "model.export",
            "model.gateway.call",
            "model.operation.cancel",
            "model.source.acquire",
            "model.storage.activate",
            "model.storage.promote",
            "model.storage.reconcile",
            "model.storage.stage",
        }
    )


def test_structured_model_events_and_spans_drop_secrets_paths_and_authority() -> None:
    logger = RecordingLogger()
    tracer = RecordingTracer()
    observer = ModelBoundaryObserver(logger=logger, tracer=tracer)

    observer.record(
        "model.source.acquire",
        trace_id="trace-1",
        state="succeeded",
        attributes={
            "operation_id": "operation-1",
            "content_digest": "a" * 64,
            "api_token": "synthetic-private-value",
            "artifact_path": "C:/Users/private/model.onnx",
            "runtime_command": "python adapter.py --token=test-secret-value",
            "diagnostic": "token=test-secret-value",
        },
    )

    assert len(logger.events) == len(tracer.spans) == 1
    event, log_attributes = logger.events[0]
    span_name, span_attributes = tracer.spans[0]
    assert event == span_name == "model.source.acquire"
    encoded = repr((log_attributes, span_attributes))
    assert "synthetic-private-value" not in encoded
    assert "C:/Users/private" not in encoded
    assert "adapter.py" not in encoded
    assert log_attributes["trace_id"] == "trace-1"
    assert log_attributes["redacted_fields"] == 3
    assert "[REDACTED]" in log_attributes["diagnostic"]


def test_model_observer_rejects_unknown_events_and_unbounded_identity() -> None:
    observer = ModelBoundaryObserver(logger=RecordingLogger(), tracer=RecordingTracer())
    with pytest.raises(ValueError, match="event"):
        observer.record("model.unknown", trace_id="trace-1")
    with pytest.raises(ValueError, match="trace"):
        observer.record("model.cleanup", trace_id="x" * 129)


def test_content_store_emits_only_bounded_identity_transitions(tmp_path) -> None:
    logger = RecordingLogger()
    tracer = RecordingTracer()
    observer = ModelBoundaryObserver(logger=logger, tracer=tracer)
    store = ModelArtifactStore(tmp_path / "wright-data", observer=observer)
    content = b'{"scale":2,"offset":1}'
    digest = hashlib.sha256(content).hexdigest()

    staged = store.stage_bytes(
        operation_id="operation-1",
        expected_digest=digest,
        content=content,
        maximum_bytes=len(content),
        trace_id="trace-store",
    )
    store.promote(staged, trace_id="trace-store")
    store.activate(
        installation_id="installation-1",
        manifest_digest="a" * 64,
        artifacts={"model/coefficients.json": digest},
        trace_id="trace-store",
    )
    store.reconcile(trace_id="trace-store")

    assert [event for event, _ in logger.events] == [
        "model.storage.stage",
        "model.storage.promote",
        "model.storage.activate",
        "model.storage.reconcile",
    ]
    encoded = repr(logger.events)
    assert str(tmp_path) not in encoded
    assert content.decode() not in encoded


def test_model_repository_emits_identity_only_database_transitions(tmp_path) -> None:
    logger = RecordingLogger()
    tracer = RecordingTracer()
    observer = ModelBoundaryObserver(logger=logger, tracer=tracer)
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = ModelRepository(str(database), observer=observer)
    now = datetime(2026, 8, 13, tzinfo=UTC)

    repository.save_plan(
        plan_id="plan-1",
        principal_id="engineer-1",
        plan_digest="a" * 64,
        state="confirmed",
        plan={"model_id": "wright-affine-test", "effects": []},
        created_at=now,
        expires_at=now + timedelta(minutes=5),
        trace_id="trace-db",
    )
    repository.create_operation(
        operation_id="operation-1",
        plan_id="plan-1",
        plan_digest="a" * 64,
        kind="install",
        trace_id="trace-db",
        created_at=now,
    )
    assert repository.transition_operation(
        "operation-1",
        expected_state="prepared",
        state="running",
        phase="acquiring",
        progress={"completed_bytes": 0, "maximum_bytes": 10},
        updated_at=now,
        trace_id="trace-db",
    )

    assert [event for event, _ in logger.events] == [
        "model.database.plan",
        "model.database.operation",
        "model.database.operation",
    ]
    encoded = repr(logger.events)
    assert str(database) not in encoded
    assert "effects" not in encoded


def _approved_package() -> ModelPackage:
    package = ModelCatalog.load_bundled().get("wright-affine-test").package
    assert package is not None
    return package


def test_hostile_manifest_archive_and_source_fail_before_readiness(tmp_path) -> None:
    package = _approved_package()
    manifest = package.model_dump(mode="json")
    manifest["description"] = "".join(("to", "ken", "=", "synthetic", "-", "secret"))
    with pytest.raises(ModelRegistryError) as secret:
        ModelPackage.model_validate(manifest)
    assert secret.value.code == "secret_forbidden"

    archive = tmp_path / "hostile.wright-model.zip"
    with zipfile.ZipFile(archive, "w") as stream:
        stream.writestr("../outside.json", b"{}")
    with pytest.raises(OfflinePackageError) as escaped:
        inspect_offline_package(archive)
    assert escaped.value.code == "path_unsafe"

    content = b"reviewed"

    class RedirectTransport:
        def get(self, _url, *, headers, timeout):
            del headers, timeout
            return SourceResponse(
                status=302,
                headers={"Location": "https://unapproved.example/model.onnx"},
                chunks=(),
            )

    request = SourceRequest(
        url="https://models.example/revisions/rev-123/model.onnx",
        immutable_revision="rev-123",
        expected_digest=hashlib.sha256(content).hexdigest(),
        expected_size=len(content),
        maximum_bytes=len(content),
        allowed_hosts=("models.example",),
    )
    with pytest.raises(HttpSourceError) as redirected:
        HttpArtifactSource(RedirectTransport()).fetch(request)
    assert redirected.value.code == "source_host_unapproved"


def test_physical_actuation_package_is_policy_blocked() -> None:
    document = _approved_package().model_dump(mode="json")
    document["tasks"][0]["task_id"] = "start_spindle"
    document["variants"][0]["test_vectors"][0]["task_id"] = "start_spindle"
    package = ModelPackage.model_validate(document)
    result = ModelPolicy().evaluate(
        package,
        variant_id=package.variants[0].variant_id,
        host=HostObservation.reference(),
    )
    assert result.state == "blocked"
    assert "physical_actuation_forbidden" in {
        blocker.category for blocker in result.blockers
    }


@pytest.mark.asyncio
async def test_hostile_adapter_paths_and_field_bounds_stop_before_launch(
    tmp_path,
) -> None:
    package = _approved_package()
    values = affine_artifacts(package)
    source = tmp_path / "coefficients.json"
    source.write_bytes(values["model/coefficients.json"])
    supervisor = RuntimeSupervisor(
        built_in_runtime_registry(), scratch_root=tmp_path / "runtime"
    )
    system, architecture = current_runtime_platform()
    with pytest.raises(RuntimeFailure) as escaped:
        await supervisor.start_session(
            adapter_id="wright-deterministic",
            installation_id="installation-hostile",
            artifacts={"../outside": source},
            model_format="wright-affine-json",
            task_id="predict",
            platform=system,
            architecture=architecture,
            execution_provider="cpu",
        )
    assert escaped.value.category == "artifact_invalid"
    assert supervisor.active_process_count == 0

    oversized = package.model_dump(mode="json")
    oversized["description"] = "x" * 5000
    with pytest.raises(ValueError):
        ModelPackage.model_validate(oversized)


def _local_model_api(tmp_path) -> tuple[TestClient, EngineeringModelService]:
    database = tmp_path / "model-api.db"
    upgrade_database(database)
    service = EngineeringModelService(
        repository=ModelRepository(str(database)),
        artifact_store=ModelArtifactStore(tmp_path / "model-data"),
    )
    app = FastAPI()
    app.state.security_settings = SecuritySettings(
        mode="compat",
        api_token=None,
        allowed_origins=("http://127.0.0.1:5173",),
        bind_host="127.0.0.1",
    )
    app.state.engineering_model_application = service
    app.add_middleware(ControlPlaneSecurityMiddleware)
    app.include_router(engineering_models_router, prefix="/api/v1/engineering-models")
    return TestClient(app), service


def test_api_confirmation_is_single_use_under_concurrency_and_bounds_requests(
    tmp_path,
) -> None:
    client, _service = _local_model_api(tmp_path)
    with client:
        created = client.post(
            "/api/v1/engineering-models/plans",
            json={
                "operation_kind": "install",
                "model_id": "wright-affine-test",
                "variant_id": "json-cpu-f64",
            },
        )
        assert created.status_code == 200
        target = f"/api/v1/engineering-models/plans/{created.json()['plan_id']}/confirm"
        body = {"plan_digest": created.json()["plan_digest"]}
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = tuple(
                executor.map(lambda _item: client.post(target, json=body), range(2))
            )
        assert sorted(response.status_code for response in results) == [200, 409]

        physical = client.post(
            "/api/v1/engineering-models/workspaces/workspace-one/bindings",
            headers={"X-Wright-Workspace-ID": "workspace-one"},
            json={
                "installation_id": "installation-one",
                "task_id": "physical_actuation",
            },
        )
        oversized = client.post(
            "/api/v1/engineering-models/plans",
            json={
                "operation_kind": "install",
                "model_id": "x" * 1000,
                "variant_id": "json-cpu-f64",
            },
        )
    assert physical.status_code == oversized.status_code == 422
