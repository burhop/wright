# Investigate MCP Server: freecad-engineering-sandraschi

## Server ID

freecad-engineering-sandraschi

## Source URL

https://github.com/sandraschi/freecad-mcp

## Verification State

community_mcp

## Current Installability Tier

non_working

## Environment

ubuntu-linux-x64-container

## Observed Failure

Clean Intel Ubuntu validation installed FreeCAD 1.1.1 from the Linux x86_64 AppImage and installed `freecad-mcp` from the upstream GitHub repository.

The MCP server successfully:

- Cloned upstream commit `a71f60a71987ac23a65a3bdeda5f71c8f1579efb`.
- Installed with `uv sync --extra dev`.
- Passed upstream tests: 94 passed, 2 integration tests deselected.
- Initialized over stdio.
- Reported serverInfo `FreeCAD MCP` version `3.4.2`.
- Listed 47 tools.

Backend evidence:

- `/tmp/freecadcmd --version` reported `FreeCAD 1.1.1 Revision: 20260414`.
- A direct FreeCAD CLI command created `/tmp/direct_freecad_box.stl` at 684 bytes.

MCP failures:

- `freecad_status` returned `success:false`, `freecad_ok:false`, and `version:null` even when `FREECAD_PATH=/tmp/freecadcmd` was provided.
- Starting MCP with the advertised `--freecad-path /tmp/freecadcmd` did not affect the subprocess path; `create_shape` returned `FreeCADCmd not found`.
- Starting MCP with `FREECAD_PATH=/tmp/freecadcmd` did run FreeCAD, but `create_shape` with a 10 mm box returned `success:true` while the tool payload included stderr: `Exception while processing file: /tmp/fc_3_xf1gse.py [Cannot create a mesh out of a 'Part.Solid']`.
- No `wright_mcp_box_env.stl` was produced by the MCP call.

## Reproduction Commands

```bash
FREECAD_PATH=/tmp/freecadcmd uv run python -m freecad_mcp.server --mode stdio
```

The advertised CLI option also reproduces a separate path issue:

```bash
uv run python -m freecad_mcp.server --mode stdio --freecad-path /tmp/freecadcmd
```

With that launch path, `create_shape` returns `FreeCADCmd not found`.

MCP call:

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "create_shape",
    "arguments": {
      "shape_type": "box",
      "params": {"width": 10, "height": 10, "depth": 10},
      "output_name": "wright_validation_box.stl"
    }
  }
}
```

Direct FreeCAD CLI control that succeeded:

```bash
/tmp/freecadcmd -c "import FreeCAD, Part, Mesh, os; doc=FreeCAD.newDocument('WrightValidation'); obj=doc.addObject('Part::Box','Box'); obj.Length=10; obj.Width=10; obj.Height=10; doc.recompute(); Mesh.export([obj], '/tmp/direct_freecad_box.stl'); print(os.path.getsize('/tmp/direct_freecad_box.stl'))"
```

## Expected Behavior

`freecad_status` should report the configured FreeCAD executable as available, and `create_shape` should either produce an STL file or return `success:false` with a clear error. It should not return `success:true` when no output file was created.

## Missing Context Or Dependencies

None for this validation path. FreeCAD 1.1.1 was installed and directly exported an STL successfully.

## Suggested Next Action

Open an upstream fix to update `create_shape` mesh export for FreeCAD 1.1.1 and to make status/output validation authoritative. Candidate fix areas:

- Use a FreeCAD 1.1.1-compatible mesh export path, such as creating a document object and calling `Mesh.export`.
- Verify `output_name` exists and has nonzero size before returning success.
- Make `freecad_status` probe `FREECAD_PATH` directly when bridge state has not been initialized.

## GitHub PR/Issue URL

TBD
