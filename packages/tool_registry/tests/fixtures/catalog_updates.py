from __future__ import annotations

import base64
import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


TEST_PRIVATE_KEY = Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
TEST_PUBLIC_KEY = TEST_PRIVATE_KEY.public_key().public_bytes(
    Encoding.Raw, PublicFormat.Raw
)
TEST_KEY_ID = hashlib.sha256(TEST_PUBLIC_KEY).hexdigest()


def canonical_json(document: object) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":")).encode()


def signed_catalog(
    payload: dict,
    *,
    sequence: int = 2,
    issued_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> dict:
    issued = issued_at or datetime(2026, 8, 12, tzinfo=UTC)
    expiry = expires_at or issued + timedelta(days=7)
    signed = {
        "envelope_version": 1,
        "channel": "test",
        "sequence": sequence,
        "issued_at": issued.isoformat().replace("+00:00", "Z"),
        "expires_at": expiry.isoformat().replace("+00:00", "Z"),
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
