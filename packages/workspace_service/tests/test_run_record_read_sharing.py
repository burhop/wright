"""Read contention must not fabricate or replay durable execution outcomes."""

import errno
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from workspace_service import workflow_run_record as records
from workspace_service.workspace_path import WorkspacePath


@pytest.fixture
def record_file(tmp_path):
    target = tmp_path / "run.json"
    content = b'{"workflow_path":"workflows/exact.workflow.wflow","run_id":"exact","status":"running","events":[]}'
    target.write_bytes(content)
    return target, content


def read_record(target):
    return records._read_run_record(
        WorkspacePath(target.parent), target.name, "workflows/exact.workflow.wflow"
    )


def test_transient_windows_read_denial_recovers_exact_record(record_file, monkeypatch):
    target, content = record_file
    opened, slept = [], []
    original = Path.open

    def denied_once(path, *args, **kwargs):
        if path == target:
            opened.append(path)
            if len(opened) == 1:
                raise PermissionError(errno.EACCES, "Windows sharing contention")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(records, "_RUN_RECORD_READ_DELAYS", (0.02, 0.04), raising=False)
    monkeypatch.setattr(Path, "open", denied_once)
    monkeypatch.setattr(records.time, "sleep", slept.append)
    result = read_record(target)
    assert result["run_id"] == "exact" and result["status"] == "running"
    assert len(opened) == 2 and slept == [0.02]
    assert target.read_bytes() == content


@pytest.mark.parametrize(
    "delays,code,attempts",
    [
        ((0.02, 0.04), errno.EACCES, 3),
        ((), errno.EACCES, 1),
        ((0.02, 0.04), errno.EIO, 1),
    ],
)
def test_persistent_or_other_error_remains_failure(
    record_file, monkeypatch, delays, code, attempts
):
    target, _ = record_file
    opened, slept = [], []
    error = OSError(code, "read denied")

    def denied(path, *args, **kwargs):
        opened.append(path)
        raise error

    monkeypatch.setattr(records, "_RUN_RECORD_READ_DELAYS", delays, raising=False)
    monkeypatch.setattr(Path, "open", denied)
    monkeypatch.setattr(records.time, "sleep", slept.append)
    with pytest.raises(OSError) as caught:
        read_record(target)
    assert caught.value is error
    assert len(opened) == attempts
    assert slept == (list(delays) if code == errno.EACCES else [])


def test_malformed_record_is_never_retried(record_file, monkeypatch):
    target, _ = record_file
    target.write_bytes(b'{"workflow_path":')
    original = Path.open
    opened = []

    def observe(path, *args, **kwargs):
        opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(records, "_RUN_RECORD_READ_DELAYS", (0.02, 0.04), raising=False)
    monkeypatch.setattr(Path, "open", observe)
    with pytest.raises(ValueError):
        read_record(target)
    assert len(opened) == 1


@pytest.mark.parametrize("failure", ["missing", "denied"])
def test_transient_resolution_failure_rechecks_exact_record(
    record_file, monkeypatch, failure
):
    target, content = record_file
    original = WorkspacePath.resolve
    resolved, slept = [], []

    def resolve(paths, relative, **kwargs):
        resolved.append((relative, kwargs))
        if len(resolved) == 1:
            if failure == "missing":
                raise FileNotFoundError(relative)
            raise PermissionError(errno.EACCES, "Transient resolution denial")
        return original(paths, relative, **kwargs)

    monkeypatch.setattr(WorkspacePath, "resolve", resolve)
    monkeypatch.setattr(records, "_RUN_RECORD_READ_DELAYS", (0.02,))
    monkeypatch.setattr(records.time, "sleep", slept.append)
    assert read_record(target)["run_id"] == "exact"
    assert resolved == [(target.name, {"must_exist": True})] * 2
    assert slept == [0.02]
    assert target.read_bytes() == content


def test_missing_record_remains_missing_after_bounded_observation(
    record_file, monkeypatch
):
    target, _ = record_file
    target.unlink()
    slept = []
    monkeypatch.setattr(records, "_RUN_RECORD_READ_DELAYS", (0.02, 0.04))
    monkeypatch.setattr(records.time, "sleep", slept.append)
    with pytest.raises(FileNotFoundError):
        read_record(target)
    assert slept == [0.02, 0.04]
    assert not target.exists()


def test_reobservation_never_bypasses_changed_confinement(record_file, monkeypatch):
    target, content = record_file
    attempts = []

    def resolve(paths, relative, **kwargs):
        attempts.append(relative)
        if len(attempts) == 1:
            raise FileNotFoundError(relative)
        raise ValueError("Access denied: symbolic links and reparse points")

    monkeypatch.setattr(WorkspacePath, "resolve", resolve)
    monkeypatch.setattr(records, "_RUN_RECORD_READ_DELAYS", (0.02, 0.04))
    monkeypatch.setattr(records.time, "sleep", lambda _: None)
    with pytest.raises(ValueError, match="Access denied"):
        read_record(target)
    assert len(attempts) == 2
    assert target.read_bytes() == content


@pytest.mark.skipif(os.name != "nt", reason="Requires actual Windows file sharing")
def test_actual_windows_read_lock_release_recovers(record_file, monkeypatch):
    from packages.workspace_service.tests.test_generated_file_sharing import (
        windows_reader,
    )

    target, content = record_file
    held, denied = threading.Event(), threading.Event()
    original = Path.open
    errors = []

    def hold():
        with windows_reader(target, share_mode=0):
            held.set()
            assert denied.wait(2)

    def observe(path, *args, **kwargs):
        try:
            return original(path, *args, **kwargs)
        except PermissionError as error:
            errors.append(error.errno)
            denied.set()
            raise

    monkeypatch.setattr(Path, "open", observe)
    with ThreadPoolExecutor(max_workers=1) as pool:
        holder = pool.submit(hold)
        assert held.wait(2)
        result = read_record(target)
        holder.result(timeout=2)
    assert errors and set(errors) == {errno.EACCES}
    assert result["run_id"] == "exact"
    assert target.read_bytes() == content


@pytest.mark.skipif(os.name != "nt", reason="Requires actual Windows file sharing")
def test_actual_windows_persistent_read_lock_remains_error(record_file, monkeypatch):
    from packages.workspace_service.tests.test_generated_file_sharing import (
        windows_reader,
    )

    target, content = record_file
    original = Path.open
    attempts = []

    def observe(path, *args, **kwargs):
        attempts.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observe)
    with windows_reader(target, share_mode=0), pytest.raises(PermissionError):
        read_record(target)
    assert len(attempts) == 6
    assert target.read_bytes() == content
