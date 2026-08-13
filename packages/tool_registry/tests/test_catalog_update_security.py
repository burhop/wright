from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import httpx
import pytest
from data_vault import upgrade_database
from tool_registry.canonical_catalog import (
    ApprovedCatalogChannel,
    CatalogFetchError,
    fetch_catalog_envelope,
)
from tool_registry.catalog_signing import CatalogTrustRoot
from tool_registry.catalog_snapshots import bootstrap_bundled_snapshot
from tool_registry.catalog_updates import (
    CatalogUpdateError,
    activate_catalog_update,
    preview_catalog_update,
)

from catalog_update_fixtures import (
    TEST_KEY_ID,
    TEST_PUBLIC_KEY,
    candidate_70_catalog,
    prior_69_catalog,
    signed_catalog,
)

NOW = datetime(2026, 8, 13, 1, 0, tzinfo=UTC)
ROOT = CatalogTrustRoot("test", TEST_KEY_ID, TEST_PUBLIC_KEY)


def test_channel_rejects_unsafe_url_redirect_size_timeout_and_ambient_credentials(
    monkeypatch,
) -> None:
    for unsafe in (
        "http://updates.example/catalog.json",
        "https://user:secret@updates.example/catalog.json",
        "https://updates.example/catalog.json#unreviewed",
    ):
        with pytest.raises(CatalogFetchError) as rejected:
            fetch_catalog_envelope(ApprovedCatalogChannel("test", unsafe))
        assert rejected.value.code == "catalog_channel_unsafe"

    with pytest.raises(CatalogFetchError) as redirected:
        fetch_catalog_envelope(
            ApprovedCatalogChannel("test", "https://updates.example/catalog.json"),
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    307, headers={"location": "https://elsewhere.example/catalog.json"}
                )
            ),
        )
    assert redirected.value.code == "catalog_channel_redirect_rejected"

    with pytest.raises(CatalogFetchError) as oversized:
        fetch_catalog_envelope(
            ApprovedCatalogChannel(
                "test", "https://updates.example/catalog.json", max_bytes=32
            ),
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    content=json.dumps({"payload": "x" * 100}).encode(),
                )
            ),
        )
    assert oversized.value.code == "catalog_envelope_too_large"

    with pytest.raises(CatalogFetchError) as timed_out:
        fetch_catalog_envelope(
            ApprovedCatalogChannel(
                "test", "https://updates.example/catalog.json", timeout_seconds=0.01
            ),
            transport=httpx.MockTransport(
                lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("fixture"))
            ),
        )
    assert timed_out.value.code == "catalog_channel_unavailable"

    monkeypatch.setenv("HTTPS_PROXY", "http://user:password@proxy.invalid")
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200, json=signed_catalog(candidate_70_catalog(), issued_at=NOW)
        )

    fetch_catalog_envelope(
        ApprovedCatalogChannel("test", "https://updates.example/catalog.json"),
        transport=httpx.MockTransport(handler),
    )
    assert len(seen) == 1
    assert "authorization" not in seen[0].headers
    assert "proxy-authorization" not in seen[0].headers
    assert "cookie" not in seen[0].headers


def _prepared_preview(database):
    upgrade_database(database)
    bootstrap_bundled_snapshot(database, payload=prior_69_catalog())
    return preview_catalog_update(
        database,
        signed_catalog(candidate_70_catalog(), issued_at=NOW),
        trust_root=ROOT,
        actor="admin-a",
        now=NOW,
        trace_id="security-preview",
    )


def test_activation_replay_fails_closed(tmp_path) -> None:
    database = tmp_path / "replay.db"
    preview = _prepared_preview(database)
    activate_catalog_update(
        database,
        preview["preview_id"],
        preview["preview_digest"],
        actor="admin-a",
        now=NOW,
        trace_id="first-activation",
    )
    with pytest.raises(CatalogUpdateError) as replay:
        activate_catalog_update(
            database,
            preview["preview_id"],
            preview["preview_digest"],
            actor="admin-a",
            now=NOW,
            trace_id="replay-activation",
        )
    assert replay.value.code == "catalog_preview_stale"


def test_concurrent_writers_serialize_to_one_activation(tmp_path) -> None:
    database = tmp_path / "concurrent.db"
    preview = _prepared_preview(database)

    def activate(trace_id: str) -> str:
        try:
            activate_catalog_update(
                database,
                preview["preview_id"],
                preview["preview_digest"],
                actor="admin-a",
                now=NOW,
                trace_id=trace_id,
            )
            return "succeeded"
        except CatalogUpdateError as error:
            return error.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(activate, ("writer-a", "writer-b")))

    assert sorted(outcomes) == ["catalog_preview_stale", "succeeded"]
