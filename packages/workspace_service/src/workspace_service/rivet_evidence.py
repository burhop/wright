"""Bounded redaction and artifact projection for Rivet run evidence."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import unquote

from core.rivet_mcp import ArtifactReference, canonical_digest
from tool_registry.gateway_models import GatewayToolResult


_SECRET = re.compile(
    r"(?i)(token|secret|password|passwd|api[_-]?key|authorization|credential)"
)
_URL_SECRET = re.compile(r"(?i)([?&](?:token|access_token|api_key|key)=)[^&\s]+")


class RivetEvidenceError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def redact_value(value: Any, *, maximum_text: int = 4096) -> tuple[Any, int]:
    redactions = 0

    def visit(item: Any) -> Any:
        nonlocal redactions
        if isinstance(item, Mapping):
            result: dict[str, Any] = {}
            for key, child in item.items():
                name = str(key)
                if _SECRET.search(name):
                    result[name] = "[redacted]"
                    redactions += 1
                else:
                    result[name] = visit(child)
            return result
        if isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            return [visit(child) for child in item]
        if isinstance(item, str):
            sanitized, count = _URL_SECRET.subn(r"\1[redacted]", item)
            redactions += count
            if len(sanitized) > maximum_text:
                return sanitized[:maximum_text] + "…[truncated]"
            return sanitized
        return item

    return visit(value), redactions


def safe_argument_summary(
    arguments: Mapping[str, Any], *, maximum_bytes: int = 4096
) -> tuple[dict[str, Any], int, bool]:
    safe, redactions = redact_value(arguments)
    encoded = json.dumps(safe, sort_keys=True, default=str).encode("utf-8")
    if len(encoded) <= maximum_bytes:
        return dict(safe), redactions, False
    return (
        {
            "summary": "Arguments exceeded the evidence limit",
            "argument_digest": canonical_digest(arguments),
            "bytes": len(encoded),
        },
        redactions,
        True,
    )


def authorized_artifacts(
    result: GatewayToolResult, *, workspace_id: str
) -> tuple[ArtifactReference, ...]:
    prefix = f"wright://artifact/{workspace_id}/"
    artifacts: list[ArtifactReference] = []
    for item in result.content:
        if item.get("type") != "resource_link":
            continue
        uri = str(item.get("uri") or "")
        if not uri.startswith(prefix):
            raise RivetEvidenceError(
                "RIVET_MCP_ARTIFACT_DENIED",
                "Child artifact reference is not authorized for this workspace",
            )
        locator = unquote(uri.removeprefix(prefix))
        if (
            not locator
            or "\\" in locator
            or "\x00" in locator
            or any(part in {"", ".", ".."} for part in locator.split("/"))
        ):
            raise RivetEvidenceError(
                "RIVET_MCP_ARTIFACT_DENIED",
                "Child artifact reference is not authorized for this workspace",
            )
        digest = item.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise RivetEvidenceError(
                "RIVET_MCP_ARTIFACT_DENIED",
                "Child artifact reference has no verified digest",
            )
        artifacts.append(
            ArtifactReference(
                artifact_id=locator,
                media_type=str(item.get("mimeType") or "application/octet-stream"),
                sha256=digest,
                bytes=max(0, int(item.get("bytes") or 0)),
                label=str(item.get("name") or item.get("title") or locator)[:255],
            )
        )
    return tuple(artifacts)


def sanitize_gateway_result(
    result: GatewayToolResult, *, workspace_id: str
) -> tuple[GatewayToolResult, tuple[ArtifactReference, ...], int]:
    artifacts = authorized_artifacts(result, workspace_id=workspace_id)
    content, content_redactions = redact_value(result.content)
    structured, structured_redactions = redact_value(result.structured_content)
    meta, meta_redactions = redact_value(result.meta)
    return (
        GatewayToolResult(
            content=tuple(content),
            structured_content=(
                dict(structured) if isinstance(structured, Mapping) else None
            ),
            meta=dict(meta) if isinstance(meta, Mapping) else {},
            is_error=result.is_error,
            error_code=result.error_code,
        ),
        artifacts,
        content_redactions + structured_redactions + meta_redactions,
    )


__all__ = [
    "RivetEvidenceError",
    "authorized_artifacts",
    "redact_value",
    "safe_argument_summary",
    "sanitize_gateway_result",
]
