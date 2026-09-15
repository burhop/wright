"""Trusted static lifecycle helper loaded only into a fresh owned Blender.

File IPC has five fixed operations. There is no eval, exec, arbitrary code,
addon installation operation, printer access or configurable Python operation.
At process startup only, this trusted helper may verify and enable one pinned
add-on copied into the session's isolated script directory.
"""

import hashlib
import json
import os
import sys
from pathlib import Path


def write_json(path, value):
    temporary = path.with_name(path.name + ".next")
    temporary.write_text(json.dumps(value), encoding="utf-8")
    temporary.replace(path)


class LifecycleHost:
    def __init__(self, config, *, bpy_module=None):
        if bpy_module is None:
            import bpy as bpy_module
        bpy = self.bpy = bpy_module
        self.config = config
        self.document_id = None
        self.unsaved = False
        if os.environ.get("BLENDER_MCP_SAFE_MODE", "").lower() not in {"1", "true"}:
            raise RuntimeError("Blender safe mode must remain enabled")
        if (
            str(Path(os.environ["BLENDER_USER_CONFIG"]).resolve())
            != config["profile_path"]
        ):
            raise RuntimeError("Dedicated Blender profile does not match")
        if bpy.app.background:
            raise RuntimeError(
                "Lifecycle file notifications require Blender's normal event loop"
            )
        # Only this fresh --factory-startup process is reset. No .blend file is
        # accepted on the command line and no existing process is attached.
        result = bpy.ops.wm.read_factory_settings(use_empty=True)
        if "FINISHED" not in result:
            raise RuntimeError("Dedicated blank Blender state was not established")
        bpy.context.preferences.view.show_splash = False
        bpy.context.preferences.filepaths.use_scripts_auto_execute = False

    def enable_pinned_addon(self, addon_module=None):
        addon = self.config.get("addon")
        if addon is None:
            return None
        if not isinstance(addon, dict) or addon.get("module") != "blender_mcp":
            raise RuntimeError("Dedicated Blender add-on identity is invalid")
        port = addon.get("port")
        if (
            addon.get("host") != "127.0.0.1"
            or type(port) is not int
            or not 1024 <= port <= 65535
        ):
            raise RuntimeError(
                "Dedicated Blender add-on endpoint must be loopback and bounded"
            )
        expected = (
            Path(os.environ["BLENDER_USER_SCRIPTS"]).resolve()
            / "addons"
            / "blender_mcp.py"
        )
        source = Path(addon.get("source_path", "")).resolve()
        if source != expected or not source.is_file():
            raise RuntimeError("Dedicated Blender add-on source path is invalid")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != addon.get("source_sha256"):
            raise RuntimeError("Dedicated Blender add-on source hash changed")
        if addon_module is None:
            import importlib.util

            spec = importlib.util.spec_from_file_location(addon["module"], source)
            if spec is None or spec.loader is None:
                raise RuntimeError("Dedicated Blender add-on could not be loaded")
            addon_module = importlib.util.module_from_spec(spec)
            sys.modules[addon["module"]] = addon_module
            try:
                spec.loader.exec_module(addon_module)
            except BaseException:
                sys.modules.pop(addon["module"], None)
                raise
        # Run the pin's own registration so every RNA property its command
        # dispatcher reads exists.  Replace only its constructor reference
        # while registration runs: the pinned source still supplies the exact
        # server implementation, but cannot fall back to its global 9876 port.
        server_type = addon_module.BlenderMCPServer

        def dedicated_server(*_args, **_kwargs):
            return server_type(host="127.0.0.1", port=port)

        addon_module.BlenderMCPServer = dedicated_server
        try:
            addon_module.register()
        finally:
            addon_module.BlenderMCPServer = server_type
        server = getattr(self.bpy.types, "blendermcp_server", None)
        if (
            server is None
            or not server.running
            or server.port != port
            or server.host not in {"localhost", "127.0.0.1"}
        ):
            raise RuntimeError("Dedicated Blender add-on endpoint identity is invalid")
        return {
            "kind": "blender_mcp_socket",
            "host": "127.0.0.1",
            "port": port,
            "addon_sha256": digest,
        }

    def document(self):
        bpy = self.bpy
        path = bpy.data.filepath or None
        current_id = bpy.context.scene.get("wright_lifecycle_document")
        if (
            self.document_id is None
            and path is None
            and not len(bpy.data.objects)
            and current_id is None
        ):
            return None
        return {
            "native_id": current_id or "untracked_blender_file",
            "path": path,
            "dirty": bool(bpy.data.is_dirty or self.unsaved),
        }

    def verify_document(self, payload):
        document = self.document()
        if (
            document is None
            or document["native_id"] != self.document_id
            or self.document_id != payload.get("native_id")
            or document["path"] != payload.get("current_path")
        ):
            raise RuntimeError(
                "Blender document identity/path changed; native mutation refused"
            )
        return document

    def operation(self, action, payload):
        bpy = self.bpy
        if payload.get("native_session_id") != self.config["native_session_id"]:
            raise RuntimeError("Blender request belongs to a different native session")
        if action == "inspect":
            document = self.document()
            modal = any(
                bool(window.modal_operators)
                for window in bpy.context.window_manager.windows
            )
            active = any(
                bpy.app.is_job_running(kind) for kind in ("RENDER", "OBJECT_BAKE")
            )
            return {
                "native_session_id": self.config["native_session_id"],
                "version": bpy.app.version_string,
                "healthy": not modal and not active,
                "modal": modal,
                "document_state_known": True,
                "active_operation": active,
                "documents": [document] if document else [],
            }
        if action == "create_document":
            if (
                self.document() is not None
                or not isinstance(payload.get("native_id"), str)
                or not payload["native_id"]
            ):
                raise RuntimeError(
                    "A new Blender document requires an empty dedicated application"
                )
            self.document_id = payload["native_id"]
            bpy.context.scene["wright_lifecycle_document"] = self.document_id
            self.unsaved = True
            return {
                "created": True,
                "native_id": self.document_id,
                "path": None,
                "dirty": True,
            }
        if action == "save_document":
            self.verify_document(payload)
            target = Path(payload["path"]).resolve()
            roots = [Path(root).resolve() for root in self.config["allowed_roots"]]
            if target.suffix.lower() != ".blend" or not any(
                target.is_relative_to(root) and target != root for root in roots
            ):
                raise RuntimeError("Blender recovery path is outside approved roots")
            if target.exists() and str(target) != bpy.data.filepath:
                raise RuntimeError(
                    "Blender recovery cannot overwrite another existing file"
                )
            target.parent.mkdir(parents=True, exist_ok=True)
            result = bpy.ops.wm.save_as_mainfile(
                filepath=str(target), check_existing=False
            )
            if (
                "FINISHED" not in result
                or not target.is_file()
                or target.stat().st_size == 0
            ):
                raise RuntimeError(
                    "Blender recovery save did not establish a nonempty file"
                )
            self.unsaved = False
            # Return to Blender's event loop after this request so its normal
            # save notification clears the WM dirty flag. The manager inspects
            # it afresh before issuing close; this helper never clears the flag.
            return {
                "saved": True,
                "path": str(target),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            }
        if action == "close_document":
            document = self.verify_document(payload)
            if document["dirty"]:
                raise RuntimeError("Blender document is dirty; save before closing")
            result = bpy.ops.wm.read_factory_settings(use_empty=True)
            if "FINISHED" not in result:
                raise RuntimeError("Blender document did not close")
            self.document_id = None
            self.unsaved = False
            return {"closed": True}
        if action == "quit":
            if self.document() is not None:
                raise RuntimeError(
                    "Blender application still contains an open or untracked document"
                )
            return {"quit_requested": True}
        raise RuntimeError("Unsupported fixed Blender lifecycle operation")


def hide_owned_windows():
    if os.name != "nt":
        return
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def hide(window, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(window, ctypes.byref(owner))
        if owner.value == os.getpid():
            user32.ShowWindow(window, 0)
        return True

    user32.EnumWindows(hide, 0)


def main():
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    if len(arguments) != 1:
        raise RuntimeError("Exactly one dedicated lifecycle configuration is required")
    config_path = Path(arguments[0]).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    directory = config_path.parent
    host = LifecycleHost(config)
    mesh_endpoint = host.enable_pinned_addon()
    write_json(
        directory / "ready.json",
        {
            "pid": os.getpid(),
            "native_session_id": config["native_session_id"],
            "version": host.bpy.app.version_string,
            "profile_path": config["profile_path"],
            "safe_mode": True,
            "mesh_endpoint": mesh_endpoint,
        },
    )

    def poll():
        hide_owned_windows()
        for path in sorted((directory / "requests").glob("*.json")):
            response_path = directory / "responses" / path.name
            if response_path.exists():
                continue
            action = None
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                if payload.get("id") != path.stem:
                    raise RuntimeError("Request identity differs from its filename")
                action = payload.get("action")
                result = host.operation(action, payload)
                response = {
                    "id": path.stem,
                    "native_session_id": config["native_session_id"],
                    "result": result,
                }
            except Exception as error:
                response = {
                    "id": path.stem,
                    "native_session_id": config["native_session_id"],
                    "error": f"{type(error).__name__}: {error}",
                }
            write_json(response_path, response)
            if action == "quit" and "error" not in response:
                host.bpy.ops.wm.quit_blender()
                return None
            # Process one request per callback, allowing Blender's native
            # save/load notification queue to run before the next inspection.
            break
        return 0.1

    hide_owned_windows()
    host.bpy.app.timers.register(poll, first_interval=0.1, persistent=True)


if __name__ == "__main__":
    main()
