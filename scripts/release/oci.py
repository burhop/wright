from __future__ import annotations

import re


DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


class OciPolicyError(ValueError):
    """Raised when OCI promotion would change the tested subject."""


def require_digest(value: str) -> str:
    if not DIGEST.fullmatch(value):
        raise OciPolicyError(f"invalid immutable OCI digest: {value!r}")
    return value


def verify_promotion(source_digest: str, destination_digest: str) -> None:
    require_digest(source_digest)
    require_digest(destination_digest)
    if source_digest != destination_digest:
        raise OciPolicyError(
            f"promoted manifest differs: {source_digest} != {destination_digest}"
        )
