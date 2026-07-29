from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from wright_engineering import appliance


class _Response:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_appliance_status_forwards_optional_token_and_returns_document(
    monkeypatch,
) -> None:
    requests = []

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return _Response({"status": "healthy"})

    monkeypatch.setenv("WRIGHT_API_TOKEN", "test-secret-value")
    monkeypatch.setattr(appliance, "urlopen", fake_urlopen)
    assert appliance.appliance_status("http://127.0.0.1:8000/") == {"status": "healthy"}
    assert requests[0][0].headers["Authorization"] == "Bearer test-secret-value"
    assert requests[0][1] == 5


def test_appliance_status_rejects_transport_and_non_object_payloads(
    monkeypatch,
) -> None:
    def unavailable(*_args, **_kwargs):
        raise URLError("offline")

    monkeypatch.setattr(appliance, "urlopen", unavailable)
    with pytest.raises(appliance.ApplianceError, match="URLError"):
        appliance.appliance_status("http://127.0.0.1:8000")

    monkeypatch.setattr(
        appliance, "urlopen", lambda *_args, **_kwargs: _Response(["invalid"])
    )
    with pytest.raises(appliance.ApplianceError, match="invalid health document"):
        appliance.appliance_status("http://127.0.0.1:8000")
