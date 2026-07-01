# Contract: Agent Runtime Registry

## Purpose

The API must select active agent engines through an agent-neutral registry/factory boundary. Hermes remains the default provider and must keep existing behavior.

## Provider Contract

Required provider metadata:

```text
name: lowercase unique runtime identifier
display_name: user-facing label
description: short runtime description
is_default: true for Hermes unless explicitly changed later
supported: true only when an engine factory can create a usable runtime
health_capabilities: supported health checks for this provider
gateway_profile: optional Wright gateway profile
factory: callable that returns a BaseAgentEngine
```

## Selection Rules

- Missing or blank active runtime resolves to the default provider.
- `hermes` resolves to the Hermes provider.
- Unknown runtime names raise a typed unsupported-runtime error.
- Known but unimplemented future runtime names may be exposed as metadata only if selection rejects them safely.
- API boot must not import `HermesAdapter` directly.

## API Compatibility

Existing response shapes stay unchanged:

```json
{"state":"connected","latencyMs":1.5,"baseUrl":"http://127.0.0.1:8642","error":null}
```

```json
{"agent":"hermes"}
```

Unsupported runtime handling must preserve current setup behavior unless explicitly approved.

## Required Tests

- Default runtime resolves to Hermes.
- Explicit Hermes selection resolves to Hermes.
- Unsupported runtime is rejected.
- API import/startup does not instantiate Hermes directly outside the registry.
- Agent health and inference health retain response fields.

