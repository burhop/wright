from __future__ import annotations

import hashlib
import json

from data_vault.model_artifact_store import ModelArtifactStore


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def test_restart_keeps_partials_untrusted_and_verified_content_available(
    tmp_path,
) -> None:
    root = tmp_path / "wright-data"
    store = ModelArtifactStore(root)
    partial = b"partial"
    verified = b"verified"
    store.stage_bytes(
        operation_id="partial-operation",
        expected_digest=digest(partial),
        content=partial,
        maximum_bytes=len(partial),
    )
    store.promote(
        store.stage_bytes(
            operation_id="verified-operation",
            expected_digest=digest(verified),
            content=verified,
            maximum_bytes=len(verified),
        )
    )

    restarted = ModelArtifactStore(root)
    report = restarted.reconcile()

    assert report.partial_operations == ("partial-operation",)
    assert restarted.has_verified(digest(verified))
    assert not restarted.has_verified(digest(partial))


def test_unknown_objects_and_invalid_activation_are_quarantined(tmp_path) -> None:
    root = tmp_path / "wright-data"
    store = ModelArtifactStore(root)
    unknown = store.objects_root / "sha256" / "ff" / ("f" * 64)
    unknown.parent.mkdir(parents=True, exist_ok=True)
    unknown.write_bytes(b"unknown-content")
    activation = store.installations_root / "installation-1.json"
    activation.parent.mkdir(parents=True, exist_ok=True)
    activation.write_text(
        json.dumps(
            {
                "installation_id": "installation-1",
                "manifest_digest": "a" * 64,
                "artifacts": {"model/value.json": "e" * 64},
            }
        ),
        encoding="utf-8",
    )

    report = store.reconcile()

    assert "f" * 64 in report.quarantined_digests
    assert report.missing_installations == ("installation-1",)
