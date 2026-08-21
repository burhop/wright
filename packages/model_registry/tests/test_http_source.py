from __future__ import annotations

import hashlib

import pytest

from model_registry.http_source import (
    HttpArtifactSource,
    HttpPackageArtifactSource,
    HttpSourceError,
    SourceRequest,
    SourceResponse,
)
from model_registry.models import ModelPackage
from fixture_factory import generate_affine_fixture


class QueueTransport:
    def __init__(self, *responses: SourceResponse) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, dict[str, str], float]] = []

    def get(self, url: str, *, headers: dict[str, str], timeout: float):
        self.requests.append((url, dict(headers), timeout))
        return self.responses.pop(0)


class TimeoutTransport:
    def get(self, url: str, *, headers: dict[str, str], timeout: float):
        raise TimeoutError("synthetic timeout")


def request(content: bytes, **changes) -> SourceRequest:
    values = {
        "url": "https://models.example/revisions/rev-123/model.bin",
        "immutable_revision": "rev-123",
        "expected_digest": hashlib.sha256(content).hexdigest(),
        "expected_size": len(content),
        "maximum_bytes": len(content),
        "allowed_hosts": ("models.example",),
    }
    values.update(changes)
    return SourceRequest(**values)


def test_https_source_streams_exact_pinned_content_and_digest() -> None:
    content = b"reviewed-model-data"
    transport = QueueTransport(
        SourceResponse(
            status=200,
            headers={"Content-Length": str(len(content)), "ETag": '"v1"'},
            chunks=(content[:5], content[5:]),
        )
    )
    result = HttpArtifactSource(transport).fetch(request(content))

    assert result.content == content
    assert result.sha256 == hashlib.sha256(content).hexdigest()
    assert result.etag == '"v1"'
    assert transport.requests[0][0].startswith("https://")


@pytest.mark.parametrize(
    ("response", "code"),
    [
        (SourceResponse(200, {"Content-Length": "99"}, (b"x",)), "size_exceeded"),
        (
            SourceResponse(200, {"Content-Length": "1"}, (b"different",)),
            "size_exceeded",
        ),
        (SourceResponse(200, {"Content-Length": "1"}, (b"x",)), "digest_mismatch"),
    ],
)
def test_https_source_rejects_length_overrun_truncation_and_digest(
    response: SourceResponse, code: str
) -> None:
    transport = QueueTransport(response)
    with pytest.raises(HttpSourceError) as raised:
        HttpArtifactSource(transport).fetch(request(b"expected", maximum_bytes=8))
    assert raised.value.code == code


def test_redirects_are_bounded_host_checked_and_strip_authorization() -> None:
    content = b"ok"
    transport = QueueTransport(
        SourceResponse(302, {"Location": "https://cdn.example/rev-123/model.bin"}, ()),
        SourceResponse(200, {"Content-Length": "2"}, (content,)),
    )
    result = HttpArtifactSource(transport).fetch(
        request(
            content,
            allowed_hosts=("models.example", "cdn.example"),
            authorization="Bearer synthetic-do-not-log",
        )
    )
    assert result.content == content
    assert transport.requests[0][1]["Authorization"].startswith("Bearer")
    assert "Authorization" not in transport.requests[1][1]

    denied = QueueTransport(
        SourceResponse(302, {"Location": "https://unapproved.example/model.bin"}, ())
    )
    with pytest.raises(HttpSourceError) as raised:
        HttpArtifactSource(denied).fetch(request(content))
    assert raised.value.code == "source_host_unapproved"


def test_source_requires_https_exact_revision_timeout_and_cancellation() -> None:
    content = b"ok"
    source = HttpArtifactSource(QueueTransport())
    for changed, code in [
        (
            {"url": "http://models.example/revisions/rev-123/model.bin"},
            "source_insecure",
        ),
        ({"url": "https://models.example/latest/model.bin"}, "source_changed"),
    ]:
        with pytest.raises(HttpSourceError) as raised:
            source.fetch(request(content, **changed))
        assert raised.value.code == code

    cancelled = HttpArtifactSource(
        QueueTransport(SourceResponse(200, {"Content-Length": "2"}, (b"o", b"k")))
    )
    with pytest.raises(HttpSourceError) as raised:
        cancelled.fetch(request(content), is_cancelled=lambda: True)
    assert raised.value.code == "cancelled"

    with pytest.raises(HttpSourceError) as raised:
        HttpArtifactSource(TimeoutTransport(), timeout=0.01).fetch(request(content))
    assert raised.value.code == "source_unavailable"

    truncated = QueueTransport(
        SourceResponse(200, {"Content-Length": "1"}, (content[:1],))
    )
    with pytest.raises(HttpSourceError) as raised:
        HttpArtifactSource(truncated).fetch(request(content))
    assert raised.value.code == "digest_mismatch"


def test_package_source_uses_exact_declaration_and_opaque_authorization(
    tmp_path,
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    document = fixture.package.model_dump(mode="json")
    document["source"] = {
        "kind": "https",
        "uri": "https://models.example/revisions/rev-123",
        "immutable_revision": "rev-123",
        "access": "public",
        "allowed_hosts": ["models.example"],
    }
    artifact = document["variants"][0]["artifacts"][0]
    content = fixture.artifacts[artifact["path"]]
    artifact["source_uri"] = (
        f"https://models.example/revisions/rev-123/{artifact['path']}"
    )
    package = ModelPackage.model_validate(document)
    transport = QueueTransport(
        SourceResponse(200, {"Content-Length": str(len(content))}, (content,))
    )
    source = HttpPackageArtifactSource(
        HttpArtifactSource(transport),
        authorization_provider=lambda: "Bearer synthetic-test-only",
    )

    result = source.fetch_artifact(
        package,
        package.variants[0].artifacts[0],
        maximum_bytes=len(content),
        is_cancelled=lambda: False,
    )
    assert result == content
    assert transport.requests[0][1]["Authorization"] == "Bearer synthetic-test-only"
