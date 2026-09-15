from __future__ import annotations

import copy
import hashlib
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from core.native_application import NativeApplicationConflict
from data_vault.migrations import upgrade_database
from data_vault.native_application_repository import NativeApplicationRepository
from tool_registry.native_application_lifecycle import NativeApplicationLifecycle


class NativeAdapter:
    def __init__(self):
        self.alive = True
        self.docs = []
        self.calls = []
        self.creation_time = "2026-09-13T01:00:00Z"
        self.endpoint_matches = True
        self.fail_save = False
        self.fail_quit = False

    def inspect(self, session):
        return {
            "alive": self.alive,
            "identity": {**session["identity"], "creation_time": self.creation_time},
            "native_session_id": session["native_session_id"],
            "version": session["version"],
            "endpoint_matches": self.endpoint_matches,
            "healthy": True,
            "modal": False,
            "document_state_known": True,
            "documents": copy.deepcopy(self.docs),
            "active_operation": False,
        }

    def save_document(self, session, document):
        self.calls.append(("save", document["native_id"]))
        if self.fail_save:
            raise TimeoutError("Native save outcome unknown")
        path = Path(document["recovery_path"])
        path.write_bytes(b"owned native recovery")
        native = next(
            item for item in self.docs if item["native_id"] == document["native_id"]
        )
        native.update(dirty=False, path=str(path))
        return {
            "saved": True,
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }

    def close_document(self, session, document):
        self.calls.append(("close", document["native_id"]))
        self.docs = [
            item for item in self.docs if item["native_id"] != document["native_id"]
        ]
        return {"closed": True}

    def quit_application(self, session):
        self.calls.append(("quit", session["session_id"]))
        if not self.fail_quit:
            self.alive = False
        return {"requested": True}


def session_record(session_id="app-1", ownership="owned"):
    identity = {
        "pid": 1234,
        "creation_time": "2026-09-13T01:00:00Z",
        "executable": "C:/CAD/Edge.exe",
    }
    return {
        "session_id": session_id,
        "resource_id": "host-a/solid-edge",
        "app_kind": "solid_edge",
        "version": "226",
        "host": "host-a",
        "ownership": ownership,
        "identity": identity,
        "native_session_id": session_id,
        "endpoint": "local-helper",
        "launch_receipt": {
            "ownership_basis": "dedicated_launch",
            "baseline_absent": True,
            "native_session_verified": True,
            "identity": identity,
        },
    }


@pytest.fixture
def lifecycle(tmp_path):
    db = tmp_path / "state.db"
    upgrade_database(db)
    repo = NativeApplicationRepository(str(db))
    adapter = NativeAdapter()
    service = NativeApplicationLifecycle(repo, adapter)
    service.register_session(session_record(), trace_id="trace")
    return service, repo, adapter


def acquire(service, session_id="app-1"):
    return service.acquire(
        session_id,
        owner_id="worker",
        case_id="case-1",
        attempt="attempt-1",
        trace_id="trace",
    )


def document(tmp_path, **overrides):
    return {
        "native_id": "doc-1",
        "path": str(tmp_path / "part.psm"),
        "ownership": "owned",
        "preexisted": False,
        "dirty": True,
        "recovery_path": str(tmp_path / "recovery.psm"),
        "case_id": "case-1",
        "attempt": "attempt-1",
        "creation_evidence": "probe-create.json",
        **overrides,
    }


def test_dirty_owned_document_saved_closed_and_application_exit_verified(
    lifecycle, tmp_path
):
    service, repo, adapter = lifecycle
    lease = acquire(service)
    doc = document(tmp_path)
    service.register_document("app-1", lease["lease_id"], doc, trace_id="trace")
    adapter.docs.append({key: doc[key] for key in ("native_id", "path", "dirty")})
    receipt = service.cleanup("app-1", "cleanup-1", reason="success", trace_id="trace")
    assert receipt["status"] == "completed"
    assert adapter.calls == [("save", "doc-1"), ("close", "doc-1"), ("quit", "app-1")]
    saved = repo.list_documents("app-1")[0]
    assert saved["closed"] and saved["current_path"] == doc["recovery_path"]
    assert saved["path"] == doc["path"]  # initial path/provenance stays immutable
    assert repo.get_lease(lease["lease_id"])["state"] == "released"
    assert repo.get_session("app-1")["state"] == "exited"


def test_double_cleanup_after_restart_does_not_repeat_native_calls(lifecycle):
    service, repo, adapter = lifecycle
    acquire(service)
    first = service.cleanup("app-1", "cleanup-1", reason="success", trace_id="trace")
    fresh = NativeApplicationLifecycle(
        NativeApplicationRepository(repo.db_path), adapter
    )
    assert (
        fresh.cleanup("app-1", "cleanup-1", reason="success", trace_id="trace") == first
    )
    assert adapter.calls == [("quit", "app-1")]


@pytest.mark.parametrize("failure", ["pid_reuse", "endpoint_mismatch"])
def test_identity_mismatch_quarantines_without_native_actions(lifecycle, failure):
    service, repo, adapter = lifecycle
    lease = acquire(service)
    if failure == "pid_reuse":
        adapter.creation_time = "2026-09-13T02:00:00Z"
    else:
        adapter.endpoint_matches = False
    result = service.cleanup(
        "app-1", "cleanup-1", reason="case_failed", trace_id="trace"
    )
    assert result["status"] == "cleanup_blocked"
    assert adapter.calls == []
    assert repo.get_lease(lease["lease_id"])["state"] == "quarantined"


def test_borrowed_dirty_user_document_preserved_while_owned_doc_closes(
    lifecycle, tmp_path
):
    service, repo, adapter = lifecycle
    service.register_session(session_record("borrowed", "borrowed"), trace_id="trace")
    user_doc = {"native_id": "user", "path": "C:/Users/user/design.psm", "dirty": True}
    adapter.docs.append(copy.deepcopy(user_doc))
    lease = acquire(service, "borrowed")
    doc = document(tmp_path, dirty=False)
    service.register_document("borrowed", lease["lease_id"], doc, trace_id="trace")
    adapter.docs.append({key: doc[key] for key in ("native_id", "path", "dirty")})
    result = service.cleanup(
        "borrowed", "cleanup-1", reason="success", trace_id="trace"
    )
    assert result["status"] == "completed"
    assert result["application_receipt"]["preserved_borrowed_application"]
    assert adapter.calls == [("close", "doc-1")]
    assert adapter.alive and adapter.docs == [user_doc]
    assert repo.get_lease(lease["lease_id"])["state"] == "released"


def test_unknown_operation_remains_quarantined_after_worker_restart_and_process_exit(
    lifecycle,
):
    service, repo, adapter = lifecycle
    lease = acquire(service)
    service.begin_operation("app-1", lease["lease_id"], "extrude", trace_id="trace")
    service.finish_operation(
        "app-1",
        "extrude",
        outcome="unknown",
        evidence_reference="timeout.json",
        trace_id="trace",
    )
    adapter.alive = False
    fresh = NativeApplicationLifecycle(
        NativeApplicationRepository(repo.db_path), adapter
    )
    result = fresh.reconcile("app-1", trace_id="restart")
    assert result["active_operation"]["operation_id"] == "extrude"
    assert result["state"] == "cleanup_blocked"
    with pytest.raises(NativeApplicationConflict, match="Unknown native outcome"):
        repo.transition_lease(
            lease["lease_id"], "released", reason="expired", trace_id="trace"
        )
    receipt = fresh.cleanup("app-1", "cleanup-1", reason="timeout", trace_id="trace")
    assert receipt["status"] == "cleanup_blocked"
    assert adapter.calls == []


def test_two_repository_instances_cannot_lease_shared_resource(lifecycle):
    service, repo, adapter = lifecycle
    acquire(service)
    service.register_session(session_record("app-2"), trace_id="trace")
    other = NativeApplicationLifecycle(
        NativeApplicationRepository(repo.db_path), adapter
    )
    with pytest.raises(NativeApplicationConflict, match="outstanding lease"):
        acquire(other, "app-2")


def test_stale_transition_cannot_overwrite_a_new_lease(lifecycle):
    service, repo, _ = lifecycle
    stale = repo.get_session("app-1")
    acquire(service)
    stale["state"] = "exited"
    with pytest.raises(NativeApplicationConflict, match="changed"):
        repo.update_session(stale, kind="bad_stale_write", trace_id="trace")
    assert repo.get_session("app-1")["lease_id"] is not None


@pytest.mark.parametrize("failure", ["save", "quit", "untracked_document"])
def test_cleanup_failures_keep_resource_and_never_force_kill(
    lifecycle, tmp_path, failure
):
    service, repo, adapter = lifecycle
    lease = acquire(service)
    if failure == "save":
        doc = document(tmp_path)
        service.register_document("app-1", lease["lease_id"], doc, trace_id="trace")
        adapter.docs = [{key: doc[key] for key in ("native_id", "path", "dirty")}]
        adapter.fail_save = True
    elif failure == "quit":
        adapter.fail_quit = True
    else:
        adapter.docs = [{"native_id": "unknown-user-doc", "path": None, "dirty": True}]
    result = service.cleanup("app-1", "cleanup-1", reason="cancelled", trace_id="trace")
    assert result["status"] == "cleanup_blocked"
    assert repo.get_lease(lease["lease_id"])["state"] == "quarantined"
    assert adapter.alive
    assert not any(call[0] in ("terminate", "kill") for call in adapter.calls)
    calls = list(adapter.calls)
    # Interrupted cleanup is not replayed with a fresh request ID either.
    again = NativeApplicationLifecycle(repo, adapter).cleanup(
        "app-1", "cleanup-2", reason="restart", trace_id="trace"
    )
    assert again["status"] == "cleanup_blocked" and adapter.calls == calls


def test_warm_reuse_then_idle_shutdown(lifecycle):
    service, repo, adapter = lifecycle
    acquire(service)
    result = service.cleanup(
        "app-1",
        "cleanup-1",
        reason="success",
        trace_id="trace",
        keep_warm=True,
        next_case_at=datetime.now(UTC) + timedelta(seconds=5),
    )
    assert result["application_receipt"]["kept_warm"]
    assert adapter.alive and adapter.calls == []
    assert repo.get_session("app-1")["idle_deadline"]
    acquire(service)
    result = service.cleanup("app-1", "cleanup-2", reason="idle", trace_id="trace")
    assert result["status"] == "completed" and not adapter.alive


def test_incomplete_ownership_and_preexisting_document_adoption_are_rejected(
    lifecycle, tmp_path
):
    service, _, adapter = lifecycle
    record = session_record("unproven")
    record["launch_receipt"] = {"pid": 1234}
    with pytest.raises(ValueError, match="evidence"):
        service.register_session(record, trace_id="trace")
    lease = acquire(service)
    with pytest.raises(ValueError, match="creation evidence"):
        service.register_document(
            "app-1",
            lease["lease_id"],
            document(tmp_path, preexisted=True),
            trace_id="trace",
        )
    assert not adapter.calls


def test_immutable_cleanup_and_redacted_event_evidence(lifecycle):
    service, repo, _ = lifecycle
    acquire(service)
    receipt = service.cleanup(
        "app-1", "cleanup-1", reason="secret=hidden-value", trace_id="trace"
    )
    with sqlite3.connect(repo.db_path) as db:
        assert "hidden-value" not in "".join(
            row[0] for row in db.execute("SELECT record FROM native_application_events")
        )
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            db.execute("DELETE FROM native_application_cleanup")
    with pytest.raises(NativeApplicationConflict, match="immutable"):
        repo.record_cleanup({**receipt, "status": "invented"})


def test_explicit_cleanup_reconciliation_preserves_failed_receipt_and_allows_new_cleanup(
    lifecycle,
):
    service, repo, adapter = lifecycle
    lease = acquire(service)
    adapter.fail_quit = True
    failed = service.cleanup(
        "app-1", "cleanup-1", reason="native_failed", trace_id="trace"
    )
    assert failed["status"] == "cleanup_blocked"
    adapter.fail_quit = False
    service.reconcile("app-1", trace_id="restart")
    assert repo.get_session("app-1")["cleanup_in_progress"] == "cleanup-1"
    service.reconcile(
        "app-1", evidence_reference="healthy-native-probe.json", trace_id="recovery"
    )
    assert repo.get_session("app-1")["cleanup_in_progress"] is None
    assert repo.get_lease(lease["lease_id"])["state"] == "quarantined"
    succeeded = service.cleanup(
        "app-1", "cleanup-2", reason="fixed_native", trace_id="trace"
    )
    assert succeeded["status"] == "completed"
    assert repo.get_cleanup("app-1", "cleanup-1") == failed


def test_reconciliation_evidence_cannot_override_pid_reuse(lifecycle):
    service, repo, adapter = lifecycle
    acquire(service)
    adapter.creation_time = "2026-09-14T00:00:00Z"
    service.cleanup("app-1", "cleanup-1", reason="native_failed", trace_id="trace")
    result = service.reconcile(
        "app-1", evidence_reference="untrusted-claim.json", trace_id="trace"
    )
    assert result["cleanup_in_progress"] == "cleanup-1"
    assert result["state"] == "cleanup_blocked"
    assert not adapter.calls


@pytest.mark.parametrize("state", ["available", "released"])
def test_repository_cannot_clear_lease_after_cleanup_failure(lifecycle, state):
    service, repo, adapter = lifecycle
    lease = acquire(service)
    adapter.fail_quit = True
    service.cleanup("app-1", "cleanup-1", reason="native_failed", trace_id="trace")
    with pytest.raises(NativeApplicationConflict):
        repo.transition_lease(
            lease["lease_id"], state, reason="force_unlock", trace_id="trace"
        )
    assert repo.get_lease(lease["lease_id"])["state"] == "quarantined"
