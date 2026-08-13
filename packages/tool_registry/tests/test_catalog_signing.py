from __future__ import annotations

import base64
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from tool_registry.catalog_signing import (
    CatalogTrustRoot,
    CatalogVerificationError,
    canonical_json,
    parse_json_strict,
    verify_catalog_envelope,
)
from catalog_update_fixtures import (
    TEST_KEY_ID,
    TEST_PRIVATE_KEY,
    TEST_PUBLIC_KEY,
    candidate_70_catalog,
    signed_catalog,
    tampered_catalog,
)

NOW = datetime(2026, 8, 12, 12, 0, tzinfo=UTC)
ROOT = CatalogTrustRoot("test", TEST_KEY_ID, TEST_PUBLIC_KEY)


def test_canonical_json_is_deterministic_and_rejects_floats() -> None:
    assert canonical_json({"z": "é", "a": [2, 1]}) == (b'{"a":[2,1],"z":"\xc3\xa9"}')
    with pytest.raises(CatalogVerificationError, match="Floating-point"):
        canonical_json({"unsafe": 1.5})


def test_valid_envelope_verifies_signature_digest_time_sequence_and_schema() -> None:
    snapshot = verify_catalog_envelope(
        signed_catalog(candidate_70_catalog(), issued_at=NOW),
        trust_root=ROOT,
        now=NOW,
        minimum_sequence=1,
    )

    assert snapshot.sequence == 2
    assert snapshot.signer_key_id == TEST_KEY_ID
    assert snapshot.verification_state == "verified"
    assert len(snapshot.payload_json["servers"]) == 70


@pytest.mark.parametrize(
    ("mutator", "code"),
    [
        (lambda envelope: tampered_catalog(envelope), "catalog_signature_invalid"),
        (
            lambda envelope: {
                **envelope,
                "signed": {**envelope["signed"], "payload_sha256": "0" * 64},
            },
            "catalog_signature_invalid",
        ),
        (
            lambda envelope: {**envelope, "unexpected": True},
            "catalog_envelope_invalid",
        ),
    ],
)
def test_tampered_digest_and_schema_fail_closed(mutator, code) -> None:
    envelope = mutator(signed_catalog(candidate_70_catalog(), issued_at=NOW))
    with pytest.raises(CatalogVerificationError) as caught:
        verify_catalog_envelope(envelope, trust_root=ROOT, now=NOW, minimum_sequence=1)
    assert caught.value.code == code


def test_resigned_wrong_digest_is_detected_after_signature() -> None:
    envelope = signed_catalog(candidate_70_catalog(), issued_at=NOW)
    envelope["signed"]["payload_sha256"] = "0" * 64
    envelope["signature"] = (
        base64.urlsafe_b64encode(
            TEST_PRIVATE_KEY.sign(canonical_json(envelope["signed"]))
        )
        .decode()
        .rstrip("=")
    )
    with pytest.raises(CatalogVerificationError) as caught:
        verify_catalog_envelope(envelope, trust_root=ROOT, now=NOW, minimum_sequence=1)
    assert caught.value.code == "catalog_digest_mismatch"


def test_wrong_key_expiry_future_issue_replay_and_downgrade_are_rejected() -> None:
    other_public = (
        Ed25519PrivateKey.generate()
        .public_key()
        .public_bytes(Encoding.Raw, PublicFormat.Raw)
    )
    cases = [
        (
            signed_catalog(
                candidate_70_catalog(),
                issued_at=NOW - timedelta(days=2),
                expires_at=NOW - timedelta(days=1),
            ),
            ROOT,
            1,
            "catalog_expired",
        ),
        (
            signed_catalog(candidate_70_catalog(), issued_at=NOW + timedelta(hours=1)),
            ROOT,
            1,
            "catalog_time_invalid",
        ),
        (
            signed_catalog(candidate_70_catalog(), sequence=2, issued_at=NOW),
            ROOT,
            2,
            "catalog_sequence_stale",
        ),
        (
            signed_catalog(candidate_70_catalog(), sequence=1, issued_at=NOW),
            ROOT,
            2,
            "catalog_sequence_stale",
        ),
        (
            signed_catalog(candidate_70_catalog(), issued_at=NOW),
            CatalogTrustRoot("test", TEST_KEY_ID, other_public),
            1,
            "catalog_key_untrusted",
        ),
    ]
    for envelope, root, minimum, code in cases:
        with pytest.raises(CatalogVerificationError) as caught:
            verify_catalog_envelope(
                envelope, trust_root=root, now=NOW, minimum_sequence=minimum
            )
        assert caught.value.code == code


def test_alias_conflict_and_duplicate_json_keys_are_rejected() -> None:
    payload = candidate_70_catalog()
    payload["servers"][1]["aliases"].append(payload["servers"][0]["id"])
    with pytest.raises(CatalogVerificationError) as caught:
        verify_catalog_envelope(
            signed_catalog(payload, issued_at=NOW),
            trust_root=ROOT,
            now=NOW,
            minimum_sequence=1,
        )
    assert caught.value.code == "catalog_payload_invalid"

    with pytest.raises(CatalogVerificationError) as duplicate:
        parse_json_strict(b'{"signed":{},"signed":{},"signature":"x"}')
    assert duplicate.value.code == "catalog_json_duplicate_key"
