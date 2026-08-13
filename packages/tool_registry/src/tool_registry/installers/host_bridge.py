from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ..capability_models import InstallPlan


class HostBridgeError(RuntimeError):
    pass


def _not_configured(*_args, **_kwargs):
    raise HostBridgeError("Host bridge adapter boundary is not configured")


class HostBridgeAdapter:
    kind = "host_bridge"
    version = "1"

    def __init__(
        self,
        *,
        host_detectors: Mapping[str, Callable[[], Mapping[str, Any]]],
        addon_verifiers: Mapping[str, Callable[[], Mapping[str, Any]]],
        handshake: Callable[[InstallPlan], Mapping[str, Any]] = _not_configured,
        register: Callable[[InstallPlan], Mapping[str, Any]] = _not_configured,
        unregister: Callable[[InstallPlan], Mapping[str, Any]] = _not_configured,
    ) -> None:
        self.host_detectors = dict(host_detectors)
        self.addon_verifiers = dict(addon_verifiers)
        self.handshake = handshake
        self.register = register
        self.unregister = unregister

    def _hosts(self, plan: InstallPlan) -> list[str]:
        hosts = list(plan.requirements.host)
        if not hosts:
            raise HostBridgeError("Host bridge plan has no allowlisted host")
        return hosts

    def prepare(self, plan: InstallPlan) -> dict[str, Any]:
        evidence = []
        for host in self._hosts(plan):
            detector = self.host_detectors.get(host)
            if detector is None:
                raise HostBridgeError(f"Host detector is not allowlisted: {host}")
            fact = dict(detector())
            if not fact.get("available"):
                raise HostBridgeError(f"Required host is unavailable: {host}")
            evidence.append(
                {"host": host, "available": True, "version": fact.get("version")}
            )
        return {"step": "prepare", "status": "succeeded", "hosts": evidence}

    def apply(self, plan: InstallPlan) -> dict[str, Any]:
        for host in self._hosts(plan):
            verifier = self.addon_verifiers.get(host)
            if verifier is None or not dict(verifier()).get("available"):
                raise HostBridgeError(f"Approved bridge add-on is unavailable: {host}")
        handshake = dict(self.handshake(plan))
        if not handshake.get("connected"):
            raise HostBridgeError("The read-only host handshake failed")
        registration = dict(self.register(plan))
        return {"step": "apply", "status": "succeeded", "registration": registration}

    def validate(self, plan: InstallPlan) -> dict[str, Any]:
        handshake = dict(self.handshake(plan))
        return {
            "step": "validate",
            "status": "succeeded" if handshake.get("connected") else "failed",
        }

    def rollback(self, plan: InstallPlan) -> dict[str, Any]:
        return {
            "step": "rollback",
            "status": "succeeded",
            "registration": dict(self.unregister(plan)),
        }

    def remove(self, plan: InstallPlan) -> dict[str, Any]:
        return self.rollback(plan)
