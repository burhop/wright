"""Bounded tool-free model transport over the existing installed Hermes SDK."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile

from .base import AgentInvocationContext


class HermesRoleInvocationError(ValueError):
    def __init__(self, code):
        self.code = (
            code
            if isinstance(code, str)
            and code
            in {
                "SCOPED_MODEL_TIMEOUT",
                "SCOPED_MODEL_AUTH_REQUIRED",
                "SCOPED_MODEL_RATE_LIMITED",
            }
            else "SCOPED_INVOCATION_UNAVAILABLE"
        )
        super().__init__("The confined model invocation is unavailable")


@dataclass(frozen=True)
class HermesRoleTransport:
    python: Path
    runtime_root: Path
    timeout_seconds: int = 150

    def __post_init__(self):
        if (
            type(self.timeout_seconds) is not int
            or not 1 <= self.timeout_seconds <= 150
        ):
            raise ValueError("Confined model timeout must be within 1–150 seconds")

    @classmethod
    def from_host(cls):
        """Trusted explicit settings or the official native installation only."""
        explicit_python = os.getenv("HERMES_ROLE_PYTHON", "")
        explicit_root = os.getenv("HERMES_ROLE_RUNTIME_ROOT", "")
        if bool(explicit_python) != bool(explicit_root):
            return None
        if explicit_python:
            candidate = cls(Path(explicit_python), Path(explicit_root))
        else:
            local = os.getenv("LOCALAPPDATA", "")
            if not local:
                return None
            root = Path(local) / "hermes/hermes-agent"
            candidate = cls(root / "venv/Scripts/python.exe", root)
        try:
            if (
                not candidate.python.is_file()
                or not (
                    candidate.runtime_root / "hermes_cli/runtime_provider.py"
                ).is_file()
            ):
                return None
        except OSError:
            return None
        return candidate

    async def call(self, request: dict) -> dict:
        raw = json.dumps(request, ensure_ascii=False).encode("utf-8")
        if len(raw) > 2_200_000:
            raise ValueError("Authoring invocation exceeds the fixed input bound")
        child = None
        with tempfile.TemporaryDirectory(prefix="wright-model-role-") as cwd:
            try:
                child = await asyncio.create_subprocess_exec(
                    str(self.python),
                    "-I",
                    str(Path(__file__).with_name("hermes_role_worker.py")),
                    str(self.runtime_root.resolve()),
                    cwd=cwd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                async with asyncio.timeout(self.timeout_seconds):
                    child.stdin.write(raw)
                    await child.stdin.drain()
                    child.stdin.close()
                    content = await child.stdout.read(1_200_001)
                    if len(content) > 1_200_000:
                        raise ValueError(
                            "Confined model output exceeds the fixed bound"
                        )
                    await child.wait()
                result = json.loads(content)
                if (
                    child.returncode
                    or not isinstance(result, dict)
                    or result.get("ok") is not True
                ):
                    raise HermesRoleInvocationError(
                        result.get("code") if isinstance(result, dict) else None
                    )
                return result
            finally:
                if child is not None and child.returncode is None:
                    child.kill()
                    await child.wait()

    async def probe(self) -> dict:
        return (await self.call({"operation": "probe"}))["resolution"]

    async def generate(
        self, context: AgentInvocationContext, message: str, resolution: dict
    ) -> dict:
        return await self.call(
            {
                "operation": "generate",
                "expected_resolution": resolution,
                "messages": [
                    {"role": "system", "content": context.instructions},
                    {"role": "user", "content": message},
                ],
            }
        )
