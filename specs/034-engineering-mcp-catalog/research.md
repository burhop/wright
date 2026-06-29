# Phase 0 Research: Engineering MCP Catalog

## Decision: Extend the existing catalog instead of creating a parallel plugin manager

**Rationale**: The repo already has `hermes-plugin-wright/catalog.yaml`, `CatalogLoader`, `CatalogEntry`, runtime `McpServer` models, API routes under `/api/mcp`, and a tool registry UI. Adding a separate registry loader/UI layer would split source-of-truth behavior and make existing cards stale.

**Alternatives considered**:

- Build a new standalone plugin-manager package from the handoff diagram. Rejected because the current repo already owns this lifecycle across plugin catalog, backend registry, and UI.
- Keep only documentation updates. Rejected because the user requested runnable catalog behavior, UI card updates, validation, and tests.

## Decision: Use explicit evidence states and installability tiers

**Rationale**: The handoff is careful that some rows are verified MCPs, some are docs MCPs, some are wrapper candidates, and some are user-reported seeds. A single boolean `is_installed` or current `status` cannot represent this safely. The registry needs both evidence state and current validation result.

**Alternatives considered**:

- Map everything to active/inactive/error. Rejected because it would mislabel wrapper candidates and blocked seeds as broken runtime servers.
- Hide blocked entries. Rejected because the product recommendation says valuable uncertain entries should remain visible.

## Decision: Validate first in Ubuntu x64 and classify host-dependent gaps as expected limitations

**Rationale**: The user specifically requested a single Ubuntu Docker container first. Many CAD integrations require commercial desktop software, GUI sessions, licenses, Windows COM, hardware, or cloud credentials. Those conditions must not become ambiguous test failures.

**Alternatives considered**:

- Require all hosts and credentials during CI. Rejected as impossible for paid CAD, hardware, and cloud-token dependencies.
- Skip all host-dependent entries. Rejected because users need to see that the package may install while the host app is unavailable.

## Decision: Generate local follow-up records for non-working entries

**Rationale**: The request asks for GitHub PRs for MCP servers that do not work. The current execution environment may not have credentials or a remote workflow for automatic PR creation. A local markdown follow-up record with stable naming, source evidence, observed failure, environment, and suggested next action satisfies the data needed to create a PR or issue later and can be linked from the catalog.

**Alternatives considered**:

- Automatically open GitHub PRs from validation. Deferred because it requires authentication, remote branch policy, and ownership decisions not present in this sprint.
- Only log failures. Rejected because logs are not durable enough for triage.

## Decision: Update current cards with dense status metadata

**Rationale**: `ToolRegistryPage` and `ToolCard` already provide discovery, installation, credentials, workspace enablement, details, and test IDs. The handoff's UI layer should map into these cards: readiness tier, evidence state, risk, platform support, dependencies, credentials, health check, and follow-up link.

**Alternatives considered**:

- Build a separate table-only page. Rejected because the user explicitly noted mapping to the current UI cards.
- Add only a raw JSON details drawer. Rejected because users need scannable status at card level.

## Decision: Safety policy belongs in catalog metadata and install guards

**Rationale**: High-risk servers can execute Python, mutate CAD, upload cloud files, or control machines. The default disabled/read-only policy must be visible in the catalog and enforced before installation or activation where possible.

**Alternatives considered**:

- Trust server descriptions. Rejected because descriptions are not reliable enough for safety gating.
- Remove safety-critical entries. Rejected because watchlist visibility is still valuable.
