from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .capability_models import InstallPlan
from .canonical_catalog import LEGACY_SERVER_IDS
from .db import delete_server, get_server, insert_server, update_server
from .models import McpServer


class RegistryOnboardingError(RuntimeError):
    pass


class RegistryOnboardingAdapter:
    """Apply reviewed MCP plans through Wright's existing registry.

    Package launchers such as uvx and npx acquire their pinned package when the
    subsequent protocol validation starts the registered server. This adapter
    owns only the reversible registry state required before that validation.
    """

    version = "1"

    def __init__(self, database_path: str | Path, *, kind: str) -> None:
        if kind not in {
            "local_package",
            "local_command",
            "remote_endpoint",
            "host_bridge",
        }:
            raise ValueError(f"Unsupported registry onboarding backend: {kind}")
        self.database_path = str(database_path)
        self.kind = kind
        self._created: set[str] = set()
        self._prior_installed: dict[str, bool] = {}

    @staticmethod
    def _server_id(plan: InstallPlan) -> str:
        return LEGACY_SERVER_IDS.get(plan.capability_id, plan.capability_id)

    @staticmethod
    def _command(plan: InstallPlan) -> str | list[str] | None:
        endpoint = plan.source.get("endpoint")
        if endpoint:
            return str(endpoint)
        command = plan.source.get("command")
        if not command:
            return None
        if isinstance(command, list):
            return [str(item) for item in command]
        arguments = [str(item) for item in plan.source.get("arguments", [])]
        return [str(command), *arguments]

    def prepare(self, plan: InstallPlan) -> dict[str, Any]:
        if plan.backend_kind != self.kind:
            raise RegistryOnboardingError("The approved backend kind changed")
        server_id = self._server_id(plan)
        existing = get_server(self.database_path, server_id)
        if existing is not None:
            self._prior_installed[server_id] = existing.is_installed
        elif not plan.import_draft_id:
            raise RegistryOnboardingError(
                "The reviewed catalog registration is no longer available"
            )
        return {
            "step": "prepare",
            "status": "succeeded",
            "server_id": server_id,
            "changed": False,
        }

    def apply(self, plan: InstallPlan) -> dict[str, Any]:
        server_id = self._server_id(plan)
        server = get_server(self.database_path, server_id)
        if server is None:
            command = self._command(plan)
            transport = str(plan.source.get("transport") or "stdio")
            if command is None:
                raise RegistryOnboardingError(
                    "The approved registration has no executable or endpoint"
                )
            timestamp = int(datetime.now(UTC).timestamp())
            server = McpServer(
                server_id=server_id,
                name=str(plan.source.get("name") or plan.capability_id),
                type="stdio" if transport == "stdio" else "sse",
                transport_variant=transport,
                command=command,
                is_active=False,
                is_installed=True,
                status="inactive",
                category="utilities",
                created_at=timestamp,
                updated_at=timestamp,
                description="User-reviewed MCP configuration imported through Wright.",
                source_url=(
                    str(plan.source.get("endpoint"))
                    if plan.source.get("endpoint")
                    else None
                ),
                verification_state="user_reported_url_needed",
                installability_tier="might_work",
                risk_level="medium" if self.kind == "remote_endpoint" else "low",
                deployment_mode="user-reviewed-import",
                credentials_required=list(plan.requirements.credentials),
                default_enabled=False,
                approval_gates=list(plan.approval_gates),
            )
            insert_server(self.database_path, server)
            self._created.add(server_id)
        else:
            self._prior_installed.setdefault(server_id, server.is_installed)
            update_server(
                self.database_path,
                server_id,
                {
                    "is_installed": True,
                    "is_active": False,
                    "status": "inactive",
                    "error_message": None,
                    "updated_at": int(datetime.now(UTC).timestamp()),
                },
            )
        return {
            "step": "apply",
            "status": "succeeded",
            "server_id": server_id,
            "installed_or_connected": True,
        }

    def validate(self, plan: InstallPlan) -> dict[str, Any]:
        server_id = self._server_id(plan)
        server = get_server(self.database_path, server_id)
        if server is None or not server.is_installed:
            raise RegistryOnboardingError("The reviewed registration was not applied")
        return {
            "step": "validate",
            "status": "succeeded",
            "server_id": server_id,
            "limitation": (
                "Registry state only; MCP protocol validation is the next required step."
            ),
        }

    def rollback(self, plan: InstallPlan) -> dict[str, Any]:
        server_id = self._server_id(plan)
        if server_id in self._created:
            delete_server(self.database_path, server_id)
        elif server_id in self._prior_installed:
            update_server(
                self.database_path,
                server_id,
                {
                    "is_installed": self._prior_installed[server_id],
                    "is_active": False,
                    "status": "inactive",
                    "updated_at": int(datetime.now(UTC).timestamp()),
                },
            )
        return {
            "step": "rollback",
            "status": "succeeded",
            "server_id": server_id,
        }

    def remove(self, plan: InstallPlan) -> dict[str, Any]:
        return self.rollback(plan)
