from __future__ import annotations

import contextlib
import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest

from data_vault.model_artifact_store import ModelArtifactStore
from data_vault import ModelRepository, upgrade_database
from model_registry.observability import MODEL_BOUNDARY_EVENTS, ModelBoundaryObserver


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
