"""Workspace-scoped engineering-model projection for Wright's gateway."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from core.rivet_mcp import ProviderEvidence
from core.tools import ToolContext
from tool_registry.gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewaySessionContext,
    GatewayTool,
)
from tool_registry.model_library_port import EngineeringModelApplicationPort

from .model_tool import EngineeringModelTool

_DIGEST = re.compile(r"^[a-f0-9]{64}$")
_ACTUATION = re.compile(
    r"(?i)(?:actuat|start[_-]?(?:spindle|machine|motor)|jog|move[_-]?axis|execute[_-]?(?:gcode|toolpath))"
)


def engineering_model_tool_name(model_id: str, task_id: str) -> str:
    def normalize(value: str) -> str:
        result = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
        return result[:96]

    model = normalize(model_id)
    task = normalize(task_id)
    if not model or not task:
        raise ValueError("Engineering model tool identity is invalid")
    return f"wright_model__{model}__{task}"


def _valid_capability(value: Mapping[str, Any], session: GatewaySessionContext) -> bool:
    try:
        expected_name = engineering_model_tool_name(
            str(value["model_id"]), str(value["task_id"])
        )
        identities = (
            value["binding_id"],
            value["installation_id"],
            value["variant_id"],
            value["adapter_id"],
            value["adapter_version"],
            value["runtime_version"],
            value["evidence_id"],
        )
        description = value["description"]
        schemas = (value["input_schema"], value["output_schema"])
        digests = (
            value["binding_digest"],
            value["installation_digest"],
            value["material_digest"],
            value["policy_snapshot_digest"],
            value["manifest_digest"],
            value["artifact_set_digest"],
            value["test_material_digest"],
            value["input_schema_digest"],
            value["output_schema_digest"],
            value["resource_digest"],
        )
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        expected_name
        and not _ACTUATION.search(str(value["task_id"]))
        and isinstance(description, str)
        and 1 <= len(description) <= 1000
        and all(
            isinstance(identity, str) and 1 <= len(identity) <= 128
            for identity in identities
        )
        and isinstance(value.get("package_revision"), int)
        and value["package_revision"] >= 1
        and value.get("workspace_id") == session.workspace_id
        and value.get("binding_state") == "enabled"
        and value.get("installation_state") == "ready"
        and value.get("evidence_state") == "passed"
        and value.get("policy_current") is True
        and all(
            isinstance(schema, Mapping) and schema.get("type") == "object"
            for schema in schemas
        )
        and all(
            isinstance(digest, str) and _DIGEST.fullmatch(digest) for digest in digests
        )
    )


class EngineeringModelGatewayProvider:
    provider_id = "engineering-models"

    def __init__(self, application: EngineeringModelApplicationPort) -> None:
        self.application = application
        self.declared_tool_names = frozenset(application.declared_model_tool_names())
        if not self.declared_tool_names:
            raise ValueError("Engineering model provider declares no capabilities")

    def _capabilities(
        self, session: GatewaySessionContext
    ) -> tuple[Mapping[str, Any], ...]:
        values = self.application.discover_model_capabilities(
            principal_id=session.principal_id,
            workspace_id=session.workspace_id,
            session_id=session.session_id,
        )
        return tuple(value for value in values if _valid_capability(value, session))

    @staticmethod
    def _projection(value: Mapping[str, Any]) -> GatewayTool:
        name = engineering_model_tool_name(
            str(value["model_id"]), str(value["task_id"])
        )

        async def unavailable(_arguments, _context):
            raise RuntimeError(
                "Engineering model tool requires a provider call context"
            )

        base = EngineeringModelTool(
            name=name,
            description=str(value["description"])[:1000],
            input_schema=dict(value["input_schema"]),
            output_schema=dict(value["output_schema"]),
            executor=unavailable,
        )
        contract = base.contract()
        provider = ProviderEvidence(
            provider_kind="engineering_model",
            provider_id=str(value["model_id"]),
            capability_id=str(value["task_id"]),
            resource_class="small",
            evidence={
                "model_id": value["model_id"],
                "package_revision": value["package_revision"],
                "manifest_digest": value["manifest_digest"],
                "variant_id": value["variant_id"],
                "artifact_set_digest": value["artifact_set_digest"],
                "installation_id": value["installation_id"],
                "installation_digest": value["installation_digest"],
                "adapter_id": value["adapter_id"],
                "adapter_version": value["adapter_version"],
                "runtime_version": value["runtime_version"],
                "test_evidence_id": value["evidence_id"],
                "test_material_digest": value["test_material_digest"],
                "workspace_binding_digest": value["binding_digest"],
                "task_id": value["task_id"],
                "input_schema_digest": value["input_schema_digest"],
                "output_schema_digest": value["output_schema_digest"],
                "threshold": value.get("threshold"),
                "resource_digest": value["resource_digest"],
            },
        )
        return GatewayTool(
            name=name,
            server_id="wright-models",
            tool_name=str(value["task_id"]),
            title=str(value.get("title") or value["model_id"])[:120],
            description=contract["description"],
            input_schema=contract["input_schema"],
            output_schema=contract["output_schema"],
            annotations={
                "readOnlyHint": True,
                "idempotentHint": True,
                "destructiveHint": False,
                "openWorldHint": False,
                "model": {
                    "model_id": value["model_id"],
                    "task_id": value["task_id"],
                    "installation_id": value["installation_id"],
                    "adapter_id": value["adapter_id"],
                    "adapter_version": value["adapter_version"],
                    "evidence_id": value["evidence_id"],
                },
            },
            provenance={
                "server_revision": value["installation_digest"],
                "capability_digest": value["binding_digest"],
                "validation_evidence_id": value["evidence_id"],
                "binding_digest": value["binding_digest"],
                "installation_digest": value["installation_digest"],
                "material_evidence_digest": value["material_digest"],
                "policy_snapshot_digest": value["policy_snapshot_digest"],
                "provider": provider.canonical(),
                "provider_evidence_digest": provider.provider_evidence_digest,
            },
        )

    def tools(self, session: GatewaySessionContext) -> tuple[GatewayTool, ...]:
        tools = tuple(self._projection(value) for value in self._capabilities(session))
        names = [tool.name for tool in tools]
        if len(names) != len(set(names)):
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING,
                "Engineering model binding tool identity is duplicated",
            )
        return tools

    async def call(
        self,
        session: GatewaySessionContext,
        tool: GatewayTool,
        arguments: Mapping[str, Any],
        *,
        request_id: str,
        approval_context: Any,
        progress_callback,
    ) -> Mapping[str, Any]:
        current = next(
            (
                value
                for value in self._capabilities(session)
                if engineering_model_tool_name(
                    str(value["model_id"]), str(value["task_id"])
                )
                == tool.name
            ),
            None,
        )
        if current is None or any(
            tool.provenance.get(key) != current[value_key]
            for key, value_key in (
                ("binding_digest", "binding_digest"),
                ("installation_digest", "installation_digest"),
                ("material_evidence_digest", "material_digest"),
                ("policy_snapshot_digest", "policy_snapshot_digest"),
            )
        ):
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING,
                "Engineering model binding changed; review the workflow again",
            )

        async def invoke(bound_arguments, context):
            return await self.application.invoke_model_capability(
                principal_id=context.principal_id,
                workspace_id=context.workspace_id,
                session_id=session.session_id,
                request_id=context.request_id,
                trace_id=context.trace_id,
                tool_name=tool.name,
                binding_digest=str(current["binding_digest"]),
                arguments=dict(bound_arguments),
                approval_context=approval_context,
                progress_callback=progress_callback,
            )

        base = EngineeringModelTool(
            name=tool.name,
            description=tool.description,
            input_schema=tool.input_schema,
            output_schema=tool.output_schema or {"type": "object"},
            executor=invoke,
        )
        return await base.execute(
            arguments,
            context=ToolContext(
                principal_id=session.principal_id,
                workspace_id=session.workspace_id,
                trace_id=request_id,
                request_id=request_id,
            ),
        )

    async def cancel(self, session: GatewaySessionContext, request_id: str) -> None:
        await self.application.cancel_model_request(
            session_id=session.session_id, request_id=request_id
        )

    async def close_session(self, session: GatewaySessionContext) -> None:
        await self.application.close_model_session(session_id=session.session_id)

    async def shutdown(self) -> None:
        await self.application.shutdown_model_runtime()


__all__ = ["EngineeringModelGatewayProvider", "engineering_model_tool_name"]
