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

    def create_plan(
        self,
        *,
        operation_kind: str,
        model_id: str,
        variant_id: str,
        principal_id: str,
    ) -> Mapping[str, Any]: ...

    def create_import_plan(
        self, *, archive: bytes, principal_id: str
    ) -> Mapping[str, Any]: ...

    def get_plan(self, plan_id: str, *, principal_id: str) -> Mapping[str, Any]: ...

    def confirm_plan(
        self,
        plan_id: str,
        *,
        principal_id: str,
        plan_digest: str,
        trace_id: str,
    ) -> Mapping[str, Any]: ...

    def get_operation(
        self, operation_id: str, *, principal_id: str
    ) -> Mapping[str, Any]: ...

    def cancel_operation(
        self, operation_id: str, *, principal_id: str
    ) -> Mapping[str, Any]: ...

    def operation_events(
        self, operation_id: str, *, principal_id: str, after: int
    ) -> tuple[Mapping[str, Any], ...]: ...


__all__ = ["EngineeringModelApplicationPort", "EngineeringModelPortError"]
