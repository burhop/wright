from __future__ import annotations

import hashlib
import uuid
from pathlib import Path

import pytest

from data_vault.native_process_artifacts import NativeArtifactStore
from data_vault.native_process_repository import NativeRepositoryError


class ConfinedTestPaths:
    """Test path capability; real workspace-service confinement is tested above it."""

    def __init__(self, root):
        self.root = root.resolve()

    def resolve(self, user_path: str, *, must_exist=False):
        candidate = self.root / user_path
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root) or resolved != candidate:
            raise ValueError("Unconfined path")
        if must_exist and not resolved.exists():
            raise FileNotFoundError(user_path)
        return resolved


def test_generated_storage_and_digest_verification_include_device_filename_metadata(
    tmp_path,
):
    store = NativeArtifactStore(ConfinedTestPaths(tmp_path))
    run_id = str(uuid.uuid4())
    record = store.promote(
        run_id,
        b"Mass: 135 g",
        filename="CON.txt",
        port_id="mass-artifact",
        provenance={"operation": "artifact.write-text@1"},
    )
    assert Path(record["storage_key"]).suffix == ".bin"
    assert "CON.txt" not in record["storage_key"]
    indexed = {**record, "run_id": run_id}
    assert store.read(indexed) == b"Mass: 135 g"
    assert record["content_digest"] == hashlib.sha256(b"Mass: 135 g").hexdigest()
    (tmp_path / record["storage_key"]).write_bytes(b"Mass: 999 g")
    with pytest.raises(NativeRepositoryError, match="recorded evidence"):
        store.read(indexed)


def test_artifact_identity_and_size_limits_reject_without_escape(tmp_path):
    store = NativeArtifactStore(ConfinedTestPaths(tmp_path))
    run_id = str(uuid.uuid4())
    record = store.promote(
        run_id, b"verified", filename="file.txt", port_id="output-port", provenance={}
    )
    with pytest.raises(NativeRepositoryError):
        store.read({**record, "run_id": str(uuid.uuid4())})
    with pytest.raises(NativeRepositoryError):
        store.read({**record, "run_id": run_id, "storage_key": "../outside.bin"})
    with pytest.raises(NativeRepositoryError):
        store.promote(
            "../../outside",
            b"bad",
            filename="file.txt",
            port_id="output-port",
            provenance={},
        )
    with pytest.raises(NativeRepositoryError):
        store.promote(
            run_id,
            b"x" * (10 * 1024 * 1024 + 1),
            filename="file.txt",
            port_id="output-port",
            provenance={},
        )


def test_reconciliation_removes_only_generated_unindexed_residue(tmp_path):
    store = NativeArtifactStore(ConfinedTestPaths(tmp_path))
    run_id = str(uuid.uuid4())
    retained = store.promote(
        run_id, b"keep", filename="keep.txt", port_id="output-port", provenance={}
    )
    orphan = store.promote(
        run_id, b"orphan", filename="orphan.txt", port_id="output-port", provenance={}
    )
    root = tmp_path / ".wright/native/staging"
    generated = root / f"{uuid.uuid4()}.tmp"
    generated.write_bytes(b"partial")
    unrelated = root / "user-note.tmp"
    unrelated.write_bytes(b"user note")
    result = store.reconcile(frozenset({retained["storage_key"]}))
    assert result["residue"] == []
    assert orphan["storage_key"] in result["removed"]
    assert not generated.exists()
    assert unrelated.read_bytes() == b"user note"
    assert store.read({**retained, "run_id": run_id}) == b"keep"


def test_confined_input_and_cancelled_unindexed_cleanup(tmp_path):
    store = NativeArtifactStore(ConfinedTestPaths(tmp_path))
    source = tmp_path / "input.txt"
    source.write_bytes(b"actual input")
    assert store.input_bytes("input.txt") == b"actual input"
    with pytest.raises(ValueError):
        store.input_bytes("../outside.txt")
    with pytest.raises(NativeRepositoryError):
        store.input_bytes(".")
    run_id = str(uuid.uuid4())
    promoted = store.promote(
        run_id, b"late", filename="late.md", port_id="output-port", provenance={}
    )
    assert store.discard_unindexed(run_id, promoted)
    assert store.discard_unindexed(run_id, promoted)
    assert not (tmp_path / promoted["storage_key"]).exists()
