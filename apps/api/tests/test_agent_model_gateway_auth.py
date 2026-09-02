from types import SimpleNamespace
import asyncio
import threading

import httpx
import pytest

from api.routers import agent


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
