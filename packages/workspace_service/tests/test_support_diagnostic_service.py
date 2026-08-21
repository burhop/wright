from __future__ import annotations

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import pytest

from data_vault import upgrade_database
from workspace_service.adapters.runtime import create_workspace
from workspace_service.support_diagnostic_service import (
    SupportDiagnosticError,
    SupportDiagnosticService,
)


def _service(tmp_path, *, clock=None, token_values=None) -> SupportDiagnosticService:
    db_path = tmp_path / "state.db"
    upgrade_database(db_path)
    workspace = tmp_path / "workspace"
    workspace.mkdir(exist_ok=True)
    create_workspace(str(db_path), "ws-1", "session-1", str(workspace), "Fixture")
    tokens = iter(token_values or ["snapshot_12345678", "confirmation-token"])
    return SupportDiagnosticService(
        db_path,
        clock=clock or (lambda: datetime(2026, 8, 13, 12, tzinfo=UTC)),
        token_factory=lambda _bytes: next(tokens),
        principal_digest_key=b"test-principal-digest-key",
    )


def test_preview_is_inert_and_export_is_exact_single_use(tmp_path) -> None:
    service = _service(tmp_path)
    before = sorted(
        path.relative_to(tmp_path)
        for path in tmp_path.rglob("*")
        if path.name not in {"state.db-shm", "state.db-wal"}
    )

    preview = service.preview(
        principal_id="engineer-1",
        workspace_id="ws-1",
        scope={"session_id": "session-1"},
    )
    after = sorted(
        path.relative_to(tmp_path)
        for path in tmp_path.rglob("*")
        if path.name not in {"state.db-shm", "state.db-wal"}
    )

    assert before == after
    assert preview.snapshot.workspace_id == "ws-1"
    assert preview.snapshot.principal_digest != "engineer-1"
    assert preview.snapshot.snapshot_digest.startswith("sha256:")
    assert preview.filename.endswith(".json")
    assert "local_path" not in preview.snapshot.export_bytes().decode("utf-8")

    exported = service.export(
        principal_id="engineer-1",
        workspace_id="ws-1",
        snapshot_digest=preview.snapshot.snapshot_digest,
        confirmation_token=preview.confirmation_token,
    )
    assert exported.content == preview.snapshot.export_bytes()
    assert (
        json.loads(exported.content)["snapshot_digest"]
        == preview.snapshot.snapshot_digest
    )

    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_EXPORT_DENIED"):
        service.export(
            principal_id="engineer-1",
            workspace_id="ws-1",
            snapshot_digest=preview.snapshot.snapshot_digest,
            confirmation_token=preview.confirmation_token,
        )


@pytest.mark.parametrize(
    ("principal", "workspace", "digest", "token"),
    [
        ("other-engineer", "ws-1", None, None),
        ("engineer-1", "other-workspace", None, None),
        ("engineer-1", "ws-1", f"sha256:{'f' * 64}", None),
        ("engineer-1", "ws-1", None, "different-token"),
    ],
)
def test_export_denies_cross_scope_digest_and_token_substitution(
    tmp_path, principal, workspace, digest, token
) -> None:
    service = _service(tmp_path)
    preview = service.preview(principal_id="engineer-1", workspace_id="ws-1")

    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_EXPORT_DENIED"):
        service.export(
            principal_id=principal,
            workspace_id=workspace,
            snapshot_digest=digest or preview.snapshot.snapshot_digest,
            confirmation_token=token or preview.confirmation_token,
        )


def test_expired_and_restart_invalidated_previews_fail_closed(tmp_path) -> None:
    observed = [datetime(2026, 8, 13, 12, tzinfo=UTC)]
    service = _service(tmp_path, clock=lambda: observed[0])
    preview = service.preview(principal_id="engineer-1", workspace_id="ws-1")
    observed[0] += timedelta(minutes=6)

    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_PREVIEW_EXPIRED"):
        service.export(
            principal_id="engineer-1",
            workspace_id="ws-1",
            snapshot_digest=preview.snapshot.snapshot_digest,
            confirmation_token=preview.confirmation_token,
        )

    restarted = SupportDiagnosticService(tmp_path / "state.db")
    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_EXPORT_DENIED"):
        restarted.export(
            principal_id="engineer-1",
            workspace_id="ws-1",
            snapshot_digest=preview.snapshot.snapshot_digest,
            confirmation_token=preview.confirmation_token,
        )


def test_preview_rejects_session_outside_workspace(tmp_path) -> None:
    service = _service(tmp_path)

    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_SCOPE_FORBIDDEN"):
        service.preview(
            principal_id="engineer-1",
            workspace_id="ws-1",
            scope={"session_id": "session-other"},
        )


def test_concurrent_export_consumes_grant_exactly_once(tmp_path) -> None:
    service = _service(tmp_path)
    preview = service.preview(principal_id="engineer-1", workspace_id="ws-1")

    def export_once() -> bool:
        try:
            service.export(
                principal_id="engineer-1",
                workspace_id="ws-1",
                snapshot_digest=preview.snapshot.snapshot_digest,
                confirmation_token=preview.confirmation_token,
            )
            return True
        except SupportDiagnosticError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: export_once(), range(2)))
    assert sorted(results) == [False, True]


def test_material_identity_change_invalidates_the_exact_preview(tmp_path) -> None:
    service = _service(tmp_path)
    preview = service.preview(principal_id="engineer-1", workspace_id="ws-1")
    with sqlite3.connect(tmp_path / "state.db") as connection:
        connection.execute(
            """INSERT INTO model_catalog_snapshots(
                   snapshot_id, channel, sequence, schema_version,
                   catalog_digest, source_kind, trust_state, freshness,
                   metadata_json, created_at, activated_at)
               VALUES ('models-new', 'stable', 1, '1.0', ?, 'bundled',
                       'bundled', 'cached', '{}', 1, 1)""",
            ("f" * 64,),
        )

    with pytest.raises(SupportDiagnosticError, match="DIAGNOSTIC_PREVIEW_STALE"):
        service.export(
            principal_id="engineer-1",
            workspace_id="ws-1",
            snapshot_digest=preview.snapshot.snapshot_digest,
            confirmation_token=preview.confirmation_token,
        )
