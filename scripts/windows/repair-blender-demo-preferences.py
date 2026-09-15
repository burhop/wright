"""Repair only the running demo Blender host's configuration, without scene edits."""

import json
from pathlib import Path
import socket


root = Path(__file__).resolve().parents[2]
config = root / ".local-run/feature-081-live/tools/blender-user/config"
config.mkdir(parents=True, exist_ok=True)
code = (
    "import os, json\n"
    f"os.environ['BLENDER_USER_CONFIG'] = {str(config)!r}\n"
    "bpy.context.preferences.view.show_splash = False\n"
    "saved = bpy.ops.wm.save_userpref()\n"
    "print(json.dumps({'saved': sorted(saved), 'config': bpy.utils.user_resource('CONFIG')}))\n"
)
with socket.create_connection(("127.0.0.1", 9876), timeout=30) as connection:
    connection.sendall(json.dumps({"type": "execute_code", "params": {"code": code}}).encode())
    raw = b""
    while len(raw) < 2_000_000:
        block = connection.recv(65536)
        if not block:
            raise RuntimeError("Blender closed the maintenance connection without a response")
        raw += block
        try:
            response = json.loads(raw)
            break
        except json.JSONDecodeError:
            continue
    else:
        raise RuntimeError("Blender maintenance response exceeded its limit")
if response.get("status") != "success":
    raise RuntimeError(response)
preferences = config / "userpref.blend"
if not preferences.is_file() or not preferences.read_bytes().startswith(b"BLENDER"):
    raise RuntimeError("Blender did not publish a valid preferences file in the demo configuration")
print(json.dumps({"status": "saved", "preferences": str(preferences), "size_bytes": preferences.stat().st_size,
                  "scene_modified": False, "blender_response": response}))
