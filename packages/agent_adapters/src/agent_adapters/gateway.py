from __future__ import annotations

from dataclasses import dataclass


WRIGHT_GATEWAY_PROTOCOL = "mcp-gateway"


def build_wright_gateway_args(repo_dir: str) -> list[str]:
    return [
        "run",
        "--project",
        repo_dir,
        "python",
        "-m",
        "tool_registry.gateway",
    ]


@dataclass(frozen=True)
class WrightGatewayProfile:
    provider_name: str
    server_name: str
    command: str
    args: list[str]
    terminal_cwd: str
    display_name: str = "Wright gateway"
    protocol: str = WRIGHT_GATEWAY_PROTOCOL
    workspace_context_filename: str | None = None
    supports_tool_list_changed: bool = True

    def mcp_server_config(self) -> dict:
        return {"command": self.command, "args": list(self.args)}

    def terminal_config(self) -> dict:
        return {"cwd": self.terminal_cwd}

