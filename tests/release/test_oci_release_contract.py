import pytest

from scripts.release.oci import OciPolicyError, verify_promotion


def test_promotion_requires_identical_digest() -> None:
    digest = "sha256:" + "a" * 64
    verify_promotion(digest, digest)
    with pytest.raises(OciPolicyError, match="differs"):
        verify_promotion(digest, "sha256:" + "b" * 64)


def test_promotion_rejects_mutable_tag_as_subject() -> None:
    with pytest.raises(OciPolicyError, match="immutable"):
        verify_promotion("ghcr.io/burhop/wright:latest", "sha256:" + "a" * 64)
