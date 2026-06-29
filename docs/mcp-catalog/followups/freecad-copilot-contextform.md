# Investigate MCP Server: freecad-copilot-contextform

## Server ID

freecad-copilot-contextform

## Source URL

https://github.com/contextform/freecad-mcp

## Verification State

community_mcp

## Current Installability Tier

non_working

## Environment

ubuntu-linux-x64-container

## Observed Failure

The seeded command `npx freecad-mcp --help` failed because `freecad-mcp` is not published under that npm name.

The upstream README documents the installer package as `freecad-mcp-setup` and the actual MCP bridge as `working_bridge.py`, installed to `~/.freecad-mcp/working_bridge.py`.

Protocol validation without FreeCAD:

- `uv run --with mcp python working_bridge.py` initialized as server `freecad` version `2.0.0`.
- `tools/list` returned `check_freecad_connection` and `test_echo`.
- `check_freecad_connection` returned `FreeCAD not running. Please start FreeCAD and switch to AI Copilot workbench`.

Fuller Linux container validation:

- Cloned commit `de4fed2a7a4352fcb0de60d2b784063c54eeb812`.
- `freecad-mcp-setup` version `1.0.8` installed and passed `npm test`.
- Ubuntu apt did not provide a `freecad` package candidate.
- Installed FreeCAD 1.1.1 Linux x86_64 AppImage.
- Installed Xvfb and required X/GL libraries.
- Installed the workbench under FreeCAD's versioned user Mod path: `~/.local/share/FreeCAD/v1-1/Mod/AICopilot`.
- Launched FreeCAD under Xvfb.
- `/tmp/freecad_mcp.sock` appeared after 6 seconds.
- MCP initialized as serverInfo `freecad` version `2.0.0`.
- The bridge listed 7 tools: `check_freecad_connection`, `test_echo`, `partdesign_operations`, `part_operations`, `view_control`, `execute_python`, and `continue_selection`.
- `check_freecad_connection` returned `FreeCAD running with AI Copilot workbench`.
- `test_echo` returned `Bridge received: wright validation`.

The first safe backend operation did not complete:

```json
{
  "name": "part_operations",
  "arguments": {
    "operation": "box",
    "length": 10,
    "width": 8,
    "height": 6,
    "name": "WrightBox"
  }
}
```

The MCP bridge did not return a response before the 30 second timeout in the
latest clean-container run. An earlier run also hung until a 180 second timeout.

FreeCAD log excerpts:

```text
Event observer error: No module named 'PySide2'
QObject::setParent: Cannot set parent, new parent is in a different thread
QObject: Cannot create children for a parent that is in a different thread.
QObject::startTimer: Timers cannot be started from another thread
QObject::installEventFilter(): Cannot filter events for objects in a different thread.
QObject::startTimer: Timers can only be used with threads started with QThread
```

## Expected Behavior

Once FreeCAD and the AI Copilot workbench are running, `part_operations` should return promptly with either a successful box creation result or a clear structured failure.

## Missing Context Or Dependencies

No proprietary dependency is missing for this validation path. The failure occurred after FreeCAD 1.1.1 and the workbench socket were running under Xvfb.

## Suggested Next Action

Open upstream work to make the socket server execute GUI-affecting operations on FreeCAD's main GUI thread, or document that this MCP cannot support headless/Xvfb operation. Also update installer docs to mention the FreeCAD 1.1 versioned Mod path on Linux.

## GitHub PR/Issue URL

TBD
