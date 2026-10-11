"""SDK request construction with synthetic clients; no live inference or tools."""

import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from agent_adapters.hermes_role_worker import (
    failure_code,
    invoke,
    WorkflowSdkConfigurationChangedError,
)


@pytest.mark.parametrize(
    "name,code",
    [
        ("APITimeoutError", "SCOPED_MODEL_TIMEOUT"),
        ("AuthenticationError", "SCOPED_MODEL_AUTH_REQUIRED"),
        ("PermissionDeniedError", "SCOPED_MODEL_AUTH_REQUIRED"),
        ("RateLimitError", "SCOPED_MODEL_RATE_LIMITED"),
        ("UnknownProviderError", "SCOPED_INVOCATION_UNAVAILABLE"),
    ],
)
def test_worker_failure_category_never_includes_sdk_exception_text(name, code):
    error = type(name, (Exception,), {})("SECRET token and provider URL")
    assert failure_code(error) == code
    assert "SECRET" not in failure_code(error)


def test_standard_deadline_has_the_fixed_timeout_category():
    assert failure_code(TimeoutError("SECRET transport")) == "SCOPED_MODEL_TIMEOUT"


@pytest.fixture
def sdk(monkeypatch, tmp_path):
    calls = []
    state = {
        "model": "configured-default",
        "tool_calls": None,
        "content": '{"source":"synthetic"}',
        "closed": 0,
    }

    def create(**kwargs):
        calls.append(kwargs)
        message = SimpleNamespace(
            content=state["content"], tool_calls=state["tool_calls"]
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)], model="configured-default"
        )

    def close():
        state["closed"] += 1

    client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=create)), close=close
    )
    runtime = {
        "provider": "openai-codex",
        "api_mode": "codex_responses",
        "api_key": "synthetic-secret-never-export",
        "base_url": "https://model.example.invalid",
    }

    def resolve(**kwargs):
        assert kwargs["target_model"] == "configured-default"
        return runtime

    def resolve_client(provider, **kwargs):
        assert provider == runtime["provider"]
        assert kwargs["model"] == "configured-default"
        assert kwargs["explicit_api_key"] == runtime["api_key"]
        assert kwargs["main_runtime"] == runtime
        return client, state["model"]

    for parent in ("hermes_cli", "agent"):
        module = ModuleType(parent)
        module.__path__ = []
        monkeypatch.setitem(sys.modules, parent, module)
    monkeypatch.setitem(
        sys.modules,
        "hermes_cli.runtime_provider",
        SimpleNamespace(
            _get_model_config=lambda: {"default": "configured-default"},
            resolve_runtime_provider=resolve,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "agent.auxiliary_client",
        SimpleNamespace(resolve_provider_client=resolve_client),
    )
    for name in (
        "hermes_cli/runtime_provider.py",
        "agent/auxiliary_client.py",
        "agent/codex_runtime.py",
        "agent/codex_responses_adapter.py",
    ):
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.write_text("# Synthetic SDK identity\n")
    return SimpleNamespace(
        root=tmp_path, calls=calls, state=state, runtime=runtime, client=client
    )


def request(resolution):
    return {
        "operation": "generate",
        "expected_resolution": resolution,
        "messages": [
            {"role": "system", "content": "Prepared interface role"},
            {"role": "user", "content": "Create a static interface"},
        ],
    }


def test_probe_and_generation_never_export_credentials_or_execute_tools(sdk):
    probe = invoke({"operation": "probe"}, sdk.root)
    assert sdk.calls == [] and sdk.state["closed"] == 1
    assert "synthetic-secret-never-export" not in json.dumps(probe)
    result = invoke(request(probe["resolution"]), sdk.root)
    assert len(sdk.calls) == 1
    assert sdk.calls[0]["tools"] == [] and sdk.calls[0]["tool_choice"] == "none"
    assert sdk.calls[0]["model"] == "configured-default"
    assert sdk.calls[0]["messages"][0]["content"] == "Prepared interface role"
    assert "synthetic-secret-never-export" not in json.dumps(result)
    assert result["response_model"] == "configured-default"
    assert sdk.state["closed"] == 2


@pytest.mark.parametrize("operation", ["generate", "generate-workflow"])
def test_multimodal_workflow_input_does_not_widen_confined_authoring(sdk, operation):
    body = request(invoke({"operation": "probe"}, sdk.root)["resolution"])
    body["operation"] = operation
    body["messages"][1]["content"] = [
        {"type": "text", "text": "Inspect the exact image"},
        {
            "type": "image_url",
            "image_url": {"url": "data:image/png;base64,c3ludGhldGlj"},
        },
    ]
    if operation == "generate":
        with pytest.raises(ValueError):
            invoke(body, sdk.root)
        assert sdk.calls == []
    else:
        invoke(body, sdk.root)
        assert sdk.calls[0]["messages"] == body["messages"]
        assert sdk.calls[0]["tools"] == [] and sdk.calls[0]["tool_choice"] == "none"


@pytest.mark.parametrize(
    "part",
    [
        {
            "type": "image_url",
            "image_url": {"url": "https://external.invalid/image.png"},
        },
        {"type": "file", "path": "outside-workspace"},
        {"type": "text", "text": "scope", "tools": ["terminal"]},
    ],
)
def test_workflow_worker_rejects_unqualified_content_before_provider_call(sdk, part):
    body = request(invoke({"operation": "probe"}, sdk.root)["resolution"])
    body["operation"] = "generate-workflow"
    body["messages"][1]["content"] = [part]
    with pytest.raises(ValueError):
        invoke(body, sdk.root)
    assert sdk.calls == []


def test_workflow_worker_detects_route_change_after_parent_probe(sdk):
    route = invoke({"operation": "probe"}, sdk.root)["resolution"]
    body = request(route)
    body["operation"] = "generate-workflow"
    sdk.runtime["base_url"] = "https://changed.invalid"
    with pytest.raises(WorkflowSdkConfigurationChangedError) as failed:
        invoke(body, sdk.root)
    assert failure_code(failed.value) == "WORKFLOW_MODEL_CHANGED"
    assert sdk.calls == []


@pytest.mark.parametrize(
    "change", ["configuration", "tool-request", "model", "messages", "oversized"]
)
def test_confined_sdk_rejects_changed_scope_or_invalid_response(sdk, change):
    resolution = invoke({"operation": "probe"}, sdk.root)["resolution"]
    body = request(resolution)
    if change == "configuration":
        sdk.runtime["base_url"] = "https://changed.invalid"
    elif change == "tool-request":
        sdk.state["tool_calls"] = [{"function": {"name": "terminal"}}]
    elif change == "model":
        sdk.state["model"] = "unrequested-model"
    elif change == "messages":
        body["messages"].append({"role": "tool", "content": "Unrelated authority"})
    elif change == "oversized":
        sdk.state["content"] = "x" * 1_048_577
    with pytest.raises(ValueError):
        invoke(body, sdk.root)
    assert len(sdk.calls) == (1 if change in {"tool-request", "oversized"} else 0)


@pytest.mark.parametrize(
    "extra",
    [{"tools": ["terminal"]}, {"operation": "execute"}, {"command": "arbitrary"}],
)
def test_worker_has_no_generic_invocation_shape(sdk, extra):
    with pytest.raises(ValueError):
        invoke({"operation": "probe", **extra}, sdk.root)
    assert sdk.calls == []
