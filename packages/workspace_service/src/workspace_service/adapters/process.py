from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

from ..models import ProcessResult


class LocalProcessRunner:
    def run(
        self,
        argv: Sequence[str],
        *,
        cwd: Path,
        timeout_seconds: float,
        env: Mapping[str, str] | None = None,
        check: bool = False,
    ) -> ProcessResult:
        completed = subprocess.run(
            list(argv),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=dict(env) if env is not None else None,
            check=check,
        )
        return ProcessResult(completed.returncode, completed.stdout, completed.stderr)
