"""Additive, workspace-scoped validation ledger; terminal evidence is immutable."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from core.process_validation import (
    Assessment,
    Lifecycle,
    ReviewDecision,
    SubjectBinding,
    ValidationRequest,
    canonical_digest,
    canonical_json,
)
from core.tracing import traced

from .state_store import connect_state_db

_SCHEMA = """
CREATE TABLE IF NOT EXISTS process_validation_schema (version INTEGER PRIMARY KEY);
INSERT OR IGNORE INTO process_validation_schema VALUES (1);
CREATE TABLE IF NOT EXISTS process_validation_attempts (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
 workspace_id TEXT NOT NULL, invocation_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,
 stream_key TEXT NOT NULL, request_digest TEXT NOT NULL, request_json TEXT NOT NULL,
 state TEXT NOT NULL CHECK(state IN ('queued','running','completed','blocked','error','cancelled')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL, terminal_reason TEXT,
 assessment_id TEXT,
 UNIQUE(workspace_id, invocation_id, idempotency_key)
);
CREATE INDEX IF NOT EXISTS process_validation_current
 ON process_validation_attempts(workspace_id, stream_key, sequence DESC);
CREATE TABLE IF NOT EXISTS process_validation_assessments (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT, id TEXT NOT NULL UNIQUE,
 attempt_id TEXT NOT NULL REFERENCES process_validation_attempts(id),
 workspace_id TEXT NOT NULL, digest TEXT NOT NULL, payload_json TEXT NOT NULL,
 supersedes TEXT REFERENCES process_validation_assessments(id)
);
CREATE TABLE IF NOT EXISTS process_validation_reviews (
 id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL,
 assessment_id TEXT NOT NULL REFERENCES process_validation_assessments(id),
 payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS process_validation_outputs (
 workspace_id TEXT NOT NULL, id TEXT NOT NULL,
 run_id TEXT NOT NULL, step_id TEXT NOT NULL, attempt INTEGER NOT NULL,
 output_port TEXT NOT NULL, payload_json TEXT NOT NULL,
 PRIMARY KEY(workspace_id,id),
 UNIQUE(workspace_id,run_id,step_id,attempt,output_port)
);
"""
_TERMINAL = {"completed", "blocked", "error", "cancelled"}
_MAX_RECORD_BYTES = 16 * 1024 * 1024


class ValidationConflict(ValueError):
    """An identity or state transition conflicts with retained evidence."""


@dataclass(frozen=True)
class AttemptRecord:
    id: str
    sequence: int
    stream_key: str
    request: ValidationRequest
    state: Lifecycle
    created_at: str
    updated_at: str
    terminal_reason: str | None
    assessment_id: str | None


def _now():
    return datetime.now(timezone.utc).isoformat()


def _payload(value):
    raw = canonical_json(value)
    if len(raw.encode("utf-8")) > _MAX_RECORD_BYTES:
        raise ValueError("Validation record exceeds 16 MiB")
    return raw


def _stream_key(request):
    # Versions/subject hashes are intentionally absent: a newer changed or
    # unfinished check supersedes the old one, even if it never reaches a pass.
    return canonical_digest(
        {
            "run_id": request.run_id,
            "check": request.check_step_id or request.invocation_id,
        }
    )


def _record(row):
    return AttemptRecord(
        id=row["id"],
        sequence=row["sequence"],
        stream_key=row["stream_key"],
        request=ValidationRequest.model_validate_json(row["request_json"]),
        state=row["state"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        terminal_reason=row["terminal_reason"],
        assessment_id=row["assessment_id"],
    )


class ProcessValidationRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        with connect_state_db(db_path, ensure_parent=True) as db:
            db.executescript(_SCHEMA)

    def register_output(self, workspace_id: str, subject: SubjectBinding):
        """Only the canonical runner registers an actual completed output revision."""
        subject = SubjectBinding.model_validate_json(subject.model_dump_json())
        raw = _payload(subject)
        owner = subject.producer
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_json FROM process_validation_outputs WHERE workspace_id=? AND run_id=? AND step_id=? AND attempt=? AND output_port=?",
                (
                    workspace_id,
                    owner.run_id,
                    owner.step_id,
                    owner.attempt,
                    owner.output_port,
                ),
            ).fetchone()
            if row:
                if row["payload_json"] != raw:
                    raise ValidationConflict(
                        "Completed output revision cannot be replaced"
                    )
                return
            db.execute(
                "INSERT INTO process_validation_outputs VALUES (?,?,?,?,?,?,?)",
                (
                    workspace_id,
                    subject.id,
                    owner.run_id,
                    owner.step_id,
                    owner.attempt,
                    owner.output_port,
                    raw,
                ),
            )

    def output(self, workspace_id: str, subject_id: str) -> SubjectBinding:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_validation_outputs WHERE workspace_id=? AND id=?",
                (workspace_id, subject_id),
            ).fetchone()
            if row is None:
                raise KeyError("Producer output not found in this workspace")
            return SubjectBinding.model_validate_json(row["payload_json"])

    def output_is_current(self, workspace_id: str, subject: SubjectBinding) -> bool:
        owner = subject.producer
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_validation_outputs WHERE workspace_id=? AND run_id=? AND step_id=? AND output_port=? ORDER BY attempt DESC LIMIT 1",
                (workspace_id, owner.run_id, owner.step_id, owner.output_port),
            ).fetchone()
            if row is None:
                return False
            actual = SubjectBinding.model_validate_json(row["payload_json"])
            # A profile assigns a semantic role; it cannot rewrite provenance,
            # content, representation, revision or the registered output ID.
            return actual.model_copy(update={"role": subject.role}) == subject

    @traced("db.process_validation.create")
    def create(self, request: ValidationRequest) -> tuple[AttemptRecord, bool]:
        raw, digest = _payload(request), canonical_digest(request)
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM process_validation_attempts WHERE workspace_id=? AND invocation_id=? AND idempotency_key=?",
                (request.workspace_id, request.invocation_id, request.idempotency_key),
            ).fetchone()
            if row:
                if row["request_digest"] != digest:
                    raise ValidationConflict(
                        "Idempotency key was used for different input"
                    )
                return _record(row), False
            identifier, now = uuid4().hex, _now()
            db.execute(
                "INSERT INTO process_validation_attempts (id,workspace_id,invocation_id,idempotency_key,stream_key,request_digest,request_json,state,created_at,updated_at) VALUES (?,?,?,?,?,?,?,'queued',?,?)",
                (
                    identifier,
                    request.workspace_id,
                    request.invocation_id,
                    request.idempotency_key,
                    _stream_key(request),
                    digest,
                    raw,
                    now,
                    now,
                ),
            )
            row = db.execute(
                "SELECT * FROM process_validation_attempts WHERE id=?", (identifier,)
            ).fetchone()
            return _record(row), True

    @traced("db.process_validation.get")
    def get(self, workspace_id: str, attempt_id: str) -> AttemptRecord:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = self._get(db, workspace_id, attempt_id)
            return _record(row)

    @staticmethod
    def _get(db, workspace_id, attempt_id):
        row = db.execute(
            "SELECT * FROM process_validation_attempts WHERE workspace_id=? AND id=?",
            (workspace_id, attempt_id),
        ).fetchone()
        if row is None:
            raise KeyError("Validation attempt not found in this workspace")
        return row

    @traced("db.process_validation.start")
    def start(self, workspace_id: str, attempt_id: str) -> AttemptRecord:
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._get(db, workspace_id, attempt_id)
            if row["state"] != "queued":
                raise ValidationConflict("Only a queued attempt can be started")
            db.execute(
                "UPDATE process_validation_attempts SET state='running',updated_at=? WHERE id=?",
                (_now(), attempt_id),
            )
        return self.get(workspace_id, attempt_id)

    @traced("db.process_validation.resume")
    def resume(self, request: ValidationRequest, attempt_id: str) -> AttemptRecord:
        record = self.get(request.workspace_id, attempt_id)
        if record.state not in {"queued", "running"} or canonical_digest(
            record.request
        ) != canonical_digest(request):
            raise ValidationConflict(
                "Resume requires unchanged nonterminal request identity"
            )
        # Reader/resource ownership is checked by the application service.
        return record

    @traced("db.process_validation.finalize")
    def finalize(self, assessment: Assessment) -> AttemptRecord:
        # Revalidate rather than trusting an unchecked model_copy from a caller.
        assessment = Assessment.model_validate_json(_payload(assessment))
        raw = _payload(assessment)
        request = assessment.request
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._get(db, request.workspace_id, assessment.attempt_id)
            if row["request_digest"] != canonical_digest(request):
                raise ValidationConflict(
                    "Assessment does not match the retained request"
                )
            if row["state"] in _TERMINAL:
                previous = db.execute(
                    "SELECT payload_json FROM process_validation_assessments WHERE id=? AND workspace_id=?",
                    (row["assessment_id"], request.workspace_id),
                ).fetchone()
                if previous and previous["payload_json"] == raw:
                    return _record(row)
                raise ValidationConflict(
                    "Terminal attempt evidence is immutable; create a new attempt"
                )
            if row["state"] != "running" or assessment.supersedes:
                raise ValidationConflict(
                    "Initial finalization requires a running attempt"
                )
            state = (
                "cancelled"
                if any(f.code == "validation.cancelled" for f in assessment.findings)
                else "error"
                if any(c.state == "error" for c in assessment.checks)
                else "blocked"
                if not assessment.subject_current
                or any(c.state == "blocked" for c in assessment.checks)
                else "completed"
            )
            db.execute(
                "INSERT INTO process_validation_assessments (id,attempt_id,workspace_id,digest,payload_json) VALUES (?,?,?,?,?)",
                (
                    assessment.id,
                    assessment.attempt_id,
                    request.workspace_id,
                    canonical_digest(assessment),
                    raw,
                ),
            )
            db.execute(
                "UPDATE process_validation_attempts SET state=?,updated_at=?,assessment_id=? WHERE id=?",
                (state, _now(), assessment.id, assessment.attempt_id),
            )
        return self.get(request.workspace_id, assessment.attempt_id)

    @traced("db.process_validation.stop")
    def stop(
        self, workspace_id: str, attempt_id: str, state: str, reason: str
    ) -> AttemptRecord:
        if (
            state not in {"blocked", "error", "cancelled"}
            or not reason.strip()
            or len(reason) > 8192
        ):
            raise ValueError(
                "Stop requires a bounded reason and non-success terminal state"
            )
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._get(db, workspace_id, attempt_id)
            if row["state"] in _TERMINAL:
                raise ValidationConflict("Terminal attempt cannot be changed")
            db.execute(
                "UPDATE process_validation_attempts SET state=?,updated_at=?,terminal_reason=? WHERE id=?",
                (state, _now(), reason, attempt_id),
            )
        return self.get(workspace_id, attempt_id)

    @traced("db.process_validation.current")
    def current(self, workspace_id: str, stream_key: str) -> AttemptRecord | None:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT * FROM process_validation_attempts WHERE workspace_id=? AND stream_key=? ORDER BY sequence DESC LIMIT 1",
                (workspace_id, stream_key),
            ).fetchone()
            if row is None:
                return None
            record = _record(row)
            # Late reviews append an assessment; retain the initial terminal
            # attempt as-is and project its latest assessment at query time.
            latest = db.execute(
                "SELECT id FROM process_validation_assessments WHERE workspace_id=? AND attempt_id=? ORDER BY sequence DESC LIMIT 1",
                (workspace_id, record.id),
            ).fetchone()
            if latest and latest["id"] != record.assessment_id:
                from dataclasses import replace

                record = replace(record, assessment_id=latest["id"])
            return record

    @traced("db.process_validation.assessment")
    def assessment(self, workspace_id: str, assessment_id: str) -> Assessment:
        with connect_state_db(self.db_path, read_only=True) as db:
            row = db.execute(
                "SELECT payload_json FROM process_validation_assessments WHERE workspace_id=? AND id=?",
                (workspace_id, assessment_id),
            ).fetchone()
            if row is None:
                raise KeyError("Validation assessment not found in this workspace")
            return Assessment.model_validate_json(row["payload_json"])

    def assessment_successors(
        self, workspace_id: str, assessment_id: str
    ) -> tuple[str, ...]:
        """Return the immutable supersession chain after an assessment."""
        with connect_state_db(self.db_path, read_only=True) as db:
            rows = db.execute(
                "SELECT id,supersedes FROM process_validation_assessments WHERE workspace_id=? ORDER BY sequence",
                (workspace_id,),
            ).fetchall()
        by_parent = {row["supersedes"]: row["id"] for row in rows if row["supersedes"]}
        successors = []
        current = assessment_id
        while current in by_parent:
            current = by_parent[current]
            successors.append(current)
        return tuple(successors)

    @traced("db.process_validation.review")
    def append_review(self, decision: ReviewDecision, revised: Assessment) -> None:
        decision = ReviewDecision.model_validate_json(_payload(decision))
        revised = Assessment.model_validate_json(_payload(revised))
        # Authenticated actor authority is established at the application boundary.
        original = self.assessment(decision.workspace_id, decision.assessment_id)
        if canonical_digest(original) != decision.assessment_digest:
            raise ValidationConflict("Review subject digest changed")
        if (
            revised.supersedes != original.id
            or revised.attempt_id != original.attempt_id
            or revised.request != original.request
            or revised.profile != original.profile
            or revised.measurements != original.measurements
            or decision.id not in revised.review_ids
        ):
            raise ValidationConflict(
                "Late review must append to the exact original subject"
            )
        if not any(
            r.id == decision.requirement_id and r.review_required
            for r in original.profile.baseline.requirements
        ):
            raise ValidationConflict("Requirement does not permit a review decision")
        allowed = {
            check.id
            for check in original.profile.checks
            if check.constraint.operator == "review"
            and decision.requirement_id in check.requirement_ids
        }
        old_checks = {check.check_id: check for check in original.checks}
        if {check.check_id for check in revised.checks} != set(old_checks):
            raise ValidationConflict("Review cannot add or remove checks")
        for check in revised.checks:
            if check.check_id not in allowed and check != old_checks[check.check_id]:
                raise ValidationConflict("Review cannot change measured checks")
            if check.check_id in allowed and (
                check.state != ("pass" if decision.decision == "approved" else "fail")
                or decision.id not in check.evidence_refs
            ):
                raise ValidationConflict(
                    "Review outcome must match the recorded decision"
                )
        if set(revised.review_ids) != set(original.review_ids) | {decision.id}:
            raise ValidationConflict("Review history must be retained")
        if tuple(f for f in revised.findings if f.check_id not in allowed) != tuple(
            f for f in original.findings if f.check_id not in allowed
        ):
            raise ValidationConflict("Review cannot remove unrelated findings")
        with connect_state_db(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            attempt = self._get(db, decision.workspace_id, original.attempt_id)
            current = db.execute(
                "SELECT id FROM process_validation_attempts WHERE workspace_id=? AND stream_key=? ORDER BY sequence DESC LIMIT 1",
                (decision.workspace_id, attempt["stream_key"]),
            ).fetchone()
            if current["id"] != original.attempt_id:
                raise ValidationConflict("Review attempt is no longer current")
            latest = db.execute(
                "SELECT id FROM process_validation_assessments WHERE workspace_id=? AND attempt_id=? ORDER BY sequence DESC LIMIT 1",
                (decision.workspace_id, original.attempt_id),
            ).fetchone()
            if latest is None or latest["id"] != original.id:
                raise ValidationConflict("Review assessment is no longer current")
            db.execute(
                "INSERT INTO process_validation_reviews VALUES (?,?,?,?)",
                (decision.id, decision.workspace_id, original.id, _payload(decision)),
            )
            db.execute(
                "INSERT INTO process_validation_assessments (id,attempt_id,workspace_id,digest,payload_json,supersedes) VALUES (?,?,?,?,?,?)",
                (
                    revised.id,
                    revised.attempt_id,
                    decision.workspace_id,
                    canonical_digest(revised),
                    _payload(revised),
                    original.id,
                ),
            )
