from __future__ import annotations

import os
from dataclasses import dataclass

from .context import (
    AgentContextMaterializationRequest,
    AgentContextMaterializationResult,
)
from .gateway import WrightGatewayProfile, build_wright_gateway_args


def hermes_config_paths() -> list[str]:
    return [
        os.path.expanduser("~/.hermes/profiles/wright/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml"),
    ]


def hermes_wright_gateway_profile(repo_dir: str) -> WrightGatewayProfile:
    return WrightGatewayProfile(
        provider_name="hermes",
        server_name="wrightgateway",
        command="uv",
        args=build_wright_gateway_args(repo_dir),
        terminal_cwd=repo_dir,
        workspace_context_filename=".hermes.md",
    )


def write_workspace_hermes_md(
    db_path: str, workspace_path: str, context_filename: str = ".hermes.md"
) -> None:
    """Materialize Hermes workspace instructions into .hermes.md."""
    from core.workspace import write_workspace_agent_context

    write_workspace_agent_context(db_path, workspace_path, context_filename)


@dataclass(frozen=True)
class HermesContextMaterializer:
    provider_id: str = "hermes"
    support_level: str = "supported"
    context_filename: str = ".hermes.md"

    def materialize(
        self, request: AgentContextMaterializationRequest
    ) -> AgentContextMaterializationResult:
        write_workspace_hermes_md(
            request.db_path,
            request.workspace_path,
            self.context_filename,
        )
        return AgentContextMaterializationResult(
            provider_id=self.provider_id,
            support_level="supported",
            files_written=(
                os.path.join(request.workspace_path, self.context_filename),
            ),
        )


def hermes_context_materializer() -> HermesContextMaterializer:
    return HermesContextMaterializer()
