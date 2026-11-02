from __future__ import annotations

import io
import json
from types import SimpleNamespace
import urllib.error

import pytest

from wright_engineering.runtime import lifecycle as owner
from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.lifecycle import NativeLifecycle

from .test_lifecycle_start import FakeInstaller, FakeProcessManager, _artifact


def _transport(monkeypatch, *, ready_at: float | None, wrong_field=None):
    clock = SimpleNamespace(now=0.0)
    processes = FakeProcessManager()

    def sleep(duration):
        clock.now += duration

    def request(url, *, timeout):
        assert url == "http://127.0.0.1:8000/api/runtime/identity"
        if ready_at is None or clock.now < ready_at:
            raise urllib.error.URLError("not serving yet")
        identity = processes.identity
        payload = {
            "product": "wright",
            "runtime_id": identity.runtime_id,
            "instance_id": identity.instance_id,
            "challenge_hash": identity.challenge_hash,
        }
        if wrong_field:
            payload[wrong_field] = "different-subject"
        return io.BytesIO(json.dumps(payload).encode())

    monkeypatch.setattr(owner.time, "monotonic", lambda: clock.now)
    monkeypatch.setattr(owner.time, "sleep", sleep)
    monkeypatch.setattr(owner.urllib.request, "urlopen", request)
    return clock, processes


def test_start_accepts_actual_identity_after_slow_cold_start(tmp_path, monkeypatch):
    clock, processes = _transport(monkeypatch, ready_at=40.0)
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    lifecycle = NativeLifecycle(
        layout,
        installer=FakeInstaller(layout),
        process_manager=processes,
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
    )
    result = lifecycle.start(artifact=_artifact(tmp_path))
    assert result.ok and result.code == "ok"
    assert clock.now == 40.0
    assert processes.launches == 1


def test_start_never_ready_remains_bounded_and_failed(tmp_path, monkeypatch):
    clock, processes = _transport(monkeypatch, ready_at=None)
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    lifecycle = NativeLifecycle(
        layout,
        installer=FakeInstaller(layout),
        process_manager=processes,
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
    )
    result = lifecycle.start(artifact=_artifact(tmp_path))
    assert not result.ok and result.code == "health_failed"
    assert clock.now == 120.0
    assert lifecycle.store.load().active_runtime_id is None


@pytest.mark.parametrize(
    "field", ["product", "runtime_id", "instance_id", "challenge_hash"]
)
def test_start_rejects_wrong_identity_even_with_extended_budget(
    tmp_path, monkeypatch, field
):
    _, processes = _transport(monkeypatch, ready_at=40.0, wrong_field=field)
    layout = NativeLayout.from_wright_home(tmp_path / "wright-home")
    result = NativeLifecycle(
        layout,
        installer=FakeInstaller(layout),
        process_manager=processes,
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
    ).start(artifact=_artifact(tmp_path))
    assert not result.ok and result.code == "health_failed"


def test_normal_health_observation_retains_its_existing_budget(monkeypatch):
    clock, processes = _transport(monkeypatch, ready_at=40.0)
    processes.launch(
        ["python"],
        runtime_id="timing",
        host="127.0.0.1",
        port=8000,
        operation_id="status-observation",
    )
    assert not NativeLifecycle._probe_health(processes.identity)
    assert clock.now == 30.0
