from __future__ import annotations

import os
from dataclasses import dataclass
from collections.abc import Callable

from .context import (
    AgentContextMaterializationRequest,
    AgentContextMaterializationResult,
    SupportLevel,
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
