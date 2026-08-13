from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from data_vault import upgrade_database
from tool_registry.catalog_signing import CatalogTrustRoot
from tool_registry.catalog_snapshots import bootstrap_bundled_snapshot
from tool_registry.catalog_updates import catalog_diff, preview_catalog_update
from catalog_update_fixtures import (
    TEST_KEY_ID,
    TEST_PUBLIC_KEY,
    candidate_70_catalog,
    prior_69_catalog,
    signed_catalog,
)

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
ROOT = CatalogTrustRoot("test", TEST_KEY_ID, TEST_PUBLIC_KEY)


def test_diff_is_sorted_exact_and_carries_field_provenance() -> None:
    before = prior_69_catalog()
    after = candidate_70_catalog()
    after["servers"][0]["description"] = "Changed fixture description"

    diff = catalog_diff(before, after)

    assert diff["summary"] == {
        "added": 1,
        "removed": 0,
        "changed": 1,
        "total_before": 69,
        "total_after": 70,
    }
    assert diff["added"][0]["id"] == "onshape-labs-featurescript-mcp"
    assert diff["added"][0]["provenance"][0]["authority"] == "vendor"
    assert diff["changed"][0]["fields"][0]["field"] == "description"


def test_preview_binds_actor_active_candidate_diff_and_expiry(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    bootstrap_bundled_snapshot(database, payload=prior_69_catalog())

    preview = preview_catalog_update(
        database,
        signed_catalog(candidate_70_catalog(), issued_at=NOW),
        trust_root=ROOT,
        actor="admin-a",
        now=NOW,
        trace_id="trace-preview",
    )

    assert preview["diff"]["summary"]["added"] == 1
    assert preview["candidate"]["sequence"] == 2
    assert len(preview["preview_digest"]) == 64
    assert preview["risk_summary"]["new_remote_entries"] == 1
    with sqlite3.connect(database) as connection:
        row = connection.execute(
            """SELECT actor, state, preview_digest FROM catalog_update_previews
               WHERE preview_id=?""",
            (preview["preview_id"],),
        ).fetchone()
    assert row == ("admin-a", "open", preview["preview_digest"])
