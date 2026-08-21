from __future__ import annotations

import hashlib
import stat

import pytest

from data_vault.model_artifact_store import ModelArtifactStore


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def test_stage_verify_promote_deduplicate_and_activate(tmp_path) -> None:
    store = ModelArtifactStore(tmp_path / "wright-data")
    content = b'{"scale":2,"offset":1}'
    content_digest = digest(content)

    stage = store.stage_bytes(
        operation_id="operation-1",
        expected_digest=content_digest,
        content=content,
        maximum_bytes=len(content),
    )
    assert stage.state == "staging"
    first = store.promote(stage)
    assert first.state == "verified"
    assert first.created is True
    second_stage = store.stage_bytes(
        operation_id="operation-2",
        expected_digest=content_digest,
        content=content,
        maximum_bytes=len(content),
    )
    second = store.promote(second_stage)
    assert second.created is False
    assert store.read_verified(content_digest) == content

    activation = store.activate(
        installation_id="installation-1",
        manifest_digest="a" * 64,
        artifacts={"model/coefficients.json": content_digest},
    )
    assert activation["installation_id"] == "installation-1"
    assert store.read_activation("installation-1") == activation


def test_stage_rejects_overrun_digest_mismatch_and_unsafe_identity(tmp_path) -> None:
    store = ModelArtifactStore(tmp_path / "wright-data")
    content = b"content"
    with pytest.raises(ValueError, match="maximum"):
        store.stage_bytes(
            operation_id="operation-1",
            expected_digest=digest(content),
            content=content,
            maximum_bytes=1,
        )
    with pytest.raises(ValueError, match="digest"):
        store.stage_bytes(
            operation_id="operation-1",
            expected_digest="a" * 64,
            content=content,
            maximum_bytes=len(content),
        )
    with pytest.raises(ValueError):
        store.stage_bytes(
            operation_id="../escape",
            expected_digest=digest(content),
            content=content,
            maximum_bytes=len(content),
        )


def test_verified_content_is_immutable_and_corruption_is_quarantined(tmp_path) -> None:
    store = ModelArtifactStore(tmp_path / "wright-data")
    content = b"trusted"
    key = digest(content)
    promoted = store.promote(
        store.stage_bytes(
            operation_id="operation-1",
            expected_digest=key,
            content=content,
            maximum_bytes=len(content),
        )
    )
    promoted.path.chmod(stat.S_IWRITE | stat.S_IREAD)
    promoted.path.write_bytes(b"corrupt")
    report = store.reconcile()
    assert key in report.quarantined_digests
    assert not store.has_verified(key)


def test_cleanup_is_confined_and_reports_residue(tmp_path) -> None:
    root = tmp_path / "wright-data"
    outside = tmp_path / "outside.txt"
    outside.write_text("keep", encoding="utf-8")
    store = ModelArtifactStore(root)
    content = b"partial"
    key = digest(content)
    store.stage_bytes(
        operation_id="operation-1",
        expected_digest=key,
        content=content,
        maximum_bytes=len(content),
    )
    result = store.cleanup_staging("operation-1")
    assert result.state == "clean"
    assert outside.read_text(encoding="utf-8") == "keep"
