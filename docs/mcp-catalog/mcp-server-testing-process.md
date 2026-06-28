# MCP Server Testing Process

This process is the required workflow for validating engineering MCP servers in
the Wright catalog. The goal is to prove the user workflow from a clean Wright
container to a selected MCP server, without preloading every possible CAD, CAM,
CAE, or vendor backend into the base image.

## Base Container Boundary

The base Docker image is a Wright runtime and validation harness. It may include
general Wright dependencies such as Python, Node.js, uv, Hermes, the Wright
plugin, the API, and the web build.

The base image must not include MCP-specific host software such as OpenSCAD,
FreeCAD, Blender, Rhino, SolidWorks, Fusion 360, OpenFOAM, CalculiX, vendor SDKs,
license managers, or hardware drivers unless that software is itself part of
Wright's core runtime.

## Per-MCP Validation Loop

For each MCP server, work in catalog order:

1. Start a clean Intel Linux Wright container.
2. Read and display the catalog metadata for the next MCP server: source URL,
   command, installability tier, host software, credentials, platform support,
   risk level, and existing validation notes.
3. Install only what is needed for that MCP server: the MCP package or
   repository, and any testable free/open host dependencies needed to start it.
4. Do not install expensive, proprietary, unavailable, unsafe, or hardware-bound
   dependencies. Instead, verify that the server installs or starts far enough to
   produce a clear diagnostic such as "FreeCAD not installed", "license
   required", "SolidWorks unavailable", or "credentials missing".
5. Run the standard MCP protocol probes: `initialize`,
   `notifications/initialized`, and `tools/list`.
6. Run at least one safe backend-touching tool call before marking an MCP as
   fully tested. Prefer read-only status checks first, then the smallest
   non-destructive execution probe that proves the backend is usable. Examples:
   `check_openscad`, exporting a tiny OpenSCAD cube to `/tmp`, or a CAD host
   status/no-op call. Do not run destructive CAD, CAM, robot, hardware, or
   manufacturing actions during catalog validation.
7. Verify the Wright/Hermes gateway layer when the MCP is expected to be usable
   by an agent. The Hermes-facing `wrightgateway` MCP must list the selected
   server's prefixed tools and successfully proxy at least one safe backend tool
   call.
8. Record what was learned on the MCP server entry: validation status, date,
   platform, dependency outcome, message, and evidence.
9. If the MCP has a problem that needs later engineering work, create a follow-up
   record under `docs/mcp-catalog/followups/` with the exact command,
   environment, observed output, and proposed next action. When GitHub
   credentials and branch policy are available, open a GitHub PR from that
   follow-up work.
10. Reset to a clean container state before moving to the next MCP server.

## Ordering Policy

Catalog entries must remain sorted as:

1. Fully tested MCP servers.
2. MCP servers that might work but need host software, credentials, licenses, or
   more evidence.
3. MCP servers that do not work and have follow-up records.

Blocked URL-needed, unsafe, or insufficiently sourced entries stay visible, but
automated install is disabled until the missing evidence is resolved.

## Required Problem Log

During validation, keep a running problem log with this format:

```text
Problem:
  <What failed, including command and platform.>
Solution:
  <What fixed it, or the current blocking reason if not fixed.>
Result:
  <Retested outcome and catalog/follow-up update.>
```

The current sprint log is `docs/mcp-catalog/testing-problem-log.md`.

## Required Setup Recipes

When a server has been attempted, add or update its setup recipe in
`docs/mcp-catalog/mcp-server-setup-recipes.md`. The recipe should include the
exact install command, selected-server backend dependencies, MCP launch command,
safe backend probes, and known version-specific traps. The problem log remains
the chronological record; the setup recipe is the reusable retest guide.
