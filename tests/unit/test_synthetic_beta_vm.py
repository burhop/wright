"""Local protocol/ownership fixtures; these are not real VM qualification."""

import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import threading
import time

import pytest


MODULE = Path(__file__).resolve().parents[2] / "scripts/synthetic_beta_testing/vm.py"
SPEC = importlib.util.spec_from_file_location("synthetic_beta_vm", MODULE)
vm = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vm)


@pytest.fixture
def qmp_server(tmp_path):
    servers = []
    threads = []
    errors = []

    def start(handler):
        path = tmp_path / f"q{len(servers)}.sock"
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(path))
        server.listen(1)
        server.settimeout(2)
        servers.append(server)

        def run():
            try:
                connection, _ = server.accept()
                with connection, connection.makefile("rwb") as stream:
                    stream.write(b'{"QMP":{"version":{}}}\n')
                    stream.flush()
                    request = json.loads(stream.readline())
                    assert request["execute"] == "qmp_capabilities"
                    stream.write(
                        (
                            json.dumps({"return": {}, "id": request["id"]}) + "\n"
                        ).encode()
                    )
                    stream.flush()
                    handler(stream)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as error:
                errors.append(error)

        thread = threading.Thread(target=run)
        thread.start()
        threads.append(thread)
        return path

    yield start
    for thread in threads:
        thread.join(timeout=3)
        assert not thread.is_alive()
    for server in servers:
        server.close()
    assert not errors


def test_qmp_negotiates_and_ignores_events(qmp_server):
    def handler(stream):
        request = json.loads(stream.readline())
        stream.write(b'{"event":"STOP"}\n')
        stream.write(
            (
                json.dumps({"return": {"name": "customer-1"}, "id": request["id"]})
                + "\n"
            ).encode()
        )
        stream.flush()

    with vm.QMPClient(qmp_server(handler), 1) as client:
        assert client.execute("query-name") == {"name": "customer-1"}
        assert client.events == [{"event": "STOP"}]


@pytest.mark.parametrize(
    "reply,message",
    [
        ({"return": {}, "id": "other"}, "identity mismatch"),
        ({"error": {"class": "CommandNotFound"}}, "rejected"),
        ({"unexpected": True}, "no result"),
    ],
)
def test_qmp_rejects_wrong_or_failed_reply(qmp_server, reply, message):
    def handler(stream):
        request = json.loads(stream.readline())
        value = dict(reply)
        value.setdefault("id", request["id"])
        stream.write((json.dumps(value) + "\n").encode())
        stream.flush()

    with vm.QMPClient(qmp_server(handler), 1) as client:
        with pytest.raises(vm.VMError, match=message):
            client.execute("query-name")


def test_qmp_bounded_timeout(qmp_server):
    def handler(stream):
        stream.readline()
        time.sleep(0.15)

    with vm.QMPClient(qmp_server(handler), 0.04) as client:
        before = time.monotonic()
        with pytest.raises(vm.VMError, match="timeout"):
            client.execute("query-name")
        assert time.monotonic() - before < 0.2


def test_visible_ascii_input_mapping_and_prevalidation(monkeypatch):
    calls = []
    client = vm.QMPClient("unused")
    monkeypatch.setattr(
        client, "execute", lambda command, arguments: calls.append((command, arguments))
    )
    monkeypatch.setattr(vm.time, "sleep", lambda _: None)
    client.type_text("A:$\n")
    events = [arguments["events"][0]["data"] for _, arguments in calls]
    assert [(item["key"]["data"], item["down"]) for item in events] == [
        ("shift", True),
        ("a", True),
        ("a", False),
        ("shift", False),
        ("shift", True),
        ("semicolon", True),
        ("semicolon", False),
        ("shift", False),
        ("shift", True),
        ("4", True),
        ("4", False),
        ("shift", False),
        ("ret", True),
        ("ret", False),
    ]
    assert all(command == "input-send-event" for command, _ in calls)
    calls.clear()
    with pytest.raises(vm.VMError, match="US-ASCII"):
        client.type_text("valid then \N{GREEK SMALL LETTER ALPHA}")
    assert calls == []


def test_failed_key_press_explicitly_releases_key_and_shift(monkeypatch):
    calls = []
    client = vm.QMPClient("unused")

    def fail_down(command, arguments):
        item = arguments["events"][0]["data"]
        calls.append((item["key"]["data"], item["down"]))
        if item["key"]["data"] == "a" and item["down"]:
            raise vm.VMError("Injected uncertain DOWN transport")

    monkeypatch.setattr(client, "execute", fail_down)
    monkeypatch.setattr(vm.time, "sleep", lambda _: None)
    with pytest.raises(vm.VMError, match="uncertain DOWN"):
        client.type_text("A")
    assert calls == [("shift", True), ("a", True), ("a", False), ("shift", False)]


def test_shift_down_failure_still_sends_shift_release(monkeypatch):
    calls = []
    client = vm.QMPClient("unused")

    def fail_shift(command, arguments):
        item = arguments["events"][0]["data"]
        calls.append((item["key"]["data"], item["down"]))
        if item["down"]:
            raise vm.VMError("Injected modifier transport failure")

    monkeypatch.setattr(client, "execute", fail_shift)
    with pytest.raises(vm.VMError, match="modifier transport"):
        client.type_text("A")
    assert calls == [("shift", True), ("shift", False)]


def test_absolute_pointer_scaling_and_limits(monkeypatch):
    calls = []
    client = vm.QMPClient("unused")
    monkeypatch.setattr(
        client, "execute", lambda command, arguments: calls.append(arguments)
    )
    client.pointer(1279, 799)
    assert [event["data"]["value"] for event in calls[0]["events"]] == [32767, 32767]
    with pytest.raises(vm.VMError, match="outside"):
        client.pointer(1280, 0)
    with pytest.raises(vm.VMError, match="signed ticks"):
        client.scroll(100)


@pytest.fixture
def lab(tmp_path, monkeypatch):
    root = tmp_path / "lab"
    backend = vm.VMBackend(root)
    base = root / "baseline.qcow2"
    base.write_bytes(b"Fixture image; not a real guest")

    def create_overlay(argv, **kwargs):
        assert argv[:2] == ["qemu-img", "create"]
        Path(argv[-1]).write_bytes(b"fixture overlay")
        return subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(vm.subprocess, "run", create_overlay)
    digest = hashlib.sha256(base.read_bytes()).hexdigest()
    backend.prepare(base, digest, "customer-1")
    return backend, base, digest


def test_prepare_reset_reuses_exact_base_and_preserves_other_files(lab):
    backend, base, digest = lab
    path = backend.root / "sessions/customer-1"
    (path / "report.txt").write_text("Retain customer failure")
    (path / "disk.qcow2").write_text("customer changes")
    manifest = backend.reset("customer-1")
    assert manifest["base_sha256"] == digest
    assert (path / "disk.qcow2").read_bytes() == b"fixture overlay"
    assert (path / "report.txt").read_text() == "Retain customer failure"
    assert hashlib.sha256(base.read_bytes()).hexdigest() == digest


def test_reset_rejects_changed_base_without_removing_overlay(lab):
    backend, base, _ = lab
    overlay = backend.root / "sessions/customer-1/disk.qcow2"
    base.write_bytes(b"changed")
    with pytest.raises(vm.VMError, match="base identity changed"):
        backend.reset("customer-1")
    assert overlay.exists()


def test_running_guest_cannot_be_reset(lab, monkeypatch):
    backend, _, _ = lab
    monkeypatch.setattr(backend, "state", lambda _: {"live": True})
    with pytest.raises(vm.VMError, match="running guest"):
        backend.reset("customer-1")


@pytest.mark.parametrize(
    "session_id", ["../escape", "/tmp/escape", "", "a/b", "a" * 49]
)
def test_session_confinement(lab, session_id):
    backend, base, digest = lab
    with pytest.raises(vm.VMError, match="session ID"):
        backend.prepare(base, digest, session_id)


def test_no_adoption_of_unknown_directory(tmp_path):
    (tmp_path / "important.txt").write_text("existing")
    with pytest.raises(vm.VMError, match="must be empty"):
        vm.VMBackend(tmp_path)


def test_symlinked_lab_marker_and_manifest_are_not_authority(lab, tmp_path):
    backend, _, _ = lab
    manifest_path = backend.root / "sessions/customer-1/vm.json"
    external = tmp_path / "external-manifest.json"
    external.write_bytes(manifest_path.read_bytes())
    manifest_path.unlink()
    manifest_path.symlink_to(external)
    with pytest.raises(vm.VMError, match="manifest cannot be a symlink"):
        backend.reset("customer-1")
    marker = backend.root / ".synthetic-beta-lab.json"
    external_marker = tmp_path / "marker.json"
    external_marker.write_bytes(marker.read_bytes())
    marker.unlink()
    marker.symlink_to(external_marker)
    with pytest.raises(vm.VMError, match="marker cannot be a symlink"):
        vm.VMBackend(backend.root)


def test_manifest_owner_and_overlay_path_enforced(lab):
    backend, _, _ = lab
    path = backend.root / "sessions/customer-1/vm.json"
    manifest = json.loads(path.read_text())
    manifest["owner"] = "different-lab"
    path.write_text(json.dumps(manifest))
    with pytest.raises(vm.VMError, match="ownership mismatch"):
        backend.reset("customer-1")
    manifest["owner"] = backend.owner
    manifest["overlay"] = "/tmp/unowned-image"
    path.write_text(json.dumps(manifest))
    with pytest.raises(vm.VMError, match="path identity"):
        backend.reset("customer-1")


def test_symlinked_overlay_and_session_are_rejected(lab, tmp_path):
    backend, _, _ = lab
    overlay = backend.root / "sessions/customer-1/disk.qcow2"
    external = tmp_path / "unowned.qcow2"
    external.write_text("preserve")
    overlay.unlink()
    overlay.symlink_to(external)
    with pytest.raises(vm.VMError, match="symlink"):
        backend.reset("customer-1")
    assert external.read_text() == "preserve"
    (backend.root / "sessions/redirect").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(vm.VMError, match="escapes"):
        backend.state("redirect")


def test_unknown_qmp_guest_cannot_be_stopped(lab, monkeypatch):
    backend, _, _ = lab
    monkeypatch.setattr(backend, "state", lambda _: {"live": True})
    called = []

    class OtherGuest:
        def __init__(self, *_):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def execute(self, command):
            called.append(command)
            return {"name": "another-customer"}

    monkeypatch.setattr(vm, "QMPClient", OtherGuest)
    with pytest.raises(vm.VMError, match="ownership mismatch"):
        backend.stop("customer-1")
    assert called == ["query-name"]


def test_screenshot_scope_and_input_operations_are_enforced(lab, tmp_path):
    backend, _, _ = lab
    with pytest.raises(vm.VMError, match="inside its owned session"):
        backend.screenshot("customer-1", tmp_path / "outside.ppm")
    with pytest.raises(vm.VMError, match="Unsupported visible input"):
        backend.input("customer-1", "host_shell", command="anything")


def test_start_cannot_override_owned_identity(lab):
    backend, _, _ = lab
    with pytest.raises(vm.VMError, match="cannot replace"):
        backend.start("customer-1", ["-qmp", "tcp:0:1"])


@pytest.mark.parametrize(
    "drive",
    [
        "file=/tmp/unowned,if=virtio,format=raw,readonly=on",
        "file=relative.img,if=virtio,format=raw,readonly=off",
        "file=relative.img,if=virtio,format=raw,readonly=on,cache=unsafe",
    ],
)
def test_start_rejects_unowned_or_writable_ancillary_drive(lab, drive):
    backend, _, _ = lab
    with pytest.raises(vm.VMError, match="Ancillary drive"):
        backend.start("customer-1", ["-drive", drive])


def test_dead_launcher_pid_cannot_borrow_reused_identity(lab, monkeypatch):
    backend, _, _ = lab
    path, manifest = backend._load("customer-1")
    manifest.update(pid=12345, pid_start="old-start-ticks")
    backend._save(path, manifest)
    monkeypatch.setattr(backend, "_pid_identity", lambda _: "new-start-ticks")
    assert backend.state("customer-1")["live"] is False
