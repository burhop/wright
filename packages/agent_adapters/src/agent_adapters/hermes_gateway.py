from __future__ import annotations

import os

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

