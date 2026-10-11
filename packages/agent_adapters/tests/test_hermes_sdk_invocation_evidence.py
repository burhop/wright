"""Actual SDK fields survive worker failure without exposing credentials/images."""

import asyncio
import json
from pathlib import Path

import pytest

from agent_adapters.hermes_role import HermesRoleTransport, HermesRoleInvocationError
from agent_adapters.hermes_role_worker import invoke
from agent_adapters.hermes_sdk_evidence import sdk_invocation_evidence
from core.process_validation import canonical_digest

from test_hermes_role_worker import sdk as sdk_fixture
from test_workflow_native_images import image_sdk as image_sdk_fixture, image_request


@pytest.fixture
def image_sdk(monkeypatch, tmp_path):
    return image_sdk_fixture.__wrapped__(monkeypatch, tmp_path)


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
    assert children[0].returncode is not None
