from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from wright_engineering.runtime.models import ProcessIdentity, utc_now
from wright_engineering.runtime.process import (
    ProcessError,
    ProcessManager,
    ProcessObservation,
)


class FakeInspector:
    def __init__(self, observation: ProcessObservation | None) -> None:
        self.observation = observation
        self.signals: list[tuple[int, bool]] = []

    def observe(self, pid: int) -> ProcessObservation | None:
        return self.observation

    def signal(self, pid: int, *, force: bool = False) -> None:
        self.signals.append((pid, force))

    def wait(self, pid: int, timeout: float) -> bool:
        return True


def _identity(runtime: Path, *, challenge: str = "secret") -> ProcessIdentity:
    return ProcessIdentity(
        pid=42,
        started_at=utc_now(),
        runtime_id="runtime-1",
        executable_path=str(runtime / "bin" / "python"),
        host="127.0.0.1",
        port=8765,
        instance_id="00000000-0000-4000-8000-000000000042",
        challenge_hash=hashlib.sha256(challenge.encode()).hexdigest(),
        operation_id="00000000-0000-4000-8000-000000000001",
    )


def test_identity_requires_pid_start_runtime_and_contained_executable(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    executable = runtime / "bin" / "python"
    identity = _identity(runtime)
    observation = ProcessObservation(42, identity.started_at, executable)
    manager = ProcessManager(FakeInspector(observation))
    manager.require_identity(identity, runtime, expected_runtime_id="runtime-1")

    with pytest.raises(ProcessError, match="process_runtime_mismatch"):
        manager.require_identity(
            _identity(runtime), runtime, expected_runtime_id="other"
        )
    with pytest.raises(ProcessError, match="process_not_found"):
        ProcessManager(FakeInspector(None)).require_identity(
            _identity(runtime), runtime, expected_runtime_id="runtime-1"
        )
    outside = tmp_path / "outside" / "python"
    outside_identity = _identity(runtime)
    with pytest.raises(ProcessError, match="process_executable_outside_runtime"):
        manager.require_identity(
            outside_identity,
            runtime,
            expected_runtime_id="runtime-1",
            observation=ProcessObservation(42, outside_identity.started_at, outside),
        )
    mismatched_identity = _identity(runtime)
    with pytest.raises(ProcessError, match="process_executable_mismatch"):
        manager.require_identity(
            mismatched_identity,
            runtime,
            expected_runtime_id="runtime-1",
            observation=ProcessObservation(
                42,
                mismatched_identity.started_at,
                runtime / "bin" / "other-python",
            ),
        )


def test_pid_reuse_and_challenge_mismatch_block_signals(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    identity = _identity(runtime)
    reused = ProcessObservation(
        42, "2000-01-01T00:00:00Z", Path(identity.executable_path)
    )
    inspector = FakeInspector(reused)
    manager = ProcessManager(inspector)
    with pytest.raises(ProcessError, match="process_start_mismatch"):
        manager.stop(identity, runtime, expected_runtime_id="runtime-1")
    assert inspector.signals == []
    with pytest.raises(ProcessError, match="health_challenge_mismatch"):
        manager.verify_challenge(identity, "wrong")


def test_verified_process_stops_gracefully(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    identity = _identity(runtime)
    inspector = FakeInspector(
        ProcessObservation(
            identity.pid, identity.started_at, Path(identity.executable_path)
        )
    )
    ProcessManager(inspector).stop(identity, runtime, expected_runtime_id="runtime-1")
    assert inspector.signals == [(42, False)]


class FakeProcess:
    pid = 42

    def __init__(self) -> None:
        self.terminated = False
        self.killed = False

    def poll(self):
        return None

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout=None):
        return 0

    def kill(self) -> None:
        self.killed = True


def test_launch_records_observed_os_identity(monkeypatch, tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    executable = runtime / "bin" / "python"
    process = FakeProcess()
    observation = ProcessObservation(42, "2026-07-28T12:00:00Z", executable)
    monkeypatch.setattr("subprocess.Popen", lambda *_args, **_kwargs: process)

    _, identity, _ = ProcessManager(FakeInspector(observation)).launch(
        [str(executable)],
        runtime_id="runtime-1",
        runtime_path=runtime,
        operation_id="operation-1",
        host="127.0.0.1",
        port=8765,
    )

    assert identity.started_at == observation.started_at
    assert identity.executable_path == str(executable.resolve(strict=False))


def test_launch_terminates_when_os_identity_is_unavailable(
    monkeypatch, tmp_path: Path
) -> None:
    runtime = tmp_path / "runtime"
    executable = runtime / "bin" / "python"
    process = FakeProcess()
    monkeypatch.setattr("subprocess.Popen", lambda *_args, **_kwargs: process)
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    with pytest.raises(ProcessError, match="process_identity_unavailable"):
        ProcessManager(FakeInspector(None)).launch(
            [str(executable)],
            runtime_id="runtime-1",
            runtime_path=runtime,
            operation_id="operation-1",
            host="127.0.0.1",
            port=8765,
        )

    assert process.terminated is True


class SequencedWaitInspector(FakeInspector):
    def __init__(
        self, observation: ProcessObservation, wait_results: list[bool]
    ) -> None:
        super().__init__(observation)
        self.wait_results = iter(wait_results)

    def wait(self, pid: int, timeout: float) -> bool:
        return next(self.wait_results)


def test_stop_escalates_only_after_graceful_timeout(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    identity = _identity(runtime)
    observation = ProcessObservation(
        identity.pid, identity.started_at, Path(identity.executable_path)
    )
    inspector = SequencedWaitInspector(observation, [False, True])

    ProcessManager(inspector).stop(
        identity, runtime, expected_runtime_id="runtime-1", graceful_timeout=0.1
    )

    assert inspector.signals == [(42, False), (42, True)]


def test_stop_reports_timeout_after_verified_force_signal(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    identity = _identity(runtime)
    observation = ProcessObservation(
        identity.pid, identity.started_at, Path(identity.executable_path)
    )
    inspector = SequencedWaitInspector(observation, [False, False])

    with pytest.raises(ProcessError, match="process_stop_timeout"):
        ProcessManager(inspector).stop(
            identity, runtime, expected_runtime_id="runtime-1", graceful_timeout=0.1
        )


def test_launch_refuses_an_empty_command(tmp_path: Path) -> None:
    with pytest.raises(ProcessError, match="process_command_missing"):
        ProcessManager(FakeInspector(None)).launch(
            [],
            runtime_id="runtime-1",
            runtime_path=tmp_path / "runtime",
            operation_id="operation-1",
            host="127.0.0.1",
            port=8765,
        )


def test_launch_refuses_executable_outside_runtime(tmp_path: Path) -> None:
    with pytest.raises(ProcessError, match="process_executable_outside_runtime"):
        ProcessManager(FakeInspector(None)).launch(
            [str(tmp_path / "outside" / "python")],
            runtime_id="runtime-1",
            runtime_path=tmp_path / "runtime",
            operation_id="operation-1",
            host="127.0.0.1",
            port=8765,
        )
