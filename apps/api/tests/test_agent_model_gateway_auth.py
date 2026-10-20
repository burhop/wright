from types import SimpleNamespace
import asyncio
import threading

import httpx
import pytest

from api.routers import agent


@pytest.mark.asyncio
async def test_chat_discovery_uses_gateway_even_when_workflow_sdk_is_selected(
    client, monkeypatch
):
    from agent_adapters import workflow_sdk

    monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TRANSPORT", "hermes-model-sdk")

    calls = []

    async def forbidden_sdk():
        pytest.fail("Chat selection must not depend on workflow SDK readiness")

    async def chat_models(*args, **kwargs):
        calls.append((args, kwargs))
        return {"provider": "chat-provider", "model": "chat-model"}

    monkeypatch.setattr(workflow_sdk, "workflow_sdk_capabilities", forbidden_sdk)
    monkeypatch.setattr(agent, "_hermes_json_request", chat_models)
    response = await client.get("/api/agent/models")
    assert response.status_code == 200
    result = response.json()
    assert result["current_value"] == "chat-provider::chat-model"
    assert result["selection_supported"] is True
    assert calls[0][0] == ("GET", "/api/model/options")
    assert len(result["groups"]) == len(result["groups"][0]["options"]) == 1
    rejected = await client.post(
        "/api/agent/model",
        json={
            "provider": "configured-provider",
            "model": "another-model",
        },
    )
    assert (
        rejected.status_code == 409 and "No session model was changed" in rejected.text
    )


@pytest.mark.asyncio
async def test_chat_discovery_failure_is_explicit_without_sdk_substitution(
    client, monkeypatch
):
    from fastapi import HTTPException

    monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TRANSPORT", "hermes-model-sdk")

    async def unavailable(*args, **kwargs):
        raise HTTPException(503, "Chat model service unavailable")

    monkeypatch.setattr(agent, "_hermes_json_request", unavailable)
    response = await client.get("/api/agent/models")
    assert response.status_code == 503
    assert "Chat model service unavailable" in response.text


@pytest.mark.asyncio
@pytest.mark.parametrize("transport", ["hermes-http", "hermes-model-sdk"])
@pytest.mark.parametrize(
    "defect", [None, "model", "provider", "session", "lock", "object", "denied"]
)
async def test_exact_chat_session_lock_never_updates_profile_default(
    client, monkeypatch, transport, defect
):
    from fastapi import HTTPException

    monkeypatch.setenv("WRIGHT_WORKFLOW_MODEL_TRANSPORT", transport)
    calls = []
    receipt = {
        "object": "hermes.session.model_lock",
        "session_id": "pilot-session",
        "runtime": {
            "provider": "openai-codex",
            "model": "gpt-6-astra",
            "model_lock": "accepted",
        },
    }
    if defect in {"provider", "model"}:
        receipt["runtime"][defect] = "different"
    elif defect == "session":
        receipt["session_id"] = "another-session"
    elif defect == "lock":
        receipt["runtime"]["model_lock"] = "rejected"
    elif defect == "object":
        receipt["object"] = "other-receipt"

    async def gateway(method, path, **kwargs):
        calls.append((method, path, kwargs))
        assert path == "/api/sessions/pilot-session/model"
        if defect == "denied":
            raise HTTPException(403, "Session model denied")
        return receipt

    monkeypatch.setattr(agent, "_hermes_json_request", gateway)
    result = await client.post(
        "/api/agent/model",
        json={
            "provider": "openai-codex",
            "model": "gpt-6-astra",
            "session_id": "pilot-session",
        },
    )
    assert len(calls) == 1
    assert calls[0][2]["json_body"] == {
        "provider": "openai-codex",
        "model": "gpt-6-astra",
        "require_model_lock": True,
    }
    if defect is None:
        assert result.status_code == 200
        assert result.json()["session_locked"] is True
    else:
        assert result.status_code == (403 if defect == "denied" else 409)


@pytest.mark.asyncio
@pytest.mark.parametrize("upstream_status", [404, 405, 501])
async def test_missing_model_service_is_unavailable_not_missing_workspace(
    client, monkeypatch, upstream_status
):
    original_request = httpx.AsyncClient.request
    calls = []

    async def gateway_request(self, method, url, **kwargs):
        if str(url).startswith("http://127.0.0.1:8642/"):
            calls.append((method, str(url)))
            return httpx.Response(
                upstream_status,
                text="fake-private-upstream-response",
                request=httpx.Request(method, url),
            )
        return await original_request(self, method, url, **kwargs)

    monkeypatch.setattr(
        agent,
        "resolve_agent_api_settings",
        lambda _: SimpleNamespace(base_url="http://127.0.0.1:8642", api_key=""),
    )
    monkeypatch.setattr(httpx.AsyncClient, "request", gateway_request)
    response = await client.get("/api/agent/models")
    assert response.status_code == 503
    assert response.json()["error_code"] != "WORKSPACE_NOT_FOUND"
    assert "required model service" in response.json()["message"]
    assert f"HTTP {upstream_status}" in response.json()["message"]
    assert "fake-private-upstream-response" not in response.text
    assert calls == [("GET", "http://127.0.0.1:8642/api/model/options")]


@pytest.mark.asyncio
async def test_model_auth_failure_retains_auth_status(monkeypatch):
    from fastapi import HTTPException

    async def gateway_request(self, method, url, **kwargs):
        return httpx.Response(401, request=httpx.Request(method, url))

    monkeypatch.setattr(
        agent,
        "resolve_agent_api_settings",
        lambda _: SimpleNamespace(base_url="http://127.0.0.1:8642", api_key=""),
    )
    monkeypatch.setattr(httpx.AsyncClient, "request", gateway_request)
    with pytest.raises(HTTPException) as failure:
        await agent._hermes_json_request("GET", "/api/model/options")
    assert failure.value.status_code == 401


@pytest.mark.asyncio
async def test_model_discovery_does_not_block_api_health(client, monkeypatch):
    loop = asyncio.get_running_loop()
    loop_thread = threading.get_ident()
    entered = asyncio.Event()
    release = threading.Event()
    original_request = httpx.AsyncClient.request

    def resolve_settings(name: str, env=None):
        loop.call_soon_threadsafe(entered.set)
        assert threading.get_ident() != loop_thread, "discovery ran on request loop"
        assert release.wait(3), "test did not release discovery"
        assert (name, env) == ("hermes", None)
        return SimpleNamespace(base_url="http://127.0.0.1:8642", api_key="")

    async def gateway_request(self, method, url, **kwargs):
        if str(url).startswith("http://127.0.0.1:8642/"):
            return httpx.Response(
                200, json={"providers": []}, request=httpx.Request(method, url)
            )
        return await original_request(self, method, url, **kwargs)

    monkeypatch.setattr(agent, "resolve_agent_api_settings", resolve_settings)
    monkeypatch.setattr(httpx.AsyncClient, "request", gateway_request)
    pending = asyncio.create_task(client.get("/api/agent/models"))
    try:
        await asyncio.wait_for(entered.wait(), 1)
        health = await asyncio.wait_for(client.get("/api/health"), 1)
        assert health.status_code == 200
        assert not release.is_set()
        assert not pending.done(), "model request completed before discovery release"
    finally:
        release.set()
        result = await pending
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_model_request_uses_running_gateway_credentials_not_model_profile(
    monkeypatch,
) -> None:
    resolver_calls: list[tuple[str, object]] = []

    def resolve_settings(name: str, env=None):
        resolver_calls.append((name, env))
        return SimpleNamespace(
            base_url="http://127.0.0.1:8642",
            api_key="test-secret-current-gateway-key",
        )

    async def request(self, method, url, **kwargs):
        assert kwargs["headers"]["Authorization"] == (
            "Bearer test-secret-current-gateway-key"
        )
        return httpx.Response(
            200,
            json={"providers": []},
            request=httpx.Request(method, url),
        )

    monkeypatch.setenv("WRIGHT_HERMES_PROFILE", "wright")
    monkeypatch.setattr(agent, "resolve_agent_api_settings", resolve_settings)
    monkeypatch.setattr(httpx.AsyncClient, "request", request)

    result = await agent._hermes_json_request(
        "GET",
        "/api/model/options",
        params={"profile": agent._hermes_profile()},
    )

    assert result == {"providers": []}
    assert resolver_calls == [("hermes", None)]


def test_model_options_only_include_account_accessible_models() -> None:
    result = agent._build_model_options_response(
        {
            "provider": "openai-codex",
            "model": "gpt-5.6-sol",
            "providers": [
                {
                    "slug": "openai-codex",
                    "name": "OpenAI Codex",
                    "authenticated": True,
                    "models": [
                        "gpt-6-astra",
                        "gpt-5.6-sol",
                        "gpt-5.6-sol-pro",
                    ],
                },
                {
                    "slug": "openai-api",
                    "name": "OpenAI API",
                    "authenticated": False,
                    "models": ["gpt-5.6-sol"],
                },
                {
                    "slug": "copilot",
                    "name": "GitHub Copilot",
                    "models": ["gpt-5.6-sol"],
                },
                {
                    "slug": "custom-team",
                    "name": "Team Gateway",
                    "authenticated": True,
                    "models": ["team-model"],
                },
            ],
        }
    )

    assert [group.provider for group in result.groups] == [
        "openai-codex",
    ]
    assert [option.model for option in result.groups[0].options] == [
        "gpt-6-astra",
        "gpt-5.6-sol",
    ]


def test_model_options_keep_current_provider_for_older_hermes_payloads() -> None:
    result = agent._build_model_options_response(
        {
            "provider": "openai-codex",
            "model": "gpt-5.6-sol",
            "providers": [
                {
                    "slug": "openai-codex",
                    "name": "OpenAI Codex",
                    "models": ["gpt-5.6-sol"],
                },
                {
                    "slug": "copilot",
                    "name": "GitHub Copilot",
                    "models": ["gpt-5.6-sol"],
                },
            ],
        }
    )

    assert [group.provider for group in result.groups] == ["openai-codex"]


def test_model_options_do_not_restore_an_inaccessible_current_model() -> None:
    result = agent._build_model_options_response(
        {
            "provider": "openai-codex",
            "model": "gpt-5.6-sol-pro",
            "providers": [
                {
                    "slug": "openai-codex",
                    "name": "OpenAI Codex",
                    "authenticated": True,
                    "models": ["gpt-5.6-sol", "gpt-5.6-sol-pro"],
                }
            ],
        }
    )

    assert result.current_provider == "openai-codex"
    assert result.current_model is None
    assert result.current_value is None
    assert [option.model for option in result.groups[0].options] == ["gpt-5.6-sol"]
