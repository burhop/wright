"""Enable the pinned Blender MCP add-on for a hidden local Blender host."""

import bpy

bpy.context.preferences.view.show_splash = False
saved = bpy.ops.wm.save_userpref()
if "FINISHED" not in saved:
    raise RuntimeError("The isolated Blender configuration could not be saved")

result = bpy.ops.preferences.addon_enable(module="blender_mcp")
if "FINISHED" not in result:
    raise RuntimeError(f"Could not enable blender_mcp: {sorted(result)}")

print("Wright Blender MCP host enabled on 127.0.0.1:9876", flush=True)
