from __future__ import annotations

import asyncio
import json
import subprocess
import textwrap
from datetime import datetime, timezone
from typing import Any, Callable, Protocol

from .mcp_validation import ValidationResult
from .validation_evidence import ValidationEvidence, ValidationStepEvidence
from .validation_plan import ValidationPlan


class ValidationExecutionUnavailable(RuntimeError):
    pass


class ValidationExecutor(Protocol):
    async def execute(self, plan: ValidationPlan) -> ValidationEvidence: ...


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MockValidationExecutor:
    async def execute(self, plan: ValidationPlan) -> ValidationEvidence:
        started = _now()
        protocol_steps = [
            ValidationStepEvidence(name=probe.name, status="passed", output="mock")
            for probe in plan.protocol_probes
        ]
        gateway_steps = [
            ValidationStepEvidence(name=probe.name, status="passed", output="mock")
            for probe in plan.gateway_probe
        ]
        safe_step = (
            ValidationStepEvidence(
                name=plan.safe_backend_probe.name,
                status="passed",
                output="mock safe backend probe",
            )
            if plan.safe_backend_probe
            else None
        )
        steps = protocol_steps + ([safe_step] if safe_step else []) + gateway_steps
        return ValidationEvidence(
            server_id=plan.server_id,
            validation_started_at=started,
            validation_finished_at=_now(),
            environment=plan.environment,
            container_image="local-mock",
            install_steps=plan.install_steps,
            protocol_probes=protocol_steps,
            safe_backend_probe=safe_step,
            gateway_proxy_probe=gateway_steps,
            network_requirements={"requires_network": plan.requires_network},
            result="passed",
            status="passed",
            steps=steps,
            diagnostics="Mock validation executor completed. This is not clean-container evidence.",
            follow_up_required=False,
            redactions=["mock-output"],
        )


DockerRunner = Callable[..., subprocess.CompletedProcess[str]]


class DockerCleanContainerExecutor:
    IMAGE_ALIASES = {
        "ubuntu-x64": "wright-agent:latest",
        "linux-x64": "wright-agent:latest",
    }

    def __init__(
        self,
        container: str,
        *,
        runner: DockerRunner = subprocess.run,
        timeout_seconds: int = 900,
    ) -> None:
        self.container = container
        self.runner = runner
        self.timeout_seconds = timeout_seconds

    async def execute(self, plan: ValidationPlan) -> ValidationEvidence:
        started = _now()
        image = self._container_image()
        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network",
            ("bridge" if plan.requires_network else "none"),
            "--entrypoint",
            "python3",
            image,
            "-",
        ]
        script = self._probe_script(plan)
        try:
            completed = await asyncio.to_thread(
                self.runner,
                command,
                input=script,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise ValidationExecutionUnavailable(
                "Docker executable was not found; clean-container validation did not run."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            return self._evidence_from_probe_result(
                plan,
                started,
                image,
                {
                    "status": "failed",
                    "steps": [
                        {
                            "name": "docker.clean_container",
                            "status": "failed",
                            "output": exc.stdout or "",
                            "error": f"Timed out after {self.timeout_seconds} seconds.",
                        }
                    ],
                    "protocol_probes": [],
                    "gateway_proxy_probe": [],
                    "diagnostics": f"Docker validation timed out after {self.timeout_seconds} seconds.",
                },
            )

        if completed.returncode not in {0, 2}:
            return self._evidence_from_probe_result(
                plan,
                started,
                image,
                {
                    "status": "failed",
                    "steps": [
                        {
                            "name": "docker.clean_container",
                            "status": "failed",
                            "output": completed.stdout,
                            "error": completed.stderr,
                        }
                    ],
                    "protocol_probes": [],
                    "gateway_proxy_probe": [],
                    "diagnostics": "Docker clean-container command failed before MCP probes completed.",
                },
            )

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = {
                "status": "failed",
                "steps": [
                    {
                        "name": "docker.clean_container",
                        "status": "failed",
                        "output": completed.stdout,
                        "error": completed.stderr,
                    }
                ],
                "protocol_probes": [],
                "gateway_proxy_probe": [],
                "diagnostics": "Docker probe did not return JSON evidence.",
            }
        return self._evidence_from_probe_result(plan, started, image, payload)

    def _container_image(self) -> str:
        return self.IMAGE_ALIASES.get(self.container, self.container)

    def _evidence_from_probe_result(
        self,
        plan: ValidationPlan,
        started: str,
        image: str,
        payload: dict[str, Any],
    ) -> ValidationEvidence:
        protocol_steps = [
            ValidationStepEvidence.model_validate(step)
            for step in payload.get("protocol_probes", [])
        ]
        safe_step = (
            ValidationStepEvidence.model_validate(payload["safe_backend_probe"])
            if payload.get("safe_backend_probe")
            else None
        )
        gateway_steps = [
            ValidationStepEvidence.model_validate(step)
            for step in payload.get("gateway_proxy_probe", [])
        ]
        steps = [
            ValidationStepEvidence.model_validate(step)
            for step in payload.get("steps", [])
        ]
        status = str(payload.get("status") or "failed")
        if status == "passed" and plan.gateway_probe and not gateway_steps:
            status = "partial"
            diagnostics = (
                str(payload.get("diagnostics") or "")
                + " Direct clean-container protocol probes ran, but Wright gateway proxy probes were not executed."
            ).strip()
        else:
            diagnostics = str(payload.get("diagnostics") or "")
        return ValidationEvidence(
            server_id=plan.server_id,
            validation_started_at=started,
            validation_finished_at=_now(),
            environment=plan.environment,
            container_image=image,
            install_steps=plan.install_steps,
            protocol_probes=protocol_steps,
            safe_backend_probe=safe_step,
            gateway_proxy_probe=gateway_steps,
            credential_requirements=[],
            network_requirements={"requires_network": plan.requires_network},
            result=status,
            status=status,
            steps=steps
            + protocol_steps
            + ([safe_step] if safe_step else [])
            + gateway_steps,
            diagnostics=diagnostics,
            follow_up_required=status != "passed",
            redactions=["credentials", "environment", "commands", "subprocess_output"],
        )

    def _probe_script(self, plan: ValidationPlan) -> str:
        plan_json = plan.model_dump_json()
        return textwrap.dedent(
            f"""
            import json
            import os
            import selectors
            import shlex
            import subprocess
            import sys
            import time

            plan = json.loads({plan_json!r})

            def step(name, status, output="", error=None):
                item = {{"name": name, "status": status, "output": output or ""}}
                if error:
                    item["error"] = error
                return item

            steps = [
                step(
                    "docker.clean_container",
                    "passed",
                    "python=" + sys.version.split()[0] + "; cwd=" + os.getcwd(),
                )
            ]
            protocol_probes = []
            safe_backend_probe = None
            diagnostics = ""
            status = "failed"

            def read_response(proc, request_id, timeout=30):
                selector = selectors.DefaultSelector()
                selector.register(proc.stdout, selectors.EVENT_READ)
                deadline = time.time() + timeout
                while time.time() < deadline:
                    events = selector.select(max(0.1, deadline - time.time()))
                    if not events:
                        continue
                    line = proc.stdout.readline()
                    if not line:
                        break
                    try:
                        payload = json.loads(line)
                    except Exception:
                        continue
                    if payload.get("id") == request_id:
                        if "error" in payload:
                            raise RuntimeError(json.dumps(payload["error"]))
                        return payload.get("result", {{}})
                raise TimeoutError(f"Timed out waiting for response id {{request_id}}")

            command = plan.get("install_steps", [None])[0]
            if not command:
                diagnostics = "No stdio command was available for clean-container probing."
                status = "skipped"
            else:
                proc = None
                try:
                    proc = subprocess.Popen(
                        shlex.split(command),
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    init_payload = {{
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {{
                            "protocolVersion": "2024-11-05",
                            "capabilities": {{}},
                            "clientInfo": {{"name": "wright-clean-container", "version": "0.1.0"}},
                        }},
                    }}
                    proc.stdin.write(json.dumps(init_payload) + "\\n")
                    proc.stdin.flush()
                    init_result = read_response(proc, 1)
                    protocol_probes.append(step("initialize", "passed", json.dumps(init_result)[:4000]))

                    proc.stdin.write(json.dumps({{"jsonrpc": "2.0", "method": "notifications/initialized"}}) + "\\n")
                    proc.stdin.flush()
                    protocol_probes.append(step("notifications/initialized", "passed", "sent"))

                    proc.stdin.write(json.dumps({{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}}) + "\\n")
                    proc.stdin.flush()
                    tools_result = read_response(proc, 2)
                    protocol_probes.append(step("tools/list", "passed", json.dumps(tools_result)[:4000]))

                    safe_probe = plan.get("safe_backend_probe")
                    if safe_probe:
                        proc.stdin.write(json.dumps({{
                            "jsonrpc": "2.0",
                            "id": 3,
                            "method": "tools/call",
                            "params": safe_probe.get("arguments", {{}}),
                        }}) + "\\n")
                        proc.stdin.flush()
                        safe_result = read_response(proc, 3)
                        safe_backend_probe = step("safe_backend_probe", "passed", json.dumps(safe_result)[:4000])

                    status = "passed"
                    diagnostics = "Direct MCP stdio probes completed in a clean container."
                except Exception as exc:
                    stderr = ""
                    if proc and proc.stderr:
                        try:
                            stderr = proc.stderr.read(4000)
                        except Exception:
                            stderr = ""
                    failed_name = "mcp.protocol_probe"
                    if not protocol_probes:
                        failed_name = "mcp.server_start"
                    protocol_probes.append(step(failed_name, "failed", stderr, str(exc)))
                    diagnostics = str(exc)
                    status = "failed"
                finally:
                    if proc:
                        try:
                            proc.terminate()
                            proc.wait(timeout=3)
                        except Exception:
                            try:
                                proc.kill()
                            except Exception:
                                pass

            print(json.dumps({{
                "status": status,
                "steps": steps,
                "protocol_probes": protocol_probes,
                "safe_backend_probe": safe_backend_probe,
                "gateway_proxy_probe": [],
                "diagnostics": diagnostics,
            }}))
            sys.exit(0 if status == "passed" else 2)
            """
        )


def skipped_evidence_from_unavailable(
    plan: ValidationPlan, container: str, error: Exception
) -> ValidationEvidence:
    now = _now()
    result = ValidationResult(
        server_id=plan.server_id,
        environment=plan.environment,
        status="skipped",
        installability_tier=plan.preflight.get("installability_tier", "might_work"),
        message=str(error),
        diagnostics=str(error),
    )
    return ValidationEvidence(
        server_id=plan.server_id,
        validation_started_at=now,
        validation_finished_at=now,
        environment=plan.environment,
        container_image=container,
        install_steps=plan.install_steps,
        protocol_probes=[],
        network_requirements={"requires_network": plan.requires_network},
        result=result.status,
        status=result.status,
        diagnostics=result.diagnostics,
        follow_up_required=True,
        redactions=["credentials", "environment", "commands", "subprocess_output"],
    )
