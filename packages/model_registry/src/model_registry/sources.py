"""Injected, bounded source contracts for model acquisition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Mapping, Protocol

from .models import ArtifactDeclaration, ModelPackage


@dataclass(frozen=True, slots=True)
class SourceRequest:
    url: str
    immutable_revision: str
    expected_digest: str
    expected_size: int
    maximum_bytes: int
    allowed_hosts: tuple[str, ...]
    authorization: str | None = None


@dataclass(frozen=True, slots=True)
class SourceResponse:
    status: int
    headers: Mapping[str, str]
    chunks: Iterable[bytes]
    close: Callable[[], None] = lambda: None


@dataclass(frozen=True, slots=True)
class ResumeState:
    content: bytes
    etag: str
    url: str


@dataclass(frozen=True, slots=True)
class AcquiredArtifact:
    content: bytes
    sha256: str
    size: int
    source_uri: str
    etag: str | None = None
    reused: bool = False
    restarted: bool = False


class SourceTransport(Protocol):
    def get(
        self, url: str, *, headers: dict[str, str], timeout: float
    ) -> SourceResponse: ...


class ArtifactSource(Protocol):
    def fetch_artifact(
        self,
        package: ModelPackage,
        artifact: ArtifactDeclaration,
        *,
        maximum_bytes: int,
        is_cancelled: Callable[[], bool],
    ) -> bytes: ...


__all__ = [
    "AcquiredArtifact",
    "ArtifactSource",
    "ResumeState",
    "SourceRequest",
    "SourceResponse",
    "SourceTransport",
]
