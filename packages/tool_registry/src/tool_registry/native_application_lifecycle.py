"""Native application lifetime, separate from its MCP transport lifetime.

Adapters must bound every native call using the persisted session policy. Run
this synchronous service outside an API event loop (COM often requires its own
thread or subprocess). No process-name or forced termination exists here.
"""

from __future__ import annotations

import hashlib
import ntpath
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from core.native_application import (
    NativeApplicationConflict,
    NativeApplicationStore,
    utc_now,
)
from core.native_tracing import traced_native
from core.redaction import redact_text


DEFAULT_POLICY = {
    "startup_timeout_seconds": 120,
    "document_close_timeout_seconds": 30,
    "quit_timeout_seconds": 30,
    "idle_grace_seconds": 60,
}


class NativeApplicationAdapter(Protocol):
    """Exact session/document adapters; never attach and quit an arbitrary app."""

    def inspect(self, session: dict) -> dict: ...
    def save_document(self, session: dict, document: dict) -> dict: ...
    def close_document(self, session: dict, document: dict) -> dict: ...
    def quit_application(self, session: dict) -> dict: ...


def same_process(expected: dict, observed: dict | None) -> bool:
    """A live PID or executable alone is never ownership evidence."""
    if not observed:
        return False
    return (
        isinstance(expected.get("pid"), int)
        and expected["pid"] > 0
        and expected["pid"] == observed.get("pid")
        and bool(expected.get("creation_time"))
        and expected["creation_time"] == observed.get("creation_time")
        and bool(expected.get("executable"))
        and _path_key(expected["executable"])
        == _path_key(observed.get("executable", ""))
    )


def _path_key(path: str) -> str:
    # Native Windows receipt paths may use either slash style; POSIX paths
    # remain case-sensitive when used by an adapter on a different host.
    return (
        ntpath.normcase(ntpath.normpath(path))
        if ntpath.splitdrive(path)[0]
        else str(Path(path))
    )


def _document_matches(document: dict, observed: dict) -> bool:
    path = document.get("current_path") or document.get("path")
    return document["native_id"] == observed.get("native_id") and (
        path == observed.get("path")
        or bool(path and observed.get("path"))
        and _path_key(path) == _path_key(observed["path"])
    )


class NativeApplicationLifecycle:
    def __init__(
        self, repository: NativeApplicationStore, adapter: NativeApplicationAdapter
    ) -> None:
        self.repository = repository
        self.adapter = adapter

    @traced_native("native.application.manage.register")
    def register_session(self, record: dict, *, trace_id: str) -> dict:
        required = (
            "session_id",
            "resource_id",
            "app_kind",
            "version",
            "host",
            "ownership",
            "identity",
            "native_session_id",
        )
        if any(not record.get(key) for key in required):
            raise ValueError(
                "Native session requires exact process, host and application identities"
            )
        if record["ownership"] not in ("owned", "borrowed", "unknown"):
            raise ValueError("Invalid application ownership")
        if not same_process(record["identity"], record["identity"]):
            raise ValueError("Native process identity is incomplete")
        launch = record.get("launch_receipt", {})
        if record["ownership"] == "owned":
            dedicated = (
                launch.get("ownership_basis") == "dedicated_launch"
                and launch.get("baseline_absent") is True
            )
            adopted = launch.get("ownership_basis") == "exact_adoption" and bool(
                launch.get("authorization_reference")
            )
            if not (
                (dedicated or adopted)
                and launch.get("native_session_verified") is True
                and same_process(record["identity"], launch.get("identity"))
            ):
                raise ValueError(
                    "Owned application requires exact launch or authorized adoption evidence"
                )
        policy = {**DEFAULT_POLICY, **record.get("policy", {})}
        if any(
            not isinstance(policy[key], (int, float)) or policy[key] <= 0
            for key in DEFAULT_POLICY
        ):
            raise ValueError("Native lifecycle time bounds must be positive")
        # Runtime state cannot be imported as caller-supplied ownership proof.
        return self.repository.register_session(
            {
                **record,
                "launch_receipt": launch,
                "policy": policy,
                "state": "starting",
                "heartbeat_at": utc_now(),
                "idle_deadline": None,
                "lease_id": None,
                "active_operation": None,
                "cleanup_in_progress": None,
                "trace_id": trace_id,
            }
        )

    def _observe(self, session: dict) -> dict:
        observation = self.adapter.inspect(session)
        if observation.get("alive") is not True:
            raise NativeApplicationConflict(
                "Native process exit or liveness is unresolved"
            )
        if not same_process(session["identity"], observation.get("identity")):
            raise NativeApplicationConflict(
                "Native PID identity changed; possible PID reuse"
            )
        if observation.get("native_session_id") != session["native_session_id"]:
            raise NativeApplicationConflict("Native session identity does not match")
        if observation.get("version") != session["version"]:
            raise NativeApplicationConflict("Native application version does not match")
        if observation.get("endpoint_matches") is not True:
            raise NativeApplicationConflict("Native endpoint ownership is unresolved")
        if not observation.get("healthy") or observation.get("modal") is not False:
            raise NativeApplicationConflict(
                "Native application is unhealthy or has modal state"
            )
        if observation.get("document_state_known") is not True or not isinstance(
            observation.get("documents"), list
        ):
            raise NativeApplicationConflict("Native document state is unknown")
        if observation.get("active_operation") is not False:
            raise NativeApplicationConflict(
                "Native application has active or unknown work"
            )
        return observation

    def observe(self, session_id: str) -> dict:
        """Return a verified, read-only native observation for an orchestration seam."""
        return self._observe(self.repository.get_session(session_id))

    def _quarantine(self, session_id: str, reason: str, trace_id: str) -> dict:
        session = self.repository.get_session(session_id)
        session.update(
            state="cleanup_blocked", blocker=redact_text(reason), heartbeat_at=utc_now()
        )
        session = self.repository.update_session(
            session, kind="resource_quarantined", trace_id=trace_id
        )
        if session.get("lease_id"):
            self.repository.transition_lease(
                session["lease_id"], "quarantined", reason=reason, trace_id=trace_id
            )
        return session

    @traced_native("native.application.manage.acquire")
    def acquire(
        self,
        session_id: str,
        *,
        owner_id: str,
        case_id: str,
        attempt: str,
        trace_id: str,
    ) -> dict:
        session = self.repository.get_session(session_id)
        if session["ownership"] == "unknown":
            raise NativeApplicationConflict(
                "Unknown application ownership cannot be leased"
            )
        lease = {
            "lease_id": uuid4().hex,
            "resource_id": session["resource_id"],
            "session_id": session_id,
            "owner_id": owner_id,
            "case_id": case_id,
            "attempt": attempt,
            "state": "leased",
            "created_at": utc_now(),
            "trace_id": trace_id,
        }
        self.repository.acquire_lease(lease, expected_revision=session["revision"])
        try:
            session = self.repository.get_session(session_id)
            observed = self._observe(session)
            if session["ownership"] == "owned" and observed["documents"]:
                raise NativeApplicationConflict(
                    "Owned application is not empty at acquisition"
                )
            session.update(state="healthy", heartbeat_at=utc_now())
            self.repository.update_session(
                session, kind="lease_verified", trace_id=trace_id
            )
        except Exception as exc:
            self._quarantine(session_id, str(exc), trace_id)
            raise
        return lease

    def _leased(self, session_id: str, lease_id: str) -> dict:
        session = self.repository.get_session(session_id)
        lease = self.repository.get_lease(lease_id)
        if (
            session.get("lease_id") != lease_id
            or lease["session_id"] != session_id
            or lease["state"] != "leased"
            or session.get("cleanup_in_progress")
        ):
            raise NativeApplicationConflict(
                "Native operation requires its exclusive active lease"
            )
        return session

    def begin_operation(
        self, session_id: str, lease_id: str, operation_id: str, *, trace_id: str
    ) -> dict:
        session = self._leased(session_id, lease_id)
        if session.get("active_operation"):
            raise NativeApplicationConflict(
                "Previous native operation must be reconciled"
            )
        self._observe(session)
        session["active_operation"] = {
            "operation_id": operation_id,
            "state": "in_flight",
            "started_at": utc_now(),
        }
        return self.repository.update_session(
            session, kind="operation_started", trace_id=trace_id
        )

    def finish_operation(
        self,
        session_id: str,
        operation_id: str,
        *,
        outcome: str,
        evidence_reference: str,
        trace_id: str,
    ) -> dict:
        """Use unknown on timeout/cancellation; later reconciliation needs evidence."""
        if (
            outcome not in ("succeeded", "failed_known", "unknown")
            or not evidence_reference
        ):
            raise ValueError("Native outcome and retained evidence are required")
        session = self.repository.get_session(session_id)
        if (session.get("active_operation") or {}).get("operation_id") != operation_id:
            raise NativeApplicationConflict("Native operation identity does not match")
        session["last_operation"] = {
            **session["active_operation"],
            "outcome": outcome,
            "evidence_reference": evidence_reference,
            "finished_at": utc_now(),
        }
        if outcome == "unknown":
            session["active_operation"]["state"] = "unknown"
        else:
            session["active_operation"] = None
        session = self.repository.update_session(
            session, kind="operation_" + outcome, trace_id=trace_id
        )
        if outcome == "unknown":
            return self._quarantine(
                session_id, "Native operation outcome is unknown", trace_id
            )
        return session

    def register_document(
        self, session_id: str, lease_id: str, document: dict, *, trace_id: str
    ) -> None:
        self._leased(session_id, lease_id)
        if document.get("ownership") not in (
            "owned",
            "borrowed",
            "unknown",
        ) or not document.get("native_id"):
            raise ValueError("Document identity and ownership are required")
        lease = self.repository.get_lease(lease_id)
        if (document.get("case_id"), document.get("attempt")) != (
            lease["case_id"],
            lease["attempt"],
        ):
            raise NativeApplicationConflict(
                "Document does not belong to this case lease"
            )
        if document["ownership"] == "owned" and (
            document.get("preexisted") is not False
            or not document.get("creation_evidence")
        ):
            raise ValueError("Owned document requires campaign creation evidence")
        self.repository.put_document(
            session_id, {"closed": False, **document}, trace_id=trace_id
        )

    def reconcile(
        self, session_id: str, *, trace_id: str, evidence_reference: str | None = None
    ) -> dict:
        """Read-only startup recovery; expired heartbeats never release unknown work."""
        session = self.repository.get_session(session_id)
        if session.get("active_operation") or (
            session.get("cleanup_in_progress") and not evidence_reference
        ):
            return self._quarantine(
                session_id,
                "Interrupted operation or cleanup requires outcome evidence",
                trace_id,
            )
        try:
            observation = self.adapter.inspect(session)
            if observation.get("alive") is False:
                state = "exited"
            else:
                observation = self._observe(session)
                state = "idle"
            if session.get("cleanup_in_progress"):
                # The caller retains a diagnostic; the adapter independently
                # proves no work is active. Neither a new cleanup ID nor a
                # heartbeat expiry supplies that proof.
                documents = self.repository.list_documents(session_id)
                observed = observation.get("documents", []) if state != "exited" else []
                for document in documents:
                    if document["ownership"] != "owned" or document.get("closed"):
                        continue
                    matches = [
                        item for item in observed if _document_matches(document, item)
                    ]
                    if not matches:
                        if document.get("dirty") and not document.get(
                            "recovery_receipt"
                        ):
                            raise NativeApplicationConflict(
                                "Unresolved save or missing dirty document prevents recovery"
                            )
                        document.update(
                            closed=True,
                            close_receipt={
                                "reconciled_absent": True,
                                "evidence_reference": evidence_reference,
                            },
                        )
                        self.repository.put_document(
                            session_id, document, trace_id=trace_id
                        )
                    elif len(matches) != 1:
                        raise NativeApplicationConflict(
                            "Duplicate native document identity prevents recovery"
                        )
                session["last_reconciliation"] = {
                    "cleanup_id": session["cleanup_in_progress"],
                    "evidence_reference": evidence_reference,
                    "occurred_at": utc_now(),
                }
                session["cleanup_in_progress"] = None
            session.update(state=state, heartbeat_at=utc_now(), blocker=None)
            return self.repository.update_session(
                session, kind="session_reconciled", trace_id=trace_id
            )
        except Exception as exc:
            return self._quarantine(session_id, str(exc), trace_id)

    @traced_native("native.application.manage.cleanup")
    def cleanup(
        self,
        session_id: str,
        cleanup_id: str,
        *,
        reason: str,
        trace_id: str,
        keep_warm: bool = False,
        next_case_at: datetime | None = None,
    ) -> dict:
        """Idempotent cleanup, preserving user work and uncertain mutations.

        A repeated cleanup ID returns its immutable receipt. A crash in a native
        call leaves cleanup_in_progress persisted and cannot blindly replay it.
        """
        prior = self.repository.get_cleanup(session_id, cleanup_id)
        if prior:
            return prior
        session = self.repository.get_session(session_id)
        lease = (
            self.repository.get_lease(session["lease_id"])
            if session.get("lease_id")
            else {}
        )
        receipt = {
            "session_id": session_id,
            "cleanup_id": cleanup_id,
            "reason": reason,
            "ownership": session["ownership"],
            "identity": session["identity"],
            "case_id": lease.get("case_id"),
            "attempt": lease.get("attempt"),
            "document_receipts": [],
            "application_receipt": None,
            "trace_id": trace_id,
        }
        try:
            if session.get("active_operation") or session.get("cleanup_in_progress"):
                raise NativeApplicationConflict(
                    "Native work or interrupted cleanup requires reconciliation"
                )
            if session["ownership"] == "unknown":
                raise NativeApplicationConflict(
                    "Unknown ownership forbids native cleanup"
                )
            session.update(cleanup_in_progress=cleanup_id, state="closing")
            session = self.repository.update_session(
                session, kind="cleanup_started", trace_id=trace_id
            )
            observation = self.adapter.inspect(session)
            if observation.get("alive") is False:
                if any(
                    doc.get("dirty") and not doc.get("recovery_receipt")
                    for doc in self.repository.list_documents(session_id)
                    if doc["ownership"] == "owned"
                ):
                    raise NativeApplicationConflict(
                        "Exited application has unsaved owned work"
                    )
                final_state = "exited"
                receipt["application_receipt"] = {"already_exited": True}
            else:
                observation = self._observe(session)
                for document in self.repository.list_documents(session_id):
                    if document["ownership"] != "owned" or document.get("closed"):
                        continue
                    candidates = [
                        item
                        for item in observation["documents"]
                        if _document_matches(document, item)
                    ]
                    if len(candidates) != 1:
                        raise NativeApplicationConflict(
                            "Owned document presence is unresolved"
                        )
                    if candidates[0].get("dirty") is not False:
                        recovery_path = document.get("recovery_path")
                        if not recovery_path:
                            raise NativeApplicationConflict(
                                "Dirty document has no approved recovery path"
                            )
                        saved = self.adapter.save_document(session, document)
                        path = Path(recovery_path)
                        if (
                            saved.get("saved") is not True
                            or not saved.get("path")
                            or _path_key(saved["path"]) != _path_key(recovery_path)
                            or not path.is_file()
                            or path.stat().st_size == 0
                            or hashlib.sha256(path.read_bytes()).hexdigest()
                            != saved.get("sha256")
                        ):
                            raise NativeApplicationConflict(
                                "Native recovery save is not verified"
                            )
                        document["recovery_receipt"] = saved
                        document["current_path"] = recovery_path
                        document["dirty"] = False
                        self.repository.put_document(
                            session_id, document, trace_id=trace_id
                        )
                        observation = self._observe(session)
                    observed_doc = next(
                        (
                            item
                            for item in observation["documents"]
                            if _document_matches(document, item)
                        ),
                        None,
                    )
                    if observed_doc is None or observed_doc.get("dirty") is not False:
                        raise NativeApplicationConflict(
                            "Native document is not confirmed saved before close"
                        )
                    closed = self.adapter.close_document(session, document)
                    observation = self._observe(session)
                    if closed.get("closed") is not True or any(
                        _document_matches(document, item)
                        for item in observation["documents"]
                    ):
                        raise NativeApplicationConflict(
                            "Native document close is not verified"
                        )
                    document.update(closed=True, dirty=False, close_receipt=closed)
                    self.repository.put_document(
                        session_id, document, trace_id=trace_id
                    )
                    receipt["document_receipts"].append(document)
                if session["ownership"] == "borrowed":
                    receipt["application_receipt"] = {
                        "preserved_borrowed_application": True
                    }
                    final_state = "idle"
                else:
                    observation = self._observe(session)
                    if observation["documents"]:
                        raise NativeApplicationConflict(
                            "Unrelated or untracked native documents prevent quit"
                        )
                    deadline = datetime.now(UTC) + timedelta(
                        seconds=session["policy"]["idle_grace_seconds"]
                    )
                    warm = (
                        keep_warm
                        and next_case_at is not None
                        and datetime.now(UTC) <= next_case_at <= deadline
                    )
                    if warm:
                        final_state = "idle"
                        session["idle_deadline"] = deadline.isoformat()
                        receipt["application_receipt"] = {
                            "kept_warm": True,
                            "idle_deadline": session["idle_deadline"],
                        }
                    else:
                        receipt["application_receipt"] = self.adapter.quit_application(
                            session
                        )
                        exited = self.adapter.inspect(session)
                        if exited.get("alive") is not False or exited.get(
                            "endpoint_alive", False
                        ):
                            raise NativeApplicationConflict(
                                "Native process or endpoint exit is not verified"
                            )
                        final_state = "exited"
            session.update(
                state=final_state,
                cleanup_in_progress=None,
                heartbeat_at=utc_now(),
                blocker=None,
            )
            self.repository.update_session(
                session, kind="cleanup_finished", trace_id=trace_id
            )
            if lease:
                self.repository.transition_lease(
                    lease["lease_id"], "released", reason=reason, trace_id=trace_id
                )
            receipt["status"] = "completed"
        except Exception as exc:
            # A failed native cleanup is never escalated to a kill. Persist and
            # retain the lease so a restart cannot mistake it for free capacity.
            self._quarantine(session_id, str(exc), trace_id)
            receipt.update(status="cleanup_blocked", blocker=redact_text(exc))
        receipt["completed_at"] = utc_now()
        return self.repository.record_cleanup(receipt)
