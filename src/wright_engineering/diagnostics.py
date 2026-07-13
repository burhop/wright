from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import sys


@dataclass(frozen=True, slots=True)
class Diagnostic:
    name: str
    ok: bool
    detail: str


def run_diagnostics() -> list[Diagnostic]:
    return [
        Diagnostic("python", sys.version_info >= (3, 11), sys.version.split()[0]),
        Diagnostic(
            "docker",
            shutil.which("docker") is not None,
            shutil.which("docker") or "not found",
        ),
        Diagnostic("workspace", Path.cwd().exists(), str(Path.cwd())),
        Diagnostic(
            "api-token",
            bool(os.environ.get("WRIGHT_API_TOKEN")),
            "set" if os.environ.get("WRIGHT_API_TOKEN") else "not set",
        ),
    ]
