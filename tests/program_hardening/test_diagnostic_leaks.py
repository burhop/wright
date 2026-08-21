from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from data_vault import upgrade_database
from workspace_service.adapters.runtime import create_workspace
from workspace_service.support_diagnostic_service import SupportDiagnosticService


def test_diagnostic_export_and_logs_exclude_private_and_executable_values(
    tmp_path, caplog
) -> None:
    database = tmp_path / "program.db"
    upgrade_database(database)
    private_path = tmp_path / "Customer Phoenix" / "secret bracket.step"
    private_path.parent.mkdir()
    secret_values = (
        "sk-live-private-token-123456",
        "Bearer reusable-authority-98765",
        str(private_path),
        "customer-bracket-feature-vector-42",
        "M3 S12000",
        "G28",
        "curl https://example.invalid/upload",
        "<script>alert('run')</script>",
        "#!/bin/sh",
    )
    create_workspace(
        str(database),
        "workspace-safe-id",
        "session-safe-id",
        str(private_path.parent),
        "Private customer workspace",
    )
    with sqlite3.connect(database) as connection:
        connection.execute(
            """UPDATE engineering_workspaces
               SET workspace_prompt = ?, git_token = ?, git_remote_url = ?
               WHERE workspace_id = ?""",
            (
                " ".join(secret_values),
                secret_values[0],
                "https://private.example.invalid/customer/repository",
                "workspace-safe-id",
            ),
        )
    tokens = iter(["snapshot_12345678", "confirmation-reusable-token"])
    service = SupportDiagnosticService(
        database,
        clock=lambda: datetime(2026, 8, 13, 12, tzinfo=UTC),
        token_factory=lambda _bytes: next(tokens),
        principal_digest_key=b"program-hardening-test-key",
    )

    with caplog.at_level("INFO"):
        preview = service.preview(
            principal_id="engineer-safe-id",
            workspace_id="workspace-safe-id",
            scope={"session_id": "session-safe-id"},
        )
        exported = service.export(
            principal_id="engineer-safe-id",
            workspace_id="workspace-safe-id",
            snapshot_digest=preview.snapshot.snapshot_digest,
            confirmation_token=preview.confirmation_token,
        )

    surfaces = "\n".join(
        (
            exported.content.decode("utf-8"),
            caplog.text,
            preview.filename,
        )
    )
    for prohibited in (*secret_values, preview.confirmation_token):
        assert prohibited not in surfaces
    assert len(exported.content) <= 2 * 1024 * 1024
    assert exported.content.startswith(b"{") and exported.content.endswith(b"}")
    assert b"raw-engineering-payloads" in exported.content
    assert b"PROPRIETARY_CONTENT_FORBIDDEN" in exported.content
    assert b"REUSABLE_AUTHORITY_FORBIDDEN" in exported.content
