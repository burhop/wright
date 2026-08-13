from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.resources import files
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker

from .canonical_catalog import CatalogValidationError, _validate_catalog_document
from .capability_models import CatalogSnapshot

MAX_ENVELOPE_BYTES = 5 * 1024 * 1024
MAX_CLOCK_SKEW = timedelta(minutes=5)


@dataclass(frozen=True, slots=True)
class CatalogTrustRoot:
    channel: str
    key_id: str
    public_key: bytes


class CatalogVerificationError(ValueError):
    def __init__(self, code: str, message: str, recovery: str) -> None:
        self.code = code
        self.recovery = recovery
        super().__init__(message)


def canonical_json(document: object) -> bytes:
    _reject_noncanonical_numbers(document)
    return json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _reject_noncanonical_numbers(value: object, path: str = "$") -> None:
    if isinstance(value, float):
        raise CatalogVerificationError(
            "catalog_number_unsupported",
            f"Floating-point value is not permitted at {path}.",
            "Publish catalog metadata using integers and strings only.",
        )
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_noncanonical_numbers(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_noncanonical_numbers(item, f"{path}[{index}]")


def parse_json_strict(raw: bytes, *, max_bytes: int = MAX_ENVELOPE_BYTES) -> dict:
    if len(raw) > max_bytes:
        raise CatalogVerificationError(
            "catalog_envelope_too_large",
            "Catalog update exceeds the configured size limit.",
            "Keep the current catalog and use a smaller reviewed snapshot.",
        )

    def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise CatalogVerificationError(
                    "catalog_json_duplicate_key",
                    "Catalog update contains a duplicate JSON key.",
                    "Correct the publisher artifact and retry.",
                )
            result[key] = value
        return result

    try:
        value = json.loads(
            raw,
            object_pairs_hook=pairs_hook,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"invalid constant {token}")
            ),
        )
    except CatalogVerificationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise CatalogVerificationError(
            "catalog_json_invalid",
            "Catalog update is not valid strict JSON.",
            "Correct the publisher artifact and retry.",
        ) from error
    if not isinstance(value, dict):
        raise CatalogVerificationError(
            "catalog_envelope_invalid",
            "Catalog update envelope must be a JSON object.",
            "Correct the publisher artifact and retry.",
        )
    return value


def _envelope_schema() -> dict[str, Any]:
    return json.loads(
        files("tool_registry.catalog")
        .joinpath("catalog-snapshot-envelope.schema.json")
        .read_text("utf-8")
    )


def _datetime(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise CatalogVerificationError(
            "catalog_envelope_invalid",
            f"Catalog {field} must be an RFC 3339 timestamp.",
            "Correct the publisher artifact and retry.",
        )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise CatalogVerificationError(
            "catalog_envelope_invalid",
            f"Catalog {field} must be an RFC 3339 timestamp.",
            "Correct the publisher artifact and retry.",
        ) from error
    if parsed.tzinfo is None:
        raise CatalogVerificationError(
            "catalog_envelope_invalid",
            f"Catalog {field} must include a timezone.",
            "Correct the publisher artifact and retry.",
        )
    return parsed.astimezone(UTC)


def _decode_signature(value: str) -> bytes:
    try:
        decoded = base64.urlsafe_b64decode(value.encode("ascii") + b"==")
    except (UnicodeEncodeError, ValueError) as error:
        raise CatalogVerificationError(
            "catalog_signature_invalid",
            "Catalog update signature could not be verified.",
            "Keep the current catalog and verify the configured update source.",
        ) from error
    if len(decoded) != 64:
        raise CatalogVerificationError(
            "catalog_signature_invalid",
            "Catalog update signature could not be verified.",
            "Keep the current catalog and verify the configured update source.",
        )
    return decoded


def verify_catalog_envelope(
    envelope: dict[str, Any] | bytes,
    *,
    trust_root: CatalogTrustRoot,
    now: datetime,
    minimum_sequence: int,
) -> CatalogSnapshot:
    if isinstance(envelope, bytes):
        document = parse_json_strict(envelope)
        envelope_size = len(envelope)
    else:
        document = envelope
        envelope_size = len(canonical_json(document))
    if envelope_size > MAX_ENVELOPE_BYTES:
        raise CatalogVerificationError(
            "catalog_envelope_too_large",
            "Catalog update exceeds the configured size limit.",
            "Keep the current catalog and use a smaller reviewed snapshot.",
        )

    schema_errors = sorted(
        Draft202012Validator(
            _envelope_schema(), format_checker=FormatChecker()
        ).iter_errors(document),
        key=lambda error: tuple(error.absolute_path),
    )
    if schema_errors:
        raise CatalogVerificationError(
            "catalog_envelope_invalid",
            "Catalog update envelope does not match schema version 1.",
            "Correct the publisher artifact and retry.",
        )

    signed = document["signed"]
    if signed["channel"] != trust_root.channel:
        raise CatalogVerificationError(
            "catalog_channel_mismatch",
            "Catalog update was signed for a different channel.",
            "Keep the current catalog and verify the configured channel.",
        )
    expected_key_id = hashlib.sha256(trust_root.public_key).hexdigest()
    if trust_root.key_id != expected_key_id or signed["key_id"] != trust_root.key_id:
        raise CatalogVerificationError(
            "catalog_key_untrusted",
            "Catalog update signing key is not trusted for this channel.",
            "Keep the current catalog and verify the configured update source.",
        )

    try:
        Ed25519PublicKey.from_public_bytes(trust_root.public_key).verify(
            _decode_signature(document["signature"]), canonical_json(signed)
        )
    except (InvalidSignature, ValueError) as error:
        raise CatalogVerificationError(
            "catalog_signature_invalid",
            "Catalog update signature could not be verified.",
            "Keep the current catalog and verify the configured update source.",
        ) from error

    payload_bytes = canonical_json(signed["payload"])
    payload_digest = hashlib.sha256(payload_bytes).hexdigest()
    if payload_digest != signed["payload_sha256"]:
        raise CatalogVerificationError(
            "catalog_digest_mismatch",
            "Catalog update payload digest does not match its signed metadata.",
            "Keep the current catalog and request a corrected snapshot.",
        )

    now = now.astimezone(UTC)
    issued_at = _datetime(signed["issued_at"], "issued_at")
    expires_at = _datetime(signed["expires_at"], "expires_at")
    if expires_at <= issued_at or issued_at > now + MAX_CLOCK_SKEW:
        raise CatalogVerificationError(
            "catalog_time_invalid",
            "Catalog update has an invalid issue or expiry window.",
            "Keep the current catalog and verify the publisher clock.",
        )
    if expires_at <= now:
        raise CatalogVerificationError(
            "catalog_expired",
            "Catalog update has expired.",
            "Keep the current catalog and request a newer signed snapshot.",
        )
    if signed["sequence"] <= minimum_sequence:
        raise CatalogVerificationError(
            "catalog_sequence_stale",
            "Catalog update does not advance the active sequence.",
            "Keep the current catalog and request a newer signed snapshot.",
        )

    try:
        _validate_catalog_document(signed["payload"])
    except CatalogValidationError as error:
        raise CatalogVerificationError(
            "catalog_payload_invalid",
            "Catalog update payload failed catalog validation.",
            "Keep the current catalog and correct the publisher artifact.",
        ) from error

    snapshot_id = f"{signed['channel']}-{signed['sequence']}-{payload_digest[:20]}"
    return CatalogSnapshot(
        snapshot_id=snapshot_id,
        channel=signed["channel"],
        sequence=signed["sequence"],
        schema_version=signed["schema_version"],
        issued_at=issued_at,
        expires_at=expires_at,
        payload_sha256=payload_digest,
        payload_json=signed["payload"],
        envelope_json=document,
        signer_key_id=signed["key_id"],
        signature=document["signature"],
        verification_state="verified",
        verified_at=now,
    )
