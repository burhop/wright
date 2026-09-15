from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tool_registry.native_application_blender import (
    BlenderFileChannel,
    BlenderLifecycleError,
    BlenderNativeApplicationAdapter,
)
from tool_registry.native_application_blender_host import LifecycleHost


IDENTITY = {
    "pid": 123,
    "creation_time": "2026-09-13T01:00:00Z",
    "executable": "C:/Blender/blender.exe",
}


def environment(tmp_path, monkeypatch):
    profile = str(tmp_path / "profile")
    monkeypatch.setenv("BLENDER_USER_CONFIG", profile)
    monkeypatch.setenv("BLENDER_MCP_SAFE_MODE", "true")
    scene = {}
    data = SimpleNamespace(filepath="", is_dirty=False, objects=[])
    calls = []

    def reset(**kwargs):
        calls.append("reset")
        data.filepath = ""
        data.is_dirty = False
        data.objects.clear()
        scene.clear()
        return {"FINISHED"}

    def save(filepath, **kwargs):
        calls.append("save")
        Path(filepath).write_bytes(b"BLENDER-fake-only-unit-test")
        data.filepath = filepath
        data.is_dirty = False
        return {"FINISHED"}

    bpy = SimpleNamespace(
        app=SimpleNamespace(
            background=False,
            version_string="4.5.10 LTS",
            is_job_running=lambda _: False,
        ),
        data=data,
        context=SimpleNamespace(
            scene=scene,
            window_manager=SimpleNamespace(windows=[]),
            preferences=SimpleNamespace(
                view=SimpleNamespace(show_splash=False),
                filepaths=SimpleNamespace(use_scripts_auto_execute=False),
            ),
        ),
        ops=SimpleNamespace(
            wm=SimpleNamespace(read_factory_settings=reset, save_as_mainfile=save)
        ),
    )
    config = {
        "native_session_id": "blender-test",
        "profile_path": profile,
        "allowed_roots": [str(tmp_path)],
    }
    host = LifecycleHost(config, bpy_module=bpy)
    return host, bpy, calls


def test_static_bootstrap_enables_exact_pinned_addon_on_dedicated_port(
    tmp_path, monkeypatch
):
    host, bpy, calls = environment(tmp_path, monkeypatch)
    scripts = tmp_path / "scripts"
    source = scripts / "addons" / "blender_mcp.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"# exact pinned addon\n")
    monkeypatch.setenv("BLENDER_USER_SCRIPTS", str(scripts))

    class Server:
        def __init__(self, *, host, port):
            self.host, self.port, self.running = host, port, False

        def start(self):
            self.running = True

    bpy.types = SimpleNamespace()
    addon = SimpleNamespace(BlenderMCPServer=Server)

    def register():
        bpy.types.blendermcp_server = addon.BlenderMCPServer(port=9876)
        bpy.types.blendermcp_server.start()

    addon.register = register
    host.config["addon"] = {
        "module": "blender_mcp",
        "host": "127.0.0.1",
        "port": 31337,
        "source_path": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }

    assert host.enable_pinned_addon(addon) == {
        "kind": "blender_mcp_socket",
        "host": "127.0.0.1",
        "port": 31337,
        "addon_sha256": host.config["addon"]["source_sha256"],
    }
    assert bpy.types.blendermcp_server.running is True
    assert addon.BlenderMCPServer is Server
    assert calls == ["reset"]


def test_static_bootstrap_rejects_addon_hash_change_before_enable(
    tmp_path, monkeypatch
):
    host, bpy, calls = environment(tmp_path, monkeypatch)
    scripts = tmp_path / "scripts"
    source = scripts / "addons" / "blender_mcp.py"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"changed")
    monkeypatch.setenv("BLENDER_USER_SCRIPTS", str(scripts))
    host.config["addon"] = {
        "module": "blender_mcp",
        "host": "127.0.0.1",
        "port": 31337,
        "source_path": str(source),
        "source_sha256": "0" * 64,
    }

    with pytest.raises(RuntimeError, match="hash changed"):
        host.enable_pinned_addon(
            SimpleNamespace(BlenderMCPServer=lambda **_: pytest.fail("must not enable"))
        )
    assert calls == ["reset"]


def request(host, action, **payload):
    return host.operation(action, {"native_session_id": "blender-test", **payload})


def test_owned_scene_must_be_saved_before_close_then_graceful_quit(
    tmp_path, monkeypatch
):
    host, bpy, calls = environment(tmp_path, monkeypatch)
    assert request(host, "inspect")["documents"] == []
    request(host, "create_document", native_id="owned-blank")
    with pytest.raises(RuntimeError, match="dirty"):
        request(host, "close_document", native_id="owned-blank", current_path=None)
    with pytest.raises(RuntimeError, match="open or untracked"):
        request(host, "quit")
    saved = request(
        host,
        "save_document",
        native_id="owned-blank",
        current_path=None,
        path=str(tmp_path / "recovery.blend"),
    )
    assert saved["saved"] and len(saved["sha256"]) == 64
    assert request(
        host, "close_document", native_id="owned-blank", current_path=saved["path"]
    )["closed"]
    assert request(host, "inspect")["documents"] == []
    assert request(host, "quit")["quit_requested"]
    assert calls == ["reset", "save", "reset"]


@pytest.mark.parametrize("change", ["identity", "path"])
def test_scene_identity_or_path_replacement_is_preserved(tmp_path, monkeypatch, change):
    host, bpy, calls = environment(tmp_path, monkeypatch)
    request(host, "create_document", native_id="owned")
    if change == "identity":
        bpy.context.scene["wright_lifecycle_document"] = "user-work"
    else:
        bpy.data.filepath = str(tmp_path / "different.blend")
    with pytest.raises(RuntimeError, match="identity/path changed"):
        request(
            host,
            "save_document",
            native_id="owned",
            current_path=None,
            path=str(tmp_path / "recovery.blend"),
        )
    assert calls == ["reset"]


def test_untracked_and_existing_files_and_outside_paths_are_not_overwritten(
    tmp_path, monkeypatch
):
    host, bpy, calls = environment(tmp_path, monkeypatch)
    bpy.data.objects.append("user-object")
    with pytest.raises(RuntimeError, match="empty dedicated"):
        request(host, "create_document", native_id="owned")
    with pytest.raises(RuntimeError, match="untracked"):
        request(host, "quit")
    bpy.data.objects.clear()
    request(host, "create_document", native_id="owned")
    existing = tmp_path / "prior.blend"
    existing.write_bytes(b"prior evidence")
    with pytest.raises(RuntimeError, match="overwrite"):
        request(
            host,
            "save_document",
            native_id="owned",
            current_path=None,
            path=str(existing),
        )
    with pytest.raises(RuntimeError, match="outside approved"):
        request(
            host,
            "save_document",
            native_id="owned",
            current_path=None,
            path=str(tmp_path.parent / "outside.blend"),
        )
    assert existing.read_bytes() == b"prior evidence"
    assert calls == ["reset"]


def test_safe_mode_and_fixed_operation_allowlist_are_mandatory(tmp_path, monkeypatch):
    host, bpy, calls = environment(tmp_path, monkeypatch)
    for action in (
        "eval",
        "execute_code",
        "install_addon",
        "disable_safe_mode",
        "print",
    ):
        with pytest.raises(RuntimeError, match="Unsupported fixed"):
            request(host, action, code="raise Exception('never evaluated')")
    monkeypatch.setenv("BLENDER_MCP_SAFE_MODE", "false")
    with pytest.raises(RuntimeError, match="safe mode"):
        LifecycleHost(host.config, bpy_module=bpy)
    assert calls == ["reset"]


def test_native_dirty_flag_and_modal_jobs_are_never_hidden(tmp_path, monkeypatch):
    host, bpy, _ = environment(tmp_path, monkeypatch)
    request(host, "create_document", native_id="owned")
    saved = request(
        host,
        "save_document",
        native_id="owned",
        current_path=None,
        path=str(tmp_path / "recovery.blend"),
    )
    # A post-save native change must still block close, regardless of the
    # helper's own unsaved bookkeeping or a successful file receipt.
    bpy.data.is_dirty = True
    assert request(host, "inspect")["documents"][0]["dirty"] is True
    with pytest.raises(RuntimeError, match="dirty"):
        request(host, "close_document", native_id="owned", current_path=saved["path"])
    bpy.context.window_manager.windows = [SimpleNamespace(modal_operators=["modal-op"])]
    assert request(host, "inspect")["modal"] is True
    assert request(host, "inspect")["healthy"] is False
    bpy.context.window_manager.windows = []
    bpy.app.is_job_running = lambda _: True
    assert request(host, "inspect")["active_operation"] is True


def test_background_loop_is_rejected_before_native_factory_reset(tmp_path, monkeypatch):
    host, bpy, calls = environment(tmp_path, monkeypatch)
    bpy.app.background = True
    with pytest.raises(RuntimeError, match="normal event loop"):
        LifecycleHost(host.config, bpy_module=bpy)
    assert calls == ["reset"]


def test_timed_out_mutation_remains_quarantined_after_adapter_restart(tmp_path):
    (tmp_path / "requests").mkdir()
    (tmp_path / "responses").mkdir()
    channel = BlenderFileChannel(tmp_path)
    with pytest.raises(BlenderLifecycleError, match="outcome remains unknown"):
        channel.request("save_document", {"native_session_id": "test"}, 0.01)
    restored = BlenderFileChannel(tmp_path)
    with pytest.raises(BlenderLifecycleError, match="quarantined"):
        restored.request("quit", {"native_session_id": "test"}, 0.01)
    assert len(list((tmp_path / "requests").glob("*.json"))) == 1
    assert json.loads((tmp_path / "channel-state.json").read_text())["unresolved"]


@pytest.mark.parametrize("action", ["create", "save", "close", "quit"])
def test_borrowed_application_never_reaches_mutating_channel(tmp_path, action):
    adapter = BlenderNativeApplicationAdapter(
        allowed_roots=(tmp_path,),
        identity_reader=lambda _: pytest.fail("No native attachment"),
    )
    session = {"identity": IDENTITY, "ownership": "borrowed"}
    document = {
        "ownership": "owned",
        "native_id": "owned",
        "recovery_path": str(tmp_path / "recovery.blend"),
    }
    operation = {
        "create": lambda: adapter.create_document(session, "owned"),
        "save": lambda: adapter.save_document(session, document),
        "close": lambda: adapter.close_document(session, document),
        "quit": lambda: adapter.quit_application(session),
    }[action]
    with pytest.raises(BlenderLifecycleError, match="dedicated owned"):
        operation()


def test_pid_reuse_is_refused_before_any_file_channel_request(tmp_path):
    adapter = BlenderNativeApplicationAdapter(
        allowed_roots=(tmp_path,),
        identity_reader=lambda _: {**IDENTITY, "creation_time": "different creation"},
    )
    with pytest.raises(BlenderLifecycleError, match="identity changed"):
        adapter.inspect({"identity": IDENTITY})


def test_endpoint_identity_and_safe_mode_mismatch_are_refused(tmp_path):
    control = tmp_path / "control"
    control.mkdir()
    profile = str(tmp_path / "profile")
    config = {"native_session_id": "expected", "profile_path": profile}
    (control / "config.json").write_text(json.dumps(config))
    (control / "ready.json").write_text(
        json.dumps({**config, "pid": 999, "safe_mode": True})
    )
    adapter = BlenderNativeApplicationAdapter(
        allowed_roots=(tmp_path,),
        identity_reader=lambda _: IDENTITY,
        channel_factory=lambda _: pytest.fail("Mismatched endpoint must not be called"),
    )
    with pytest.raises(BlenderLifecycleError, match="ownership is unresolved"):
        adapter.inspect(
            {
                "identity": IDENTITY,
                "endpoint": {"directory": str(control)},
                "profile_path": profile,
                "native_session_id": "expected",
            }
        )


def test_exited_process_reports_endpoint_not_alive_without_loading_control_files():
    adapter = BlenderNativeApplicationAdapter(identity_reader=lambda _: None)
    assert adapter.inspect({"identity": IDENTITY}) == {
        "alive": False,
        "endpoint_alive": False,
        "identity": None,
    }
