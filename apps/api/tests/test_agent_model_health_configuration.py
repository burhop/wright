from unittest.mock import AsyncMock

from fastapi import HTTPException
import pytest

from api.agent_model_health import reconcile_agent_model_configuration


MISSING_LOCAL = {
    "state": "disconnected",
    "latencyMs": 0,
    "baseUrl": None,
    "error": "Hermes model base_url is not configured",
}


@pytest.mark.asyncio
async def test_selected_native_provider_without_local_url_is_unknown_not_red_or_green(
    monkeypatch,
):
    from api.routers import agent

    request = AsyncMock(
        return_value={
            "provider": "openai-codex",
            "model": "gpt-6.1-sol",
            "providers": [{"slug": "openai-codex", "models": ["gpt-6.1-sol"]}],
        }
    )
    monkeypatch.setattr(agent, "_hermes_json_request", request)
    monkeypatch.setattr(agent, "_hermes_profile", lambda: "wright")
    result = await reconcile_agent_model_configuration(MISSING_LOCAL)
    assert result["state"] == "unknown"
    assert "provider connection has not been checked" in result["error"]
    assert "workflow model readiness is assessed separately" in result["error"]
    request.assert_awaited_once_with(
        "GET",
        "/api/model/options",
        params={
            "profile": "wright",
            "explicit_only": "true",
            "include_unconfigured": "false",
            "refresh": "false",
        },
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error", ["Hermes openai-codex credentials were rejected", "LLM backend is offline"]
)
async def test_true_provider_failure_is_not_replaced_by_catalog_selection(
    monkeypatch, error
):
    from api.routers import agent

    request = AsyncMock()
    monkeypatch.setattr(agent, "_hermes_json_request", request)
    failed = {**MISSING_LOCAL, "error": error}
    assert await reconcile_agent_model_configuration(failed) == failed
    request.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {
            "provider": "openai-codex",
            "model": "missing",
            "providers": [{"slug": "openai-codex", "models": ["other"]}],
        },
    ],
)
async def test_gateway_does_not_confirm_selected_model(monkeypatch, payload):
    from api.routers import agent

    monkeypatch.setattr(agent, "_hermes_json_request", AsyncMock(return_value=payload))
    result = await reconcile_agent_model_configuration(MISSING_LOCAL)
    assert result["state"] == "disconnected"
    assert "No selected agent model" in result["error"]


@pytest.mark.asyncio
async def test_gateway_auth_failure_is_explicit_without_exposing_private_response(
    monkeypatch,
):
    from api.routers import agent

    monkeypatch.setattr(
        agent,
        "_hermes_json_request",
        AsyncMock(side_effect=HTTPException(401, "private provider response")),
    )
    result = await reconcile_agent_model_configuration(MISSING_LOCAL)
    assert result["state"] == "disconnected"
    assert "HTTP 401" in result["error"]
    assert "private provider" not in result["error"]


@pytest.mark.asyncio
async def test_inference_endpoint_reconciles_only_missing_local_configuration(
    client, mock_agent_engine, monkeypatch
):
    from api.routers import agent

    mock_agent_engine.check_llm_backend_health = AsyncMock(return_value=MISSING_LOCAL)
    monkeypatch.setattr(
        agent,
        "_hermes_json_request",
        AsyncMock(
            return_value={
                "provider": "openai-codex",
                "model": "gpt-6.1-sol",
                "providers": [{"slug": "openai-codex", "models": ["gpt-6.1-sol"]}],
            }
        ),
    )
    response = await client.get("/api/inference/health")
    assert response.status_code == 200
    assert response.json()["state"] == "unknown"
