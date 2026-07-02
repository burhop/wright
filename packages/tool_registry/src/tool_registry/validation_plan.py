from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from .mcp_validation import classify_server, current_environment
from .models import EnvVarDefinition, McpServer


class ValidationProbeStep(BaseModel):
    name: str
    method: str
    required: bool = True
    arguments: dict[str, Any] = Field(default_factory=dict)


class ValidationPlan(BaseModel):
    server_id: str
    environment: str
    preflight: dict[str, Any]
    install_steps: list[str] = Field(default_factory=list)
    protocol_probes: list[ValidationProbeStep] = Field(default_factory=list)
    safe_backend_probe: ValidationProbeStep | None = None
    gateway_probe: list[ValidationProbeStep] = Field(default_factory=list)
    requires_docker: bool = True
    requires_network: bool = False
    requires_credentials: bool = False
    execution_mode: Literal["clean-container", "local-mock"] = "clean-container"


def _command_install_step(server: McpServer) -> list[str]:
    if not server.command:
        return []
    if isinstance(server.command, list):
        return [" ".join(server.command)]
    return [server.command]


def _requires_credentials(server: McpServer) -> bool:
    if server.credentials_required:
        return True
    if server.env_vars and isinstance(server.env_vars, list):
        return any(
            isinstance(var, EnvVarDefinition) and var.required
            for var in server.env_vars
        )
    return False


def _requires_network(server: McpServer) -> bool:
    if server.type in {"sse", "webmcp"}:
        return True
    command_text = ""
    if isinstance(server.command, str):
        command_text = server.command
    elif isinstance(server.command, list):
        command_text = " ".join(str(part) for part in server.command)
    lower_command = command_text.lower()
    if lower_command.startswith(("http://", "https://")):
        return True
    network_markers = (
        "git+",
        "http://",
        "https://",
        "uvx ",
        "uv run --with",
        "npx ",
        "npm ",
        "pip install",
    )
    if any(marker in lower_command for marker in network_markers):
        return True
    return False


def build_validation_plan(
    server: McpServer,
    *,
    environment: str | None = None,
    requires_docker: bool = True,
    safe_tool_name: str | None = None,
    safe_tool_arguments: dict[str, Any] | None = None,
) -> ValidationPlan:
    env = environment or current_environment()
    preflight = classify_server(server, environment=env)
    safe_probe = None
    if safe_tool_name:
        safe_probe = ValidationProbeStep(
            name="safe_backend_probe",
            method="tools/call",
            required=False,
            arguments={
                "name": safe_tool_name,
                "arguments": safe_tool_arguments or {},
            },
        )

    return ValidationPlan(
        server_id=server.server_id,
        environment=env,
        preflight=preflight.model_dump(),
        install_steps=_command_install_step(server),
        protocol_probes=[
            ValidationProbeStep(name="initialize", method="initialize"),
            ValidationProbeStep(
                name="notifications/initialized",
                method="notifications/initialized",
            ),
            ValidationProbeStep(name="tools/list", method="tools/list"),
        ],
        safe_backend_probe=safe_probe,
        gateway_probe=[
            ValidationProbeStep(
                name="wright_gateway.tools/list",
                method="tools/list",
            )
        ]
        + (
            [
                ValidationProbeStep(
                    name="wright_gateway.safe_backend_probe",
                    method="tools/call",
                    required=False,
                    arguments=safe_probe.arguments,
                )
            ]
            if safe_probe
            else []
        ),
        requires_docker=requires_docker,
        requires_network=_requires_network(server),
        requires_credentials=_requires_credentials(server),
        execution_mode="clean-container" if requires_docker else "local-mock",
    )
