from __future__ import annotations

import base64
import hashlib
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from data_vault import upgrade_database
from fastapi import HTTPException
from fastapi.testclient import TestClient
from tool_registry import McpEngine
from tool_registry.capability_services import CapabilityServiceDependencies
from tool_registry.catalog_reconcile import reconcile_engineering_catalog_document
from tool_registry.catalog_signing import CatalogTrustRoot
from tool_registry.catalog_snapshots import bootstrap_bundled_snapshot
from tool_registry.canonical_catalog import load_catalog_document
from tool_registry.catalog_signing import canonical_json
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from api.main import app
from api.routers.mcp import require_admin
from api.services.mcp_services import McpApiService, get_mcp_api_service

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
TEST_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
TEST_PUBLIC_KEY = TEST_PRIVATE_KEY.public_key().public_bytes(
    Encoding.Raw, PublicFormat.Raw
)
TEST_KEY_ID = hashlib.sha256(TEST_PUBLIC_KEY).hexdigest()


def candidate_70_catalog() -> dict:
    return deepcopy(load_catalog_document())


def prior_69_catalog() -> dict:
    payload = candidate_70_catalog()
    payload["servers"] = [
        item
        for item in payload["servers"]
        if item["id"] != "onshape-labs-featurescript-mcp"
    ]
    return payload


def signed_catalog(payload: dict, *, issued_at: datetime) -> dict:
    signed = {
        "envelope_version": 1,
        "channel": "test",
        "sequence": 2,
        "issued_at": issued_at.isoformat().replace("+00:00", "Z"),
        "expires_at": (issued_at + timedelta(days=7))
        .isoformat()
        .replace("+00:00", "Z"),
        "schema_version": 1,
        "key_id": TEST_KEY_ID,
        "payload_sha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
        "payload": payload,
    }
    signature = (
        base64.urlsafe_b64encode(TEST_PRIVATE_KEY.sign(canonical_json(signed)))
        .decode()
        .rstrip("=")
    )
    return {"signed": signed, "signature": signature}


def tampered_catalog(envelope: dict) -> dict:
    result = deepcopy(envelope)
    result["signed"]["payload"]["servers"].append({"id": "tampered"})
    return result


@pytest.fixture
def catalog_client(tmp_path):
    database = tmp_path / "catalog-api.db"
    upgrade_database(database)
    prior = prior_69_catalog()
    bootstrap_bundled_snapshot(database, payload=prior)
    reconcile_engineering_catalog_document(str(database), prior)
    service = McpApiService(
        McpEngine(str(database)),
        SimpleNamespace(),
        CapabilityServiceDependencies(
            database_path=database,
            clock=lambda: NOW,
            trust_roots={
                "test": CatalogTrustRoot("test", TEST_KEY_ID, TEST_PUBLIC_KEY)
            },
        ),
    )
    app.dependency_overrides[get_mcp_api_service] = lambda: service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.pop(get_mcp_api_service, None)
    app.dependency_overrides.pop(require_admin, None)


def test_state_preview_activate_restart_projection_and_rollback(catalog_client) -> None:
    client = catalog_client
    initial = client.get("/api/mcp/catalog/state")
    assert initial.status_code == 200
    assert initial.json()["active_sequence"] == 1
    assert initial.json()["configured_channels"] == []

    preview = client.post(
        "/api/mcp/catalog/updates/preview",
        json={"envelope": signed_catalog(candidate_70_catalog(), issued_at=NOW)},
    )
    assert preview.status_code == 200
    preview_body = preview.json()
    assert preview_body["diff"]["summary"]["added"] == 1
    assert "signature" not in preview.text

    activated = client.post(
        f"/api/mcp/catalog/updates/{preview_body['preview_id']}/activate",
        json={"preview_digest": preview_body["preview_digest"]},
    )
    assert activated.status_code == 200
    assert activated.json()["preserved_user_state"] is True

    capabilities = client.get(
        "/api/mcp/capabilities",
        params={"search": "FeatureScript", "evidence_class": "official_preview"},
    )
    assert capabilities.status_code == 200
    assert capabilities.json()["total"] == 1
    assert capabilities.json()["snapshot"]["channel"] == "test"

    state = client.get("/api/mcp/catalog/state").json()
    rolled_back = client.post(
        "/api/mcp/catalog/rollback",
        json={
            "active_snapshot_id": state["active_snapshot_id"],
            "previous_snapshot_id": state["previous_snapshot_id"],
        },
    )
    assert rolled_back.status_code == 200
    assert rolled_back.json()["preserved_user_state"] is True
    after = client.get(
        "/api/mcp/capabilities", params={"search": "FeatureScript"}
    ).json()
    assert all(
        item["canonical_id"] != "onshape-labs-featurescript-mcp"
        for item in after["capabilities"]
    )
    assert after["snapshot"]["channel"] == "bundled"


def test_stale_preview_and_tampered_envelope_fail_closed_with_redacted_error(
    catalog_client,
) -> None:
    client = catalog_client
    envelope = signed_catalog(candidate_70_catalog(), issued_at=NOW)
    rejected = client.post(
        "/api/mcp/catalog/updates/preview",
        json={"envelope": tampered_catalog(envelope)},
    )
    assert rejected.status_code == 422
    detail = rejected.json()
    assert detail["error_code"] == "catalog_signature_invalid"
    assert detail["trace_id"]
    assert envelope["signature"] not in rejected.text

    preview = client.post(
        "/api/mcp/catalog/updates/preview", json={"envelope": envelope}
    ).json()
    stale = client.post(
        f"/api/mcp/catalog/updates/{preview['preview_id']}/activate",
        json={"preview_digest": "0" * 64},
    )
    assert stale.status_code == 409
    assert stale.json()["error_code"] == "catalog_preview_digest_mismatch"


def test_catalog_update_routes_require_administrator(catalog_client) -> None:
    def deny_admin():
        raise HTTPException(status_code=403, detail="Administrator role required")

    app.dependency_overrides[require_admin] = deny_admin
    response = catalog_client.get("/api/mcp/catalog/state")
    assert response.status_code == 403
    assert response.json()["message"] == "Administrator role required"
