"""Saved UI revisions and authoring jobs, scoped independently of run execution."""

from __future__ import annotations

from datetime import datetime
import re
import sqlite3

from core.process_interfaces import AuthoringJob, InterfaceRevision, ProcessUI
from core.process_validation import canonical_digest
from core.tracing import traced

from .process_input_repository import ProcessRecordConflict, encoded
from .state_store import connect_state_db

PROCESS_INTERFACE_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS process_uis (
        workspace_id TEXT NOT NULL, ui_id TEXT NOT NULL, payload_json TEXT NOT NULL,
        PRIMARY KEY(workspace_id,ui_id)
    )""",
    """CREATE TABLE IF NOT EXISTS process_ui_revisions (
        workspace_id TEXT NOT NULL, ui_id TEXT NOT NULL, revision_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        PRIMARY KEY(workspace_id,ui_id,revision_id),
        FOREIGN KEY(workspace_id,ui_id) REFERENCES process_uis(workspace_id,ui_id)
    )""",
    """CREATE TABLE IF NOT EXISTS process_ui_authoring_jobs (
        workspace_id TEXT NOT NULL, job_id TEXT NOT NULL, source_path TEXT NOT NULL,
        request_id TEXT NOT NULL, payload_json TEXT NOT NULL,
        PRIMARY KEY(workspace_id,job_id),
        UNIQUE(workspace_id,source_path,request_id)
    )""",
    *(
        f"""CREATE TRIGGER IF NOT EXISTS process_ui_revisions_no_{operation.lower()}
        BEFORE {operation} ON process_ui_revisions
        BEGIN SELECT RAISE(ABORT, 'Process UI revision is immutable'); END"""
        for operation in ("UPDATE", "DELETE")
    ),
)

PROCESS_AUTHORING_RECORD_SCHEMA = (
    """CREATE TABLE IF NOT EXISTS process_ui_authoring_records (
        workspace_id TEXT NOT NULL, job_id TEXT NOT NULL, record_key TEXT NOT NULL,
        payload_json TEXT NOT NULL, PRIMARY KEY(workspace_id,job_id,record_key),
        FOREIGN KEY(workspace_id,job_id)
            REFERENCES process_ui_authoring_jobs(workspace_id,job_id)
    )""",
    *(
        f"""CREATE TRIGGER IF NOT EXISTS process_ui_authoring_records_no_{operation.lower()}
        BEFORE {operation} ON process_ui_authoring_records
        BEGIN SELECT RAISE(ABORT, 'Authoring provenance is immutable'); END"""
        for operation in ("UPDATE", "DELETE")
    ),
)

_JOB_TRANSITIONS = {
    "queued": {"resolving", "cancelled", "failed"},
    "resolving": {"generating", "cancelled", "failed"},
    "generating": {"validating", "cancelled", "failed"},
    "validating": {"building", "generating", "cancelled", "failed"},
    "building": {"preview_ready", "generating", "cancelled", "failed"},
    "preview_ready": {"saved", "cancelled", "failed"},
    "saved": set(),
    "failed": set(),
    "cancelled": set(),
}


class ProcessInterfaceRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        with connect_state_db(db_path, ensure_parent=True) as db:
            for statement in (
                *PROCESS_INTERFACE_SCHEMA,
                *PROCESS_AUTHORING_RECORD_SCHEMA,
            ):
                db.execute(statement)

    @traced("process.ui.create")
    def create_ui(self, ui: ProcessUI) -> ProcessUI:
        raw = encoded(ui)
        if ui.active_revision is not None:
            raise ProcessRecordConflict(
                "New interface cannot select an unsaved revision"
            )
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_json FROM process_uis WHERE workspace_id=? AND ui_id=?",
                (ui.process.workspace_id, ui.ui_id),
            ).fetchone()
            if row:
                if row["payload_json"] != raw:
                    raise ProcessRecordConflict("Interface identity already exists")
                return ProcessUI.model_validate_json(row["payload_json"])
            db.execute(
                "INSERT INTO process_uis VALUES (?,?,?)",
                (ui.process.workspace_id, ui.ui_id, raw),
            )
        return ProcessUI.model_validate_json(raw)

    @traced("process.ui.read")
    def get_ui(self, workspace_id: str, ui_id: str) -> ProcessUI:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_uis WHERE workspace_id=? AND ui_id=?",
                (workspace_id, ui_id),
            ).fetchone()
        if not row:
            raise KeyError("Interface not found in workspace")
        return ProcessUI.model_validate_json(row["payload_json"])

    def list_uis(
        self, workspace_id: str, source_path: str, *, limit: int = 256
    ) -> tuple[ProcessUI, ...]:
        """Saved and draft UI identities for one exact process association."""
        if not 1 <= limit <= 256:
            raise ValueError("Interface page must contain 1 to 256 items")
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT payload_json FROM process_uis WHERE workspace_id=? "
                "AND json_extract(payload_json, '$.process.source_path')=? "
                "ORDER BY rowid DESC LIMIT ?",
                (workspace_id, source_path, limit),
            ).fetchall()
        return tuple(ProcessUI.model_validate_json(row["payload_json"]) for row in rows)

    @traced("process.ui.revision.save")
    def save_revision(
        self, workspace_id: str, revision: InterfaceRevision
    ) -> InterfaceRevision:
        raw = encoded(revision)
        manifest = revision.manifest
        if manifest.process.workspace_id != workspace_id:
            raise ProcessRecordConflict("Revision belongs to another workspace")
        scope = (workspace_id, manifest.ui_id, manifest.revision_id)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            ui_row = db.execute(
                "SELECT payload_json FROM process_uis WHERE workspace_id=? AND ui_id=?",
                scope[:2],
            ).fetchone()
            if not ui_row:
                raise ProcessRecordConflict(
                    "Revision requires an existing scoped interface"
                )
            ui = ProcessUI.model_validate_json(ui_row["payload_json"])
            if ui.archived or ui.process.source_path != manifest.process.source_path:
                raise ProcessRecordConflict(
                    "Revision cannot change the interface's associated process"
                )
            prior = db.execute(
                "SELECT payload_json FROM process_ui_revisions WHERE workspace_id=? AND ui_id=? AND revision_id=?",
                scope,
            ).fetchone()
            if prior:
                if prior["payload_json"] != raw:
                    raise ProcessRecordConflict(
                        "Saved revision identity already has different content"
                    )
                return InterfaceRevision.model_validate_json(prior["payload_json"])
            if (
                manifest.parent_revision
                and not db.execute(
                    "SELECT 1 FROM process_ui_revisions WHERE workspace_id=? AND ui_id=? AND revision_id=?",
                    (*scope[:2], manifest.parent_revision),
                ).fetchone()
            ):
                raise ProcessRecordConflict(
                    "Parent revision must belong to this saved interface"
                )
            if manifest.parent_revision == manifest.revision_id:
                raise ProcessRecordConflict("Revision cannot be its own parent")
            db.execute(
                "INSERT INTO process_ui_revisions VALUES (?,?,?,?)", (*scope, raw)
            )
        return InterfaceRevision.model_validate_json(raw)

    @traced("process.ui.revision.read")
    def get_revision(
        self, workspace_id: str, ui_id: str, revision_id: str
    ) -> InterfaceRevision:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_ui_revisions WHERE workspace_id=? AND ui_id=? AND revision_id=?",
                (workspace_id, ui_id, revision_id),
            ).fetchone()
        if not row:
            raise KeyError("Saved revision not found in interface scope")
        return InterfaceRevision.model_validate_json(row["payload_json"])

    def list_revisions(
        self, workspace_id: str, ui_id: str, *, limit: int = 256
    ) -> tuple[InterfaceRevision, ...]:
        if not 1 <= limit <= 256:
            raise ValueError("Revision page must contain 1 to 256 items")
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT payload_json FROM process_ui_revisions WHERE workspace_id=? AND ui_id=? ORDER BY rowid DESC LIMIT ?",
                (workspace_id, ui_id, limit),
            ).fetchall()
        return tuple(
            InterfaceRevision.model_validate_json(row["payload_json"]) for row in rows
        )

    @traced("process.ui.activate")
    def activate(
        self,
        workspace_id: str,
        ui_id: str,
        revision_id: str,
        *,
        expected_revision: str | None,
        updated_at: str,
    ) -> ProcessUI:
        # Compatibility/grant checks belong to the owning service immediately
        # before this CAS. Selecting metadata cannot grant process authority.
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_json FROM process_uis WHERE workspace_id=? AND ui_id=?",
                (workspace_id, ui_id),
            ).fetchone()
            if not row:
                raise KeyError("Interface not found in workspace")
            ui = ProcessUI.model_validate_json(row["payload_json"])
            if ui.archived or ui.active_revision != expected_revision:
                raise ProcessRecordConflict("Interface changed before activation")
            if not db.execute(
                "SELECT 1 FROM process_ui_revisions WHERE workspace_id=? AND ui_id=? AND revision_id=?",
                (workspace_id, ui_id, revision_id),
            ).fetchone():
                raise ProcessRecordConflict(
                    "Activation requires an exact saved revision"
                )
            changed = ProcessUI.model_validate(
                {
                    **ui.model_dump(),
                    "active_revision": revision_id,
                    "updated_at": updated_at,
                }
            )
            db.execute(
                "UPDATE process_uis SET payload_json=? WHERE workspace_id=? AND ui_id=?",
                (encoded(changed), workspace_id, ui_id),
            )
        return changed

    @traced("process.ui.authoring.create")
    def create_job(self, job: AuthoringJob) -> tuple[AuthoringJob, bool]:
        raw = encoded(job)
        if job.state != "queued" or job.repair_attempt or job.revision_id:
            raise ProcessRecordConflict("New authoring job must begin queued")
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_json FROM process_ui_authoring_jobs WHERE workspace_id=? AND source_path=? AND request_id=?",
                (job.process.workspace_id, job.process.source_path, job.request_id),
            ).fetchone()
            if row:
                prior = AuthoringJob.model_validate_json(row["payload_json"])
                if any(
                    getattr(prior, field) != getattr(job, field)
                    for field in (
                        "request_digest",
                        "process",
                        "base_revision",
                        "role_resolution",
                    )
                ):
                    raise ProcessRecordConflict(
                        "Authoring request identity already has different content"
                    )
                return prior, False
            try:
                db.execute(
                    "INSERT INTO process_ui_authoring_jobs VALUES (?,?,?,?,?)",
                    (
                        job.process.workspace_id,
                        job.job_id,
                        job.process.source_path,
                        job.request_id,
                        raw,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ProcessRecordConflict(
                    "Authoring job identity already exists"
                ) from exc
        return AuthoringJob.model_validate_json(raw), True

    @traced("process.ui.authoring.read")
    def get_job(self, workspace_id: str, job_id: str) -> AuthoringJob:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_ui_authoring_jobs WHERE workspace_id=? AND job_id=?",
                (workspace_id, job_id),
            ).fetchone()
        if not row:
            raise KeyError("Authoring job not found in workspace")
        return AuthoringJob.model_validate_json(row["payload_json"])

    def job_for_request(
        self, workspace_id: str, source_path: str, request_id: str
    ) -> AuthoringJob | None:
        """Reconcile an acknowledgement before resolving a model or allocating work."""
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_ui_authoring_jobs WHERE workspace_id=? AND source_path=? AND request_id=?",
                (workspace_id, source_path, request_id),
            ).fetchone()
        return AuthoringJob.model_validate_json(row["payload_json"]) if row else None

    def retain_authoring_record(
        self, workspace_id: str, job_id: str, record_key: str, payload: dict
    ) -> dict:
        """Immutable bounded request/attempt/artifact provenance, never credentials."""
        import json
        from core.process_validation import canonical_json

        raw = canonical_json(payload)
        if len(raw.encode("utf-8")) > 2_200_000 or (
            record_key
            not in {
                "request",
                "build-0",
                "build-1",
                "build-2",
                "attempt-0",
                "attempt-1",
                "attempt-2",
                "built",
                "preview",
            }
            and not re.fullmatch(r"view-start-[0-9a-f]{64}", record_key)
        ):
            raise ValueError("Unsupported or oversized authoring provenance record")
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute(
                "SELECT 1 FROM process_ui_authoring_jobs WHERE workspace_id=? AND job_id=?",
                (workspace_id, job_id),
            ).fetchone():
                raise ProcessRecordConflict("Authoring record requires its scoped job")
            existing = db.execute(
                "SELECT payload_json FROM process_ui_authoring_records WHERE workspace_id=? AND job_id=? AND record_key=?",
                (workspace_id, job_id, record_key),
            ).fetchone()
            if existing:
                if existing["payload_json"] != raw:
                    raise ProcessRecordConflict("Authoring provenance is immutable")
                return json.loads(existing["payload_json"])
            db.execute(
                "INSERT INTO process_ui_authoring_records VALUES (?,?,?,?)",
                (workspace_id, job_id, record_key, raw),
            )
        return json.loads(raw)

    def get_authoring_record(
        self, workspace_id: str, job_id: str, record_key: str
    ) -> dict:
        import json

        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_ui_authoring_records WHERE workspace_id=? AND job_id=? AND record_key=?",
                (workspace_id, job_id, record_key),
            ).fetchone()
        if not row:
            raise KeyError("Authoring provenance is unavailable in this workspace")
        return json.loads(row["payload_json"])

    def job_for_revision(
        self, workspace_id: str, ui_id: str, revision_id: str
    ) -> AuthoringJob:
        """Exact built revision provenance; no unscoped revision-name lookup."""
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT jobs.payload_json FROM process_ui_authoring_jobs AS jobs "
                "JOIN process_ui_authoring_records AS records "
                "ON jobs.workspace_id=records.workspace_id AND jobs.job_id=records.job_id "
                "WHERE jobs.workspace_id=? AND records.record_key='built' "
                "AND json_extract(records.payload_json,'$.manifest.ui_id')=? "
                "AND json_extract(records.payload_json,'$.manifest.revision_id')=? LIMIT 2",
                (workspace_id, ui_id, revision_id),
            ).fetchall()
        if not rows:
            raise KeyError("Revision has no retained authoring provenance")
        if len(rows) != 1:
            raise ProcessRecordConflict("Revision provenance is ambiguous")
        return AuthoringJob.model_validate_json(rows[0]["payload_json"])

    @traced("process.ui.authoring.update")
    def update_job(self, job: AuthoringJob, *, expected_digest: str) -> AuthoringJob:
        raw = encoded(job)
        mutable = {
            "state",
            "updated_at",
            "repair_attempt",
            "diagnostics",
            "revision_id",
        }
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_json FROM process_ui_authoring_jobs WHERE workspace_id=? AND job_id=?",
                (job.process.workspace_id, job.job_id),
            ).fetchone()
            if not row:
                raise ProcessRecordConflict("Authoring identity changed or is absent")
            prior = AuthoringJob.model_validate_json(row["payload_json"])
            if canonical_digest(prior) != expected_digest or prior.model_dump(
                exclude=mutable
            ) != job.model_dump(exclude=mutable):
                raise ProcessRecordConflict("Authoring job changed before update")
            if job.state not in _JOB_TRANSITIONS[prior.state]:
                raise ProcessRecordConflict("Unsupported authoring state transition")
            if datetime.fromisoformat(job.updated_at) < datetime.fromisoformat(
                prior.updated_at
            ):
                raise ProcessRecordConflict(
                    "Authoring observation cannot move backwards"
                )
            repairing = job.state == "generating" and prior.state in {
                "validating",
                "building",
            }
            if job.repair_attempt != prior.repair_attempt + int(repairing):
                raise ProcessRecordConflict(
                    "Repair budget must advance exactly once for a correction"
                )
            if prior.revision_id and job.revision_id != prior.revision_id:
                raise ProcessRecordConflict(
                    "Built revision identity cannot be replaced in this job"
                )
            db.execute(
                "UPDATE process_ui_authoring_jobs SET payload_json=? WHERE workspace_id=? AND job_id=?",
                (raw, job.process.workspace_id, job.job_id),
            )
        return AuthoringJob.model_validate_json(raw)
