# Data Model: FreeCAD MCP Server Integration

This feature utilizes the existing tool registry schema to store the new server configuration and its queried tools.

## Seeding Catalog Entry

The database migration seeds the `mcp_servers` table with a stable entry for the FreeCAD MCP gateway.

### Entity Attributes (`mcp_servers`)

- **`server_id`**: `freecad-engineering-sandraschi`
- **`name`**: `FreeCAD Engineering`
- **`type`**: `stdio`
- **`command`**: `["uvx", "freecad-mcp"]`
- **`is_active`**: `0` (False by default, toggled to `1` on active session configuration)
- **`is_installed`**: `0` (False by default, marked as `1` when user clicks "Install" / "Connect")
- **`status`**: `inactive`
- **`category`**: `cad`
- **`image_url`**: `https://avatars.githubusercontent.com/u/1413352?s=64`
- **`description`**: `End-to-end engineering pipeline: FreeCAD geometric kernel connected to OpenFOAM CFD, CalculiX FEA, and PrusaSlicer for automated 3D-print G-code generation.`
- **`source_url`**: `https://github.com/sandraschi/freecad-mcp`

## Discovered Tools (`mcp_tools`)

Upon installation and server startup, the following key tools are discovered and populated into the `mcp_tools` table (referencing `server_id = "freecad-engineering-sandraschi"`):

- **`freecad_status`**: Reads FreeCAD version and availability (`bridge_mode` check).
- **`step_to_stl`**: Converts `.step` or `.stp` files in the upload directory to `.stl` meshes.
- **`model_info`**: Reads bounding box and volume diagnostics.
- **`create_shape`**: Generates box, cylinder, sphere, or cone primitives.
- **`slicer_status`**: Detects PrusaSlicer version.
- **`slice_stl`**: Generates 3D print G-code from an STL file.
- **`mesh_to_solid`**: Extrudes STL meshes to solid BREP.
- **`cfd_status`**: Detects OpenFOAM CFD solver container availability.
- **`fem_status`**: Detects CalculiX FEA solver availability.
