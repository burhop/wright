from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from data_vault import upgrade_database
from tool_registry.missing_reports import (
    MissingCapabilityReportError,
    export_missing_capability_reports,
    get_missing_capability_report,
    submit_missing_capability_report,
    transition_missing_capability_report,
)

NOW = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "reports.db"
    upgrade_database(path)
    return path


def _submit(database, **overrides):
    values = {
        "name": "Requested Geometry MCP",
        "vendor": "Example Engineering",
        "source_url": "https://example.com/mcp?token=must-not-persist#private",
        "domains": ["CAD", "cad"],
        "expected_task": "Create a constrained bracket",
        "platform": "windows_11_x64",
        "host_application": "Example CAD",
        "notes": "Needed for the bracket workflow",
        "search_context": {"query": "bracket", "filters": {"domain": "cad"}},
        "reporter": "engineer-1",
        "now": NOW,
    }
    values.update(overrides)
    return submit_missing_capability_report(database, **values)


def test_submission_validates_normalizes_and_stays_outside_server_rows(database):
    report = _submit(database)
    assert report.state == "submitted"
    assert report.domains == ["cad"]
    assert report.source_url == "https://example.com/mcp"
    assert report.search_context["query"] == "bracket"
    with sqlite3.connect(database) as connection:
        assert connection.execute("SELECT count(*) FROM mcp_servers").fetchone()[0] == 0
        assert (
            connection.execute(
                "SELECT count(*) FROM missing_capability_reports"
            ).fetchone()[0]
            == 1
        )


def test_idempotency_returns_same_report_and_conflicts_on_changed_payload(database):
    first = _submit(database, idempotency_key="retry-1")
    retried = _submit(
        database, idempotency_key="retry-1", now=NOW + timedelta(minutes=1)
    )
    assert retried.report_id == first.report_id
    with pytest.raises(MissingCapabilityReportError) as conflict:
        _submit(
            database,
            idempotency_key="retry-1",
            expected_task="A different request",
        )
    assert conflict.value.status_code == 409


def test_explicit_export_review_match_and_close_transitions(database):
    report = _submit(database)
    exported = export_missing_capability_reports(
        database, now=NOW + timedelta(minutes=1)
    )
    assert exported[0]["state"] == "exported"
    reviewing = transition_missing_capability_report(
        database,
        report.report_id,
        "under_review",
        now=NOW + timedelta(minutes=2),
    )
    assert reviewing.state == "under_review"
    matched = transition_missing_capability_report(
        database,
        report.report_id,
        "matched",
        matched_capability_id="reviewed-capability",
        known_capability_ids={"reviewed-capability"},
        now=NOW + timedelta(minutes=3),
    )
    assert matched.matched_capability_id == "reviewed-capability"
    closed = transition_missing_capability_report(
        database,
        report.report_id,
        "closed",
        now=NOW + timedelta(minutes=4),
    )
    assert closed.state == "closed"
    assert get_missing_capability_report(database, report.report_id) == closed


def test_invalid_transition_unknown_match_and_secret_like_context_are_rejected(
    database,
):
    report = _submit(database)
    with pytest.raises(MissingCapabilityReportError, match="cannot transition"):
        transition_missing_capability_report(database, report.report_id, "matched")
    transition_missing_capability_report(
        database, report.report_id, "under_review", now=NOW + timedelta(minutes=1)
    )
    with pytest.raises(MissingCapabilityReportError) as unknown:
        transition_missing_capability_report(
            database,
            report.report_id,
            "matched",
            matched_capability_id="unreviewed",
            known_capability_ids=set(),
        )
    assert unknown.value.code == "report_match_unknown_capability"
    with pytest.raises(ValueError, match="secret-like"):
        _submit(database, search_context={"api_token": "must-not-persist"})


def test_required_fields_and_credential_bearing_url_are_rejected(database):
    with pytest.raises(MissingCapabilityReportError) as missing:
        _submit(database, domains=[])
    assert missing.value.status_code == 422
    with pytest.raises(MissingCapabilityReportError) as credential_url:
        _submit(database, source_url="https://user:secret@example.com/mcp")
    assert credential_url.value.code == "report_source_contains_credentials"
