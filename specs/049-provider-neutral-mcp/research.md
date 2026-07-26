# Research: Provider-Neutral MCP Integration

## Decision: Use one exact trusted workspace placeholder

- **Decision**: Support the exact token `{workspace.path}` in trusted command-array elements and non-secret launch environment values. Canonicalize the bound workspace once, replace tokens literally, reject every unknown placeholder, and prohibit workspace placeholders in string commands.
- **Rationale**: This preserves server independence and supports both command-line and legacy environment contracts while avoiding shell interpolation and provider detection.
- **Alternatives considered**: MCP Roots are deprecated and informational rather than authorization; per-provider adapters recreate the coupling; injecting a universal Wright environment variable would force every server to know Wright.

## Decision: Store launch environment separately from credentials

- **Decision**: Add `launch_env` as trusted non-secret server configuration while retaining `env_vars` definitions and the existing secrets provider for credentials.
- **Rationale**: Template-bearing configuration must be inspectable and reviewable, whereas credentials must stay encrypted/redacted and must never be interpolated into diagnostics.
- **Alternatives considered**: Reusing the legacy `env_vars` dictionary conflates secrets, metadata, and launch values; a new integration plugin is unnecessary.

## Decision: Preserve complete advertised tool metadata

- **Decision**: Cache tool title, description, input schema, output schema, and standard annotations exactly as advertised. Store trusted Wright approval requirements separately and apply them in policy without treating server annotations as grants.
- **Rationale**: Agents can operate from the server contract only if Wright does not discard it. Security depends on distinguishing descriptive server claims from locally trusted policy.
- **Alternatives considered**: Rebuilding output schemas and annotations from server-level risk loses information; trusting server annotations would permit privilege self-assertion.

## Decision: Relay standard progress end to end

- **Decision**: When the outer caller supplies a progress token, Wright creates a unique child token, passes it in the child `tools/call`, receives `notifications/progress`, validates monotonic numeric values, and forwards updates through the outer SDK session using the caller's token.
- **Rationale**: This uses standard MCP behavior and lets Hermes or any other client surface server-authored progress without Wright knowing tool semantics.
- **Alternatives considered**: Polling cannot provide truthful stages; tool-name mappings recreate coupling; Wright-generated heartbeats remain useful only as generic liveness fallback.

## Decision: Normalize chat progress in the agent package

- **Decision**: Add a provider-neutral progress projector in `agent_adapters` and have the API stream job use it for fallback titles, elapsed time, monotonicity, correlation, and terminal closure.
- **Rationale**: The constitution keeps business rules out of FastAPI routes and requires all agent engines to map into the same event contract.
- **Alternatives considered**: Keeping `_CAD_PROGRESS_LABELS` violates neutrality; moving rules only into the web client creates inconsistent replay and multiple sources of truth.

## Decision: Keep live application validation optional

- **Decision**: Required Wright tests use synthetic MCP servers. Live Solid Edge evidence runs only on a prepared Windows host and does not change catalog validation claims.
- **Rationale**: Wright must remain cross-platform and offline-capable without proprietary dependencies, and repository guidance requires clean-container catalog validation to remain separate.
- **Alternatives considered**: Installing proprietary host software in CI/base images is infeasible and violates repository policy; eliminating compatibility smoke entirely would leave the migration unproven on the intended host.

## External Contract Status

The external `D:\repos\SolidEdgeMCP` checkout was clean on `codex/generic-mcp-contract` but that branch pointed to the same commit as its `dev` branch during planning. Its current contract already uses explicit `outputPath`, allowed-root enforcement, overwrite flags, and structured content. The neutral launch/progress migration must therefore remain backward-compatible and be validated again when the external branch advances.
