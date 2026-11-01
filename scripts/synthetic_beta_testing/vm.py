"""Small local QEMU/QMP owner for disposable beta-test guests.

No host provisioning, network fetching or product execution lives here. Paths and
guest names are scoped to a marked lab. The caller chooses the already-qualified
QEMU launcher, firmware, architecture and resource limits.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import socket
import subprocess
import time
import uuid


class VMError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class QMPClient:
    """One bounded QMP connection; events never count as command replies."""

    def __init__(self, socket_path, timeout=10):
        self.socket_path = str(socket_path)
        self.timeout = timeout
        self.socket = None
        self.stream = None
        self.sequence = 0
        self.events = []

    def __enter__(self):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        try:
            self.socket.connect(self.socket_path)
            self.stream = self.socket.makefile("rb")
            greeting = self._read(time.monotonic() + self.timeout)
            if "QMP" not in greeting:
                raise VMError("QMP greeting absent")
            self.execute("qmp_capabilities")
            return self
        except Exception:
            self.close()
            raise

    def __exit__(self, *_):
        self.close()

    def close(self):
        if self.stream:
            self.stream.close()
        if self.socket:
            self.socket.close()
        self.stream = self.socket = None

    def _read(self, deadline):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise VMError("QMP reply timeout")
        self.socket.settimeout(remaining)
        try:
            raw = self.stream.readline(4 * 1024 * 1024 + 1)
        except (TimeoutError, OSError) as error:
            raise VMError("QMP reply timeout or transport failure") from error
        if not raw or len(raw) > 4 * 1024 * 1024 or not raw.endswith(b"\n"):
            raise VMError("QMP closed or reply exceeded limit")
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as error:
            raise VMError("Invalid QMP JSON") from error
        if not isinstance(value, dict):
            raise VMError("Invalid QMP reply shape")
        return value

    def execute(self, command, arguments=None):
        if not self.socket:
            raise VMError("QMP is not connected")
        self.sequence += 1
        identity = f"beta-{self.sequence}"
        request = {"execute": command, "id": identity}
        if arguments is not None:
            request["arguments"] = arguments
        try:
            self.socket.sendall((json.dumps(request) + "\n").encode())
        except OSError as error:
            raise VMError("QMP send failed") from error
        deadline = time.monotonic() + self.timeout
        while True:
            reply = self._read(deadline)
            if "event" in reply:
                if len(self.events) >= 1000:
                    raise VMError("QMP event limit exceeded")
                self.events.append(reply)
                continue
            if reply.get("id") != identity:
                raise VMError("QMP reply identity mismatch")
            if "error" in reply:
                raise VMError(f"QMP {command} rejected: {reply['error']}")
            if "return" not in reply:
                raise VMError("QMP reply has no result")
            return reply["return"]

    def screenshot(self, path):
        return self.execute("screendump", {"filename": str(path)})

    def key(self, qcode, down=None):
        if not re.fullmatch(r"[a-z0-9_-]+", qcode):
            raise VMError("Invalid QEMU key name")
        value = {"type": "qcode", "data": qcode}
        if down is None:
            # Avoid depending on QEMU send-key virtual-clock release timers
            # while entering long text or successive modifier chords.
            try:
                self.key(qcode, down=True)
                time.sleep(0.02)
            finally:
                self.key(qcode, down=False)
            time.sleep(0.01)
            return None
        return self.execute(
            "input-send-event",
            {"events": [{"type": "key", "data": {"down": bool(down), "key": value}}]},
        )

    def type_text(self, text):
        if not isinstance(text, str) or len(text) > 10000:
            raise VMError("Text must be a string of at most 10000 characters")
        mapping = {
            " ": "spc",
            "\n": "ret",
            "\t": "tab",
            "-": "minus",
            "=": "equal",
            "[": "bracket_left",
            "]": "bracket_right",
            "\\": "backslash",
            ";": "semicolon",
            "'": "apostrophe",
            "`": "grave_accent",
            ",": "comma",
            ".": "dot",
            "/": "slash",
        }
        shifted = dict(zip('!@#$%^&*()_+{}|:"~<>?', "1234567890-=[]\\;'`,./"))
        # Validate the complete string before typing anything.
        if any(
            not (
                "a" <= char.lower() <= "z"
                or char.isascii()
                and char.isdigit()
                or char in mapping
                or char in shifted
            )
            for char in text
        ):
            raise VMError("Only printable US-ASCII, newline and tab are supported")
        for char in text:
            base = shifted.get(char, char.lower())
            code = mapping.get(base, base)
            needs_shift = char in shifted or char.isupper()
            try:
                if needs_shift:
                    self.key("shift", down=True)
                self.key(code)
            finally:
                if needs_shift:
                    self.key("shift", down=False)

    def pointer(self, x, y, width=1280, height=800):
        if width < 2 or height < 2 or not (0 <= x < width and 0 <= y < height):
            raise VMError("Pointer is outside declared display")
        return self.execute(
            "input-send-event",
            {
                "events": [
                    {
                        "type": "abs",
                        "data": {"axis": "x", "value": round(x * 32767 / (width - 1))},
                    },
                    {
                        "type": "abs",
                        "data": {"axis": "y", "value": round(y * 32767 / (height - 1))},
                    },
                ]
            },
        )

    def click(self, x, y, width=1280, height=800, button="left"):
        if button not in {"left", "right", "middle"}:
            raise VMError("Unsupported pointer button")
        self.pointer(x, y, width, height)
        for down in (True, False):
            self.execute(
                "input-send-event",
                {"events": [{"type": "btn", "data": {"down": down, "button": button}}]},
            )

    def scroll(self, delta):
        if not isinstance(delta, int) or not 0 < abs(delta) <= 20:
            raise VMError("Scroll must be 1–20 signed ticks")
        button = "wheel-down" if delta > 0 else "wheel-up"
        for _ in range(abs(delta)):
            for down in (True, False):
                self.execute(
                    "input-send-event",
                    {
                        "events": [
                            {"type": "btn", "data": {"down": down, "button": button}}
                        ]
                    },
                )


class VMBackend:
    """Own overlays only inside a marked local lab; never kill unknown processes."""

    def __init__(self, lab_root, launcher_prefix=(), timeout=10):
        self.root = Path(lab_root).absolute()
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink() or self.root.resolve() != self.root:
            raise VMError("Lab root must be a real absolute directory")
        marker = self.root / ".synthetic-beta-lab.json"
        if marker.is_symlink():
            raise VMError("Lab ownership marker cannot be a symlink")
        if marker.exists():
            self.owner = json.loads(marker.read_text())["owner"]
        else:
            # Adopt no unknown files: otherwise reset could claim preexisting data.
            if any(self.root.iterdir()):
                raise VMError("New lab root must be empty")
            self.owner = str(uuid.uuid4())
            marker.write_text(json.dumps({"owner": self.owner, "schema": 1}))
        self.prefix = list(launcher_prefix)
        self.timeout = timeout

    def _session(self, session_id):
        if not isinstance(session_id, str) or not re.fullmatch(
            r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}", session_id
        ):
            raise VMError("Invalid session ID")
        path = self.root / "sessions" / session_id
        if path.resolve() != path:
            raise VMError("Session escapes lab or uses symlink")
        return path

    def _load(self, session_id):
        path = self._session(session_id)
        if (path / "vm.json").is_symlink():
            raise VMError("Session manifest cannot be a symlink")
        manifest = json.loads((path / "vm.json").read_text())
        if (
            manifest.get("owner") != self.owner
            or manifest.get("session_id") != session_id
        ):
            raise VMError("Session ownership mismatch")
        for field, name in (("overlay", "disk.qcow2"), ("qmp_socket", "qmp.sock")):
            if manifest.get(field) != str(path / name):
                raise VMError("Session path identity mismatch")
        if (path / "disk.qcow2").is_symlink():
            raise VMError("Overlay cannot be a symlink")
        return path, manifest

    def _save(self, path, manifest):
        temporary = path / "vm.json.tmp"
        if temporary.is_symlink():
            raise VMError("Manifest temporary path cannot be a symlink")
        temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        temporary.replace(path / "vm.json")

    def _verify_base(self, manifest):
        base = Path(manifest["base_image"])
        if (
            base.resolve() != base
            or not base.is_file()
            or sha256(base) != manifest["base_sha256"]
        ):
            raise VMError("Immutable base identity changed")
        return base

    def _create_overlay(self, path, manifest):
        base = self._verify_base(manifest)
        result = subprocess.run(
            self.prefix
            + [
                "qemu-img",
                "create",
                "-f",
                "qcow2",
                "-F",
                "qcow2",
                "-b",
                str(base),
                str(path / "disk.qcow2"),
            ],
            capture_output=True,
            text=True,
            timeout=self.timeout,
            check=False,
        )
        if result.returncode:
            raise VMError(f"Overlay creation failed: {result.stderr[-2000:]}")

    def prepare(self, base_image, expected_sha256, session_id):
        path = self._session(session_id)
        if path.exists():
            raise VMError("Session already exists; use explicit reset")
        base = Path(base_image).absolute()
        if (
            base.resolve() != base
            or not base.is_file()
            or not re.fullmatch(r"[0-9a-f]{64}", expected_sha256)
        ):
            raise VMError("Expected real base file and exact SHA256")
        if sha256(base) != expected_sha256:
            raise VMError("Immutable base identity changed")
        path.mkdir(parents=True)
        manifest = {
            "schema": 1,
            "owner": self.owner,
            "session_id": session_id,
            "base_image": str(base),
            "base_sha256": expected_sha256,
            "overlay": str(path / "disk.qcow2"),
            "qmp_socket": str(path / "qmp.sock"),
            "state": "preparing",
        }
        self._save(path, manifest)
        self._create_overlay(path, manifest)
        manifest["state"] = "prepared"
        self._save(path, manifest)
        return manifest

    @staticmethod
    def _pid_identity(pid):
        try:
            # /proc field 22, ignoring a process name containing spaces/parens.
            fields = (
                Path(f"/proc/{int(pid)}/stat").read_text().rsplit(")", 1)[1].split()
            )
            return None if fields[0] == "Z" else fields[19]
        except (OSError, ValueError, IndexError):
            return None

    def state(self, session_id):
        path, manifest = self._load(session_id)
        pid_live = bool(
            manifest.get("pid")
            and self._pid_identity(manifest["pid"]) == manifest.get("pid_start")
        )
        socket_present = (path / "qmp.sock").exists()
        if socket_present:
            try:
                with QMPClient(path / "qmp.sock", self.timeout) as qmp:
                    name = qmp.execute("query-name").get("name")
                    if name != session_id:
                        raise VMError("QMP guest ownership mismatch")
                    status = qmp.execute("query-status")
                return {
                    **manifest,
                    "live": True,
                    "qmp_status": status,
                    "pid_live": pid_live,
                }
            except (OSError, VMError) as error:
                if pid_live:
                    return {
                        **manifest,
                        "live": True,
                        "control_error": str(error),
                        "pid_live": True,
                    }
                # A wrong-name reachable QMP server remains unknown live ownership.
                if "ownership mismatch" in str(error):
                    raise
        return {**manifest, "live": pid_live, "pid_live": pid_live}

    def start(
        self,
        session_id,
        qemu_args=(),
        binary="qemu-system-aarch64",
        start_launcher_prefix=None,
    ):
        path, manifest = self._load(session_id)
        if self.state(session_id)["live"]:
            raise VMError("Guest is already running")
        self._verify_base(manifest)
        if not (path / "disk.qcow2").is_file():
            raise VMError("Prepared overlay absent")
        # Caller may configure firmware/network/devices, not replace identity or disk.
        for index, argument in enumerate(qemu_args):
            if argument in {"-name", "-qmp", "-daemonize", "-pidfile", "-blockdev"}:
                raise VMError("Caller cannot replace owned guest identity/disk")
            if argument == "-drive":
                if index + 1 >= len(qemu_args):
                    raise VMError("Ancillary drive value is absent")
                fields = qemu_args[index + 1].split(",")
                parts = dict(field.split("=", 1) for field in fields if "=" in field)
                if len(parts) != len(fields) or set(parts) != {
                    "file",
                    "if",
                    "format",
                    "readonly",
                }:
                    raise VMError(
                        "Ancillary drive must declare file/if/format/readonly only"
                    )
                seed = Path(parts["file"]).absolute()
                if (
                    seed.resolve() != seed
                    or not seed.is_relative_to(self.root)
                    or not seed.is_file()
                    or parts["if"] != "virtio"
                    or parts["format"] not in {"raw", "qcow2"}
                    or parts["readonly"] != "on"
                ):
                    raise VMError("Ancillary drive must be a contained readonly image")
        (path / "qmp.sock").unlink(missing_ok=True)
        prefix = (
            self.prefix
            if start_launcher_prefix is None
            else list(start_launcher_prefix)
        )
        argv = (
            prefix
            + [
                binary,
                "-name",
                session_id,
                "-qmp",
                f"unix:{path / 'qmp.sock'},server=on,wait=off",
                "-drive",
                f"file={path / 'disk.qcow2'},if=virtio,format=qcow2",
            ]
            + list(qemu_args)
        )
        with (path / "qemu.log").open("ab") as log:
            process = subprocess.Popen(
                argv, stdin=subprocess.DEVNULL, stdout=log, stderr=log
            )
        manifest.update(
            state="starting",
            pid=process.pid,
            pid_start=self._pid_identity(process.pid),
            argv=argv,
        )
        self._save(path, manifest)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if process.poll() is not None:
                manifest["state"] = "start-failed"
                self._save(path, manifest)
                raise VMError(
                    f"Guest launcher exited {process.returncode}; inspect {path / 'qemu.log'}"
                )
            if (path / "qmp.sock").exists():
                current = self.state(session_id)
                if current.get("qmp_status"):
                    manifest["state"] = "running"
                    self._save(path, manifest)
                    return manifest
            time.sleep(0.05)
        raise VMError("Guest QMP startup timed out; owned guest may still be running")

    def stop(self, session_id):
        path, manifest = self._load(session_id)
        if not self.state(session_id)["live"]:
            manifest["state"] = "stopped"
            self._save(path, manifest)
            return manifest
        # Never fall back to kill/pkill/docker stop when exact QMP ownership is unknown.
        with QMPClient(path / "qmp.sock", self.timeout) as qmp:
            if qmp.execute("query-name").get("name") != session_id:
                raise VMError("Refusing stop: QMP guest ownership mismatch")
            qmp.execute("quit")
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            current = self.state(session_id)
            if not current["live"]:
                manifest["state"] = "stopped"
                self._save(path, manifest)
                return manifest
            time.sleep(0.05)
        raise VMError("Guest quit requested but shutdown not yet confirmed")

    def reset(self, session_id):
        path, manifest = self._load(session_id)
        if self.state(session_id)["live"]:
            raise VMError("Refusing to reset a running guest")
        self._verify_base(manifest)
        # Only this declared overlay is removed; no directory recursion.
        (path / "disk.qcow2").unlink(missing_ok=True)
        (path / "qmp.sock").unlink(missing_ok=True)
        self._create_overlay(path, manifest)
        manifest.update(state="prepared", pid=None, pid_start=None)
        self._save(path, manifest)
        return manifest

    def screenshot(self, session_id, path):
        session, _ = self._load(session_id)
        target = Path(path).absolute()
        if target.resolve() != target or not target.is_relative_to(session):
            raise VMError("Screenshot must be inside its owned session")
        target.parent.mkdir(parents=True, exist_ok=True)
        self._owned_input(session_id, lambda qmp: qmp.screenshot(target))
        if not target.is_file() or not target.read_bytes().startswith(b"P6"):
            raise VMError("QMP screenshot is not a PPM image")
        return {"path": str(target), "sha256": sha256(target)}

    def _owned_input(self, session_id, callback):
        path, _ = self._load(session_id)
        with QMPClient(path / "qmp.sock", self.timeout) as qmp:
            if qmp.execute("query-name").get("name") != session_id:
                raise VMError("QMP guest ownership mismatch")
            return callback(qmp)

    def input(self, session_id, operation, **kwargs):
        if operation not in {"key", "type_text", "pointer", "click", "scroll"}:
            raise VMError("Unsupported visible input operation")
        return self._owned_input(
            session_id, lambda qmp: getattr(qmp, operation)(**kwargs)
        )
