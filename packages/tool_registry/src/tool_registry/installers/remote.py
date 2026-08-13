from __future__ import annotations

from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from ..capability_models import InstallPlan


class RemoteAdapterError(RuntimeError):
    pass


def _not_configured(*_args, **_kwargs):
    raise RemoteAdapterError("Remote endpoint adapter boundary is not configured")


class RemoteEndpointAdapter:
    kind = "remote_endpoint"
    version = "1"

    def __init__(
        self,
        *,
        register: Callable[[str, InstallPlan], dict[str, Any]] = _not_configured,
        unregister: Callable[[str, InstallPlan], dict[str, Any]] = _not_configured,
        read_only_probe: Callable[[str, InstallPlan], dict[str, Any]] = _not_configured,
    ) -> None:
        self.register = register
        self.unregister = unregister
        self.read_only_probe = read_only_probe

    @staticmethod
    def _endpoint(plan: InstallPlan) -> str:
        endpoint = plan.source.get("endpoint") or plan.source.get("command")
        if not isinstance(endpoint, str):
            raise RemoteAdapterError("Remote plan has no endpoint")
        parsed = urlsplit(endpoint)
        loopback = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if parsed.scheme != "https" and not (parsed.scheme == "http" and loopback):
            raise RemoteAdapterError("Remote endpoint is not HTTPS or loopback HTTP")
        if parsed.username or parsed.password or parsed.fragment:
            raise RemoteAdapterError(
                "Remote endpoint contains forbidden URL components"
            )
        return endpoint

    def prepare(self, plan: InstallPlan) -> dict[str, Any]:
        endpoint = self._endpoint(plan)
        return {"step": "prepare", "status": "succeeded", "endpoint": endpoint}

    def apply(self, plan: InstallPlan) -> dict[str, Any]:
        return self.register(self._endpoint(plan), plan)

    def validate(self, plan: InstallPlan) -> dict[str, Any]:
        return self.read_only_probe(self._endpoint(plan), plan)

    def rollback(self, plan: InstallPlan) -> dict[str, Any]:
        return self.unregister(self._endpoint(plan), plan)

    def remove(self, plan: InstallPlan) -> dict[str, Any]:
        return self.rollback(plan)
