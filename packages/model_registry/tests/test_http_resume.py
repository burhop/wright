from __future__ import annotations

import hashlib

import pytest

from model_registry.http_source import (
    HttpArtifactSource,
    HttpSourceError,
    ResumeState,
    SourceRequest,
    SourceResponse,
)


class QueueTransport:
    def __init__(self, *responses: SourceResponse) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, str]] = []

    def get(self, url: str, *, headers: dict[str, str], timeout: float):
        self.requests.append(dict(headers))
        return self.responses.pop(0)


def source_request(content: bytes) -> SourceRequest:
    return SourceRequest(
        url="https://models.example/revisions/rev-123/model.bin",
        immutable_revision="rev-123",
        expected_digest=hashlib.sha256(content).hexdigest(),
        expected_size=len(content),
        maximum_bytes=len(content),
        allowed_hosts=("models.example",),
    )


def test_resume_requires_strong_validator_and_valid_content_range() -> None:
    content = b"abcdefgh"
    transport = QueueTransport(
        SourceResponse(
            206,
            {"Content-Range": "bytes 3-7/8", "ETag": '"v1"'},
            (content[3:],),
        )
    )
    result = HttpArtifactSource(transport).fetch(
        source_request(content),
        resume=ResumeState(content[:3], '"v1"', source_request(content).url),
    )
    assert result.content == content
    assert transport.requests == [{"Range": "bytes=3-", "If-Range": '"v1"'}]

    for validator in ("", 'W/"weak"'):
        with pytest.raises(HttpSourceError) as raised:
            HttpArtifactSource(QueueTransport()).fetch(
                source_request(content),
                resume=ResumeState(content[:3], validator, source_request(content).url),
            )
        assert raised.value.code == "source_changed"


def test_resume_restarts_when_server_returns_full_changed_representation() -> None:
    content = b"abcdefgh"
    transport = QueueTransport(
        SourceResponse(200, {"Content-Length": "8", "ETag": '"v2"'}, (content,))
    )
    result = HttpArtifactSource(transport).fetch(
        source_request(content),
        resume=ResumeState(b"old", '"v1"', source_request(content).url),
    )
    assert result.content == content
    assert result.restarted is True


def test_resume_rejects_wrong_range_or_changed_partial_etag() -> None:
    content = b"abcdefgh"
    for headers in (
        {"Content-Range": "bytes 4-7/8", "ETag": '"v1"'},
        {"Content-Range": "bytes 3-7/8", "ETag": '"v2"'},
    ):
        with pytest.raises(HttpSourceError) as raised:
            HttpArtifactSource(
                QueueTransport(SourceResponse(206, headers, (content[3:],)))
            ).fetch(
                source_request(content),
                resume=ResumeState(content[:3], '"v1"', source_request(content).url),
            )
        assert raised.value.code == "source_changed"


def test_verified_cache_reuse_makes_zero_requests() -> None:
    content = b"abcdefgh"
    transport = QueueTransport()
    result = HttpArtifactSource(transport).fetch(
        source_request(content), cached_content=content
    )
    assert result.reused is True
    assert transport.requests == []
