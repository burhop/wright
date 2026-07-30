"""Fail-closed process identity, challenge, launch, and stop primitives."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Mapping, Protocol, Sequence
from uuid import uuid4

from .models import ProcessIdentity


class ProcessError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ProcessObservation:
    pid: int
    started_at: str
    executable_path: Path


class ProcessInspector(Protocol):
    def observe(self, pid: int) -> ProcessObservation | None: ...
    def signal(self, pid: int, *, force: bool = False) -> None: ...
    def wait(self, pid: int, timeout: float) -> bool: ...


class SystemProcessInspector:
    """Use psutil when available; otherwise fail closed instead of guessing."""

    def observe(self, pid: int) -> ProcessObservation | None:
        try:
            import psutil  # type: ignore[import-not-found]

            process = psutil.Process(pid)
            started = (
                __import__("datetime")
                .datetime.fromtimestamp(
                    process.create_time(), __import__("datetime").UTC
                )
                .isoformat()
                .replace("+00:00", "Z")
            )
            return ProcessObservation(pid, started, Path(process.exe()).resolve())
        except Exception:
            return None

    def signal(self, pid: int, *, force: bool = False) -> None:
        try:
            import psutil  # type: ignore[import-not-found]

            process = psutil.Process(pid)
            process.kill() if force else process.terminate()
        except Exception as exc:
            raise ProcessError("process_signal_failed") from exc

    def wait(self, pid: int, timeout: float) -> bool:
        try:
            import psutil  # type: ignore[import-not-found]

            psutil.Process(pid).wait(timeout=timeout)
            return True
        except Exception:
            return False


class ProcessManager:
    def __init__(self, inspector: ProcessInspector | None = None) -> None:
        self.inspector = inspector or SystemProcessInspector()

    def require_identity(
        self,
        identity: ProcessIdentity,
        runtime_path: Path,
        *,
        expected_runtime_id: str,
        observation: ProcessObservation | None = None,
    ) -> ProcessObservation:
        if identity.runtime_id != expected_runtime_id:
            raise ProcessError("process_runtime_mismatch")
        observed = observation or self.inspector.observe(identity.pid)
        if observed is None or observed.pid != identity.pid:
            raise ProcessError("process_not_found")
        if observed.started_at != identity.started_at:
            raise ProcessError("process_start_mismatch")
        executable = observed.executable_path.resolve(strict=False)
        runtime = runtime_path.resolve(strict=False)
        if identity.launcher_path is not None:
            launcher = Path(identity.launcher_path).resolve(strict=False)
        elif sys.platform == "darwin":
            launcher = runtime / "bin" / "python"
            if not launcher.is_file():
                raise ProcessError("process_launcher_not_found")
        else:
            launcher = executable
        if not launcher.is_relative_to(runtime):
            code = (
                "process_launcher_outside_runtime"
                if identity.launcher_path is not None
                else "process_executable_outside_runtime"
            )
            raise ProcessError(code)
        if not executable.is_relative_to(runtime) and sys.platform != "darwin":
            raise ProcessError("process_executable_outside_runtime")
        if executable != Path(identity.executable_path).resolve(strict=False):
            raise ProcessError("process_executable_mismatch")
        return observed

    @staticmethod
    def verify_challenge(identity: ProcessIdentity, challenge: str) -> None:
        actual = hashlib.sha256(challenge.encode("utf-8")).hexdigest()
        if not hmac.compare_digest(actual, identity.challenge_hash):
            raise ProcessError("health_challenge_mismatch")

    def launch(
        self,
        command: Sequence[str],
        *,
        runtime_id: str,
        runtime_path: Path,
        operation_id: str,
        host: str,
        port: int,
        environment: Mapping[str, str] | None = None,
        log_handle: BinaryIO | None = None,
    ) -> tuple[subprocess.Popen[bytes], ProcessIdentity, str]:
        if not command:
            raise ProcessError("process_command_missing")
        launcher = Path(command[0]).resolve(strict=False)
        if not launcher.is_relative_to(runtime_path.resolve(strict=False)):
            raise ProcessError("process_executable_outside_runtime")
        challenge = secrets.token_urlsafe(32)
        instance_id = str(uuid4())
        child_environment = dict(os.environ)
        child_environment.update(environment or {})
        child_environment.update(
            {
                "WRIGHT_RUNTIME_CHALLENGE": challenge,
                "WRIGHT_RUNTIME_INSTANCE_ID": instance_id,
                "WRIGHT_RUNTIME_ID": runtime_id,
                "WRIGHT_RUNTIME_OPERATION_ID": operation_id,
            }
        )
        output = log_handle if log_handle is not None else subprocess.DEVNULL
        if os.name == "nt":
            process = subprocess.Popen(
                list(command),
                env=child_environment,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                creationflags=(
                    getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                    | getattr(subprocess, "CREATE_NO_WINDOW", 0)
                ),
            )
        else:
            process = subprocess.Popen(
                list(command),
                env=child_environment,
                stdin=subprocess.DEVNULL,
                stdout=output,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        observation = None
        for _ in range(20):
            observation = self.inspector.observe(process.pid)
            if observation is not None or process.poll() is not None:
                break
            time.sleep(0.05)
        if observation is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            raise ProcessError("process_identity_unavailable")
        started_at = observation.started_at
        observed_executable = observation.executable_path.resolve(strict=False)
        identity = ProcessIdentity(
            pid=process.pid,
            started_at=started_at,
            runtime_id=runtime_id,
            executable_path=str(observed_executable),
            host=host,
            port=port,
            instance_id=instance_id,
            challenge_hash=hashlib.sha256(challenge.encode("utf-8")).hexdigest(),
            operation_id=operation_id,
            launcher_path=str(launcher),
        )
        return process, identity, challenge

    def stop(
        self,
        identity: ProcessIdentity,
        runtime_path: Path,
        *,
        expected_runtime_id: str,
        graceful_timeout: float = 10.0,
    ) -> None:
        self.require_identity(
            identity, runtime_path, expected_runtime_id=expected_runtime_id
        )
        self.inspector.signal(identity.pid, force=False)
        if self.inspector.wait(identity.pid, graceful_timeout):
            return
        self.require_identity(
            identity, runtime_path, expected_runtime_id=expected_runtime_id
        )
        self.inspector.signal(identity.pid, force=True)
        if not self.inspector.wait(identity.pid, max(1.0, graceful_timeout / 2)):
            raise ProcessError("process_stop_timeout")
