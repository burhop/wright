from __future__ import annotations

import os
from inspect import isawaitable
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit

import httpx

from tool_registry.runners.base import ProgressCallback


class BrepPanelGatewayLifecycle:
    """Route one visible BREP server through Wright's panel-owning API process."""

    def __init__(
        self,
        delegate: Any,
        server_id: str,
        *,
        api_base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.delegate = delegate
        self.server_id = server_id
        self.api_base_url = (
            api_base_url or os.getenv("WRIGHT_API_BASE_URL") or "http://127.0.0.1:8000"
        ).rstrip("/")
        self.transport = transport
        parts = urlsplit(self.api_base_url)
        if parts.scheme != "http" or parts.hostname not in {
            "127.0.0.1",
            "localhost",
            "::1",
        }:
            raise ValueError("The Wright BREP gateway requires a loopback API URL")

    async def ensure_started(
        self, server_id: str, *, workspace_path: str, approval_context: Any
    ) -> None:
        if server_id != self.server_id:
            await self.delegate.ensure_started(
                server_id,
                workspace_path=workspace_path,
                approval_context=approval_context,
            )
            return
        await self._post(
            "/api/workspace/brep/panel",
            {"session_id": _session_id(approval_context)},
        )

    async def call_tool(
        self,
        server_id: str,
        tool_name: str,
        arguments: Mapping[str, Any],
        *,
        approval_context: Any,
        progress_callback: ProgressCallback | None = None,
    ) -> Mapping[str, Any]:
        if server_id != self.server_id:
            return await self.delegate.call_tool(
                server_id,
                tool_name,
                arguments,
                approval_context=approval_context,
                progress_callback=progress_callback,
            )
        await _report_progress(
            progress_callback,
            {
                "status": "running",
                "title": "Opening BREP in Wright",
                "message": "Starting the visible BREP panel in the active Wright workspace.",
            },
        )
        result = await self._post(
            "/api/workspace/brep/tool",
            {
                "session_id": _session_id(approval_context),
                "tool_name": tool_name,
                "arguments": dict(arguments),
            },
        )
        await _report_progress(
            progress_callback,
            {
                "status": "completed",
                "title": "BREP panel ready",
                "message": "The visible BREP panel is ready in Wright.",
            },
        )
        return result

    async def shutdown(self) -> None:
        await self.delegate.shutdown()

    async def _post(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self.api_base_url,
                transport=self.transport,
                timeout=180.0,
            ) as client:
                response = await client.post(path, json=dict(payload))
                response.raise_for_status()
                result = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise RuntimeError(
                "Wright's visible BREP process is unavailable"
            ) from error
        if not isinstance(result, Mapping):
            raise RuntimeError("Wright returned an invalid BREP tool result")
        return dict(result)


def _session_id(approval_context: Any) -> str:
    if isinstance(approval_context, Mapping):
        value = approval_context.get("session_id")
    else:
        value = getattr(approval_context, "session_id", None)
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError("The BREP gateway requires a bound Wright session")
    return value


async def _report_progress(
    callback: ProgressCallback | None,
    update: Mapping[str, Any],
) -> None:
    if callback is None:
        return
    callback_result = callback(update)
    if isawaitable(callback_result):
        await callback_result


__all__ = ["BrepPanelGatewayLifecycle"]
