"""In-process gateway capability for approved workspace text documents."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from tool_registry.gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewaySessionContext,
    GatewayTool,
)

from .workspace_document_artifacts import (
    WORKSPACE_DOCUMENT_PROVIDER_ID,
    WORKSPACE_DOCUMENT_TOOL_NAME,
    WORKSPACE_WRITE_APPROVAL,
    WorkspaceDocumentArtifactError,
    WorkspaceDocumentArtifactService,
    document_producer_declaration,
    document_producer_declaration_digest,
)


class WorkspaceDocumentGatewayProvider:
    provider_id = WORKSPACE_DOCUMENT_PROVIDER_ID
    declared_tool_names = frozenset({WORKSPACE_DOCUMENT_TOOL_NAME})

    def __init__(self, artifacts: WorkspaceDocumentArtifactService) -> None:
        self.artifacts = artifacts

    @staticmethod
    def _tool() -> GatewayTool:
        declaration = document_producer_declaration()
        declaration_digest = document_producer_declaration_digest()
        return GatewayTool(
            name=WORKSPACE_DOCUMENT_TOOL_NAME,
            server_id=WORKSPACE_DOCUMENT_PROVIDER_ID,
            tool_name="write_text_document",
            title="Create workspace document",
            description=(
                "Creates one new reviewed UTF-8 text document in this Wright "
                "workspace and returns a verified artifact reference."
            ),
            input_schema={
                "type": "object",
                "additionalProperties": False,
                "required": ["relativePath", "content", "mediaType"],
                "properties": {
                    "relativePath": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 512,
                    },
                    "content": {"type": "string"},
                    "mediaType": {
                        "type": "string",
                        "enum": [
                            "application/json",
                            "application/yaml",
                            "text/csv",
                            "text/markdown",
                            "text/plain",
                        ],
                    },
                    "overwrite": {"type": "boolean", "const": False, "default": False},
                },
            },
            output_schema={
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "artifactId",
                    "relativePath",
                    "mediaType",
                    "sha256",
                    "bytes",
                ],
                "properties": {
                    "artifactId": {"type": "string"},
                    "relativePath": {"type": "string"},
                    "mediaType": {"type": "string"},
                    "sha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                    "bytes": {"type": "integer", "minimum": 0},
                },
            },
            annotations={
                "readOnlyHint": False,
                "idempotentHint": False,
                "destructiveHint": False,
                "openWorldHint": False,
            },
            required_approvals=frozenset({WORKSPACE_WRITE_APPROVAL}),
            provenance={
                "server_revision": "wright-workspace-document-v1",
                "capability_digest": declaration_digest,
                "validation_evidence_id": "wright-reviewed:workspace-document-v1",
                "artifact_producer": declaration,
                "artifact_producer_digest": declaration_digest,
            },
        )

    def tools(self, _session: GatewaySessionContext) -> tuple[GatewayTool, ...]:
        return (self._tool(),)

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
        if tool.name != WORKSPACE_DOCUMENT_TOOL_NAME:
            raise GatewayError(GatewayErrorCode.NOT_FOUND, "Document tool not found")
        approvals = (
            set(approval_context.get("workspace_approvals") or ())
            if isinstance(approval_context, Mapping)
            else set()
        )
        if WORKSPACE_WRITE_APPROVAL not in approvals:
            raise GatewayError(
                GatewayErrorCode.POLICY_DENIED,
                "Workspace write approval is required",
            )
        correlation_id = (
            str(approval_context.get("correlation_id") or request_id)
            if isinstance(approval_context, Mapping)
            else request_id
        )
        try:
            record = self.artifacts.publish(
                session=session,
                relative_path=arguments.get("relativePath"),
                content=arguments.get("content"),
                media_type=arguments.get("mediaType"),
                overwrite=arguments.get("overwrite", False),
                request_id=request_id,
                correlation_id=correlation_id,
            )
        except WorkspaceDocumentArtifactError as error:
            raise GatewayError(GatewayErrorCode.INVALID_INPUT, str(error)) from error
        uri = f"wright://artifact/{session.workspace_id}/{record.artifact_id}"
        structured = {
            "artifactId": record.artifact_id,
            "relativePath": record.relative_path,
            "mediaType": record.media_type,
            "sha256": record.sha256,
            "bytes": record.byte_count,
        }
        return {
            "content": [
                {
                    "type": "resource_link",
                    "uri": uri,
                    "name": record.relative_path.rsplit("/", 1)[-1],
                    "mimeType": record.media_type,
                    "sha256": record.sha256,
                    "bytes": record.byte_count,
                }
            ],
            "structuredContent": structured,
        }

    async def cancel(self, _session: GatewaySessionContext, _request_id: str) -> None:
        return None

    async def close_session(self, _session: GatewaySessionContext) -> None:
        return None

    async def shutdown(self) -> None:
        return None
