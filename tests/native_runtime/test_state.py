from __future__ import annotations

from pathlib import Path

import pytest

from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.models import (
    LifecycleState,
    Manifest,
    OperationKind,
    OperationRecord,
    utc_now,
)
from wright_engineering.runtime.state import LifecycleBusy, ManifestStore, StateError


def _manifest(layout: NativeLayout) -> Manifest:
    return Manifest.create(layout.wright_home, layout.data)


def test_manifest_round_trip_is_atomic_and_snapshot_is_retained(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    store = ManifestStore(layout)
    manifest = _manifest(layout)
    store.save(manifest)
    manifest.lifecycle_state = LifecycleState.STOPPED
    store.save(manifest)

    assert store.load().lifecycle_state is LifecycleState.STOPPED
    assert store.snapshot_path.is_file()
    assert not store.manifest_path.with_suffix(".json.tmp").exists()


def test_corrupt_manifest_fails_closed_and_preserves_evidence(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    store = ManifestStore(layout)
    store.save(_manifest(layout))
    store.manifest_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(StateError, match="manifest_corrupt"):
        store.load()
    assert store.corrupt_dir.is_dir()
    assert any(store.corrupt_dir.iterdir())


def test_lock_contention_reports_active_operation(tmp_path: Path) -> None:
    store = ManifestStore(NativeLayout.from_wright_home(tmp_path / "wright-home"))
    with store.lock(operation_id="first", timeout=0.1):
        with pytest.raises(LifecycleBusy) as exc:
            with store.lock(operation_id="second", timeout=0.05):
                pass
    assert exc.value.operation_id == "first"


def test_invalid_transition_and_runtime_reference_are_rejected(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    manifest = _manifest(layout)
    with pytest.raises(ValueError, match="invalid_transition"):
        manifest.transition(LifecycleState.HEALTHY)

    manifest.active_runtime_id = "missing"
    with pytest.raises(ValueError, match="active_runtime_missing"):
        manifest.validate()


def test_interrupted_operation_remains_durable(tmp_path: Path) -> None:
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    store = ManifestStore(layout)
    manifest = _manifest(layout)
    manifest.transition(LifecycleState.INSTALLING)
    manifest.current_operation = OperationRecord(
        operation_id="00000000-0000-4000-8000-000000000001",
        kind=OperationKind.INSTALL,
        requested_by="session",
        started_at=utc_now(),
        from_state=LifecycleState.NOT_INSTALLED,
        target_state=LifecycleState.STOPPED,
        checkpoint="intent_recorded",
    )
    store.save(manifest)

    recovered = store.load()
    assert recovered.current_operation is not None
    assert recovered.current_operation.checkpoint == "intent_recorded"
