"""Ephemeral operator-only OAuth presentation; never token or validation authority."""

import time
from urllib.parse import urlsplit


class McpOAuthPresentation:
    def __init__(self, *, clock=time.monotonic):
        self._clock = clock
        self._bindings = {}

    def bind(self, server_id, workspace_id, session_id, plan_id):
        self._expire()
        if server_id in self._bindings:
            raise ValueError("A sign-in operation is already pending for this server")
        self._bindings[server_id] = {
            "scope": (workspace_id, session_id, plan_id),
            "expires": self._clock() + 330,
            "authorization_url": None,
            "callback_uri": None,
            "device": None,
        }

    def _expire(self):
        for entry in self._bindings.values():
            if self._clock() >= entry["expires"]:
                entry["authorization_url"] = None
                entry["callback_uri"] = None
                entry["device"] = None

    def clear(self, server_id):
        self._bindings.pop(server_id, None)

    async def present_device(self, server_id, challenge):
        self._expire()
        entry = self._bindings.get(server_id)
        if entry is None:
            if challenge is None:
                return
            raise ValueError("No scoped desktop device sign-in is pending")
        if challenge is None:
            entry["device"] = None
            return
        if self._clock() >= entry["expires"]:
            raise ValueError("Desktop sign-in presentation expired")
        target = urlsplit(challenge.get("verification_uri", ""))
        complete = urlsplit(
            challenge.get("verification_uri_complete")
            or challenge.get("verification_uri", "")
        )
        code, lifetime = challenge.get("user_code"), challenge.get("expires_in")
        if (
            target.scheme != "https"
            or not target.hostname
            or target.username
            or target.password
            or target.fragment
            or complete.scheme != "https"
            or complete.netloc != target.netloc
            or complete.username
            or complete.password
            or complete.fragment
            or not isinstance(code, str)
            or not code
            or len(code) > 128
            or isinstance(lifetime, bool)
            or not isinstance(lifetime, (int, float))
            or not 0 < lifetime <= 600
        ):
            raise ValueError("Unsupported device sign-in presentation")
        entry["expires"] = self._clock() + lifetime
        entry["device"] = dict(challenge)

    async def present(self, server_id, url, redirect):
        self._expire()
        entry = self._bindings.get(server_id)
        if entry is None:
            if url is None:
                return
            raise ValueError("No scoped desktop operator sign-in is pending")
        if url is None:
            entry["authorization_url"] = None
            entry["callback_uri"] = None
            return
        if self._clock() >= entry["expires"]:
            raise ValueError("Desktop sign-in presentation expired")
        target = urlsplit(url)
        callback = urlsplit(redirect or "")
        if (
            target.scheme != "https"
            or not target.hostname
            or target.username
            or target.password
            or callback.scheme != "http"
            or callback.hostname != "127.0.0.1"
            or not callback.port
            or callback.path != "/oauth/callback"
            or callback.username
            or callback.password
            or callback.query
            or callback.fragment
        ):
            raise ValueError("Unsupported sign-in presentation address")
        entry["authorization_url"] = url
        entry["callback_uri"] = redirect

    def read(self, server_id, workspace_id, session_id, plan_id):
        self._expire()
        entry = self._bindings.get(server_id)
        if entry is None:
            return {
                "presentation": "unavailable",
                "authorization_url": None,
                "callback_uri": None,
                "device": None,
            }
        if entry["scope"] != (workspace_id, session_id, plan_id):
            raise ValueError("Sign-in presentation belongs to another operator scope")
        if self._clock() >= entry["expires"]:
            return {
                "presentation": "expired",
                "authorization_url": None,
                "callback_uri": None,
                "device": None,
            }
        return {
            "presentation": "awaiting_user"
            if entry["authorization_url"] or entry["device"]
            else "waiting_for_provider",
            "authorization_url": entry["authorization_url"],
            "callback_uri": entry["callback_uri"],
            "device": entry["device"],
        }


class NativeDeviceSignIn(McpOAuthPresentation):
    """Native engineer/admin presentation of the same server-scoped device flow."""

    async def present_native(self, server_id, challenge):
        if challenge is None:
            self.clear(server_id)
            return
        if server_id not in self._bindings:
            self.bind(server_id, None, None, server_id)
        await self.present_device(server_id, challenge)

    def read_native(self, server_id):
        return self.read(server_id, None, None, server_id)
