from concurrent.futures import ThreadPoolExecutor

import pytest

from core.atomic_secret_store import AtomicSecretStore, SecretStoreError
from core.secrets import CredentialReference, FileSecretProvider


def test_file_provider_returns_status_without_serializing_value(tmp_path):
    provider = FileSecretProvider(tmp_path / "credentials.json")
    reference = CredentialReference("global", "", "OPENAI_API_KEY")

    provider.set(reference, "sensitive-value")

    assert provider.get(reference) == "sensitive-value"
    status = provider.status(reference)
    assert status.configured is True
    assert "sensitive-value" not in repr(status)


def test_atomic_store_preserves_all_concurrent_updates(tmp_path):
    path = tmp_path / "credentials.json"

    def write(index: int) -> None:
        AtomicSecretStore(path).set_many({f"key-{index}": f"value-{index}"})

    with ThreadPoolExecutor(max_workers=16) as executor:
        list(executor.map(write, range(100)))

    stored = AtomicSecretStore(path).read()
    assert stored == {f"key-{index}": f"value-{index}" for index in range(100)}


def test_atomic_store_fails_closed_on_corrupt_data(tmp_path):
    path = tmp_path / "credentials.json"
    path.write_text("{broken", encoding="utf-8")

    with pytest.raises(SecretStoreError, match="corrupt"):
        AtomicSecretStore(path).read()


def test_reference_rejects_path_characters():
    with pytest.raises(ValueError, match="invalid"):
        CredentialReference("mcp", "../escape", "TOKEN")
