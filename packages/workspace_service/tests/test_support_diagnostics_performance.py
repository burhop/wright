from __future__ import annotations

import time
from datetime import UTC, datetime

from data_vault import upgrade_database
from workspace_service.adapters.runtime import create_workspace
from workspace_service.support_diagnostic_service import SupportDiagnosticService


def test_bounded_preview_and_export_complete_within_one_second(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    create_workspace(str(database), "ws-1", "session-1", str(workspace), "Fixture")
    values = iter(["snapshot_12345678", "confirmation-token"])
    service = SupportDiagnosticService(
        database,
        clock=lambda: datetime(2026, 8, 13, 12, tzinfo=UTC),
        token_factory=lambda _bytes: next(values),
    )

    started = time.perf_counter()
    preview = service.preview(principal_id="engineer-1", workspace_id="ws-1")
    preview_elapsed = time.perf_counter() - started
    started = time.perf_counter()
    exported = service.export(
        principal_id="engineer-1",
        workspace_id="ws-1",
        snapshot_digest=preview.snapshot.snapshot_digest,
        confirmation_token=preview.confirmation_token,
    )
    export_elapsed = time.perf_counter() - started

    assert preview_elapsed < 1.0
    assert export_elapsed < 1.0
    assert len(exported.content) <= 2 * 1024 * 1024
