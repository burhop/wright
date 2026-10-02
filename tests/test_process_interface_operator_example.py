"""The operator example reads scoped native state and cannot submit work."""

import argparse
import importlib.util
from pathlib import Path

import httpx
import pytest

from core.process_interactions import ProcessRef
from core.process_interfaces import AuthoringJob, CodingRole, RoleResolution

spec = importlib.util.spec_from_file_location(
    "operator_example",
    Path(__file__).parents[1] / "examples/process-interfaces/inspect_interface.py",
)
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


def process():
    return ProcessRef(
        workspace_id="workspace",
        source_path="workflows/example.wflow",
        source_digest="a" * 64,
    )


def capabilities():
    return {
        "process": process().model_dump(mode="json"),
        "role": "process-ui-author/1",
        "available": True,
        "compiler": {"private_location": "not printed"},
        "compiler_reason": None,
        "model": {
            "adapter": "controlled",
            "available": True,
            "effective_instructions_every_turn": True,
            "no_tools": True,
            "inherited_default_model": True,
            "model_reference": "default-model",
        },
    }


def client(body, requests, status=200):
    def respond(request):
        requests.append(request)
        return httpx.Response(status, json=body)

    return httpx.Client(
        base_url="http://127.0.0.1:8030",
        transport=httpx.MockTransport(respond),
        follow_redirects=False,
    )


def test_capabilities_read_uses_exact_scope_and_omits_private_locations():
    requests = []
    with client(capabilities(), requests) as transport:
        result = example.inspect(transport, process(), "session")
    assert result["available"] is True and result["compiler_available"] is True
    assert "private_location" not in result
    assert len(requests) == 1 and requests[0].method == "GET"
    assert dict(requests[0].url.params) == {
        "session_id": "session",
        "path": process().source_path,
        "expected_storage_digest": "a" * 64,
    }


def test_job_read_validates_native_contract_and_exact_job_without_submission():
    role = RoleResolution(
        profile=CodingRole(instructions_version="1", instructions_digest="b" * 64),
        adapter="controlled",
        model_reference="default-model",
        configuration_digest="c" * 64,
        effective_instructions_digest="b" * 64,
    )
    job = AuthoringJob(
        job_id="job-one",
        request_id="request-one",
        request_digest="d" * 64,
        process=process(),
        role_resolution=role,
        state="queued",
        created_at="2026-10-02T00:00:00Z",
        updated_at="2026-10-02T00:00:00Z",
    )
    requests = []
    with client(
        {"job": job.model_dump(mode="json"), "preview": None}, requests
    ) as transport:
        assert (
            example.inspect(transport, process(), "session", "job-one")["state"]
            == "queued"
        )
    assert len(requests) == 1 and requests[0].method == "GET"
    with client({"job": job.model_dump(mode="json")}, []) as transport:
        with pytest.raises(ValueError):
            example.inspect(transport, process(), "session", "job-two")


@pytest.mark.parametrize(
    "field,value",
    [
        ("workspace_id", "foreign"),
        ("source_path", "workflows/other.wflow"),
        ("source_digest", "e" * 64),
    ],
)
def test_foreign_response_is_rejected(field, value):
    body = capabilities()
    body["process"][field] = value
    with client(body, []) as transport:
        with pytest.raises(ValueError):
            example.inspect(transport, process(), "session")


@pytest.mark.parametrize(
    "url",
    [
        "http://user:secret@localhost",
        "http://localhost/api",
        "http://localhost?token=secret",
        "file:///tmp/test",
        "http://localhost/#fragment",
    ],
)
def test_origin_rejects_credentials_paths_and_non_http(url):
    with pytest.raises(argparse.ArgumentTypeError):
        example.api_origin(url)


def test_redirect_is_not_followed_and_response_limit_is_enforced():
    calls = []

    def redirect(request):
        calls.append(request)
        return httpx.Response(302, headers={"Location": "https://other.invalid"})

    with httpx.Client(
        base_url="http://localhost",
        transport=httpx.MockTransport(redirect),
        follow_redirects=False,
    ) as transport:
        with pytest.raises(httpx.HTTPStatusError):
            example.inspect(transport, process(), "session")
    assert len(calls) == 1
    with client("x" * example.MAX_RESPONSE_BYTES, []) as transport:
        with pytest.raises(ValueError, match="read bound"):
            example.inspect(transport, process(), "session")


def test_missing_operator_credential_never_makes_request(monkeypatch):
    monkeypatch.delenv("WRIGHT_API_TOKEN", raising=False)
    with pytest.raises(SystemExit) as error:
        example.main(
            [
                "--api",
                "http://localhost",
                "--workspace-id",
                "workspace",
                "--session",
                "session",
                "--source",
                "workflows/example.wflow",
                "--digest",
                "a" * 64,
            ]
        )
    assert error.value.code == 2


@pytest.mark.parametrize(
    "change",
    [
        {"available": "true"},
        {"compiler": "missing"},
        {"compiler_reason": "raw error"},
        {"compiler": None},
        {"model": {"adapter": "unavailable", "available": False}},
    ],
)
def test_malformed_or_contradictory_capabilities_are_not_reported_ready(change):
    body = capabilities()
    body.update(change)
    with client(body, []) as transport:
        with pytest.raises((ValueError, TypeError)):
            example.inspect(transport, process(), "session")
