"""Approval-bound onboarding adapters with injected side-effect boundaries."""

from .host_bridge import HostBridgeAdapter
from .local import LocalCommandAdapter, LocalPackageAdapter
from .remote import RemoteEndpointAdapter

__all__ = [
    "HostBridgeAdapter",
    "LocalCommandAdapter",
    "LocalPackageAdapter",
    "RemoteEndpointAdapter",
]
