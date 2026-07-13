from __future__ import annotations

import json
from urllib.parse import unquote
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .canonical_catalog import load_catalog_document
from .gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewayResource,
    GatewaySessionContext,
)


@dataclass(frozen=True, slots=True)
class ResourceContent:
    content: str | bytes
    mime_type: str


ArtifactLister = Callable[[GatewaySessionContext], Sequence[GatewayResource]]
ArtifactReader = Callable[[GatewaySessionContext, str], ResourceContent]


class GatewayResourceProvider:
    CATALOG_URI = "wright://catalog/engineering"

    def __init__(
        self,
        *,
        list_artifacts: ArtifactLister | None = None,
        read_artifact: ArtifactReader | None = None,
    ) -> None:
        self._list_artifacts = list_artifacts or (lambda session: ())
        self._read_artifact = read_artifact

    def list(self, session: GatewaySessionContext) -> tuple[GatewayResource, ...]:
        base = (
            GatewayResource(
                self.CATALOG_URI,
                "Wright engineering catalog",
                "Validated engineering MCP catalog and provenance",
                "application/json",
                {"source": "canonical-catalog", "format_version": 1},
            ),
            GatewayResource(
                f"wright://workspace/{session.workspace_id}",
                "Bound Wright workspace",
                "Immutable workspace identity for this MCP session",
                "application/json",
                {
                    "source": "workspace-binding",
                    "workspace_id": session.workspace_id,
                },
            ),
        )
        return (*base, *self._list_artifacts(session))

    def read(self, session: GatewaySessionContext, uri: str) -> ResourceContent:
        if uri == self.CATALOG_URI:
            return ResourceContent(
                json.dumps(load_catalog_document(), sort_keys=True),
                "application/json",
            )
        if uri == f"wright://workspace/{session.workspace_id}":
            return ResourceContent(
                json.dumps(
                    {
                        "workspace_id": session.workspace_id,
                        "session_id": session.session_id,
                    },
                    sort_keys=True,
                ),
                "application/json",
            )
        if uri.startswith("wright://workspace/"):
            raise GatewayError(
                GatewayErrorCode.NOT_FOUND,
                "Resource is not available in this workspace",
            )
        if uri.startswith(f"wright://artifact/{session.workspace_id}/"):
            locator = unquote(
                uri.removeprefix(f"wright://artifact/{session.workspace_id}/")
            )
            if (
                not locator
                or "\\" in locator
                or "\x00" in locator
                or any(part in {"", ".", ".."} for part in locator.split("/"))
            ):
                raise GatewayError(
                    GatewayErrorCode.NOT_FOUND,
                    "Artifact resource is not available in this workspace",
                )
            if self._read_artifact is None:
                raise GatewayError(
                    GatewayErrorCode.NOT_FOUND, "Artifact resource not found"
                )
            return self._read_artifact(session, uri)
        raise GatewayError(GatewayErrorCode.NOT_FOUND, f"Unknown resource: {uri}")
