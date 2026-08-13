"""Provider-neutral application port for the Engineering Models control plane."""

from __future__ import annotations

from typing import Any, Mapping, Protocol


class EngineeringModelPortError(ValueError):
    def __init__(self, category: str, message: str, recovery: str) -> None:
        super().__init__(message)
        self.category = category
        self.recovery = recovery


class EngineeringModelApplicationPort(Protocol):
    def list_catalog(
        self,
        *,
        search: str | None = None,
        task: str | None = None,
        source_kind: str | None = None,
        readiness: tuple[str, ...] = (),
        platform: str | None = None,
        architecture: str | None = None,
        accelerator: str | None = None,
        evidence_state: str | None = None,
        maximum_bytes: int | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> Mapping[str, Any]: ...

    def get_catalog_model(self, model_id: str) -> Mapping[str, Any]: ...


__all__ = ["EngineeringModelApplicationPort", "EngineeringModelPortError"]
