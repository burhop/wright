"""The lightweight manager must use confined installed migration dependencies."""

import builtins
import json
from pathlib import Path
import subprocess

import pytest

from wright_engineering.runtime.installer import RuntimeInstaller
from wright_engineering.runtime.layout import LayoutError
from wright_engineering.runtime.lifecycle import NativeLifecycle
from wright_engineering.runtime.migrations import MigrationPreflightError
from wright_engineering.runtime.models import (
    LifecycleState,
    OperationKind,
    OperationRecord,
    RuntimeStatus,
    utc_now,
)

from .support import lifecycle, seed_runtime


@pytest.fixture
def managed(tmp_path, monkeypatch):
    runtime = lifecycle(tmp_path)
    runtime.migration_manager = NativeLifecycle(runtime.layout).migration_manager
    for name in ("active", "candidate"):
        installation = seed_runtime(
            runtime, version="0.1.5", runtime_id=name, active=name == "active"
        )
        python = RuntimeInstaller.environment_python(
            Path(installation.environment_path)
        )
        python.parent.mkdir(exist_ok=True)
        python.touch()
    manifest = runtime.store.load()
    manifest.runtimes["candidate"].status = RuntimeStatus.VERIFIED
    manifest.predecessor_runtime_id = None
    manifest.lifecycle_state = LifecycleState.UPDATING
    manifest.current_operation = OperationRecord(
        operation_id="candidate-migration",
        kind=OperationKind.UPDATE,
        requested_by="test",
        started_at=utc_now(),
        from_state=LifecycleState.STOPPED,
        target_state=LifecycleState.STOPPED,
        candidate_runtime_id="candidate",
    )
    runtime.store.save(manifest)
    original_import = builtins.__import__

    def lightweight_import(name, *args, **kwargs):
        if name == "data_vault" or name.startswith("data_vault."):
            raise AssertionError("The manager imported runtime-only dependencies")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", lightweight_import)
    return runtime


def test_schema_uses_active_runtime_but_activation_uses_candidate(managed, monkeypatch):
    calls = []
    backup = str(managed.layout.data / "backups" / "snapshot.json")

    def execute(command, **kwargs):
        calls.append((command, kwargs))
        assert command[1:3] == ["-I", "-c"]
        assert kwargs["check"] and kwargs["timeout"] == 180
        return subprocess.CompletedProcess(
            command, 0, "42" if len(calls) == 1 else json.dumps(backup)
        )

    monkeypatch.setattr(subprocess, "run", execute)
    owner = managed.migration_manager
    assert owner.current_schema(managed.layout.data) == 42
    assert (
        owner.prepare_activation(
            data_root=managed.layout.data,
            data_schema_min=0,
            data_schema_max=43,
            operation_id="exact-subject",
        )
        == backup
    )
    assert Path(calls[0][0][0]).is_relative_to(managed.layout.runtimes / "active")
    assert Path(calls[1][0][0]).is_relative_to(managed.layout.runtimes / "candidate")
    assert json.loads(calls[1][1]["input"]) == {
        "data_root": str(managed.layout.data),
        "data_schema_min": 0,
        "data_schema_max": 43,
        "operation_id": "exact-subject",
    }


@pytest.mark.parametrize("kind", ["failed", "missing", "escaped", "wrong-data"])
def test_unqualified_runtime_or_data_never_launches(
    managed, monkeypatch, tmp_path, kind
):
    manifest = managed.store.load()
    if kind == "failed":
        manifest.runtimes["candidate"].status = RuntimeStatus.FAILED
    elif kind == "missing":
        RuntimeInstaller.environment_python(
            Path(manifest.runtimes["active"].environment_path)
        ).unlink()
    elif kind == "escaped":
        manifest.runtimes["active"].environment_path = str(tmp_path / "unowned")
    managed.store.save(manifest)
    monkeypatch.setattr(
        subprocess, "run", lambda *a, **k: pytest.fail("Must reject before launch")
    )
    with pytest.raises((MigrationPreflightError, LayoutError)):
        if kind == "failed":
            managed.migration_manager.prepare_activation(
                data_root=managed.layout.data,
                data_schema_min=0,
                data_schema_max=43,
                operation_id="failed-candidate",
            )
        else:
            managed.migration_manager.current_schema(
                tmp_path if kind == "wrong-data" else managed.layout.data
            )


@pytest.mark.parametrize("output", ["true", "-1", '"42"', "not-json"])
def test_invalid_child_schema_does_not_become_compatibility_authority(
    managed, monkeypatch, output
):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kw: subprocess.CompletedProcess(command, 0, output),
    )
    with pytest.raises(MigrationPreflightError):
        managed.migration_manager.current_schema(managed.layout.data)


def test_child_failure_does_not_import_fallback_or_expose_stderr(managed, monkeypatch):
    def failed(command, **kwargs):
        raise subprocess.CalledProcessError(
            1, command, stderr="private database details"
        )

    monkeypatch.setattr(subprocess, "run", failed)
    with pytest.raises(MigrationPreflightError) as error:
        managed.migration_manager.current_schema(managed.layout.data)
    assert str(error.value) == "installed_migration_failed"


def test_backup_identity_cannot_escape_owned_data(managed, monkeypatch, tmp_path):
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kw: subprocess.CompletedProcess(
            command, 0, json.dumps(str(tmp_path / "outside"))
        ),
    )
    with pytest.raises(LayoutError):
        managed.migration_manager.prepare_activation(
            data_root=managed.layout.data,
            data_schema_min=0,
            data_schema_max=43,
            operation_id="exact-subject",
        )
