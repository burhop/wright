import asyncio
import hashlib
import json
from types import SimpleNamespace

import httpx
import pytest

from agent_adapters import report_generation
from agent_adapters.hermes_openai_bridge import (
    HermesOpenAICompatibilityBridge,
    HermesOpenAIBridgeSettings,
)
from agent_adapters.workflow_model_routing import (
    lock_workflow_model,
    workflow_model_capabilities,
)
from core.process_validation import canonical_digest


def route(model="prepared-model", endpoint="http://gateway.test"):
    public = {
        "adapter": "hermes-http",
        "provider": "configured-provider",
        "model_reference": model,
        "profile": "wright",
        "endpoint_digest": hashlib.sha256(endpoint.encode()).hexdigest(),
    }
    return {**public, "configuration_digest": canonical_digest(public)}


def acknowledgement(request, *, model="prepared-model", accepted=True):
    return {
        "object": "hermes.session.model_lock",
        "session_id": request.url.path.split("/")[-2],
        "runtime": {
            "provider": "configured-provider",
            "model": model,
            "model_lock": "accepted" if accepted else "rejected",
        },
    }


def created_session(request):
    body = json.loads(request.content)
    return httpx.Response(
        201,
        json={
            "object": "hermes.session",
            "session": {"id": body["id"], "model": body["model"]},
        },
    )


def setup(monkeypatch, handler):
    from agent_adapters import workflow_model_routing

    monkeypatch.delenv("HERMES_PROFILE", raising=False)
    monkeypatch.delenv("WRIGHT_HERMES_PROFILE", raising=False)
    settings = SimpleNamespace(base_url="http://gateway.test", api_key="private-key")
    monkeypatch.setattr(
        report_generation, "resolve_hermes_api_settings", lambda: settings
    )
    monkeypatch.setattr(
        workflow_model_routing, "resolve_hermes_api_settings", lambda: settings
    )
    actual = httpx.AsyncClient
    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kwargs: actual(
            **{**kwargs, "transport": httpx.MockTransport(handler)}
        ),
    )
    return settings


@pytest.mark.parametrize("normalized", [False, True])
def test_readonly_resolution_records_actual_selection_without_credentials(
    monkeypatch, normalized
):
    observed = []

    def handler(request):
        observed.append(request)
        if not normalized:
            return httpx.Response(
                200,
                json={
                    "provider": "configured-provider",
                    "model": "prepared-model",
                    "providers": [],
                },
            )
        return httpx.Response(
            200,
            json={
                "current_provider": "configured-provider",
                "current_model": "prepared-model",
                "current_value": "configured-provider::prepared-model",
                "groups": [],
            },
        )

    setup(monkeypatch, handler)
    result = asyncio.run(workflow_model_capabilities())
    assert result == {"available": True, "resolution": route()}
    assert observed[0].method == "GET"
    assert "private-key" not in json.dumps(result)


def test_text_lock_precedes_submission_and_actual_response_provenance(monkeypatch):
    requests, observations = [], []

    def handler(request):
        requests.append(request)
        if request.url.path == "/api/sessions":
            return created_session(request)
        if request.url.path.endswith("/model"):
            return httpx.Response(200, json=acknowledgement(request))
        return httpx.Response(
            200,
            json={
                "model": "prepared-model-provider-version",
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "version": "wright.unattended-step/1",
                                    "status": "completed",
                                    "reason": None,
                                    "response": "Report",
                                }
                            )
                        }
                    }
                ],
            },
        )

    setup(monkeypatch, handler)

    async def observe(value):
        observations.append(value)

    result = asyncio.run(
        report_generation.generate_workflow_response(
            "Create a report",
            "text",
            expected_resolution=route(),
            invocation_observer=observe,
        )
    )
    assert str(result) == "Report"
    assert [request.url.path.split("/")[-1] for request in requests] == [
        "sessions",
        "model",
        "completions",
    ]
    assert json.loads(requests[0].content)["require_model_lock"] is True
    assert observations[0]["capture_phase"] == "submission"
    assert observations[0]["frozen_model_lock"]["model_reference"] == "prepared-model"
    assert "upstream_reported_model" not in observations[0]
    assert observations[1]["capture_phase"] == "response"
    assert (
        observations[1]["upstream_reported_model"] == "prepared-model-provider-version"
    )
    assert "private-key" not in json.dumps(observations)


@pytest.mark.parametrize(
    "kind", ["wrong-model", "rejected", "wrong-session", "no-object"]
)
def test_unconfirmed_model_lock_never_sends_completion(monkeypatch, kind):
    requests = []

    def handler(request):
        requests.append(request)
        if request.url.path == "/api/sessions":
            return created_session(request)
        reply = acknowledgement(
            request,
            model="wrong" if kind == "wrong-model" else "prepared-model",
            accepted=kind != "rejected",
        )
        if kind == "wrong-session":
            reply["session_id"] = "other"
        if kind == "no-object":
            reply.pop("object")
        return httpx.Response(200, json=reply)

    setup(monkeypatch, handler)
    with pytest.raises(ValueError, match="confirm"):
        asyncio.run(
            report_generation.generate_workflow_response(
                "Create a report", "text", expected_resolution=route()
            )
        )
    assert len(requests) == 2 and requests[-1].url.path.endswith("/model")


def test_adapter_endpoint_change_blocks_even_lock_request(monkeypatch):
    requests = []
    settings = setup(monkeypatch, lambda request: requests.append(request))

    async def call():
        async with httpx.AsyncClient() as client:
            await lock_workflow_model(
                client,
                settings,
                route(endpoint="http://different.test"),
                "prepared-session",
            )

    with pytest.raises(ValueError, match="endpoint/profile changed"):
        asyncio.run(call())
    assert not requests


def test_translated_bridge_completion_uses_same_confirmed_lock_boundary(monkeypatch):
    requests, observations = [], []

    def handler(request):
        requests.append(request)
        if request.url.path == "/api/sessions":
            return created_session(request)
        if request.url.path.endswith("/model"):
            return httpx.Response(200, json=acknowledgement(request))
        return httpx.Response(
            200,
            json={
                "model": "actual-provider-model",
                "choices": [{"message": {"content": "Complete"}}],
            },
        )

    setup(monkeypatch, handler)
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://gateway.test",
            api_key="private-key",
            expected_resolution=route(),
        )
    )

    async def observe(value):
        observations.append(value)

    result = asyncio.run(
        bridge.complete(
            {
                "model": "wright-hermes",
                "messages": [{"role": "user", "content": "Create report"}],
                "tools": [],
                "tool_choice": "none",
                "stream": False,
            },
            invocation_observer=observe,
        )
    )
    assert result.wright_upstream_model == "actual-provider-model"
    assert len(requests) == 3
    assert (
        json.loads(requests[0].content)["id"]
        == requests[-1].headers["X-Hermes-Session-Id"]
    )
    assert observations[0]["frozen_model_lock"]["model_reference"] == "prepared-model"
    assert observations[1]["upstream_reported_model"] == "actual-provider-model"
    assert observations[0]["capture_phase"] == "submission"
    assert "upstream_reported_model" not in observations[0]
    assert observations[1]["capture_phase"] == "response"
    assert observations[0] is not observations[1]


@pytest.mark.parametrize("kind", ["collision", "wrong-id", "no-object", "wrong-model"])
def test_private_session_creation_failure_cannot_lock_or_complete(monkeypatch, kind):
    requests = []

    def handler(request):
        requests.append(request)
        if kind == "collision":
            return httpx.Response(409, json={"error": {"code": "session_exists"}})
        response = created_session(request)
        value = response.json()
        if kind == "wrong-id":
            value["session"]["id"] = "another-owned-session"
        elif kind == "no-object":
            value.pop("object")
        else:
            value["session"]["model"] = "different-model"
        return httpx.Response(201, json=value)

    setup(monkeypatch, handler)
    with pytest.raises(ValueError):
        asyncio.run(
            report_generation.generate_workflow_response(
                "Report", "text", expected_resolution=route()
            )
        )
    assert [request.url.path for request in requests] == ["/api/sessions"]


def test_bridge_each_actual_attempt_uses_a_new_confirmed_private_session(monkeypatch):
    sessions, completed = set(), []

    def handler(request):
        if request.url.path == "/api/sessions":
            identity = json.loads(request.content)["id"]
            assert identity not in sessions
            sessions.add(identity)
            return created_session(request)
        if request.url.path.endswith("/model"):
            assert request.url.path.split("/")[-2] in sessions
            return httpx.Response(200, json=acknowledgement(request))
        completed.append(request.headers["X-Hermes-Session-Id"])
        assert completed[-1] in sessions
        return httpx.Response(
            200, json={"choices": [{"message": {"content": "Complete"}}]}
        )

    setup(monkeypatch, handler)
    bridge = HermesOpenAICompatibilityBridge(
        HermesOpenAIBridgeSettings(
            base_url="http://gateway.test",
            api_key="private-key",
            expected_resolution=route(),
        )
    )

    async def invoke():
        await bridge._post_json({"messages": []}, "same-logical-correlation")
        await bridge._post_json({"messages": []}, "same-logical-correlation")

    asyncio.run(invoke())
    assert len(sessions) == len(set(completed)) == 2


@pytest.mark.parametrize(
    "body",
    [
        {
            "provider": "configured-provider",
            "model": "A",
            "current_provider": "configured-provider",
            "current_model": "B",
        },
        {"provider": "configured-provider", "current_model": "A"},
        {"current_provider": "configured-provider"},
    ],
)
def test_incomplete_or_ambiguous_gateway_selection_is_not_guessed(monkeypatch, body):
    setup(monkeypatch, lambda request: httpx.Response(200, json=body))
    with pytest.raises(ValueError, match="cannot confirm"):
        asyncio.run(workflow_model_capabilities())
