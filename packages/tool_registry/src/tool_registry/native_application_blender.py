"""Dedicated Blender lifecycle through fixed file IPC, independent of mesh tools.

The selected host supplies Blender and psutil. No software is added to the base
image. This adapter cannot evaluate scripts, disable safe mode, attach to user
Blender sessions or force terminate a process. An optional launch-time bootstrap
may enable one exact pinned mesh add-on on a dedicated loopback port; model code
still travels through that add-on's guarded MCP server, never through lifecycle
IPC. Unknown calls poison mutations durably; inspection remains available for
explicit outcome reconciliation.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .native_application_lifecycle import DEFAULT_POLICY, same_process


class BlenderLifecycleError(RuntimeError):
    pass


def process_identity(pid):
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


def _write_json(path, value):
    temporary = path.with_name(path.name + ".next")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    temporary.replace(path)


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _hidden_options():
    if os.name != "nt":
        return {}
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = subprocess.SW_HIDE
    return {"startupinfo": startup, "creationflags": subprocess.CREATE_NO_WINDOW}


class BlenderFileChannel:
    ACTIONS = frozenset(
        {"inspect", "create_document", "save_document", "close_document", "quit"}
    )

    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self._lock = threading.Lock()

    def request(self, action, payload, timeout):
        if action not in self.ACTIONS:
            raise BlenderLifecycleError("Unsupported fixed Blender lifecycle operation")
        state_path = self.directory / "channel-state.json"
        with self._lock:
            state = _read_json(state_path) if state_path.exists() else {}
            if state.get("unresolved") and action != "inspect":
                raise BlenderLifecycleError(
                    "Previous Blender outcome is unknown; mutations are quarantined"
                )
            request_id = uuid4().hex
            request = {"id": request_id, "action": action, **payload}
            # Keep the outstanding mutation across adapter/worker restarts.
            if action != "inspect":
                _write_json(
                    state_path,
                    {"unresolved": True, "request_id": request_id, "action": action},
                )
            _write_json(self.directory / "requests" / f"{request_id}.json", request)
            response_path = self.directory / "responses" / f"{request_id}.json"
            deadline = time.monotonic() + timeout
            while not response_path.exists() and time.monotonic() < deadline:
                time.sleep(min(0.05, max(0, deadline - time.monotonic())))
            if not response_path.exists():
                raise BlenderLifecycleError(
                    f"Blender {action} timed out; outcome remains unknown"
                )
            response = _read_json(response_path)
            if response.get("id") != request_id or response.get(
                "native_session_id"
            ) != payload.get("native_session_id"):
                raise BlenderLifecycleError(
                    "Blender response identity mismatched; outcome remains unknown"
                )
            if response.get("error"):
                # A native exception might occur after mutation. Never clear its
                # quarantine merely because an error reply was received.
                raise BlenderLifecycleError(response["error"])
            if action != "inspect":
                _write_json(
                    state_path,
                    {"unresolved": False, "request_id": request_id, "action": action},
                )
            return response["result"]


class BlenderNativeApplicationAdapter:
    def __init__(
        self,
        *,
        allowed_roots=(),
        identity_reader=process_identity,
        channel_factory=BlenderFileChannel,
    ):
        self.allowed_roots = tuple(Path(root).resolve() for root in allowed_roots)
        self.identity_reader = identity_reader
        self.channel_factory = channel_factory
        self.channels = {}

    def _allowed_path(self, path):
        resolved = Path(path).resolve()
        if not any(
            resolved.is_relative_to(root) and resolved != root
            for root in self.allowed_roots
        ):
            raise BlenderLifecycleError(
                "Blender lifecycle path is outside the approved roots"
            )
        return resolved

    def _identity(self, session):
        observed = self.identity_reader(session["identity"]["pid"])
        if observed is not None and not same_process(session["identity"], observed):
            raise BlenderLifecycleError(
                "Blender process identity changed; action refused"
            )
        return observed

    def _request(self, session, action, **payload):
        if action != "inspect" and session.get("ownership") != "owned":
            raise BlenderLifecycleError(
                "Blender mutations require a dedicated owned application"
            )
        if self._identity(session) is None:
            raise BlenderLifecycleError("The exact Blender process has exited")
        directory = self._allowed_path(session["endpoint"]["directory"])
        config = _read_json(directory / "config.json")
        ready = _read_json(directory / "ready.json")
        profile = str(self._allowed_path(session["profile_path"]))
        mesh_endpoint = session.get("mesh_endpoint")
        if (
            config.get("native_session_id") != session["native_session_id"]
            or ready.get("native_session_id") != session["native_session_id"]
            or ready.get("pid") != session["identity"]["pid"]
            or ready.get("profile_path") != profile
            or config.get("profile_path") != profile
            or ready.get("safe_mode") is not True
            or (
                mesh_endpoint is not None
                and ready.get("mesh_endpoint") != mesh_endpoint
            )
        ):
            raise BlenderLifecycleError(
                "Blender endpoint/profile ownership is unresolved"
            )
        channel = self.channels.setdefault(
            str(directory), self.channel_factory(directory)
        )
        timeout = session.get("policy", DEFAULT_POLICY).get(
            "quit_timeout_seconds"
            if action == "quit"
            else "document_close_timeout_seconds",
            30,
        )
        return channel.request(
            action,
            {"native_session_id": session["native_session_id"], **payload},
            timeout,
        )

    def inspect(self, session):
        identity = self._identity(session)
        if identity is None:
            return {"alive": False, "endpoint_alive": False, "identity": None}
        observation = self._request(session, "inspect")
        return {
            **observation,
            "identity": identity,
            "alive": True,
            "endpoint_alive": True,
            "endpoint_matches": observation.get("native_session_id")
            == session["native_session_id"],
        }

    def create_document(self, session, native_id):
        return self._request(session, "create_document", native_id=native_id)

    def save_document(self, session, document):
        if document.get("ownership") != "owned":
            raise BlenderLifecycleError(
                "Borrowed Blender documents cannot be saved by cleanup"
            )
        target = self._allowed_path(document["recovery_path"])
        if target.suffix.lower() != ".blend":
            raise BlenderLifecycleError(
                "Blender recovery files require a .blend extension"
            )
        result = self._request(
            session,
            "save_document",
            native_id=document["native_id"],
            current_path=document.get("current_path") or document.get("path"),
            path=str(target),
        )
        if (
            result.get("saved") is not True
            or not target.is_file()
            or target.stat().st_size == 0
        ):
            raise BlenderLifecycleError("Blender recovery file was not established")
        return {**result, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}

    def close_document(self, session, document):
        if document.get("ownership") != "owned":
            raise BlenderLifecycleError(
                "Borrowed Blender documents cannot be closed by cleanup"
            )
        return self._request(
            session,
            "close_document",
            native_id=document["native_id"],
            current_path=document.get("current_path") or document.get("path"),
        )

    def quit_application(self, session):
        result = self._request(session, "quit")
        deadline = time.monotonic() + session.get("policy", DEFAULT_POLICY).get(
            "quit_timeout_seconds", 30
        )
        while self._identity(session) is not None and time.monotonic() < deadline:
            time.sleep(0.05)
        if self._identity(session) is not None:
            raise BlenderLifecycleError(
                "Blender graceful exit was not verified before its deadline"
            )
        return {**result, "exited": True, "forced": False}

    def launch(
        self,
        executable,
        session_root,
        *,
        policy=None,
        addon_source=None,
        addon_port=None,
        addon_sha256=None,
    ):
        """Create a fresh dedicated profile and return registration evidence.

        The optional add-on is copied byte-for-byte into this session's isolated
        script directory and enabled once by the trusted static bootstrap. The
        lifecycle channel never accepts source code or add-on operations.
        """
        import psutil

        executable = Path(executable).resolve()
        if not executable.is_file():
            raise BlenderLifecycleError("Selected Blender executable is missing")
        root = self._allowed_path(session_root)
        root.mkdir(parents=True, exist_ok=False)
        profile = root / "profile"
        profile.mkdir()
        resources = root / "resources"
        resources.mkdir()
        for name in ("scripts", "extensions", "datafiles"):
            (resources / name).mkdir()
        addon = None
        if (addon_source is None) != (addon_port is None):
            raise BlenderLifecycleError(
                "Pinned Blender add-on source and port must be supplied together"
            )
        if addon_source is not None:
            source = Path(addon_source).resolve()
            if not source.is_file():
                raise BlenderLifecycleError("Pinned Blender add-on source is missing")
            if type(addon_port) is not int or not 1024 <= addon_port <= 65535:
                raise BlenderLifecycleError(
                    "Pinned Blender add-on requires a valid dedicated port"
                )
            source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
            if addon_sha256 is not None and source_digest != addon_sha256:
                raise BlenderLifecycleError("Pinned Blender add-on source hash changed")
            addon_directory = resources / "scripts" / "addons"
            addon_directory.mkdir()
            staged_addon = addon_directory / "blender_mcp.py"
            with staged_addon.open("xb") as output:
                output.write(source.read_bytes())
            addon = {
                "module": "blender_mcp",
                "host": "127.0.0.1",
                "port": addon_port,
                "source_path": str(staged_addon),
                "source_sha256": source_digest,
            }
        directory = root / "control"
        directory.mkdir()
        for name in ("requests", "responses"):
            (directory / name).mkdir()
        session_id = "blender-" + uuid4().hex
        config = {
            "native_session_id": session_id,
            "profile_path": str(profile),
            "allowed_roots": [str(path) for path in self.allowed_roots],
            "addon": addon,
        }
        _write_json(directory / "config.json", config)
        baseline = []
        for process in psutil.process_iter(["pid", "name"]):
            if (process.info["name"] or "").lower() in {"blender", "blender.exe"}:
                identity = self.identity_reader(process.pid)
                if identity:
                    baseline.append(identity)
        helper_source = Path(__file__).with_name("native_application_blender_host.py")
        helper = root / "blender-lifecycle-host.py"
        with helper.open("xb") as output:
            output.write(helper_source.read_bytes())
        environment = {
            **os.environ,
            "BLENDER_USER_CONFIG": str(profile),
            "BLENDER_MCP_SAFE_MODE": "true",
            "BLENDER_USER_RESOURCES": str(resources),
            "BLENDER_USER_SCRIPTS": str(resources / "scripts"),
            "BLENDER_USER_EXTENSIONS": str(resources / "extensions"),
            "BLENDER_USER_DATAFILES": str(resources / "datafiles"),
        }
        bounds = {**DEFAULT_POLICY, **(policy or {})}
        with (
            (root / "host.stdout.log").open("wb") as stdout,
            (root / "host.stderr.log").open("wb") as stderr,
        ):
            process = subprocess.Popen(
                [
                    str(executable),
                    "--factory-startup",
                    "--python",
                    str(helper),
                    "--",
                    str(directory / "config.json"),
                ],
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                env=environment,
                **_hidden_options(),
            )
        identity = self.identity_reader(process.pid)
        launch = {
            "ownership_basis": "dedicated_launch",
            "baseline_absent": identity not in baseline,
            "identity": identity,
            "baseline": baseline,
            "native_session_verified": False,
            "profile_path": str(profile),
            "resources_path": str(resources),
            "helper_path": str(helper),
            "helper_sha256": hashlib.sha256(helper.read_bytes()).hexdigest(),
        }
        _write_json(root / "launch-receipt.json", launch)
        deadline = time.monotonic() + bounds["startup_timeout_seconds"]
        while (
            not (directory / "ready.json").exists()
            and process.poll() is None
            and time.monotonic() < deadline
        ):
            time.sleep(0.05)
        if not (directory / "ready.json").exists():
            raise BlenderLifecycleError(
                f"Dedicated Blender startup did not become ready; inspect {root}"
            )
        ready = _read_json(directory / "ready.json")
        expected_mesh_endpoint = (
            None
            if addon is None
            else {
                "kind": "blender_mcp_socket",
                "host": addon["host"],
                "port": addon["port"],
                "addon_sha256": addon["source_sha256"],
            }
        )
        if (
            identity is None
            or not same_process(identity, self.identity_reader(process.pid))
            or ready.get("pid") != process.pid
            or ready.get("native_session_id") != session_id
            or ready.get("profile_path") != str(profile)
            or ready.get("safe_mode") is not True
            or ready.get("mesh_endpoint") != expected_mesh_endpoint
        ):
            raise BlenderLifecycleError(
                "Dedicated Blender startup identity was not verified"
            )
        if expected_mesh_endpoint is not None:
            deadline = time.monotonic() + bounds["startup_timeout_seconds"]
            while time.monotonic() < deadline:
                try:
                    with socket.create_connection(
                        (
                            expected_mesh_endpoint["host"],
                            expected_mesh_endpoint["port"],
                        ),
                        timeout=0.25,
                    ):
                        break
                except OSError:
                    time.sleep(0.05)
            else:
                raise BlenderLifecycleError(
                    "Dedicated Blender mesh endpoint did not become ready"
                )
        launch["native_session_verified"] = True
        launch["mesh_endpoint"] = expected_mesh_endpoint
        _write_json(root / "launch-receipt.json", launch)
        return {
            "session_id": session_id,
            "resource_id": "blender:" + str(root),
            "app_kind": "blender",
            "version": ready["version"],
            "host": socket.gethostname(),
            "ownership": "owned",
            "identity": identity,
            "native_session_id": session_id,
            "profile_path": str(profile),
            "endpoint": {"kind": "fixed_file_ipc", "directory": str(directory)},
            "mesh_endpoint": expected_mesh_endpoint,
            "launch_receipt": launch,
            "policy": bounds,
        }
