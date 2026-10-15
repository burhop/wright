from concurrent.futures import ThreadPoolExecutor

import pytest

from data_vault.atomic_secret_store import AtomicSecretStore, SecretStoreError
from core.secrets import CredentialReference
from data_vault import FileSecretProvider


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


def test_colon_owner_credentials_are_isolated_without_changing_legacy_keys(
    tmp_path, monkeypatch
):
    from data_vault.secret_provider import (
        EnvironmentSecretProvider,
        MountedSecretProvider,
    )

    imported = CredentialReference("mcp", "import:draft-abc", "CREDENTIAL_BUNDLE")
    legacy = CredentialReference("mcp", "import_draft-abc", "CREDENTIAL_BUNDLE")
    other = CredentialReference("mcp", "import:draft-def", "CREDENTIAL_BUNDLE")
    assert imported.key == "mcp/import:draft-abc/CREDENTIAL_BUNDLE"
    assert (
        legacy.environment_name
        == "WRIGHT_SECRET_MCP_IMPORT_DRAFT_ABC_CREDENTIAL_BUNDLE"
    )
    assert imported.environment_name.startswith("WRIGHT_SECRET_REF_SHA256_")
    assert (
        len(
            {imported.environment_name, legacy.environment_name, other.environment_name}
        )
        == 3
    )
    file = FileSecretProvider(tmp_path / "credentials.json")
    file.set(imported, "fixture-imported")
    file.set(legacy, "fixture-legacy")
    assert file.get(imported) == "fixture-imported"
    assert file.get(legacy) == "fixture-legacy"
    assert file.get(other) is None
    monkeypatch.setenv(legacy.environment_name, "fixture-legacy-env")
    environment = EnvironmentSecretProvider()
    assert environment.get(imported) is None
    monkeypatch.setenv(imported.environment_name, "fixture-imported-env")
    assert environment.get(imported) == "fixture-imported-env"
    assert environment.get(legacy) == "fixture-legacy-env"
    mounted = MountedSecretProvider(tmp_path)
    (tmp_path / imported.environment_name).write_text("fixture-mounted")
    assert mounted.get(imported) == "fixture-mounted"
    assert mounted.get(other) is None
    file.delete(imported)
    assert file.get(imported) is None
    assert file.get(legacy) == "fixture-legacy"


@pytest.mark.parametrize(
    "owner",
    ["import:../escape", "import:bad/name", "import:bad\\name", "import:bad\nname"],
)
def test_colon_owner_still_rejects_unsafe_path_characters(owner):
    with pytest.raises(ValueError, match="invalid"):
        CredentialReference("mcp", owner, "CREDENTIAL_BUNDLE")
