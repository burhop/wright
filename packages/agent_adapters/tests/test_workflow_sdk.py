"""Frozen SDK workflow routing; synthetic transport, no external tool effects."""

import asyncio
from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace

import pytest

from agent_adapters import report_generation, workflow_sdk
from agent_adapters.hermes_openai_bridge import (
    HermesOpenAICompatibilityBridge,
    HermesOpenAIBridgeSettings,
)
from agent_adapters.workflow_model_routing import (
    ModelRouteChangedError,
    workflow_model_capabilities,
)
from core.process_validation import canonical_digest
from core.workflow_model_routing import WorkflowModelRouting


@pytest.fixture
def sdk(monkeypatch):
    monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TRANSPORT", "hermes-model-sdk")
    monkeypatch.setenv("WRIGHT_HERMES_PROFILE", "wright")
    native = {
        "provider": "configured-provider",
        "model_reference": "configured-model",
        "api_mode": "chat_completions",
        "endpoint_digest": "a" * 64,
        "sdk_digest": "b" * 64,
    }
    native["configuration_digest"] = hashlib.sha256(
        json.dumps(native, sort_keys=True).encode()
    ).hexdigest()
    state = SimpleNamespace(native=native, calls=[], fail=False, replies=[])

    class Transport:
        async def probe(self):
            return deepcopy(state.native)

        async def call(
            self, request, *, invocation_observer=None, timeout_seconds=None
        ):
            assert request["expected_resolution"] == native
            assert request["timeout_seconds"] == timeout_seconds
            state.calls.append(request)
            if invocation_observer is not None:
                await invocation_observer({"capture_scope": "provider_sdk_request"})
            if state.fail:
                raise ValueError("synthetic unavailable SDK")
            return {
                "text": state.replies.pop(0) if state.replies else state.text,
                "response_model": "reported-provider-revision",
                "usage": {"prompt_tokens": 17, "completion_tokens": 8},
            }

    monkeypatch.setattr(
        workflow_sdk.HermesRoleTransport, "from_host", lambda: Transport()
    )
    state.text = json.dumps(
        {
            "version": "wright.unattended-step/1",
            "status": "completed",
            "response": "Engineering report",
            "reason": None,
        }
    )
    return state


def test_sdk_probe_has_exact_route_and_round_trips_without_credentials(sdk):
    observed = asyncio.run(workflow_model_capabilities())
    route = observed["resolution"]
    assert route["adapter"] == "hermes-model-sdk" and route["profile"] == "wright"
    assert route["configuration_digest"] == canonical_digest(
        {key: value for key, value in route.items() if key != "configuration_digest"}
    )
    assert workflow_sdk.native_sdk_resolution(route) == sdk.native
    assert WorkflowModelRouting(text=route).model_dump(mode="json")["text"] == route
    assert sdk.calls == []


@pytest.mark.parametrize(
    "change",
    ["model_reference", "sdk_digest", "endpoint_digest", "profile", "transport"],
)
def test_changed_route_never_submits_a_decision(sdk, monkeypatch, change):
    route = asyncio.run(workflow_model_capabilities())["resolution"]
    if change == "profile":
        monkeypatch.setenv("WRIGHT_HERMES_PROFILE", "different")
    elif change == "transport":
        monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TRANSPORT", "hermes-http")
    else:
        sdk.native[change] = "c" * 64 if "digest" in change else "different-model"
    with pytest.raises(ModelRouteChangedError):
        asyncio.run(workflow_sdk.workflow_sdk_completion({"messages": []}, route))
    assert sdk.calls == []


def test_text_response_retains_actual_sdk_evidence_and_usage(sdk):
    route = asyncio.run(workflow_model_capabilities())["resolution"]
    records = []

    async def observe(record):
        records.append(record)

    result = asyncio.run(
        report_generation.generate_workflow_response(
            "Inspect the accepted design",
            "text",
            expected_resolution=route,
            images=["data:image/png;base64,c3ludGhldGlj"],
            invocation_observer=observe,
        )
    )
    assert str(result) == "Engineering report"
    assert result.wright_usage["input_tokens"] == 17
    assert sdk.calls[0]["operation"] == "generate-workflow"
    assert sdk.calls[0]["messages"][1]["content"][1]["type"] == "image_url"
    assert any(
        record.get("capture_scope") == "provider_sdk_request" for record in records
    )
    assert (
        records[0]["frozen_model_resolution"]["qualification"]
        == "sdk_configuration_verified"
    )
    assert "model_lock" not in records[0]["frozen_model_resolution"]
    assert result.wright_invocations[1]["capture_scope"] == "provider_sdk_request"


def test_bridge_still_validates_proposals_and_never_executes_a_tool(sdk):
    route = asyncio.run(workflow_model_capabilities())["resolution"]
    sdk.text = json.dumps(
        {"kind": "tool_call", "name": "inspect", "arguments": {"part": "exact-part"}}
    )
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://unused.invalid",
            api_key="",
            workflow_task=True,
            expected_resolution=route,
        )
    )
    result = asyncio.run(
        bridge.complete(
            {
                "model": "wright-hermes",
                "messages": [{"role": "user", "content": "Inspect"}],
                "tools": [
                    {
                        "type": "function",
                        "function": {
                            "name": "inspect",
                            "description": "Inspect one exact part",
                            "parameters": {
                                "type": "object",
                                "properties": {"part": {"type": "string"}},
                                "required": ["part"],
                                "additionalProperties": False,
                            },
                        },
                    }
                ],
                "tool_choice": "required",
                "stream": False,
            }
        )
    )
    call = result["choices"][0]["message"]["tool_calls"][0]
    assert call["function"]["name"] == "inspect"
    assert json.loads(call["function"]["arguments"]) == {"part": "exact-part"}
    assert len(sdk.calls) == 1 and len(sdk.calls[0]["messages"]) == 2
    assert any(
        record.get("capture_scope") == "provider_sdk_request"
        for record in result.wright_invocations
    )


def test_failed_sdk_call_retains_boundary_evidence_without_http_fallback(sdk):
    route = asyncio.run(workflow_model_capabilities())["resolution"]
    sdk.fail = True
    records = []

    async def observe(record):
        records.append(record)

    with pytest.raises(ValueError):
        asyncio.run(
            report_generation.generate_workflow_response(
                "Create report",
                "text",
                expected_resolution=route,
                invocation_observer=observe,
            )
        )
    assert len(sdk.calls) == 1
    assert any(
        record.get("capture_scope") == "provider_sdk_request" for record in records
    )


def test_translation_correction_uses_same_frozen_sdk_route_and_records_both_calls(sdk):
    from test_hermes_openai_bridge import _request, _tool

    frozen = asyncio.run(workflow_model_capabilities())["resolution"]
    sdk.replies = [
        "invalid decision",
        '{"kind":"tool_call","name":"create_graph","arguments":{"title":"Verified"}}',
    ]
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://unused.invalid",
            api_key="",
            workflow_task=True,
            expected_resolution=frozen,
        )
    )
    payload = _request(tools=[_tool()])
    result = asyncio.run(bridge.complete(payload))
    assert len(sdk.calls) == 2
    assert all(call["expected_resolution"] == sdk.native for call in sdk.calls)
    captures = [
        item
        for item in result.wright_invocations
        if item.get("capture_scope") == "hermes_bridge_upstream_request"
    ]
    assert [item["operation"] for item in captures] == [
        "hermes-bridge-translation",
        "hermes-bridge-translation-repair",
    ]
    assert all(item["frozen_model_resolution"] == frozen for item in captures)
    assert (
        result["choices"][0]["message"]["tool_calls"][0]["function"]["name"]
        == "create_graph"
    )
