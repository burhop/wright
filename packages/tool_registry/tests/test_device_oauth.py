"""Device authorization wire behavior; no live account or desktop claims."""

import asyncio
from urllib.parse import parse_qs
from uuid import uuid4

import httpx
import pytest
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken
from tool_registry.runners.device_oauth import DEVICE_GRANT, DeviceCodeAuth

ROOT = "https://provider.example"
AUTH = "https://identity.example/realm"


class Store:
    def __init__(self):
        self.client = None
        self.token = None
        self.writes = []

    async def get_tokens(self):
        return self.token

    async def set_tokens(self, value):
        self.token = value
        self.writes.append("token")

    async def get_client_info(self):
        return self.client

    async def set_client_info(self, value):
        self.client = value
        self.writes.append("client")


class Wire:
    def __init__(self):
        self.store = Store()
        self.requests = []
        self.presentations = []
        self.clock = 1.0
        self.sleeps = []
        self.polls = []
        self.device = uuid4().hex
        self.access = uuid4().hex
        self.refresh = uuid4().hex
        self.grants = [DEVICE_GRANT, "refresh_token"]
        self.issuer = AUTH
        self.resource = ROOT + "/mcp"
        self.poll_error = None

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.clock += seconds

    async def present(self, value):
        self.presentations.append(value)

    def respond(self, request):
        self.requests.append(request)
        path = str(request.url)
        if path == ROOT + "/mcp":
            if "authorization" in request.headers:
                assert request.headers["authorization"] == "Bearer " + self.access
                return httpx.Response(200, json={"ok": True})
            return httpx.Response(
                401,
                headers={
                    "www-authenticate": 'Bearer resource_metadata="'
                    + ROOT
                    + '/.well-known/oauth-protected-resource", scope="cad:read"'
                },
            )
        if "/.well-known/oauth-protected-resource" in path:
            return httpx.Response(
                200,
                json={
                    "resource": self.resource,
                    "authorization_servers": [AUTH],
                    "scopes_supported": ["cad:read"],
                },
            )
        if ".well-known/" in path:
            return httpx.Response(
                200,
                json={
                    "issuer": self.issuer,
                    "authorization_endpoint": AUTH + "/authorize",
                    "token_endpoint": AUTH + "/token",
                    "device_authorization_endpoint": AUTH + "/device",
                    "registration_endpoint": AUTH + "/register",
                    "grant_types_supported": self.grants,
                },
            )
        data = (
            parse_qs(request.content.decode())
            if not request.headers.get("content-type", "").startswith(
                "application/json"
            )
            else {}
        )
        if path == AUTH + "/register":
            return httpx.Response(
                201,
                json={
                    "client_id": "device-client",
                    "grant_types": [DEVICE_GRANT, "refresh_token"],
                    "response_types": ["code"],
                    "redirect_uris": [],
                    "token_endpoint_auth_method": "none",
                },
            )
        if path == AUTH + "/device":
            assert data["resource"] == [ROOT + "/mcp"]
            assert data["scope"] == ["cad:read"]
            return httpx.Response(
                200,
                json={
                    "device_code": self.device,
                    "user_code": "TEST-1234",
                    "verification_uri": AUTH + "/verify",
                    "expires_in": 30,
                    "interval": 5,
                },
            )
        if path == AUTH + "/token":
            assert data["resource"] == [ROOT + "/mcp"]
            if self.poll_error:
                raise self.poll_error
            if data["grant_type"] == [DEVICE_GRANT]:
                assert data["device_code"] == [self.device]
                result = self.polls.pop(0) if self.polls else None
                if result is not None:
                    return httpx.Response(
                        400, json={"error": result, "error_description": self.access}
                    )
            else:
                assert data["grant_type"] == ["refresh_token"]
                assert data["refresh_token"] == [self.refresh]
            return httpx.Response(
                200,
                json={
                    "access_token": self.access,
                    "token_type": "Bearer",
                    "expires_in": 60,
                    "refresh_token": self.refresh,
                },
            )
        raise AssertionError(path)

    def auth(self):
        return DeviceCodeAuth(
            ROOT + "/mcp",
            self.store,
            self.present,
            clock=lambda: self.clock,
            sleep=self.sleep,
        )


@pytest.mark.asyncio
async def test_device_polling_scope_storage_and_no_credential_leak():
    wire = Wire()
    wire.polls = ["authorization_pending", "slow_down"]
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(wire.respond),
        auth=wire.auth(),
        follow_redirects=False,
    ) as client:
        assert (
            await client.post(ROOT + "/mcp", json={"method": "initialize"})
        ).json() == {"ok": True}
        assert (
            await client.post(ROOT + "/mcp", json={"method": "tools/list"})
        ).status_code == 200
    assert wire.sleeps == [5, 5, 10]
    assert wire.store.writes == ["client", "token"]
    assert wire.store.client.issuer == AUTH
    assert wire.presentations[-1] is None
    assert wire.device not in str(wire.presentations)
    assert wire.access not in str(wire.presentations)
    assert wire.refresh not in str(wire.presentations)
    assert sum(str(r.url) == AUTH + "/device" for r in wire.requests) == 1
    assert all(
        "authorization" not in r.headers
        for r in wire.requests
        if str(r.url) != ROOT + "/mcp"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        "access_denied",
        "expired_token",
        "unauthorized_client",
        "invalid_client",
        "unknown",
    ],
)
async def test_terminal_denial_never_dispatches_or_repeats(error):
    wire = Wire()
    wire.polls = [error]
    with pytest.raises(RuntimeError) as caught:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(wire.respond), auth=wire.auth()
        ) as client:
            await client.post(ROOT + "/mcp", json={"method": "tools/call"})
    assert wire.access not in str(caught.value)
    assert wire.store.token is None
    assert len(wire.sleeps) == 1 and wire.presentations[-1] is None
    assert not any("authorization" in r.headers for r in wire.requests)


@pytest.mark.asyncio
async def test_expiry_is_bounded_and_clears_operator_presentation():
    wire = Wire()
    wire.polls = ["authorization_pending"] * 10
    with pytest.raises(RuntimeError, match="expired"):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(wire.respond), auth=wire.auth()
        ) as client:
            await client.get(ROOT + "/mcp")
    assert wire.clock == 31 and wire.presentations[-1] is None
    assert wire.store.token is None


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["unsupported", "issuer", "resource"])
async def test_discovery_identity_and_missing_grant_fail_before_registration(change):
    wire = Wire()
    if change == "unsupported":
        wire.grants = ["authorization_code"]
    if change == "issuer":
        wire.issuer = "https://other.example/realm"
    if change == "resource":
        wire.resource = "https://other.example/mcp"
    with pytest.raises(Exception):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(wire.respond), auth=wire.auth()
        ) as client:
            await client.get(ROOT + "/mcp")
    assert wire.store.writes == [] and wire.presentations == []
    assert all(r.method == "GET" for r in wire.requests)


@pytest.mark.asyncio
async def test_restart_refreshes_existing_bound_client_without_another_login():
    wire = Wire()
    wire.store.client = OAuthClientInformationFull(
        client_id="saved-client",
        grant_types=[DEVICE_GRANT, "refresh_token"],
        token_endpoint_auth_method="none",
        issuer=AUTH,
        redirect_uris=None,
    )
    wire.store.token = OAuthToken(
        access_token=uuid4().hex,
        token_type="Bearer",
        expires_in=60,
        refresh_token=wire.refresh,
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(wire.respond), auth=wire.auth()
    ) as client:
        assert (await client.get(ROOT + "/mcp")).status_code == 200
    assert wire.presentations == [] and wire.store.writes == ["token", "token"]
    assert not any(
        str(r.url) in {AUTH + "/device", AUTH + "/register"} for r in wire.requests
    )


@pytest.mark.asyncio
async def test_saved_other_issuer_or_code_client_is_preserved():
    for issuer, grants in [
        (AUTH, ["authorization_code"]),
        ("https://other.example", [DEVICE_GRANT]),
    ]:
        wire = Wire()
        wire.store.client = OAuthClientInformationFull(
            client_id="saved-client",
            grant_types=grants,
            issuer=issuer,
            redirect_uris=None,
            token_endpoint_auth_method="none",
        )
        with pytest.raises(RuntimeError, match="Saved OAuth client"):
            async with httpx.AsyncClient(
                transport=httpx.MockTransport(wire.respond), auth=wire.auth()
            ) as client:
                await client.get(ROOT + "/mcp")
        assert wire.store.writes == [] and not any(
            r.method == "POST" for r in wire.requests
        )


@pytest.mark.asyncio
async def test_cancellation_clears_challenge_and_does_not_send_tool_request():
    wire = Wire()
    waiting = asyncio.Event()

    async def wait(seconds):
        waiting.set()
        await asyncio.Future()

    auth = wire.auth()
    auth.sleep = wait
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(wire.respond), auth=auth
    ) as client:
        task = asyncio.create_task(
            client.post(ROOT + "/mcp", json={"method": "tools/call"})
        )
        await asyncio.wait_for(waiting.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    assert wire.presentations[-1] is None and wire.store.token is None
    assert not any("authorization" in r.headers for r in wire.requests)


@pytest.mark.asyncio
async def test_uncertain_poll_is_not_automatically_retried():
    wire = Wire()
    wire.poll_error = httpx.ReadError("connection lost")
    with pytest.raises(httpx.ReadError):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(wire.respond), auth=wire.auth()
        ) as client:
            await client.get(ROOT + "/mcp")
    assert wire.presentations[-1] is None
    assert sum(str(r.url) == AUTH + "/token" for r in wire.requests) == 1
    assert wire.store.token is None


@pytest.mark.asyncio
async def test_streaming_wire_is_consumed_before_parsing():
    wire = Wire()

    class Body(httpx.AsyncByteStream):
        def __init__(self, data):
            self.data = data

        async def __aiter__(self):
            yield self.data

    def streaming(request):
        response = wire.respond(request)
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            stream=Body(response.content),
        )

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(streaming), auth=wire.auth()
    ) as client:
        assert (await client.get(ROOT + "/mcp")).status_code == 200
    assert wire.presentations[-1] is None and wire.store.token is not None


@pytest.mark.asyncio
async def test_uncertain_refresh_is_consumed_and_restart_requires_new_consent():
    wire = Wire()
    wire.store.client = OAuthClientInformationFull(
        client_id="saved-client",
        grant_types=[DEVICE_GRANT, "refresh_token"],
        token_endpoint_auth_method="none",
        issuer=AUTH,
        redirect_uris=None,
    )
    wire.store.token = OAuthToken(
        access_token=uuid4().hex,
        token_type="Bearer",
        expires_in=60,
        refresh_token=wire.refresh,
    )
    wire.poll_error = httpx.ReadError("connection lost")
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(wire.respond), auth=wire.auth()
    ) as client:
        with pytest.raises(httpx.ReadError):
            await client.get(ROOT + "/mcp")
    assert wire.store.token.refresh_token is None
    first = len(wire.requests)
    wire.poll_error = None
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(wire.respond), auth=wire.auth()
    ) as client:
        assert (await client.get(ROOT + "/mcp")).status_code == 200
    assert wire.presentations[0]["user_code"] == "TEST-1234"
    assert all(
        b"grant_type=refresh_token" not in r.content for r in wire.requests[first:]
    )


@pytest.mark.asyncio
async def test_device_storage_preserves_legacy_authentication_and_other_credentials(
    monkeypatch,
):
    from tool_registry.runners import sse

    saved = {
        "MCP_OAUTH_CLIENT": "retained-old-client",
        "MCP_OAUTH_TOKEN": "retained-old-token",
        "OTHER_KEY": "retained-other-value",
    }
    original = dict(saved)
    monkeypatch.setattr(sse, "read_secrets", lambda server_id: dict(saved))
    monkeypatch.setattr(
        sse,
        "write_secrets",
        lambda server_id, values: (saved.clear(), saved.update(values)),
    )
    store = sse._WrightOAuthTokenStorage("provider", device_code=True)
    token = OAuthToken(access_token=uuid4().hex, token_type="Bearer", expires_in=60)
    await store.set_tokens(token)
    await store.set_client_info(
        OAuthClientInformationFull(
            client_id="device-client",
            redirect_uris=None,
            grant_types=[DEVICE_GRANT],
            issuer=AUTH,
            token_endpoint_auth_method="none",
        )
    )
    assert await store.get_tokens() == token
    assert (await store.get_client_info()).client_id == "device-client"
    assert all(saved[k] == v for k, v in original.items())
    store.clear_oauth_state()
    assert saved == original


@pytest.mark.asyncio
async def test_remote_runner_allows_bounded_auth_rounds_without_following_redirects(
    monkeypatch,
):
    import json
    from tool_registry.runners import sse
    from mcp.types import LATEST_PROTOCOL_VERSION

    wire = Wire()
    wire.polls = ["authorization_pending"] * 25
    # Permit the full declared lifetime; fake time keeps this deterministic.
    old_response = wire.respond

    def respond(request):
        if str(request.url) == ROOT + "/mcp" and "authorization" in request.headers:
            payload = json.loads(request.content)
            if payload["method"] == "initialize":
                return httpx.Response(
                    200,
                    json={
                        "jsonrpc": "2.0",
                        "id": payload["id"],
                        "result": {
                            "protocolVersion": LATEST_PROTOCOL_VERSION,
                            "serverInfo": {"name": "fixture", "version": "1"},
                            "capabilities": {},
                        },
                    },
                )
            if payload["method"] == "notifications/initialized":
                return httpx.Response(202)
            raise AssertionError(payload["method"])
        response = old_response(request)
        if str(request.url) == AUTH + "/device":
            body = response.json()
            body["expires_in"] = 300
            return httpx.Response(200, json=body)
        return response

    actual_client = httpx.AsyncClient
    constructed = []

    def client(**kwargs):
        constructed.append(kwargs)
        return actual_client(transport=httpx.MockTransport(respond), **kwargs)

    actual_auth = DeviceCodeAuth
    monkeypatch.setattr(sse.httpx, "AsyncClient", client)
    monkeypatch.setattr(
        sse,
        "DeviceCodeAuth",
        lambda *a, **kw: actual_auth(
            *a, **kw, clock=lambda: wire.clock, sleep=wire.sleep
        ),
    )
    monkeypatch.setattr(sse, "_WrightOAuthTokenStorage", lambda *a, **kw: wire.store)

    async def scoped_present(server_id, value):
        await wire.present(value)

    runner = sse.SseRunner(ROOT + "/mcp", device_authorization_presenter=scoped_present)
    try:
        await runner.start()
        assert runner.is_running()
        assert len(wire.sleeps) == 26
        assert constructed[0]["follow_redirects"] is False

        # An actual redirect is still refused, independently of auth rounds.
        def redirect(request):
            return httpx.Response(
                302, headers={"location": "https://other.example/steal"}
            )

        async with actual_client(
            transport=httpx.MockTransport(redirect),
            follow_redirects=constructed[0]["follow_redirects"],
            max_redirects=constructed[0]["max_redirects"],
        ) as http:
            assert (await http.get(ROOT + "/mcp")).status_code == 302
    finally:
        await runner.stop()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url", ["https://public.example/mcp", "http://127.0.0.1:8123/mcp"]
)
async def test_public_mcp_needs_no_device_grant_or_credential_access(url):
    wire = Wire()
    requests = []

    def public(request):
        requests.append(request)
        return httpx.Response(200, json={"result": {"protocolVersion": "2025-11-25"}})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(public),
        auth=DeviceCodeAuth(url, wire.store, wire.present),
    ) as client:
        assert (
            await client.post(url, json={"method": "initialize"})
        ).status_code == 200
    assert len(requests) == 1 and wire.presentations == [] and wire.store.writes == []
    assert "authorization" not in requests[0].headers


@pytest.mark.asyncio
async def test_protected_http_resource_cannot_receive_oauth_credentials():
    wire = Wire()
    requests = []

    def protected(request):
        requests.append(request)
        return httpx.Response(401)

    url = "http://127.0.0.1:8123/mcp"
    with pytest.raises(RuntimeError, match="HTTPS"):
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(protected),
            auth=DeviceCodeAuth(url, wire.store, wire.present),
        ) as client:
            await client.get(url)
    assert len(requests) == 1 and wire.store.writes == [] and wire.presentations == []
