"""Explicit RFC 8628 authentication for a remote/headless MCP client.

Uses the MCP SDK's discovery/schema helpers and the existing server-scoped
TokenStorage. It never opens a loopback receiver or substitutes another grant.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

import httpx
from mcp.client.auth import TokenStorage
from mcp.client.auth.utils import (
    build_oauth_authorization_server_metadata_discovery_urls,
    build_protected_resource_metadata_discovery_urls,
    credentials_match_issuer,
    extract_resource_metadata_from_www_auth,
    extract_scope_from_www_auth,
    get_client_metadata_scopes,
    handle_auth_metadata_response,
    handle_protected_resource_response,
    validate_metadata_issuer,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
DevicePresentation = Callable[[dict | None], Awaitable[None]]


def _https(value: str) -> str:
    if not isinstance(value, str):
        raise RuntimeError("Invalid device sign-in address")
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise RuntimeError(
            "Device sign-in requires HTTPS addresses without credentials"
        )
    return value


async def _object(response: httpx.Response) -> dict:
    await response.aread()
    try:
        value = response.json()
    except ValueError:
        raise RuntimeError("Invalid device sign-in response") from None
    if not isinstance(value, dict):
        raise RuntimeError("Invalid device sign-in response")
    return value


class DeviceCodeAuth(httpx.Auth):
    """One bounded sign-in, with SDK-compatible token/client storage and refresh.

    Only authorization_pending and slow_down are polled. Transport failures,
    denial, invalid clients and uncertain refreshes fail without a retry.
    """

    requires_response_body = True

    def __init__(
        self,
        server_url: str,
        storage: TokenStorage,
        presenter: DevicePresentation,
        *,
        timeout: float = 600,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    ):
        self.server_url = server_url
        self.storage, self.presenter = storage, presenter
        self.timeout, self.clock, self.sleep = timeout, clock, sleep
        self.lock = asyncio.Lock()
        self.token: OAuthToken | None = None
        self.expires_at = 0.0
        self.metadata: dict | None = None
        self.client: OAuthClientInformationFull | None = None
        self.scope: str | None = None
        self.resource: str | None = None

    async def _discover(self, challenge: httpx.Response):
        # Discover without sending a credential to a possibly changed issuer.
        prm = None
        for url in build_protected_resource_metadata_discovery_urls(
            extract_resource_metadata_from_www_auth(challenge), self.server_url
        ):
            response = yield httpx.Request("GET", _https(url))
            if response.status_code >= 500 or response.status_code == 429:
                raise RuntimeError("MCP authorization discovery is unavailable")
            prm = await handle_protected_resource_response(response)
            if prm is not None:
                break
        if prm is None:
            raise RuntimeError("Device sign-in requires MCP resource metadata")
        # Resource may be the endpoint or its same-origin parent, never another
        # resource. Do not send an access token before validating this identity.
        resource = str(prm.resource)
        target, declared = urlsplit(self.server_url), urlsplit(resource)
        if (
            (target.scheme, target.netloc) != (declared.scheme, declared.netloc)
            or not (
                target.path == declared.path
                or target.path.startswith(declared.path.rstrip("/") + "/")
            )
            or declared.query
            or declared.fragment
        ):
            raise RuntimeError("MCP authorization resource does not match the endpoint")
        issuer = _https(str(prm.authorization_servers[0]))
        metadata = None
        for url in build_oauth_authorization_server_metadata_discovery_urls(
            issuer, self.server_url
        ):
            response = yield httpx.Request("GET", _https(url))
            ok, model = await handle_auth_metadata_response(response)
            if not ok:
                raise RuntimeError("Authorization server discovery is unavailable")
            if model is not None:
                validate_metadata_issuer(model, issuer)
                metadata = await _object(response)
                break
        if metadata is None or DEVICE_GRANT not in metadata.get(
            "grant_types_supported", []
        ):
            raise RuntimeError("Provider does not support device-code sign-in")
        for key in ("device_authorization_endpoint", "token_endpoint"):
            _https(metadata.get(key, ""))
        self.scope = get_client_metadata_scopes(
            extract_scope_from_www_auth(challenge), prm, model
        )
        self.resource, self.metadata = resource, metadata
        client = await self.storage.get_client_info()
        if client is not None and credentials_match_issuer(client, issuer, None):
            if client.client_secret or client.token_endpoint_auth_method != "none":
                raise RuntimeError("Device sign-in requires a public OAuth client")
            if DEVICE_GRANT not in client.grant_types:
                raise RuntimeError(
                    "Saved OAuth client does not permit device sign-in; reconnect with a device client"
                )
            self.client = client
            self.token = await self.storage.get_tokens()
            return
        if client is not None:
            # Preserve old credentials; migration must be an explicit operator
            # action rather than replacement during a validation attempt.
            raise RuntimeError(
                "Saved OAuth client belongs to another authorization server"
            )
        registration = _https(metadata.get("registration_endpoint", ""))
        response = yield httpx.Request(
            "POST",
            registration,
            json={
                "client_name": "Wright",
                "grant_types": [DEVICE_GRANT, "refresh_token"],
                "response_types": [],
                "token_endpoint_auth_method": "none",
            },
        )
        if response.status_code not in (200, 201):
            raise RuntimeError(
                "Provider refused registration of a device sign-in client"
            )
        data = await _object(response)
        data.pop("issuer", None)
        # RFC 8628 has no redirect URI. SDK 1.30's shared client schema permits
        # None but rejects an empty list, which providers may return for this grant.
        data["redirect_uris"] = data.get("redirect_uris") or None
        try:
            client = OAuthClientInformationFull.model_validate(data)
        except ValueError:
            raise RuntimeError("Invalid device client registration response") from None
        if not client.client_id:
            raise RuntimeError("Device client registration omitted its identity")
        if client.client_secret or client.token_endpoint_auth_method != "none":
            raise RuntimeError("Device sign-in requires a public OAuth client")
        if DEVICE_GRANT not in client.grant_types:
            raise RuntimeError("Registered OAuth client does not permit device sign-in")
        client.issuer = issuer
        await self.storage.set_client_info(client)
        self.client = client

    async def _authorize(self):
        assert self.metadata is not None and self.client is not None
        data = {"client_id": self.client.client_id, "resource": self.resource}
        if self.scope:
            data["scope"] = self.scope
        response = yield httpx.Request(
            "POST", self.metadata["device_authorization_endpoint"], data=data
        )
        if response.status_code != 200:
            raise RuntimeError(
                "Provider refused device sign-in; no other grant was attempted"
            )
        pending = await _object(response)
        code, user_code = pending.get("device_code"), pending.get("user_code")
        lifetime, interval = pending.get("expires_in"), pending.get("interval", 5)
        if (
            not isinstance(code, str)
            or not code
            or len(code) > 16384
            or not isinstance(user_code, str)
            or not user_code
            or len(user_code) > 128
            or isinstance(lifetime, bool)
            or not isinstance(lifetime, int)
            or lifetime <= 0
            or isinstance(interval, bool)
            or not isinstance(interval, int)
            or interval < 1
        ):
            raise RuntimeError("Invalid device sign-in challenge")
        url = _https(pending.get("verification_uri", ""))
        complete = pending.get("verification_uri_complete")
        if complete is not None:
            _https(complete)
            if urlsplit(complete).netloc != urlsplit(url).netloc:
                raise RuntimeError("Device sign-in addresses do not match")
        deadline = self.clock() + min(lifetime, self.timeout)
        try:
            await self.presenter(
                {
                    "verification_uri": url,
                    "verification_uri_complete": complete,
                    "user_code": user_code,
                    "expires_in": min(lifetime, self.timeout),
                }
            )
            while True:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    raise RuntimeError(
                        "Device sign-in expired; start a fresh connection check"
                    )
                await self.sleep(min(interval, remaining))
                if self.clock() >= deadline:
                    raise RuntimeError(
                        "Device sign-in expired; start a fresh connection check"
                    )
                response = yield httpx.Request(
                    "POST",
                    self.metadata["token_endpoint"],
                    data={
                        "grant_type": DEVICE_GRANT,
                        "client_id": self.client.client_id,
                        "device_code": code,
                        "resource": self.resource,
                    },
                )
                result = await _object(response)
                if response.status_code == 200:
                    await self._save_token(result)
                    return
                if (
                    response.status_code == 400
                    and result.get("error") == "authorization_pending"
                ):
                    continue
                if response.status_code == 400 and result.get("error") == "slow_down":
                    interval += 5
                    continue
                error = result.get("error")
                reason = (
                    error
                    if error
                    in {
                        "access_denied",
                        "expired_token",
                        "invalid_client",
                        "unauthorized_client",
                    }
                    else "provider_error"
                )
                raise RuntimeError("Device sign-in failed: " + reason)
        finally:
            await self.presenter(None)

    async def _save_token(self, data: dict):
        try:
            token = OAuthToken.model_validate(data)
        except ValueError:
            raise RuntimeError("Invalid device sign-in token response") from None
        if token.token_type.lower() != "bearer" or not token.access_token:
            raise RuntimeError("Unsupported device sign-in token")
        await self.storage.set_tokens(token)
        self.token = token
        self.expires_at = self.clock() + max(0, (token.expires_in or 0) - 10)

    async def async_auth_flow(self, request: httpx.Request):
        if str(request.url) != self.server_url:
            raise RuntimeError("Device authentication is bound to one MCP endpoint")
        async with self.lock:
            if self.metadata is None:
                # As in the SDK's authorization-code client, public MCPs need
                # no OAuth. Only a protected-resource challenge starts sign-in.
                response = yield request
                if response.status_code != 401:
                    return
                _https(self.server_url)
                flow = self._discover(response)
                try:
                    outgoing = await anext(flow)
                    while True:
                        response = yield outgoing
                        outgoing = await flow.asend(response)
                except StopAsyncIteration:
                    pass
                finally:
                    await flow.aclose()
            if self.token is not None and self.clock() >= self.expires_at:
                assert self.metadata is not None and self.client is not None
                if self.token.refresh_token:
                    # No retry after an uncertain refresh/rotation. Clear only
                    # this instance's token; persistent credentials stay owned by
                    # the existing store and no tool request has been dispatched.
                    refresh = self.token.refresh_token
                    # Consume the refresh reference durably before a potentially
                    # rotating request. A crash/lost response cannot cause a
                    # restart to replay it; recovery asks for device sign-in.
                    await self.storage.set_tokens(
                        self.token.model_copy(update={"refresh_token": None})
                    )
                    self.token = None
                    response = yield httpx.Request(
                        "POST",
                        self.metadata["token_endpoint"],
                        data={
                            "grant_type": "refresh_token",
                            "client_id": self.client.client_id,
                            "refresh_token": refresh,
                            "resource": self.resource,
                        },
                    )
                    if response.status_code == 200:
                        refreshed = await _object(response)
                        refreshed.setdefault("refresh_token", refresh)
                        await self._save_token(refreshed)
                    elif (
                        response.status_code != 400
                        or (await _object(response)).get("error") != "invalid_grant"
                    ):
                        raise RuntimeError(
                            "Device token refresh failed; no request was retried"
                        )
                else:
                    self.token = None
            if self.token is None:
                flow = self._authorize()
                try:
                    outgoing = await anext(flow)
                    while True:
                        response = yield outgoing
                        outgoing = await flow.asend(response)
                except StopAsyncIteration:
                    pass
                finally:
                    await flow.aclose()
            assert self.token is not None
            request.headers["Authorization"] = "Bearer " + self.token.access_token
            response = yield request
            if response.status_code in (401, 403):
                self.token = None
                raise RuntimeError(
                    "Provider rejected device authentication; reconnect explicitly"
                )
