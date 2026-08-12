from types import SimpleNamespace

import httpx
import pytest

from api.routers import agent


@pytest.mark.asyncio
async def test_model_request_uses_running_gateway_credentials_not_model_profile(
    monkeypatch,
) -> None:
    resolver_calls: list[tuple[str, object]] = []

    def resolve_settings(name: str, env=None):
        resolver_calls.append((name, env))
        return SimpleNamespace(
            base_url="http://127.0.0.1:8642",
            api_key="current-gateway-key",
        )

    async def request(self, method, url, **kwargs):
        assert kwargs["headers"]["Authorization"] == ("Bearer current-gateway-key")
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
