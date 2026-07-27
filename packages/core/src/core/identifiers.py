"""Side-effect-free domain identifiers shared across Wright packages."""

from __future__ import annotations

from dataclasses import dataclass


def _required(value: str, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class WorkspaceId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _required(self.value, "workspace_id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SessionId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _required(self.value, "session_id"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AgentId:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _required(self.value, "agent_id"))

    def __str__(self) -> str:
        return self.value
