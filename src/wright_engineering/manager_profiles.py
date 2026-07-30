"""Configuration profiles for agent managers that consume Wright directly."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from .runtime.layout import NativeLayout


ManagerId = Literal["hermes", "codex"]
Transport = Literal["stdio", "streamable-http"]


@dataclass(frozen=True, slots=True)
class ManagerProfile:
    manager_id: ManagerId
    adapter_protocol: str
    install_interface: str
    transport: Transport
    wright_home: Path
    command: str | None = None
    args: tuple[str, ...] = ()
    url: str | None = None
    prerequisites: tuple[str, ...] = ()

    def as_mcp_config(self) -> dict[str, Any]:
        if self.transport == "stdio":
            if not self.command:
                raise ValueError("stdio_profile_requires_command")
            return {
                "command": self.command,
                "args": list(self.args),
                "env": {
                    "WRIGHT_HOME": str(self.wright_home),
                    "WRIGHT_MANAGER_ID": self.manager_id,
                    "WRIGHT_MANAGER_PROTOCOL": self.adapter_protocol,
                },
            }
        if not self.url:
            raise ValueError("http_profile_requires_url")
        if self.manager_id == "codex":
            return {
                "url": self.url,
                "bearer_token_env_var": "WRIGHT_API_TOKEN",
            }
        return {"url": self.url, "transport": "streamable-http"}


def build_manager_profile(
    manager_id: ManagerId,
    *,
    workspace: str | os.PathLike[str] | None = None,
    session_id: str | None = None,
    workspace_id: str | None = None,
    transport: Transport = "stdio",
    api_url: str = "http://127.0.0.1:8000",
    wright_home: str | os.PathLike[str] | None = None,
    wright_command: str = "wright",
) -> ManagerProfile:
    if manager_id not in {"hermes", "codex"}:
        raise ValueError("manager_unsupported")
    layout = NativeLayout.discover(wright_home)
    protocols = {
        "hermes": ("hermes-git-plugin-v1", "git", ("git",)),
        "codex": ("mcp-v1", "mcp-config", ()),
    }
    protocol, install_interface, prerequisites = protocols[manager_id]
    if transport == "streamable-http":
        return ManagerProfile(
            manager_id=manager_id,
            adapter_protocol=protocol,
            install_interface=install_interface,
            transport=transport,
            wright_home=layout.wright_home,
            url=f"{api_url.rstrip('/')}/mcp",
            prerequisites=prerequisites,
        )
    if workspace is None:
        raise ValueError("stdio_profile_requires_workspace")
    resolved_session_id = (session_id or "").strip()
    resolved_workspace_id = (workspace_id or "").strip()
    if not resolved_session_id:
        raise ValueError("stdio_profile_requires_session_id")
    if not resolved_workspace_id:
        raise ValueError("stdio_profile_requires_workspace_id")
    workspace_path = Path(workspace).expanduser().resolve(strict=False)
    return ManagerProfile(
        manager_id=manager_id,
        adapter_protocol=protocol,
        install_interface=install_interface,
        transport=transport,
        wright_home=layout.wright_home,
        command=wright_command,
        args=(
            "mcp",
            "serve",
            "--stdio",
            "--workspace",
            str(workspace_path),
            "--api-url",
            api_url,
            "--session-id",
            resolved_session_id,
            "--workspace-id",
            resolved_workspace_id,
        ),
        prerequisites=prerequisites,
    )


def codex_mcp_config(**kwargs: Any) -> dict[str, Any]:
    """Return a Codex MCP server configuration without importing Codex."""
    return build_manager_profile("codex", **kwargs).as_mcp_config()
