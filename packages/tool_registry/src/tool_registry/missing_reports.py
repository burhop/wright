from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlsplit, urlunsplit

from .capability_models import MissingCapabilityReport


class MissingCapabilityReportError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int = 400) -> None:
        self.code = code
        self.safe_message = message
        self.status_code = status_code
        super().__init__(message)


_TRANSITIONS: dict[str, frozenset[str]] = {
    "submitted": frozenset({"exported", "under_review", "closed"}),
    "exported": frozenset({"under_review", "closed"}),
    "under_review": frozenset({"matched", "closed"}),
    "matched": frozenset({"closed"}),
    "closed": frozenset(),
}


def _timestamp(value: datetime) -> int:
    if value.tzinfo is None:
        raise MissingCapabilityReportError(
            "report_timestamp_invalid", "Report timestamps must include a timezone."
        )
    return int(value.timestamp())


def _datetime(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=UTC)


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def _connection(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path), factory=_ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _safe_source_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    try:
        parsed = urlsplit(value.strip())
    except ValueError as error:
        raise MissingCapabilityReportError(
            "report_source_invalid", "Source URL is not valid.", status_code=422
        ) from error
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise MissingCapabilityReportError(
            "report_source_invalid",
            "Source URL must use HTTP or HTTPS.",
            status_code=422,
        )
    if parsed.username or parsed.password:
        raise MissingCapabilityReportError(
            "report_source_contains_credentials",
            "Source URL cannot contain credentials.",
            status_code=422,
        )
    # Query strings and fragments can carry credentials and are not required to
    # identify a publisher source. Keep only the stable public location.
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path, "", ""))


def _row_to_report(row: sqlite3.Row) -> MissingCapabilityReport:
    return MissingCapabilityReport(
        report_id=row["report_id"],
        name=row["name"],
        vendor=row["vendor"],
        source_url=row["source_url"],
        domains=json.loads(row["domains_json"]),
        expected_task=row["expected_task"],
        platform=row["platform"],
        host_application=row["host_application"],
        notes=row["notes"],
        search_context=json.loads(row["search_context_json"]),
        reporter=row["reporter"],
        created_at=_datetime(row["created_at"]),
        updated_at=_datetime(row["updated_at"]),
        state=row["state"],
        matched_capability_id=row["matched_capability_id"],
    )


def submit_missing_capability_report(
    database_path: str | Path,
    *,
    name: str,
    vendor: str,
    domains: Iterable[str],
    expected_task: str,
    reporter: str,
    source_url: str | None = None,
    platform: str | None = None,
    host_application: str | None = None,
    notes: str | None = None,
    search_context: Mapping[str, Any] | None = None,
    idempotency_key: str | None = None,
    now: datetime | None = None,
) -> MissingCapabilityReport:
    observed_at = now or datetime.now(UTC)
    clean_name = name.strip()
    clean_vendor = vendor.strip() or "Unknown"
    clean_task = expected_task.strip()
    clean_domains = [
        str(domain).strip().lower() for domain in domains if str(domain).strip()
    ]
    if not clean_name or not clean_task or not clean_domains:
        raise MissingCapabilityReportError(
            "report_required_fields_missing",
            "Name, engineering domain, and expected task are required.",
            status_code=422,
        )
    if idempotency_key is not None:
        clean_key = idempotency_key.strip()
        if not clean_key or len(clean_key) > 200:
            raise MissingCapabilityReportError(
                "report_idempotency_key_invalid",
                "Idempotency key must be between 1 and 200 characters.",
                status_code=422,
            )
        report_id = (
            "report-"
            + hashlib.sha256(f"{reporter}\0{clean_key}".encode()).hexdigest()[:32]
        )
    else:
        report_id = f"report-{uuid.uuid4().hex}"
    report = MissingCapabilityReport(
        report_id=report_id,
        name=clean_name,
        vendor=clean_vendor,
        source_url=_safe_source_url(source_url),
        domains=clean_domains,
        expected_task=clean_task,
        platform=platform.strip() if platform and platform.strip() else None,
        host_application=(
            host_application.strip()
            if host_application and host_application.strip()
            else None
        ),
        notes=notes.strip() if notes and notes.strip() else None,
        search_context=dict(search_context or {}),
        reporter=reporter,
        created_at=observed_at,
        updated_at=observed_at,
        state="submitted",
    )
    payload = report.model_dump(mode="json")
    with _connection(database_path) as connection:
        existing = connection.execute(
            "SELECT * FROM missing_capability_reports WHERE report_id = ?",
            (report_id,),
        ).fetchone()
        if existing is not None:
            saved = _row_to_report(existing)
            comparable = saved.model_dump(mode="json")
            for key in ("created_at", "updated_at", "state"):
                comparable.pop(key, None)
                payload.pop(key, None)
            if comparable != payload:
                raise MissingCapabilityReportError(
                    "report_idempotency_conflict",
                    "That retry key was already used for a different report.",
                    status_code=409,
                )
            return saved
        connection.execute(
            """INSERT INTO missing_capability_reports (
                report_id, name, vendor, source_url, domains_json,
                expected_task, platform, host_application, notes,
                search_context_json, reporter, created_at, updated_at, state,
                matched_capability_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
            (
                report.report_id,
                report.name,
                report.vendor,
                report.source_url,
                json.dumps(report.domains, sort_keys=True),
                report.expected_task,
                report.platform,
                report.host_application,
                report.notes,
                json.dumps(report.search_context, sort_keys=True),
                report.reporter,
                _timestamp(report.created_at),
                _timestamp(report.updated_at),
                report.state,
            ),
        )
    return report


def get_missing_capability_report(
    database_path: str | Path, report_id: str
) -> MissingCapabilityReport:
    with _connection(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM missing_capability_reports WHERE report_id = ?",
            (report_id,),
        ).fetchone()
    if row is None:
        raise MissingCapabilityReportError(
            "report_not_found",
            "Missing-capability report was not found.",
            status_code=404,
        )
    return _row_to_report(row)


def transition_missing_capability_report(
    database_path: str | Path,
    report_id: str,
    state: Literal["exported", "under_review", "matched", "closed"],
    *,
    matched_capability_id: str | None = None,
    known_capability_ids: Iterable[str] = (),
    now: datetime | None = None,
) -> MissingCapabilityReport:
    current = get_missing_capability_report(database_path, report_id)
    if state not in _TRANSITIONS[current.state]:
        raise MissingCapabilityReportError(
            "report_transition_invalid",
            f"A {current.state} report cannot transition to {state}.",
            status_code=409,
        )
    if state == "matched" and matched_capability_id not in set(known_capability_ids):
        raise MissingCapabilityReportError(
            "report_match_unknown_capability",
            "A report can only match a reviewed capability.",
            status_code=422,
        )
    changed_at = now or datetime.now(UTC)
    with _connection(database_path) as connection:
        connection.execute(
            """UPDATE missing_capability_reports
               SET state = ?, matched_capability_id = ?, updated_at = ?
               WHERE report_id = ? AND state = ?""",
            (
                state,
                matched_capability_id if state == "matched" else None,
                _timestamp(changed_at),
                report_id,
                current.state,
            ),
        )
        if connection.total_changes != 1:
            raise MissingCapabilityReportError(
                "report_concurrent_change",
                "The report changed while it was being reviewed.",
                status_code=409,
            )
    return get_missing_capability_report(database_path, report_id)


def export_missing_capability_reports(
    database_path: str | Path, *, now: datetime | None = None
) -> list[dict[str, Any]]:
    with _connection(database_path) as connection:
        rows = connection.execute(
            "SELECT * FROM missing_capability_reports ORDER BY created_at, report_id"
        ).fetchall()
    exported: list[dict[str, Any]] = []
    for row in rows:
        report = _row_to_report(row)
        if report.state == "submitted":
            report = transition_missing_capability_report(
                database_path, report.report_id, "exported", now=now
            )
        exported.append(report.model_dump(mode="json"))
    return exported
