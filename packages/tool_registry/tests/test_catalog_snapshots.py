from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from data_vault import upgrade_database
from tool_registry.catalog_signing import CatalogTrustRoot, verify_catalog_envelope
from tool_registry.catalog_snapshots import (
    bootstrap_bundled_snapshot,
    get_catalog_state,
    get_snapshot,
    load_active_catalog,
    prune_snapshots,
    store_verified_snapshot,
)
from fixtures.catalog_updates import (
    TEST_KEY_ID,
    TEST_PUBLIC_KEY,
    candidate_70_catalog,
    prior_69_catalog,
    signed_catalog,
)

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)


def test_bootstrap_is_idempotent_and_active_payload_survives_restart(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    first = bootstrap_bundled_snapshot(database, payload=prior_69_catalog())
    second = bootstrap_bundled_snapshot(database, payload=prior_69_catalog())

    assert first.snapshot_id == second.snapshot_id
    assert get_catalog_state(database)["active_snapshot_id"] == first.snapshot_id
    document, diagnostic = load_active_catalog(database)
    assert len(document["servers"]) == 69
    assert diagnostic is None


def test_verified_candidates_are_immutable_and_retention_protects_roots(
    tmp_path,
) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    bundled = bootstrap_bundled_snapshot(database, payload=prior_69_catalog())
    candidate = verify_catalog_envelope(
        signed_catalog(candidate_70_catalog(), issued_at=NOW),
        trust_root=CatalogTrustRoot("test", TEST_KEY_ID, TEST_PUBLIC_KEY),
        now=NOW,
        minimum_sequence=1,
    )
    store_verified_snapshot(database, candidate)

    stored = get_snapshot(database, candidate.snapshot_id)
    assert stored == candidate
    assert prune_snapshots(database, retain=1) == 0
    assert get_snapshot(database, bundled.snapshot_id) is not None
    assert get_snapshot(database, candidate.snapshot_id) is not None


def test_corrupt_active_snapshot_falls_back_read_only_to_packaged_catalog(
    tmp_path,
) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    bundled = bootstrap_bundled_snapshot(database, payload=prior_69_catalog())
    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE catalog_snapshots SET payload_json='{}' WHERE snapshot_id=?",
            (bundled.snapshot_id,),
        )

    document, diagnostic = load_active_catalog(database)
    assert len(document["servers"]) == 70
    assert diagnostic["code"] == "catalog_recovery_bundled"
    assert get_catalog_state(database)["active_snapshot_id"] == bundled.snapshot_id
