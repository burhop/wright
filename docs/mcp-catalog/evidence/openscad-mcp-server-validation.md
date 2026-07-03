# MCP Validation Evidence: openscad-mcp-server

- Result: partial
- Environment: windows_11_x64
- Container: wright:latest
- Follow-up required: True

## Diagnostics

Direct MCP stdio probes completed in a clean container. Direct clean-container protocol probes ran, but Wright gateway proxy probes were not executed.

## Steps

- docker.clean_container: passed
- initialize: passed
- notifications/initialized: passed
- tools/list: passed

## Redactions

- credentials
- environment
- commands
- subprocess_output
