from __future__ import annotations

import os
from pathlib import Path

from core.secrets import (
    CredentialReference,
    CredentialStatus,
    SecretProvider,
    configure_default_secret_provider,
)

from .atomic_secret_store import AtomicSecretStore


class EnvironmentSecretProvider:
    def get(self, reference: CredentialReference) -> str | None:
        return os.environ.get(reference.environment_name) or None

    def set(self, reference: CredentialReference, value: str) -> None:
        raise RuntimeError("Environment secrets are read-only")

    def delete(self, reference: CredentialReference) -> None:
        raise RuntimeError("Environment secrets are read-only")

    def status(self, reference: CredentialReference) -> CredentialStatus:
        return CredentialStatus(self.get(reference) is not None, "environment")


class MountedSecretProvider:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory).expanduser()

    def _path(self, reference: CredentialReference) -> Path:
        return self.directory / reference.environment_name

    def get(self, reference: CredentialReference) -> str | None:
        path = self._path(reference)
        if not path.is_file():
            return None
        value = path.read_text(encoding="utf-8").rstrip("\r\n")
        return value or None

    def set(self, reference: CredentialReference, value: str) -> None:
        raise RuntimeError("Mounted secrets are read-only")

    def delete(self, reference: CredentialReference) -> None:
        raise RuntimeError("Mounted secrets are read-only")

    def status(self, reference: CredentialReference) -> CredentialStatus:
        return CredentialStatus(self.get(reference) is not None, "mounted-file")


class FileSecretProvider:
    def __init__(self, path: str | Path):
        self.store = AtomicSecretStore(path)

    def get(self, reference: CredentialReference) -> str | None:
        return self.store.read().get(reference.key)

    def set(self, reference: CredentialReference, value: str) -> None:
        if not value:
            raise ValueError("Secret value must not be empty")
        self.store.set_many({reference.key: value})

    def delete(self, reference: CredentialReference) -> None:
        self.store.set_many({}, {reference.key})

    def status(self, reference: CredentialReference) -> CredentialStatus:
        return CredentialStatus(self.get(reference) is not None, "fallback-file")


class CompositeSecretProvider:
    def __init__(self, providers: list[SecretProvider], writable: SecretProvider):
        self.providers = providers
        self.writable = writable

    def get(self, reference: CredentialReference) -> str | None:
        for provider in self.providers:
            value = provider.get(reference)
            if value is not None:
                return value
        return None

    def set(self, reference: CredentialReference, value: str) -> None:
        self.writable.set(reference, value)

    def delete(self, reference: CredentialReference) -> None:
        self.writable.delete(reference)

    def status(self, reference: CredentialReference) -> CredentialStatus:
        for provider in self.providers:
            status = provider.status(reference)
            if status.configured:
                return status
        return CredentialStatus(False, None)


def create_default_secret_provider() -> CompositeSecretProvider:
    fallback = FileSecretProvider(
        os.environ.get("WRIGHT_SECRETS_PATH", "~/.config/wright/credentials.json")
    )
    mounted = MountedSecretProvider(
        os.environ.get("WRIGHT_SECRETS_DIR", "/run/secrets/wright")
    )
    environment = EnvironmentSecretProvider()
    return CompositeSecretProvider([environment, mounted, fallback], fallback)


def install_default_secret_provider() -> CompositeSecretProvider:
    configure_default_secret_provider(create_default_secret_provider)
    return create_default_secret_provider()
