"""Feature and limit settings for Wright-governed Rivet MCP execution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class RivetMcpGatewaySettings:
    enabled: bool = False
    automatic_call_approvals: bool = True
    authority_grace_seconds: float = 5.0
    approval_ttl_seconds: float = 300.0
    maximum_request_bytes: int = 1024 * 1024
    maximum_event_bytes: int = 64 * 1024
    maximum_events_per_call: int = 2_000

    def __post_init__(self) -> None:
        if self.authority_grace_seconds <= 0 or self.approval_ttl_seconds <= 0:
            raise ValueError("Rivet MCP time limits must be positive")
        if self.maximum_request_bytes < 1024 or self.maximum_event_bytes < 256:
            raise ValueError("Rivet MCP byte limits are invalid")
        if self.maximum_event_bytes > self.maximum_request_bytes:
            raise ValueError("Rivet MCP event limit may not exceed request limit")
        if self.maximum_events_per_call < 1:
            raise ValueError("Rivet MCP event count limit must be positive")

    @classmethod
    def from_env(
        cls, env: Mapping[str, str] | None = None
    ) -> "RivetMcpGatewaySettings":
        source = env or os.environ
        return cls(
            enabled=source.get("WRIGHT_RIVET_MCP_GATEWAY_ENABLED", "0").strip().lower()
            in {"1", "true", "yes"},
            automatic_call_approvals=source.get(
                "WRIGHT_RIVET_MCP_AUTOMATIC_CALL_APPROVALS", "1"
            )
            .strip()
            .lower()
            in {"1", "true", "yes"},
            authority_grace_seconds=float(
                source.get("WRIGHT_RIVET_MCP_AUTHORITY_GRACE_SECONDS", "5")
            ),
            approval_ttl_seconds=float(
                source.get("WRIGHT_RIVET_MCP_APPROVAL_TTL_SECONDS", "300")
            ),
            maximum_request_bytes=int(
                source.get("WRIGHT_RIVET_MCP_REQUEST_BYTES", str(1024 * 1024))
            ),
            maximum_event_bytes=int(
                source.get("WRIGHT_RIVET_MCP_EVENT_BYTES", str(64 * 1024))
            ),
            maximum_events_per_call=int(
                source.get("WRIGHT_RIVET_MCP_EVENTS_PER_CALL", "2000")
            ),
        )


__all__ = ["RivetMcpGatewaySettings"]
