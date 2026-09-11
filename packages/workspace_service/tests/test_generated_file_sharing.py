"""Atomic generated-file publication under real Windows reader contention."""
from __future__ import annotations

import ctypes
import errno
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import pytest

from workspace_service.adapters import filesystem
from workspace_service.adapters.filesystem import LocalWorkspaceFiles


@contextmanager
def windows_reader(path):
    from ctypes import wintypes

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        yield
    finally:
        if not kernel.CloseHandle(handle):
            raise ctypes.WinError(ctypes.get_last_error())


@pytest.mark.skipif(os.name != "nt", reason="Uses actual Windows file sharing")
def test_real_reader_releases_and_checkpoint_replacement_succeeds(tmp_path, monkeypatch):
    target = tmp_path / "run.json"
    old, new = b'{"event":1}', b'{"event":2}'
    target.write_bytes(old)
    held, denied = threading.Event(), threading.Event()
    errors = []

    def read_then_release():
        with windows_reader(target):
            held.set()
            assert denied.wait(2)
            time.sleep(0.03)
            assert target.read_bytes() == old

    real_replace = os.replace

    def observed_replace(source, destination):
        try:
            return real_replace(source, destination)
        except OSError as error:
            errors.append(error.winerror)
            assert Path(source).read_bytes() == new
            denied.set()
            raise

    monkeypatch.setattr(filesystem.os, "replace", observed_replace)
    with ThreadPoolExecutor(max_workers=1) as pool:
        reader = pool.submit(read_then_release)
        assert held.wait(2)
        assert LocalWorkspaceFiles(str(tmp_path)).write_generated("run.json", new, "overwrite") == "run.json"
        reader.result(timeout=2)
    assert errors and set(errors) <= {5, 32, 33}
    assert target.read_bytes() == new
    assert not list(tmp_path.glob(".wright-output-*"))


@pytest.mark.skipif(os.name != "nt", reason="Uses actual Windows file sharing")
def test_real_persistent_reader_fails_bounded_and_preserves_target(tmp_path):
    target = tmp_path / "run.json"
    target.write_bytes(b"original")
    started = time.monotonic()
    with windows_reader(target), pytest.raises(OSError) as caught:
        LocalWorkspaceFiles(str(tmp_path)).write_generated("run.json", b"new", "overwrite")
    assert caught.value.winerror in {5, 32, 33}
    assert time.monotonic() - started < 3
    assert target.read_bytes() == b"original"
    assert not list(tmp_path.glob(".wright-output-*"))


@pytest.mark.parametrize("winerror", [5, 32, 33])
def test_persistent_windows_errors_have_exact_retry_bound(tmp_path, monkeypatch, winerror):
    target = tmp_path / "run.json"
    target.write_bytes(b"original")
    error = OSError(errno.EACCES, "persistent failure")
    error.winerror = winerror
    calls, delays = [], []

    def fail(source, destination):
        calls.append(source)
        assert Path(source).read_bytes() == b"new"
        assert target.read_bytes() == b"original"
        raise error

    monkeypatch.setattr(filesystem.os, "replace", fail)
    monkeypatch.setattr(filesystem.time, "sleep", delays.append)
    with pytest.raises(OSError) as caught:
        LocalWorkspaceFiles(str(tmp_path)).write_generated("run.json", b"new", "overwrite")
    assert caught.value is error
    assert len(calls) == 6 and len(set(calls)) == 1
    assert delays == [0.02, 0.04, 0.08, 0.16, 0.20]
    assert target.read_bytes() == b"original"
    assert not list(tmp_path.glob(".wright-output-*"))


@pytest.mark.parametrize("winerror,code", [(None, errno.EACCES), (112, errno.ENOSPC), (3, errno.ENOENT)])
def test_other_errors_propagate_immediately(tmp_path, monkeypatch, winerror, code):
    target = tmp_path / "run.json"
    target.write_bytes(b"original")
    error = OSError(code, "not a sharing error")
    if winerror is not None:
        error.winerror = winerror
    calls, delays = [], []

    def fail(*args):
        calls.append(args)
        raise error

    monkeypatch.setattr(filesystem.os, "replace", fail)
    monkeypatch.setattr(filesystem.time, "sleep", delays.append)
    with pytest.raises(OSError) as caught:
        LocalWorkspaceFiles(str(tmp_path)).write_generated("run.json", b"new", "overwrite")
    assert caught.value is error
    assert len(calls) == 1 and not delays
    assert target.read_bytes() == b"original"
    assert not list(tmp_path.glob(".wright-output-*"))


def test_indexed_concurrent_publications_preserve_every_complete_payload(tmp_path):
    files = LocalWorkspaceFiles(str(tmp_path))
    (tmp_path / "report.json").write_bytes(b"original")
    payloads = [bytes([i]) * 10000 for i in range(8)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        paths = list(pool.map(lambda data: files.write_generated("report.json", data, "indexed"), payloads))
    assert len(set(paths)) == 8
    assert set(paths) == {f"report-{i:03d}.json" for i in range(1, 9)}
    assert (tmp_path / "report.json").read_bytes() == b"original"
    assert all((tmp_path / path).read_bytes() == data for path, data in zip(paths, payloads, strict=True))
    assert not list(tmp_path.glob(".wright-output-*"))
