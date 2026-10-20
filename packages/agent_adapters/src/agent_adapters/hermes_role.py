"""Bounded model transport with fixed operation scopes over the installed SDK."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
from pathlib import Path
import tempfile
from core.redaction import redact_mapping

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
                "SCOPED_MODEL_REASONING_UNSUPPORTED",
                "WORKFLOW_MODEL_CHANGED",
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

    async def call(
        self, request: dict, *, invocation_observer=None, timeout_seconds=None
    ) -> dict:
        raw = json.dumps(request, ensure_ascii=False).encode("utf-8")
        image_request = request.get("operation") in {"probe-image", "generate-image"}
        workflow_request = request.get("operation") == "generate-workflow"
        if timeout_seconds is not None and (
            not workflow_request
            or type(timeout_seconds) is not int
            or not 30 <= timeout_seconds <= 600
        ):
            raise ValueError("Workflow model timeout must be within 30–600 seconds")
        deadline = timeout_seconds or self.timeout_seconds
        input_limit = (
            16_800_000
            if workflow_request
            else (12_600_000 if image_request else 2_200_000)
        )
        output_limit = 17_000_000 if image_request else 1_200_000
        if len(raw) > input_limit:
            raise ValueError("Authoring invocation exceeds the fixed input bound")
        child = None
        invocations = []
        with tempfile.TemporaryDirectory(prefix="wright-model-role-") as cwd:
            # Internal argv only: model/request fields cannot select an evidence path.
            evidence_path = Path(cwd) / "sdk-invocations.json"
            try:
                child = await asyncio.create_subprocess_exec(
                    str(self.python),
                    "-I",
                    str(Path(__file__).with_name("hermes_role_worker.py")),
                    str(self.runtime_root.resolve()),
                    str(evidence_path),
                    cwd=cwd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                async with asyncio.timeout(deadline):
                    child.stdin.write(raw)
                    await child.stdin.drain()
                    child.stdin.close()
                    chunks, size = [], 0
                    while chunk := await child.stdout.read(
                        min(65536, output_limit + 1 - size)
                    ):
                        chunks.append(chunk)
                        size += len(chunk)
                        if size > output_limit:
                            raise ValueError(
                                "Confined model output exceeds the fixed bound"
                            )
                    content = b"".join(chunks)
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
                result["wright_invocations"] = invocations
                return result
            finally:
                if child is not None and child.returncode is None:
                    child.kill()
                    await child.wait()
                if evidence_path.exists():
                    if evidence_path.stat().st_size > 2_097_152:
                        raise ValueError(
                            "SDK invocation evidence exceeds its fixed bound"
                        )
                    evidence = json.loads(evidence_path.read_bytes())
                    records = evidence.get("invocations")
                    if (
                        evidence.get("schema_version") != "wright.scoped-sdk-evidence/1"
                        or not isinstance(records, list)
                        or len(records) > 8
                    ):
                        raise ValueError("Invalid SDK invocation evidence")
                    for record in records:
                        if (
                            not isinstance(record, dict)
                            or record.get("capture_scope") != "provider_sdk_request"
                        ):
                            raise ValueError("Invalid SDK invocation evidence")
                        invocation = redact_mapping(record)
                        invocations.append(invocation)
                        if invocation_observer is not None:
                            await invocation_observer(invocation)

    async def probe(self) -> dict:
        return (await self.call({"operation": "probe"}))["resolution"]

    async def generate(
        self,
        context: AgentInvocationContext,
        message: str,
        resolution: dict,
        *,
        invocation_observer=None,
    ) -> dict:
        return await self.call(
            {
                "operation": "generate",
                "expected_resolution": resolution,
                "messages": [
                    {"role": "system", "content": context.instructions},
                    {"role": "user", "content": message},
                ],
            },
            invocation_observer=invocation_observer,
        )
