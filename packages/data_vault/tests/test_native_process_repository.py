from __future__ import annotations

import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from core.native_process import validate_definition
from data_vault.backup import restore_backup
from data_vault.migrations import MIGRATIONS, database_status, upgrade_database
from data_vault.models import DatabaseCompatibilityError
from data_vault.native_process_repository import (
    NativeProcessRepository,
    NativeRepositoryError,
)
from data_vault.state_store import connect_state_db

ROOT = Path(__file__).resolve().parents[3]


def document(title="Concept brief", process_id=None):
    data = json.loads(
        (
            ROOT / "src/wright_engineering/static/native-processes/concept-brief.json"
        ).read_text(encoding="utf-8")
    )
    data["title"] = title
    if process_id:
        data["id"] = process_id
    return validate_definition(data)


def register(path):
    with connect_state_db(path) as connection:
        for name in ("one", "two"):
            connection.execute(
                """INSERT INTO engineering_workspaces
                (workspace_id,session_id,local_path,created_at,updated_at)
                VALUES (?,?,?,1,1)""",
                (name, "session-" + name, "/workspace/" + name),
            )


@pytest.fixture
def repository(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path)
    register(path)
    return NativeProcessRepository(str(path))


def save(
    repository,
    doc=None,
    *,
    key="first-request",
    token=None,
    workspace="one",
    layout=None,
):
    return repository.save(
        workspace,
        doc or document(),
        layout or {},
        request_id=key,
        expected_token=token,
        trace_id="save-trace",
    )


def test_save_reopen_previous_revision_layout_identity_and_trace(repository):
    first = save(repository)
    layout = {"need-source": {"x": 20, "y": 40}}
    second = save(repository, key="layout", token=first["token"], layout=layout)
    assert second["revision"] == 2
    assert second["token"] != first["token"]
    assert second["semantic_digest"] == first["semantic_digest"]
    assert repository.get("one", document().process_id) == second
    assert repository.get("one", document().process_id, previous=True) == first
    reopened = NativeProcessRepository(repository.db_path)
    assert reopened.get("one", document().process_id) == second
    with connect_state_db(repository.db_path) as connection:
        assert (
            connection.execute(
                "SELECT trace_id FROM native_process_documents"
            ).fetchone()[0]
            == "save-trace"
        )
        assert {
            row[0]
            for row in connection.execute(
                "SELECT trace_id FROM native_process_requests"
            )
        } == {"save-trace"}


def test_exact_retry_returns_original_result_after_later_save(repository):
    first = save(repository)
    later = save(repository, document("Later"), key="later", token=first["token"])
    assert save(repository) == first
    assert repository.get("one", document().process_id) == later
    with pytest.raises(NativeRepositoryError) as error:
        save(repository, document("Changed replay"))
    assert error.value.code == "NATIVE_REQUEST_REUSED"


def test_stale_writers_and_create_collision_cannot_overwrite(repository):
    first = save(repository)
    with pytest.raises(NativeRepositoryError) as error:
        save(repository, key="colliding-create")
    assert error.value.code == "NATIVE_CONFLICT"
    second = save(repository, document("Second"), key="second", token=first["token"])
    with pytest.raises(NativeRepositoryError) as error:
        save(repository, document("Stale"), key="stale", token=first["token"])
    assert error.value.code == "NATIVE_CONFLICT"
    assert repository.get("one", document().process_id) == second
    with connect_state_db(repository.db_path) as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM native_process_requests"
            ).fetchone()[0]
            == 2
        )


def test_parallel_writers_have_exactly_one_success(repository):
    first = save(repository)
    barrier = Barrier(2)

    def compete(number):
        barrier.wait()
        try:
            return save(
                repository,
                document(f"Writer {number}"),
                key=f"writer-{number}",
                token=first["token"],
            )
        except NativeRepositoryError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(compete, (1, 2)))
    assert outcomes.count("NATIVE_CONFLICT") == 1
    winner = next(value for value in outcomes if isinstance(value, dict))
    assert repository.get("one", document().process_id) == winner
    assert winner["revision"] == 2


def test_fault_between_document_and_request_insertion_rolls_back_both(repository):
    first = save(repository)
    with connect_state_db(repository.db_path) as connection:
        connection.execute("""CREATE TRIGGER injected_request_failure BEFORE INSERT ON native_process_requests
            WHEN NEW.request_id = 'fault' BEGIN SELECT RAISE(ABORT, 'injected storage fault'); END""")
    with pytest.raises(sqlite3.IntegrityError):
        save(repository, document("Must roll back"), key="fault", token=first["token"])
    assert repository.get("one", document().process_id) == first
    with pytest.raises(NativeRepositoryError):
        repository.get("one", document().process_id, previous=True)
    with connect_state_db(repository.db_path) as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM native_process_requests"
            ).fetchone()[0]
            == 1
        )


def test_workspace_scope_and_bounded_pagination(repository):
    first = save(repository)
    with pytest.raises(NativeRepositoryError) as error:
        repository.get("two", document().process_id)
    assert error.value.code == "NATIVE_NOT_FOUND"
    other = save(repository, document("Other workspace"), workspace="two")
    assert other["token"] != first["token"]
    for name in ("aaa-process", "zzz-process"):
        save(repository, document(process_id=name), key=name)
    page = repository.list("one", limit=2)
    last = repository.list("one", limit=2, cursor=page["next_cursor"])
    assert len(page["documents"]) == 2 and len(last["documents"]) == 1
    assert last["next_cursor"] is None
    assert {d["id"] for d in page["documents"] + last["documents"]} == {
        document().process_id,
        "aaa-process",
        "zzz-process",
    }
    assert len(repository.list("two")["documents"]) == 1
    for bad in ("!", "../secret", "eA=="):
        with pytest.raises(NativeRepositoryError):
            repository.list("one", cursor=bad)
    with pytest.raises(NativeRepositoryError):
        repository.list("one", limit=101)


def test_migration_retains_verified_predecessor_and_forward_native_work(tmp_path):
    original = tmp_path / "native" / "state.db"
    upgrade_database(original, migrations=MIGRATIONS[:16])
    register(original)
    result = upgrade_database(original)
    assert result.applied == ({"version": 17, "name": "native_engineering_processes"},)
    assert result.backup_manifest
    native = NativeProcessRepository(str(original))
    saved = save(native)
    before = hashlib.sha256(original.read_bytes()).hexdigest()
    with pytest.raises(DatabaseCompatibilityError):
        database_status(original, MIGRATIONS[:16])
    with pytest.raises(DatabaseCompatibilityError):
        upgrade_database(original, migrations=MIGRATIONS[:16])
    assert hashlib.sha256(original.read_bytes()).hexdigest() == before
    predecessor = tmp_path / "separate-predecessor" / "state.db"
    restore_backup(predecessor, result.backup_manifest, migrations=MIGRATIONS[:16])
    assert database_status(predecessor, MIGRATIONS[:16]).ready
    assert database_status(original).ready
    assert upgrade_database(original).applied == ()
    assert native.get("one", document().process_id) == saved
    with connect_state_db(predecessor, read_only=True) as connection:
        assert (
            connection.execute(
                "SELECT count(*) FROM engineering_workspaces"
            ).fetchone()[0]
            == 2
        )
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name='native_process_documents'"
            ).fetchone()
            is None
        )


def test_interrupted_migration_does_not_leave_partial_native_tables(tmp_path):
    path = tmp_path / "state.db"
    upgrade_database(path, migrations=MIGRATIONS[:16])
    register(path)

    def interrupt(migration, connection):
        if migration.version == 17:
            raise RuntimeError("Injected interruption")

    with pytest.raises(RuntimeError, match="interruption"):
        upgrade_database(path, failure_hook=interrupt)
    assert database_status(path, MIGRATIONS[:16]).ready
    with connect_state_db(path, read_only=True) as connection:
        assert (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE name='native_process_documents'"
            ).fetchone()
            is None
        )
    assert upgrade_database(path).ending_version == 17
