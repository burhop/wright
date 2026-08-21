"""Pinned HTTPS acquisition with redirect, resume, byte, and digest controls."""

from __future__ import annotations

import hashlib
import re
from typing import Callable
from urllib.parse import urljoin, urlsplit

import httpx

from .models import ArtifactDeclaration, ModelPackage
from .sources import (
    AcquiredArtifact,
    ResumeState,
    SourceRequest,
    SourceResponse,
    SourceTransport,
)

_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_STRONG_ETAG = re.compile(r'^"[^"\r\n]+"$')
_RANGE = re.compile(r"^bytes (\d+)-(\d+)/(\d+)$")


class HttpSourceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class HttpxSourceTransport:
    """Production streaming transport; redirect policy remains in HttpArtifactSource."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(follow_redirects=False)

    def get(
        self, url: str, *, headers: dict[str, str], timeout: float
    ) -> SourceResponse:
        request = self.client.build_request(
            "GET", url, headers=headers, timeout=timeout
        )
        try:
            response = self.client.send(request, stream=True)
        except httpx.TimeoutException as error:
            raise TimeoutError("Model source timed out") from error
        except httpx.HTTPError as error:
            raise OSError("Model source transport failed") from error
        return SourceResponse(
            status=response.status_code,
            headers=dict(response.headers),
            chunks=response.iter_bytes(),
            close=response.close,
        )


def _header(headers, name: str) -> str | None:
    lower = name.lower()
    for key, value in headers.items():
        if str(key).lower() == lower:
            return str(value)
    return None


class HttpArtifactSource:
    def __init__(
        self,
        transport: SourceTransport,
        *,
        timeout: float = 30.0,
        maximum_redirects: int = 5,
    ) -> None:
        if timeout <= 0 or not 0 <= maximum_redirects <= 10:
            raise ValueError("HTTP source limits are invalid")
        self.transport = transport
        self.timeout = timeout
        self.maximum_redirects = maximum_redirects

    def _validate_request(self, request: SourceRequest) -> None:
        parsed = urlsplit(request.url)
        if parsed.scheme != "https":
            raise HttpSourceError("source_insecure", "Model acquisition requires HTTPS")
        if not parsed.hostname or parsed.hostname.lower() not in {
            host.lower() for host in request.allowed_hosts
        }:
            raise HttpSourceError(
                "source_host_unapproved", "The source host is not approved"
            )
        if request.immutable_revision not in request.url:
            raise HttpSourceError(
                "source_changed", "The source URL does not contain the exact revision"
            )
        if (
            not _DIGEST.fullmatch(request.expected_digest)
            or request.expected_size < 0
            or request.maximum_bytes < request.expected_size
        ):
            raise HttpSourceError("manifest_invalid", "Source bounds are invalid")

    def fetch(
        self,
        request: SourceRequest,
        *,
        resume: ResumeState | None = None,
        cached_content: bytes | None = None,
        is_cancelled: Callable[[], bool] = lambda: False,
    ) -> AcquiredArtifact:
        self._validate_request(request)
        if cached_content is not None:
            digest = hashlib.sha256(cached_content).hexdigest()
            if (
                digest == request.expected_digest
                and len(cached_content) == request.expected_size
            ):
                return AcquiredArtifact(
                    cached_content,
                    digest,
                    len(cached_content),
                    request.url,
                    reused=True,
                )
        if is_cancelled():
            raise HttpSourceError("cancelled", "Model acquisition was cancelled")

        headers: dict[str, str] = {}
        partial = b""
        restarted = False
        if request.authorization:
            headers["Authorization"] = request.authorization
        if resume is not None:
            if (
                resume.url != request.url
                or not _STRONG_ETAG.fullmatch(resume.etag)
                or len(resume.content) >= request.expected_size
            ):
                raise HttpSourceError(
                    "source_changed", "The partial content cannot be resumed safely"
                )
            partial = resume.content
            headers["Range"] = f"bytes={len(partial)}-"
            headers["If-Range"] = resume.etag

        url = request.url
        allowed = {host.lower() for host in request.allowed_hosts}
        response: SourceResponse | None = None
        for redirect_count in range(self.maximum_redirects + 1):
            if is_cancelled():
                raise HttpSourceError("cancelled", "Model acquisition was cancelled")
            try:
                response = self.transport.get(
                    url, headers=dict(headers), timeout=self.timeout
                )
            except TimeoutError as error:
                raise HttpSourceError(
                    "source_unavailable", "Model acquisition timed out"
                ) from error
            except OSError as error:
                raise HttpSourceError(
                    "source_unavailable", "Model acquisition transport failed"
                ) from error
            if response.status not in {301, 302, 303, 307, 308}:
                break
            location = _header(response.headers, "Location")
            response.close()
            if not location or redirect_count == self.maximum_redirects:
                raise HttpSourceError(
                    "source_unavailable", "The source redirect limit was exceeded"
                )
            target = urljoin(url, location)
            parsed = urlsplit(target)
            if parsed.scheme != "https" or not parsed.hostname:
                raise HttpSourceError(
                    "source_insecure", "A model redirect left approved HTTPS"
                )
            if parsed.hostname.lower() not in allowed:
                raise HttpSourceError(
                    "source_host_unapproved", "A model redirect used an unapproved host"
                )
            if urlsplit(url).hostname != parsed.hostname:
                headers.pop("Authorization", None)
            url = target
        if response is None:
            raise HttpSourceError("source_unavailable", "The source did not respond")

        try:
            if response.status not in {200, 206}:
                raise HttpSourceError(
                    "source_unavailable", f"The source returned HTTP {response.status}"
                )
            response_etag = _header(response.headers, "ETag")
            if response.status == 206:
                if resume is None:
                    raise HttpSourceError(
                        "source_changed", "An unsolicited partial response was rejected"
                    )
                content_range = _header(response.headers, "Content-Range") or ""
                match = _RANGE.fullmatch(content_range)
                if (
                    not match
                    or int(match.group(1)) != len(partial)
                    or int(match.group(2)) != request.expected_size - 1
                    or int(match.group(3)) != request.expected_size
                    or response_etag != resume.etag
                ):
                    raise HttpSourceError(
                        "source_changed", "The resumed representation changed"
                    )
            elif resume is not None:
                partial = b""
                restarted = True
            length = _header(response.headers, "Content-Length")
            if length is not None:
                try:
                    declared_length = int(length)
                except ValueError as error:
                    raise HttpSourceError(
                        "source_changed", "The source length is invalid"
                    ) from error
                if (
                    declared_length < 0
                    or len(partial) + declared_length > request.maximum_bytes
                ):
                    raise HttpSourceError(
                        "size_exceeded", "The source exceeds the confirmed byte ceiling"
                    )
            value = bytearray(partial)
            for chunk in response.chunks:
                if is_cancelled():
                    raise HttpSourceError(
                        "cancelled", "Model acquisition was cancelled"
                    )
                if not isinstance(chunk, bytes):
                    raise HttpSourceError(
                        "source_changed", "The source returned invalid bytes"
                    )
                value.extend(chunk)
                if len(value) > request.maximum_bytes:
                    raise HttpSourceError(
                        "size_exceeded", "The source exceeds the confirmed byte ceiling"
                    )
            content = bytes(value)
            digest = hashlib.sha256(content).hexdigest()
            if digest != request.expected_digest:
                raise HttpSourceError(
                    "digest_mismatch", "The acquired artifact digest did not match"
                )
            if len(content) != request.expected_size:
                raise HttpSourceError(
                    "source_changed", "The acquired artifact size did not match"
                )
            return AcquiredArtifact(
                content,
                digest,
                len(content),
                url,
                etag=response_etag,
                restarted=restarted,
            )
        finally:
            response.close()


class HttpPackageArtifactSource:
    """Adapt exact package declarations to the generic lifecycle source port."""

    def __init__(
        self,
        source: HttpArtifactSource | None = None,
        *,
        authorization_provider: Callable[[], str] | None = None,
    ) -> None:
        self.source = source or HttpArtifactSource(HttpxSourceTransport())
        self.authorization_provider = authorization_provider

    def fetch_artifact(
        self,
        package: ModelPackage,
        artifact: ArtifactDeclaration,
        *,
        maximum_bytes: int,
        is_cancelled: Callable[[], bool],
    ) -> bytes:
        allowed_hosts = package.source.allowed_hosts
        if not allowed_hosts:
            raise HttpSourceError(
                "source_host_unapproved", "The package declares no approved source host"
            )
        authorization = (
            self.authorization_provider()
            if self.authorization_provider is not None
            else None
        )
        result = self.source.fetch(
            SourceRequest(
                url=artifact.source_uri,
                immutable_revision=package.source.immutable_revision,
                expected_digest=artifact.sha256,
                expected_size=artifact.size,
                maximum_bytes=min(maximum_bytes, artifact.size),
                allowed_hosts=allowed_hosts,
                authorization=authorization,
            ),
            is_cancelled=is_cancelled,
        )
        return result.content


__all__ = [
    "HttpArtifactSource",
    "HttpPackageArtifactSource",
    "HttpSourceError",
    "HttpxSourceTransport",
    "ResumeState",
    "SourceRequest",
    "SourceResponse",
]
