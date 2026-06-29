# Investigate MCP Server: openscad-linter-trikos529

## Server ID

openscad-linter-trikos529

## Source URL

https://github.com/topics/cad-3d

## Verification State

user_reported_url_needed

## Current Installability Tier

non_working

## Environment

ubuntu-linux-x64-container

## Observed Failure

Clean Intel Ubuntu validation failed before MCP startup.

Command:

```bash
docker run --rm --platform linux/amd64 --entrypoint bash wright-agent:latest -lc "set -euxo pipefail; command -v uv; uv --version; timeout 60s uv tool run openscad-linter-mcp --help"
```

Output:

```text
/usr/local/bin/uv
uv 0.11.24 (x86_64-unknown-linux-musl)
No solution found when resolving tool dependencies:
Because openscad-linter-mcp was not found in the package registry and you require openscad-linter-mcp, we can conclude that your requirements are unsatisfiable.
```

Web search on 2026-06-26 did not find a specific `openscad-linter-mcp` repository or package. It only found other OpenSCAD MCP servers and the existing Quellant OpenSCAD Geometry server.

## Expected Behavior

The catalog entry should point at a specific MCP source repository or package that installs and completes a safe MCP initialization/tools-list probe, or remain non-working with a clear URL-needed reason.

## Missing Context Or Dependencies

Verified MCP source URL or package name.

## Suggested Next Action

Find the intended OpenSCAD linter MCP source, update `source_url` and `command`, then rerun clean Intel Ubuntu validation. If the intended server does not exist, remove or rename this seed entry so it does not imply a real installable MCP.

## GitHub PR/Issue URL

TBD
