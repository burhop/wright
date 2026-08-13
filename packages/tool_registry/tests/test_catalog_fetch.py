from __future__ import annotations

import json

import httpx
import pytest

from tool_registry.canonical_catalog import (
    ApprovedCatalogChannel,
    CatalogFetchError,
    fetch_catalog_envelope,
    load_catalog_document_from_url,
)
from fixtures.catalog_updates import candidate_70_catalog, signed_catalog


def test_approved_channel_is_exact_bounded_and_forwards_no_ambient_credentials() -> (
    None
):
    envelope = signed_catalog(candidate_70_catalog())
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=envelope)

    result = fetch_catalog_envelope(
        ApprovedCatalogChannel("test", "https://updates.example.test/catalog.json"),
        transport=httpx.MockTransport(handler),
    )

    assert result == envelope
    assert len(seen) == 1
    assert str(seen[0].url) == "https://updates.example.test/catalog.json"
    assert "authorization" not in seen[0].headers
    assert "cookie" not in seen[0].headers


def test_redirect_oversize_unsafe_scheme_and_direct_url_fail_closed() -> None:
    redirect = httpx.MockTransport(
        lambda request: httpx.Response(
            302, headers={"location": "https://other.example/catalog.json"}
        )
    )
    with pytest.raises(CatalogFetchError) as redirected:
        fetch_catalog_envelope(
            ApprovedCatalogChannel("test", "https://updates.example/catalog.json"),
            transport=redirect,
        )
    assert redirected.value.code == "catalog_channel_redirect_rejected"

    oversized = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            content=json.dumps({"large": "x" * 100}).encode(),
            headers={"content-length": "200"},
        )
    )
    with pytest.raises(CatalogFetchError) as too_large:
        fetch_catalog_envelope(
            ApprovedCatalogChannel(
                "test", "https://updates.example/catalog.json", max_bytes=50
            ),
            transport=oversized,
        )
    assert too_large.value.code == "catalog_envelope_too_large"

    with pytest.raises(CatalogFetchError) as unsafe:
        fetch_catalog_envelope(
            ApprovedCatalogChannel("test", "http://updates.example/catalog.json")
        )
    assert unsafe.value.code == "catalog_channel_unsafe"

    with pytest.raises(CatalogFetchError) as disabled:
        load_catalog_document_from_url("https://updates.example/catalog.yaml")
    assert disabled.value.code == "catalog_direct_url_disabled"
