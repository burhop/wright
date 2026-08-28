# Research: Browser Program Status

## Decision 1: Publish a validated local bundle; do not let the API read Git

**Decision**: A deterministic repository-side CLI validates one committed subject and atomically installs a contracted JSON bundle in Wright's stable data root. The API reads only that installed bundle.

**Rationale**: This preserves EPP-F01 as the authority, keeps routes thin, supports air-gapped packaged runtime without a checkout, and prevents refresh from observing dirty or half-written evidence.

**Alternatives rejected**: API or browser reads `docs/programs` directly (checkout coupling and validation bypass); SQLite projection (unnecessary second mutable state store).

## Decision 2: One digest-bound envelope with atomic replacement

**Decision**: `current.json` contains a schema version, exact source commit/tree/program-tree identities, generated timestamp, body digest, and one complete projection. The publisher validates a temporary file before atomic replacement.

**Rationale**: A single identity prevents mixed panels and makes conditional GET, rollback, caching, and stale diagnosis precise. The digest is an integrity binding, not a trust grant.

**Alternatives rejected**: Independent panel files permit mixed generations; API-computed status makes identical committed inputs render differently.

## Decision 3: Conditional identity polling, not a runtime Git watcher

**Decision**: The browser polls the authenticated endpoint every ten seconds with `If-None-Match`. A repository development helper may republish only when committed HEAD changes. Production observes only atomic bundle replacement.

**Rationale**: This meets automatic refresh while keeping Git and filesystem watching outside the API. A 304 is cheap and unchanged evidence is not reinterpreted.

**Alternatives rejected**: WebSocket/SSE adds needless lifecycle complexity; full-body polling wastes parsing; polling dirty files violates authority.

## Decision 4: Reuse existing Plotly with semantic fallbacks

**Decision**: Reuse Wright's lazy Plotly renderer and installed dependency. Each graph receives a descriptive label, exact timestamp/commit tooltips, prose interpretation, and an accessible table fallback.

**Rationale**: No dependency change is needed and the fallback keeps metrics usable when visualization fails or color is unavailable.

**Alternatives rejected**: Hand-built SVG repeats accessibility work; a new chart library expands supply-chain scope; graph-only display is inaccessible.

## Decision 5: Histories use exact committed observations

**Decision**: The publisher walks allowlisted committed state, transition, task, catalog, and delivery evidence. A point is included only when its metric, exact commit, and trustworthy ISO-8601 time are present. Ordering uses timestamp plus commit identity; missing data remains unavailable.

**Rationale**: This prevents misleading ordinal charts and inferred progress. Metric units are contractual.

**Alternatives rejected**: Git traversal order alone is not a time axis; file modification time is not durable evidence; hand-maintained values create a second authority.

## Decision 6: Separate populations and units

**Decision**: Display `100 proposed customer stories` with derived definition-maturity counts separately from `0/100 qualified benchmark processes`. Feature task charts use `completed tasks / tasks in <feature-id>` and appear beside product, roadmap, and release context.

**Rationale**: Proposed work is not executed evidence, and narrow feature completion must not imply product completion.

## Decision 7: Fail closed while retaining last valid context

**Decision**: Invalid newer data never replaces the active view. The API emits a typed failure and the browser retains its last valid bundle with explicit stale/failed age and recovery guidance. With no prior valid bundle, it shows unavailable values only.

**Rationale**: The operator remains oriented without mistaking stale data for current truth.

## Decision 8: Dedicated authenticated page

**Decision**: Add `/program-status` and a sidebar link. Keep the existing workspace `DashboardPage` unchanged in purpose. Protect the API with Wright's existing local session/security middleware.

**Rationale**: Program governance and workspace operation are distinct user jobs.

## Decision 9: Bounded observability without evidence leakage

**Decision**: Log event name, trace ID, bundle identity, outcome, duration, and failure class as structured fields. Never log evidence bodies, credentials, raw commands, or private paths.

**Rationale**: This supports glass-box diagnosis while honoring the allowlist boundary.

## Resolved Clarifications

- No new dependency is needed.
- No remote service or telemetry is permitted.
- No calendar-duration estimate is a progress metric.
- GitHub URLs and CI fields appear only when present in validated evidence.
- EPP-F01B never edits program state or launches benchmarks, tools, builds, pushes, or releases.
