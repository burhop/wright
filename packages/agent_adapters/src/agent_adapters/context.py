from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol

SupportLevel = Literal["supported", "experimental", "stub", "unavailable"]


@dataclass(frozen=True)
class AgentContextMaterializationRequest:
    db_path: str
    workspace_path: str
    workspace_id: str | None = None
    session_id: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class AgentContextMaterializationResult:
    provider_id: str
    support_level: SupportLevel
    files_written: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    error_code: str | None = None


class AgentContextMaterializer(Protocol):
    @property
    def provider_id(self) -> str: ...

    @property
    def support_level(self) -> SupportLevel: ...

    def materialize(
        self, request: AgentContextMaterializationRequest
    ) -> AgentContextMaterializationResult: ...


@dataclass(frozen=True)
class NoOpAgentContextMaterializer:
    provider_id: str
    support_level: SupportLevel = "stub"

    def materialize(
        self, request: AgentContextMaterializationRequest
    ) -> AgentContextMaterializationResult:
        return AgentContextMaterializationResult(
            provider_id=self.provider_id,
            support_level=self.support_level,
        )
