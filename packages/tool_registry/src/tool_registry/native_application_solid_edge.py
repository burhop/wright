"""Ownership-aware Solid Edge control on a dedicated, bounded COM STA helper.

pywin32 and psutil are selected native-host dependencies, imported lazily. They
are not prerequisites for loading the general tool registry or its base image.
No forced application or helper termination is implemented. A timed-out COM call
poisons its channel so an uncertain mutation cannot be followed by another one.
"""

from __future__ import annotations

import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from tool_registry.native_application_lifecycle import DEFAULT_POLICY, same_process


class SolidEdgeLifecycleError(RuntimeError):
    pass


def process_identity(pid: int) -> dict | None:
    import psutil

    try:
        process = psutil.Process(pid)
        with process.oneshot():
            return {
                "pid": pid,
                "creation_time": datetime.fromtimestamp(
                    process.create_time(), UTC
                ).isoformat(),
                "executable": str(Path(process.exe()).resolve()),
            }
    except psutil.NoSuchProcess:
        return None


def _hidden_options() -> dict:
    if os.name != "nt":
        return {}
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    return {"startupinfo": startup, "creationflags": subprocess.CREATE_NO_WINDOW}


class SolidEdgeComChannel:
    """One STA helper retains exact document identities across SaveAs and close."""

    def __init__(self, python_executable: str = sys.executable) -> None:
        self.python_executable = python_executable
        self.process = None
        self._responses: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self.poisoned = False

    def _start(self) -> None:
        if os.name != "nt":
            raise SolidEdgeLifecycleError("Solid Edge native control requires Windows")
        helper = Path(__file__).with_name("native_application_solid_edge_host.py")
        self.process = subprocess.Popen(
            [self.python_executable, "-u", str(helper)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            **_hidden_options(),
        )

        def read() -> None:
            try:
                for line in self.process.stdout:
                    self._responses.put(json.loads(line))
            except Exception as error:
                self._responses.put(
                    {"error": f"COM helper response failed: {type(error).__name__}"}
                )
            finally:
                self._responses.put({"error": "COM helper exited"})

        threading.Thread(
            target=read, daemon=True, name="solid-edge-com-responses"
        ).start()

    def request(self, action: str, payload: dict, timeout: float) -> dict:
        with self._lock:
            if self.poisoned:
                raise SolidEdgeLifecycleError(
                    "COM outcome is unresolved; channel is quarantined"
                )
            if self.process is None:
                self._start()
            request_id = uuid4().hex
            try:
                self.process.stdin.write(
                    json.dumps({"id": request_id, "action": action, **payload}) + "\n"
                )
                self.process.stdin.flush()
                response = self._responses.get(timeout=timeout)
            except (queue.Empty, BrokenPipeError, OSError) as error:
                self.poisoned = True
                raise SolidEdgeLifecycleError(
                    f"COM {action} outcome is unknown; channel quarantined"
                ) from error
            if response.get("id") != request_id:
                self.poisoned = True
                raise SolidEdgeLifecycleError(
                    "COM response identity mismatched; channel quarantined"
                )
            if response.get("error"):
                raise SolidEdgeLifecycleError(response["error"])
            return response["result"]

    def release(self, timeout: float = 5) -> None:
        """Release an idle helper only. Never terminate an in-flight COM call."""
        if self.process is None or self.poisoned:
            return
        self.request("release", {}, timeout)
        self.process.wait(timeout=timeout)


class SolidEdgeNativeApplicationAdapter:
    def __init__(
        self,
        *,
        channel=None,
        identity_reader=process_identity,
        allowed_roots: tuple[Path, ...] = (),
    ) -> None:
        self.channel = channel or SolidEdgeComChannel()
        self.identity_reader = identity_reader
        self.allowed_roots = tuple(path.resolve() for path in allowed_roots)

    def _identity(self, session: dict) -> dict | None:
        observed = self.identity_reader(session["identity"]["pid"])
        if observed is not None and not same_process(session["identity"], observed):
            raise SolidEdgeLifecycleError(
                "Solid Edge PID identity changed; native action refused"
            )
        return observed

    def _request(
        self,
        action: str,
        session: dict,
        document: dict | None = None,
        *,
        timeout: float | None = None,
    ) -> dict:
        if self._identity(session) is None:
            raise SolidEdgeLifecycleError("The exact Solid Edge process has exited")
        timeout_key = (
            "quit_timeout_seconds"
            if action == "quit"
            else (
                "document_close_timeout_seconds"
                if action in ("save", "close")
                else "startup_timeout_seconds"
            )
        )
        return self.channel.request(
            action,
            {"session": session, "document": document},
            timeout
            if timeout is not None
            else session.get("policy", {}).get(
                timeout_key, DEFAULT_POLICY[timeout_key]
            ),
        )

    def inspect(self, session: dict) -> dict:
        observed = self.identity_reader(session["identity"]["pid"])
        if observed is None:
            return {"alive": False, "endpoint_alive": False, "documents": []}
        if not same_process(session["identity"], observed):
            return {
                "alive": True,
                "identity": observed,
                "endpoint_matches": False,
                "healthy": False,
                "document_state_known": False,
                "active_operation": None,
            }
        return self._request("inspect", session)

    @staticmethod
    def _owned_document(document: dict) -> None:
        if (
            document.get("ownership") != "owned"
            or document.get("preexisted") is not False
            or not document.get("creation_evidence")
            or not document.get("native_id")
        ):
            raise SolidEdgeLifecycleError(
                "Exact campaign document ownership is required"
            )

    def save_document(self, session: dict, document: dict) -> dict:
        self._owned_document(document)
        recovery = Path(document["recovery_path"])
        if not recovery.is_absolute() or not any(
            recovery.resolve().is_relative_to(root) for root in self.allowed_roots
        ):
            raise SolidEdgeLifecycleError(
                "Recovery path is outside the configured native output roots"
            )
        if recovery.exists() or not recovery.parent.is_dir():
            raise SolidEdgeLifecycleError(
                "Recovery requires a new file in an existing approved directory"
            )
        return self._request("save", session, document)

    def close_document(self, session: dict, document: dict) -> dict:
        self._owned_document(document)
        return self._request("close", session, document)

    def quit_application(self, session: dict) -> dict:
        if session.get("ownership") != "owned":
            raise SolidEdgeLifecycleError(
                "Borrowed or unknown applications cannot be quit"
            )
        launch = session.get("launch_receipt", {})
        if not launch.get("native_session_verified") or not same_process(
            session["identity"], launch.get("identity")
        ):
            raise SolidEdgeLifecycleError(
                "Exact verified launch receipt is required for quit"
            )
        if self._identity(session) is None:
            return {"requested": False, "already_exited": True}
        timeout = session.get("policy", {}).get(
            "quit_timeout_seconds", DEFAULT_POLICY["quit_timeout_seconds"]
        )
        deadline = time.monotonic() + timeout
        result = self._request("quit", session, timeout=timeout)
        while time.monotonic() < deadline:
            if self._identity(session) is None:
                return {**result, "process_exited": True}
            time.sleep(0.1)
        raise SolidEdgeLifecycleError(
            "Graceful Solid Edge exit timed out; resource requires reconciliation"
        )

    def launch_owned(
        self,
        executable: Path,
        *,
        receipt_directory: Path,
        resource_id: str,
        policy: dict | None = None,
    ) -> dict:
        """Launch a dedicated empty app; leave every startup failure durably recorded."""
        import psutil

        if os.name != "nt":
            raise SolidEdgeLifecycleError("Solid Edge native startup requires Windows")
        executable = executable.resolve(strict=True)
        if executable.name.lower() != "edge.exe":
            raise SolidEdgeLifecycleError(
                "Expected the selected installed Solid Edge Edge.exe"
            )
        baseline = []
        for process in psutil.process_iter(["pid", "name", "exe"]):
            if (process.info.get("name") or "").lower() == "edge.exe":
                baseline.append(process_identity(process.pid))
        if baseline:
            raise SolidEdgeLifecycleError(
                "A preexisting Solid Edge process prevents dedicated startup"
            )
        session_id = uuid4().hex
        receipt_directory = receipt_directory.resolve()
        receipt_directory.mkdir(parents=True, exist_ok=True)
        receipt_path = receipt_directory / f"{session_id}.json"
        record = {
            "session_id": session_id,
            "resource_id": resource_id,
            "app_kind": "solid_edge",
            "host": socket.gethostname(),
            "ownership": "unknown",
            "policy": {**DEFAULT_POLICY, **(policy or {})},
            "startup_state": "intent_persisted",
            "executable": str(executable),
            "baseline": baseline,
            "created_at": datetime.now(UTC).isoformat(),
        }

        def persist() -> None:
            temporary = receipt_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, receipt_path)

        persist()
        try:
            process = subprocess.Popen(
                [str(executable), "/automation"], **_hidden_options()
            )
            identity = process_identity(process.pid)
            if identity is None:
                raise SolidEdgeLifecycleError(
                    "Launched Solid Edge exited before identity could be recorded"
                )
            record.update(
                identity=identity,
                native_session_id=f"solid-edge:{identity['pid']}:{identity['creation_time']}",
                startup_state="process_launched",
                launch_receipt_path=str(receipt_path),
            )
            persist()
            deadline = time.monotonic() + record["policy"]["startup_timeout_seconds"]
            while time.monotonic() < deadline:
                observed = self._request(
                    "inspect", record, timeout=max(0.001, deadline - time.monotonic())
                )
                if observed.get("endpoint_matches") is True:
                    if (
                        observed.get("documents")
                        or not observed.get("healthy")
                        or observed.get("modal") is not False
                    ):
                        raise SolidEdgeLifecycleError(
                            "New Solid Edge session is not healthy and empty"
                        )
                    record.update(
                        version=observed["version"],
                        ownership="owned",
                        startup_state="verified",
                        launch_receipt={
                            "ownership_basis": "dedicated_launch",
                            "baseline_absent": True,
                            "native_session_verified": True,
                            "identity": identity,
                        },
                    )
                    persist()
                    return record
                time.sleep(0.25)
            raise SolidEdgeLifecycleError("Solid Edge startup registration timed out")
        except Exception as error:
            record.update(
                startup_state="reconciliation_required", startup_error=str(error)
            )
            persist()
            raise
