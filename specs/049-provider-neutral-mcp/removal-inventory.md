# Provider-Specific Runtime Removal Inventory

## Baseline (2026-07-26)

The following Wright runtime paths contained Solid Edge-specific behavior before implementation:

| Runtime path | Provider-specific behavior | Neutral replacement |
|---|---|---|
| `packages/agent_adapters/src/agent_adapters/hermes.py` | Prescribed an exact Solid Edge recipe tool and arguments in the global Wright system hint. | Rely on each MCP server's advertised tool contract. |
| `packages/tool_registry/src/tool_registry/gateway_policy.py` | Identified SolidEdgeMCP by source URL and hid tools outside a hard-coded creation allowlist. | Project the server-advertised tool set and apply only trusted generic Wright policy. |
| `packages/tool_registry/src/tool_registry/lifecycle_adapters.py` | Identified SolidEdgeMCP by name/source URL and injected `CADMCP_SOLID_EDGE_ALLOWED_ROOTS`. | Render trusted `{workspace.path}` templates in generic command/environment configuration. |
| `apps/api/src/api/routers/agent.py` | Mapped specific CAD tool names to Solid Edge labels and asserted document visibility. | Normalize server-authored progress and generic fallbacks in `agent_adapters`. |

The associated identity-specific tests were located in:

- `packages/tool_registry/tests/test_lifecycle_adapters.py`
- `packages/tool_registry/tests/test_gateway_policy.py`
- `apps/api/tests/test_agent_stream_progress.py`

## Approved Remaining References

Solid Edge may remain named in:

- ordinary catalog/server configuration data,
- installation and operator documentation,
- feature specifications and migration evidence,
- optional Windows live compatibility tests and their host-scoped evidence.

It must not remain in Wright runtime branching, global agent prompts, progress mappings, or generic test fixtures.

## Final Audit

Completed 2026-07-26.

Removed runtime paths:

- `hermes.py`: deleted the global provider recipe; the remaining hint selects
  tools from advertised contracts.
- `gateway_policy.py`: deleted source-URL detection and the creation allowlist;
  all enabled advertised tools now follow the same trusted policy.
- `lifecycle_adapters.py`: deleted provider/name detection and the hard-coded
  allowed-root variable; generic trusted launch templates now render the bound
  workspace.
- `agent.py`: deleted tool-name progress labels and application-visibility
  claims; generic projection lives in `agent_adapters.progress`.

The enforced audit in `tests/test_provider_neutral_mcp_runtime.py` scans Python,
TypeScript, and JavaScript runtime sources under `apps/` and `packages/`. It
found zero application-specific provider identifiers. Catalog data, operator
documentation, specifications, and explicit absence assertions remain allowed.

Synthetic validation covers two unrelated server identities, literal workspace
rendering, discovery metadata, trusted approvals, progress tokens, malformed
and decreasing updates, terminal cleanup, gateway relay, cancellation,
timeouts, ownership, rebinding, concurrency, and frontend rendering.

The optional Windows live compatibility smoke was skipped. The external
`D:\repos\SolidEdgeMCP` checkout's `codex/generic-mcp-contract` branch still
pointed to the same commit as its `dev` branch during implementation, so there
was no matching advanced neutral contract to validate. Required Wright tests do
not install, modify, or execute that external repository. The current external
allowed-root contract remains representable as ordinary `launch_env` data.

## Dev Merge Gate Evidence

The exact Bash wrapper could not execute on this Windows host: `bash` resolves
to WSL, where the repository is mounted at `/mnt/d/repos/wright` but `uv` is not
installed, and Git Bash is not installed. The running Wright instance also owns
port 8000 and was intentionally left online for the user's active testing, so an
isolated Playwright server could not claim the merge-gate port.

Every non-browser gate was run directly in PowerShell with the isolated
`C:\tmp\wright-feature-049-venv` environment: diff validation; Ruff, ESLint,
Prettier, and TypeScript checks; strict release mypy; workspace mypy in the
gate's warning mode; package metadata validation; workflow policy; release
tests and 87.53% release coverage; wheel and source-distribution build,
inspection, clean installation, and import; the complete Python suite; the
forced isolated Hermes plugin suite; the complete frontend suite and production
build; and the strict MkDocs build. The workspace mypy command emitted only the
gate's accepted duplicate-`conftest.py` warning. The Playwright phase remains
deferred to clean-host pull-request CI rather than interrupting the active local
Wright service.
