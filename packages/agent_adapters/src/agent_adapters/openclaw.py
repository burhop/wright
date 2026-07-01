from __future__ import annotations

from .gateway import WrightGatewayProfile, build_wright_gateway_args


def openclaw_wright_gateway_profile(repo_dir: str) -> WrightGatewayProfile:
    return WrightGatewayProfile(
        provider_name="openclaw",
        server_name="wright-gateway",
        command="uv",
        args=build_wright_gateway_args(repo_dir),
        terminal_cwd=repo_dir,
    )

