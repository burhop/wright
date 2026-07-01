# Contract: MCP Validation Plan And Evidence

## Purpose

Validation must distinguish fast metadata preflight from full clean-container evidence.

## ValidationPlan

Required fields:

```text
server_id
environment
preflight
install_steps
protocol_probes
safe_backend_probe
gateway_probe
requires_docker
requires_network
requires_credentials
```

Required protocol probes:

- `initialize`
- `notifications/initialized`
- `tools/list`

Optional probe:

- one safe backend-touching tool call when possible

Gateway probe:

- `tools/list` through Wright gateway
- one safe proxied backend call when possible

## ValidationEvidence

Required fields:

```text
server_id
environment
status
steps
diagnostics
missing_dependencies
follow_up_url
```

Secret-like values must be redacted before evidence is written to human-readable follow-ups.

## Fast-Suite Boundary

Default tests may generate plans and run lightweight local mock probes. They must not require Docker, network, credentials, proprietary software, package registries, or hardware-bound tools.

## Required Tests

- Blocked metadata preflight produces blocked plan/evidence.
- Missing host dependency remains dependency-missing preflight.
- Passed seed metadata remains classified but is not confused with newly executed clean-container evidence.
- Lightweight mock MCP server path exercises initialize, initialized notification, tools/list, and a safe tool call without Docker.

