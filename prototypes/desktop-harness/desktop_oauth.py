"""Ephemeral operator-only OAuth presentation; never token or validation authority."""

import time
from urllib.parse import urlsplit


class DesktopOAuthPresentation:
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
        }

    def _expire(self):
        for entry in self._bindings.values():
            if self._clock() >= entry["expires"]:
                entry["authorization_url"] = None
                entry["callback_uri"] = None

    def clear(self, server_id):
        self._bindings.pop(server_id, None)

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
            }
        if entry["scope"] != (workspace_id, session_id, plan_id):
            raise ValueError("Sign-in presentation belongs to another operator scope")
        if self._clock() >= entry["expires"]:
            return {
                "presentation": "expired",
                "authorization_url": None,
                "callback_uri": None,
            }
        return {
            "presentation": "awaiting_user"
            if entry["authorization_url"]
            else "waiting_for_provider",
            "authorization_url": entry["authorization_url"],
            "callback_uri": entry["callback_uri"],
        }
