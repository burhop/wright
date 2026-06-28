# Investigate MCP Server: kicad-mcp-lamaalrajih

## Server ID

kicad-mcp-lamaalrajih

## Source URL

https://github.com/lamaalrajih/kicad-mcp

## Verification State

community_mcp

## Current Installability Tier

non_working

## Environment

ubuntu-linux-x64-container

## Observed Failure

Clean Intel Ubuntu validation used repository commit
`98c9ea41cb393393a8bafd157a93e84431e00afb`.

The installable GitHub package command starts the MCP server:

```bash
uv tool run --from git+https://github.com/lamaalrajih/kicad-mcp.git kicad-mcp
```

The README/catalog launch path is not reliable on this checkout:

```bash
uv run python main.py
```

That path starts FastMCP and then raises:

```text
ValueError: a coroutine was expected, got None
```

Protocol validation results:

- `initialize` succeeded with serverInfo `KiCad` version `1.11.0`.
- `tools/list` returned 16 tools.
- `list_projects` found a sample project at
  `/tmp/kicad-projects/WrightBoard/WrightBoard.kicad_pro`.
- `get_project_structure` returned the sample `.kicad_pro`, `.kicad_pcb`, and
  `.kicad_sch` files.

However, 11 of the 16 advertised tools expose `ctx` as a required input
property:

- `generate_pcb_thumbnail`
- `generate_project_thumbnail`
- `run_drc_check`
- `analyze_bom`
- `export_bom_csv`
- `extract_schematic_netlist`
- `extract_project_netlist`
- `analyze_schematic_connections`
- `find_component_connections`
- `identify_circuit_patterns`
- `analyze_project_circuit_patterns`

A normal MCP client call to `run_drc_check` failed before KiCad CLI execution:

```json
{
  "name": "run_drc_check",
  "arguments": {
    "project_path": "/tmp/kicad-projects/WrightBoard/WrightBoard.kicad_pro"
  }
}
```

Result:

```text
Input validation error: 'ctx' is a required property
```

Upstream tests:

- `uv run pytest -q` executed 37 tests and skipped 2, then failed the configured
  80% coverage gate with total coverage of 10.04%.
- `uv run pytest -q --no-cov` passed: 37 passed, 2 skipped.

Backend dependency note:

- Ubuntu 24.04 default apt offers KiCad 7.0.11.
- Upstream README requires KiCad 9.0+.
- Full KiCad CLI validation was not attempted because the MCP tool schema fails
  before the DRC/BOM/netlist tools can reach `kicad-cli`.

## Expected Behavior

Tools that receive FastMCP context should not expose `ctx` as a required user
input property. A normal MCP client should be able to call tools such as
`run_drc_check` with only documented user arguments.

The documented local launch path should either run the MCP server cleanly or be
updated to the package console script.

## Missing Context Or Dependencies

KiCad 9.0+ is not available from the default Ubuntu 24.04 apt repository. This
is still a backend dependency to validate after the MCP schema issue is fixed.

## Suggested Next Action

Open upstream work to hide/inject the FastMCP `ctx` parameter for tools that use
context, update README launch instructions to prefer the `kicad-mcp` console
script, and adjust the default test command or add enough tests to satisfy the
configured coverage gate.

## GitHub PR/Issue URL

TBD
