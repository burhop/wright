"""Actual SDK fields survive worker failure without exposing credentials/images."""

import asyncio
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from agent_adapters.hermes_role import HermesRoleTransport, HermesRoleInvocationError
from agent_adapters import hermes_role_worker
from agent_adapters.hermes_role_worker import invoke
from agent_adapters.hermes_sdk_evidence import (
    sdk_failure_evidence,
    sdk_invocation_evidence,
    sdk_model_observation,
)
from core.process_validation import canonical_digest

from test_hermes_role_worker import sdk as sdk_fixture
from test_workflow_native_images import image_sdk as image_sdk_fixture, image_request


@pytest.fixture
def image_sdk(monkeypatch, tmp_path):
    return image_sdk_fixture.__wrapped__(monkeypatch, tmp_path)


@pytest.mark.parametrize("name", ["BadRequestError", "_StreamErrorEvent"])
def test_sdk_failure_metadata_is_finite_and_excludes_transport_secrets(name):
    error = type(name, (Exception,), {})("SECRET message and URL")
    error.status_code = 400
    error.code = "unsupported_parameter"
    error.body = {"message": "SECRET body", "param": "SECRET parameter"}
    evidence = sdk_failure_evidence(error, "SCOPED_INVOCATION_UNAVAILABLE")
    assert evidence == {
        "schema_version": "wright.scoped-sdk-failure/1",
        "capture_scope": "worker_exception_after_sdk_capture",
        "category": "SCOPED_INVOCATION_UNAVAILABLE",
        "exception_type": name,
        "http_status": 400,
        "provider_code": "unsupported_parameter",
    }
    assert "SECRET" not in json.dumps(evidence)


@pytest.mark.parametrize("status", [True, "400 SECRET", 0, 600, None])
def test_sdk_failure_discards_unknown_names_codes_and_invalid_status(status):
    error = type("SECRET_ProviderError", (Exception,), {})("SECRET text")
    error.status_code = status
    error.code = "SECRET_provider_token"
    evidence = sdk_failure_evidence(error, "SECRET category")
    assert evidence["exception_type"] == "unclassified_error"
    assert evidence["category"] == "SCOPED_INVOCATION_UNAVAILABLE"
    assert "http_status" not in evidence and "provider_code" not in evidence
    assert "SECRET" not in json.dumps(evidence)


def test_sdk_failure_does_not_read_raw_response_or_propagate_attribute_errors():
    class HostileError(Exception):
        @property
        def status_code(self):
            raise ValueError("SECRET status")

        @property
        def code(self):
            raise ValueError("SECRET code")

        @property
        def body(self):
            pytest.fail("Raw response body must never be read")

    evidence = sdk_failure_evidence(HostileError(), "SCOPED_INVOCATION_UNAVAILABLE")
    assert "http_status" not in evidence and "provider_code" not in evidence


def test_worker_persists_safe_failure_on_existing_request_before_generic_result(
    monkeypatch, tmp_path
):
    evidence_path = tmp_path / "sdk-invocations.json"
    output = io.StringIO()
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["worker", str(tmp_path), str(evidence_path)])
    monkeypatch.setattr(sys, "stdin", SimpleNamespace(buffer=io.BytesIO(b"{}")))
    monkeypatch.setattr(sys, "stdout", output)
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    monkeypatch.setattr(hermes_role_worker, "initialize_sdk_profile", lambda: None)

    def fail(request, root, *, sdk_observer):
        sdk_observer({"model": "fixed-default", "messages": [], "tools": []}, {})
        before = json.loads(evidence_path.read_bytes())
        assert "failure" not in before["invocations"][0]
        error = type("BadRequestError", (Exception,), {})("SECRET SDK response")
        error.status_code = 400
        error.code = "unsupported_parameter"
        raise error

    monkeypatch.setattr(hermes_role_worker, "invoke", fail)
    hermes_role_worker.main()
    retained = json.loads(evidence_path.read_bytes())
    assert len(retained["invocations"]) == 1
    failure = retained["invocations"][0]["failure"]
    assert failure["exception_type"] == "BadRequestError"
    assert failure["http_status"] == 400
    assert failure["provider_code"] == "unsupported_parameter"
    result = json.loads(output.getvalue())
    assert result["ok"] is False
    assert result["code"] == "SCOPED_INVOCATION_UNAVAILABLE"
    assert "SECRET" not in json.dumps(retained) + output.getvalue()


def test_native_image_sdk_actual_kwargs_and_provider_are_captured(image_sdk):
    prepared = invoke({"operation": "probe-image"}, image_sdk.root)
    captured = []

    def observe(payload, resolution):
        assert image_sdk.calls == []
        captured.append(sdk_invocation_evidence(payload, resolution))

    result = invoke(
        image_request(prepared["resolution"]), image_sdk.root, sdk_observer=observe
    )
    actual = image_sdk.calls[0]
    assert captured[0]["request_digest"] == canonical_digest(actual)
    assert captured[0]["request_fields"]["instructions"] == actual["instructions"]
    assert (
        captured[0]["request_fields"]["input"][0]["content"][1]["type"]
        == "image_reference"
    )
    assert captured[0]["tool_schemas"] == actual["tools"]
    assert captured[0]["resolution"]["provider"] == "openai-codex"
    assert result["response_model"] == "configured-default"
    assert "data:image" not in json.dumps(captured)
    assert "synthetic-secret-never-export" not in json.dumps(captured)


def test_sdk_text_authoring_capture_retains_actual_fields_and_redacts_prompt_secret(
    monkeypatch, tmp_path
):
    sdk = sdk_fixture.__wrapped__(monkeypatch, tmp_path)
    captured = []
    request = {
        "operation": "generate",
        "messages": [
            {"role": "system", "content": "Confined author role"},
            {"role": "user", "content": "password=fake-test-secret"},
        ],
    }
    invoke(
        request,
        sdk.root,
        sdk_observer=lambda payload, resolution: captured.append(
            sdk_invocation_evidence(payload, resolution)
        ),
    )
    assert captured[0]["request_digest"] == canonical_digest(sdk.calls[0])
    assert captured[0]["request_fields"]["tools"] == []
    assert "fake-test-secret" not in json.dumps(captured)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["success", "timeout", "worker_error"])
async def test_transport_captures_internal_sdk_sidecar_before_failure(
    monkeypatch, tmp_path, failure
):
    observed, children = [], []
    payload = {
        "model": "fixed-default",
        "instructions": "Captured system",
        "input": [
            {"role": "user", "content": [{"type": "input_text", "text": "Test"}]}
        ],
        "tools": [],
    }
    record = sdk_invocation_evidence(
        payload, {"provider": "openai-codex", "model_reference": "fixed-default"}
    )
    if failure == "worker_error":
        error = type("AuthenticationError", (Exception,), {})("SECRET token")
        error.status_code = 401
        record["failure"] = sdk_failure_evidence(error, "SCOPED_MODEL_AUTH_REQUIRED")

    class Stdin:
        def write(self, raw):
            assert "evidence_path" not in json.loads(raw)

        async def drain(self):
            pass

        def close(self):
            pass

    class Stdout:
        def __init__(self):
            self.done = False

        async def read(self, size):
            if failure == "timeout":
                await asyncio.Future()
            if self.done:
                return b""
            self.done = True
            return json.dumps(
                {"ok": True}
                if failure == "success"
                else {"ok": False, "code": "SCOPED_MODEL_AUTH_REQUIRED"}
            ).encode()

    class Child:
        stdin = Stdin()
        stdout = Stdout()
        returncode = None

        def kill(self):
            self.returncode = -1

        async def wait(self):
            self.returncode = self.returncode or 0

    async def spawn(*arguments, **kwargs):
        path = Path(arguments[-1])
        assert path.parent == Path(kwargs["cwd"])
        assert path.name == "sdk-invocations.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": "wright.scoped-sdk-evidence/1",
                    "invocations": [record],
                }
            )
        )
        children.append(Child())
        return children[-1]

    async def observer(invocation):
        observed.append(invocation)

    monkeypatch.setattr(asyncio, "create_subprocess_exec", spawn)
    transport = HermesRoleTransport(
        tmp_path / "python", tmp_path / "runtime", timeout_seconds=1
    )
    if failure == "success":
        result = await transport.call(
            {"operation": "generate-image"}, invocation_observer=observer
        )
        assert result["wright_invocations"] == observed
    else:
        error = TimeoutError if failure == "timeout" else HermesRoleInvocationError
        with pytest.raises(error):
            await transport.call(
                {"operation": "generate-image"}, invocation_observer=observer
            )
    assert len(observed) == 1
    assert observed[0]["request_digest"] == canonical_digest(payload)
    if failure == "worker_error":
        assert observed[0]["failure"]["http_status"] == 401
        assert observed[0]["failure"]["exception_type"] == "AuthenticationError"
        assert "SECRET" not in json.dumps(observed)
    assert children[0].returncode is not None


@pytest.mark.parametrize("operation", ["generate-workflow", "generate-image"])
@pytest.mark.parametrize(
    "returned_model", ["configured-default", "different-adapter-alias", None]
)
def test_worker_labels_adapter_alias_without_claiming_upstream_model(
    monkeypatch, tmp_path, operation, returned_model
):
    evidence_path = tmp_path / "sdk-invocations.json"
    output = io.StringIO()
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(sys, "argv", ["worker", str(tmp_path), str(evidence_path)])
    request = {"operation": operation}
    monkeypatch.setattr(
        sys, "stdin", SimpleNamespace(buffer=io.BytesIO(json.dumps(request).encode()))
    )
    monkeypatch.setattr(sys, "stdout", output)
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    monkeypatch.setattr(hermes_role_worker, "initialize_sdk_profile", lambda: None)

    def complete(request, root, *, sdk_observer):
        sdk_observer(
            {"model": "configured-default", "messages": [], "tools": []},
            {"model_reference": "configured-default"},
        )
        return {"ok": True, "response_model": returned_model, "text": "Retained result"}

    monkeypatch.setattr(hermes_role_worker, "invoke", complete)
    hermes_role_worker.main()
    record = json.loads(evidence_path.read_bytes())["invocations"][0]
    assert record["adapter_returned_model"] == returned_model
    assert record["model_observation_scope"] == "hermes_model_sdk_adapter_result"
    assert record["upstream_reported_model"] is None
    assert record["request_fields"]["model"] == "configured-default"
    # The compatible worker response remains unchanged for authoring/image/usage callers.
    assert json.loads(output.getvalue())["response_model"] == returned_model


@pytest.mark.parametrize(
    "model", [None, "", " ", " " * 161 + "alias", {"model": "alias"}]
)
def test_sdk_model_observation_discards_unbounded_or_missing_alias(model):
    observed = sdk_model_observation(model)
    assert observed["adapter_returned_model"] is None
    assert observed["upstream_reported_model"] is None
