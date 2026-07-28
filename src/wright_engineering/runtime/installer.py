"""Install an exact Wright runtime extra into a versioned environment."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

from .artifacts import RuntimeArtifact
from .layout import NativeLayout
from .models import SourceChannel


class InstallerError(RuntimeError):
    pass


Runner = Callable[..., subprocess.CompletedProcess[str]]


class RuntimeInstaller:
    def __init__(
        self,
        layout: NativeLayout,
        *,
        python_executable: Path | None = None,
        runner: Runner = subprocess.run,
    ) -> None:
        self.layout = layout
        self.python_executable = python_executable or Path(sys.executable)
        self.runner = runner

    @staticmethod
    def environment_python(environment: Path) -> Path:
        if os.name == "nt":
            return environment / "Scripts" / "python.exe"
        return environment / "bin" / "python"

    def install_command(
        self, artifact: RuntimeArtifact, environment: Path
    ) -> list[str]:
        environment = self.layout.require_contained(environment, self.layout.runtimes)
        command = [
            str(self.environment_python(environment)),
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--only-binary=:all:",
            f"wright-engineering[runtime] @ {artifact.path.as_uri()}",
        ]
        if artifact.channel in {SourceChannel.LOCAL_CANDIDATE, SourceChannel.TEST}:
            command.extend(["--no-index", "--find-links", str(artifact.path.parent)])
        return command

    def install(self, artifact: RuntimeArtifact, runtime_id: str) -> Path:
        environment = self.layout.runtime_path(runtime_id)
        if environment.exists():
            raise InstallerError("runtime_environment_exists")
        environment.parent.mkdir(parents=True, exist_ok=True)
        self._run(
            [str(self.python_executable), "-m", "venv", "--copies", str(environment)],
            code="runtime_environment_create_failed",
        )
        self._run(
            self.install_command(artifact, environment),
            code="runtime_install_failed",
        )
        self._run(
            [
                str(self.environment_python(environment)),
                "-c",
                "import wright_engineering.runtime.server",
            ],
            code="runtime_import_verification_failed",
        )
        return environment

    def _run(self, command: Sequence[str], *, code: str) -> None:
        completed = self.runner(
            list(command),
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        if completed.returncode != 0:
            output = (completed.stderr or completed.stdout or "")[-1000:]
            raise InstallerError(f"{code}: {output}")
