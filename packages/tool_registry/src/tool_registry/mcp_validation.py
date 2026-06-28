from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field

from .models import McpServer, ValidationSummary
from .mcp_catalog import is_install_blocked


@dataclass
class ValidationResult:
    server_id: str
    environment: str
    status: str
    installability_tier: str
    message: str
    missing_dependencies: list[str] = field(default_factory=list)
    diagnostics: str = ""
    follow_up_url: str | None = None

    def as_summary(self) -> ValidationSummary:
        return ValidationSummary(
            status=self.status,
            message=self.message,
            environment=self.environment,
            missing_dependencies=self.missing_dependencies,
        )

    def model_dump(self) -> dict:
        return {
            "server_id": self.server_id,
            "environment": self.environment,
            "status": self.status,
            "installability_tier": self.installability_tier,
            "message": self.message,
            "missing_dependencies": self.missing_dependencies,
            "diagnostics": self.diagnostics,
            "follow_up_url": self.follow_up_url,
        }


def current_environment() -> str:
    if os.name == "nt":
        return "windows_11_x64"
    machine = os.uname().machine if hasattr(os, "uname") else ""
    if machine in {"x86_64", "amd64"}:
        return "ubuntu-linux-x64-container"
    if machine in {"aarch64", "arm64"}:
        return "linux-arm64"
    return "unknown"


def _missing_host_dependencies(server: McpServer) -> list[str]:
    missing = []
    for dependency in server.host_software_required:
        normalized = dependency.lower().replace(" ", "")
        candidates = {
            "freecad": ["freecad", "freecadcmd"],
            "openscad": ["openscad"],
            "blender": ["blender"],
            "kicad": ["kicad", "kicad-cli"],
            "node.js": ["node"],
            "python": ["python", "python3"],
            "uv": ["uv"],
        }.get(normalized, [normalized])
        if not any(shutil.which(candidate) for candidate in candidates):
            missing.append(dependency)
    return missing


def classify_server(server: McpServer, environment: str | None = None) -> ValidationResult:
    env = environment or current_environment()
    if is_install_blocked(server):
        message = server.install_blocked_reason or (
            f"{server.name} is blocked from automated validation."
        )
        return ValidationResult(
            server_id=server.server_id,
            environment=env,
            status="blocked",
            installability_tier="blocked",
            message=message,
            diagnostics=message,
        )

    missing = _missing_host_dependencies(server)
    if missing:
        message = (
            f"{server.name} package metadata is present, but required host "
            f"software is not installed: {', '.join(missing)}."
        )
        return ValidationResult(
            server_id=server.server_id,
            environment=env,
            status="dependency_missing",
            installability_tier="might_work",
            message=message,
            missing_dependencies=missing,
            diagnostics=message,
        )

    if server.validation_result.status == "passed":
        return ValidationResult(
            server_id=server.server_id,
            environment=env,
            status="passed",
            installability_tier="tested",
            message=server.validation_result.message,
            diagnostics=server.validation_result.message,
            follow_up_url=server.follow_up_url,
        )

    return ValidationResult(
        server_id=server.server_id,
        environment=env,
        status="skipped",
        installability_tier=server.installability_tier,
        message="No safe automated probe is defined for this validation mode.",
        diagnostics="Dry-run validation classified metadata only.",
    )

