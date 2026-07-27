from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Callable
from pathlib import Path

from .context import (
    AgentContextMaterializationRequest,
    AgentContextMaterializationResult,
    SupportLevel,
)
from .gateway import (
    WrightGatewayProfile,
    build_bound_wright_gateway_args,
    build_wright_gateway_args,
)


def hermes_config_paths() -> list[str]:
    """Return every config location Hermes may use on this host, active first."""
    hermes_home = Path(os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes"))
    candidates: list[Path] = []
    explicit = os.environ.get("HERMES_CONFIG_PATH")
    if explicit:
        candidates.append(Path(explicit))
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidates.append(Path(local_app_data) / "hermes" / "config.yaml")
    profile = os.environ.get("HERMES_PROFILE", "").strip()
    if profile:
        candidates.append(hermes_home / "profiles" / profile / "config.yaml")
    candidates.extend(
        [
            hermes_home / "profiles" / "wright" / "config.yaml",
            hermes_home / "config.yaml",
        ]
    )
    result: list[str] = []
    for candidate in candidates:
        path = str(candidate)
        if path not in result:
            result.append(path)
    return result


def hermes_wright_gateway_profile(
    repo_dir: str,
    *,
    session_id: str | None = None,
    workspace_id: str | None = None,
    terminal_cwd: str | None = None,
) -> WrightGatewayProfile:
    if (session_id is None) != (workspace_id is None):
        raise ValueError(
            "Hermes gateway binding requires both session and workspace IDs"
        )
    args = (
        build_bound_wright_gateway_args(repo_dir, session_id, workspace_id)
        if session_id is not None and workspace_id is not None
        else build_wright_gateway_args(repo_dir)
    )
    return WrightGatewayProfile(
        provider_name="hermes",
        server_name="wrightgateway",
        command="uv",
        args=args,
        terminal_cwd=terminal_cwd or repo_dir,
        gateway_project_dir=repo_dir,
        workspace_context_filename=".hermes.md",
    )


@dataclass(frozen=True)
class HermesContextMaterializer:
    provider_id: str = "hermes"
    support_level: SupportLevel = "supported"
    context_filename: str = ".hermes.md"
    context_writer: Callable[[str, str, str], None] | None = None

    def materialize(
        self, request: AgentContextMaterializationRequest
    ) -> AgentContextMaterializationResult:
        if self.context_writer is not None:
            self.context_writer(
                request.db_path, request.workspace_path, self.context_filename
            )
        files_written: tuple[str, ...] = ()
        context_path = os.path.join(request.workspace_path, self.context_filename)
        if self.context_writer is not None and os.path.exists(context_path):
            files_written = (context_path,)
        return AgentContextMaterializationResult(
            provider_id=self.provider_id,
            support_level="supported",
            files_written=files_written,
        )


def hermes_context_materializer(
    context_writer: Callable[[str, str, str], None] | None = None,
) -> HermesContextMaterializer:
    return HermesContextMaterializer(context_writer=context_writer)
