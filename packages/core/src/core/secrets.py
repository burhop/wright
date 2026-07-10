"""Side-effect-neutral secret references, status, and provider contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from collections.abc import Callable
from typing import Protocol

_PART_RE = re.compile(r"^[A-Za-z0-9_.-]*$")
_default_provider_factory: Callable[[], SecretProvider] | None = None


@dataclass(frozen=True)
class CredentialReference:
    namespace: str
    owner_id: str
    name: str

    def __post_init__(self) -> None:
        if self.namespace not in {"global", "workspace", "mcp", "integration"}:
            raise ValueError("Unsupported credential namespace")
        if not _PART_RE.fullmatch(self.owner_id):
            raise ValueError("Credential owner_id has invalid characters")
        if not self.name or not _PART_RE.fullmatch(self.name):
            raise ValueError("Credential name has invalid characters")

    @property
    def key(self) -> str:
        return "/".join((self.namespace, self.owner_id or "_", self.name.upper()))

    @property
    def environment_name(self) -> str:
        encoded = re.sub(r"[^A-Za-z0-9]", "_", self.key).upper()
        return f"WRIGHT_SECRET_{encoded}"


@dataclass(frozen=True)
class CredentialStatus:
    configured: bool
    source: str | None = None


class SecretProvider(Protocol):
    def get(self, reference: CredentialReference) -> str | None: ...

    def set(self, reference: CredentialReference, value: str) -> None: ...

    def delete(self, reference: CredentialReference) -> None: ...

    def status(self, reference: CredentialReference) -> CredentialStatus: ...


def configure_default_secret_provider(
    provider_or_factory: SecretProvider | Callable[[], SecretProvider],
) -> None:
    global _default_provider_factory
    if callable(provider_or_factory):
        _default_provider_factory = provider_or_factory
    else:
        provider = provider_or_factory

        def configured_provider() -> SecretProvider:
            return provider

        _default_provider_factory = configured_provider


def default_secret_provider() -> SecretProvider:
    if _default_provider_factory is None:
        raise RuntimeError("Secret provider has not been configured by composition")
    return _default_provider_factory()
