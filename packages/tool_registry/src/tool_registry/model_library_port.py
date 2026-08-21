"""Provider-neutral application port for the Engineering Models control plane."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Mapping, Protocol

from .runners.base import ProgressCallback


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

    def list_installations(
        self, *, model_id: str | None = None, principal_id: str
    ) -> Mapping[str, Any]: ...

    def create_plan(
        self,
        *,
        operation_kind: str,
        model_id: str | None = None,
        variant_id: str | None = None,
        installation_id: str | None = None,
        target_installation_id: str | None = None,
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

    async def run_standard_test(
        self, installation_id: str, *, principal_id: str, trace_id: str
    ) -> Mapping[str, Any]: ...

    def get_standard_test_evidence(
        self, installation_id: str, *, principal_id: str
    ) -> Mapping[str, Any]: ...

    def create_workspace_binding(
        self,
        installation_id: str,
        *,
        task_id: str,
        workspace_id: str,
        principal_id: str,
    ) -> Mapping[str, Any]: ...

    def set_workspace_binding_state(
        self,
        binding_id: str,
        *,
        state: str,
        workspace_id: str,
        principal_id: str,
    ) -> Mapping[str, Any]: ...

    def get_installation_maintenance(
        self, installation_id: str, *, principal_id: str
    ) -> Mapping[str, Any]: ...

    def compare_installation_update(
        self,
        installation_id: str,
        *,
        model_id: str,
        variant_id: str,
        principal_id: str,
    ) -> Mapping[str, Any]: ...

    def maintain_installation(
        self,
        installation_id: str,
        *,
        action: str,
        target_installation_id: str | None,
        principal_id: str,
        trace_id: str,
    ) -> Mapping[str, Any]: ...

    def set_model_reference_state(
        self, reference_id: str, *, state: str, principal_id: str
    ) -> Mapping[str, Any]: ...

    def create_offline_export(
        self, installation_id: str, *, principal_id: str, trace_id: str
    ) -> Mapping[str, Any]: ...

    def read_offline_export(self, artifact_id: str, *, principal_id: str) -> bytes: ...

    def declared_model_tool_names(self) -> frozenset[str]: ...

    def discover_model_capabilities(
        self, *, principal_id: str, workspace_id: str, session_id: str
    ) -> Sequence[Mapping[str, Any]]: ...

    async def invoke_model_capability(
        self,
        *,
        principal_id: str,
        workspace_id: str,
        session_id: str,
        request_id: str,
        trace_id: str,
        tool_name: str,
        binding_digest: str,
        arguments: Mapping[str, Any],
        approval_context: Any,
        progress_callback: ProgressCallback | None,
    ) -> Mapping[str, Any]: ...

    async def cancel_model_request(
        self, *, session_id: str, request_id: str
    ) -> None: ...

    async def close_model_session(self, *, session_id: str) -> None: ...

    async def shutdown_model_runtime(self) -> None: ...


__all__ = ["EngineeringModelApplicationPort", "EngineeringModelPortError"]
