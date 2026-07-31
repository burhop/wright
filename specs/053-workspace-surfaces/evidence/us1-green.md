# User Story 1 green evidence: beginner Python displays

**Recorded**: 2026-07-30
**Scope**: T044-T054

## Outcome

The installed `wright` package now creates bounded, accessible graphs and other
safe display values without import-time side effects or required plotting
dependencies. Wright-run files receive only an execution-scoped display
endpoint, token, workspace identifier, and contract version; authority is
revoked at process completion. The service validates and durably versions each
display, preserves exact authorized provenance, publishes scoped descriptor
events after commit, and requires truthful confirmation before durable output
deletion.

The web workspace renders safe text/table/raster/SVG/passive HTML and lazy,
bundled-offline Plotly. Stable tabs update through the authenticated SSE stream
with `Last-Event-ID`; desktop currently uses the scoped polling fallback.
Revision history, exact artifact verification, destructive retention
disclosure, accessible fallbacks, and actionable renderer errors are present.

Fresh reruns of the same workspace Python file retain the same logical surface:
the stable file-task identity plus `display_id` maps a new process's initial
revision to the next immutable server revision. Same-execution stale or skipped
revisions remain rejected, and idempotent replay returns the original artifact.

## Automated evidence

- Python US1 gate: **77 passed, 1 intentionally skipped**. This includes SDK,
  envelope contract, token/API, durable service, composition, file execution,
  real SDK-to-API-to-SQLite/vault, clean-wheel examples/package assets, and
  migrations.
- Ruff US1 gate: **passed**.
- Web Vitest gate: **34 files, 145 tests passed**.
- Web ESLint gate: **passed**.
- Production TypeScript/Vite build: **passed**; Plotly is a distinct lazy local
  chunk. Vite's existing advisory for chunks over 500 kB remains informational.
- Chromium mocked workspace journey: **2 passed** covering authenticated SSE
  update without duplicate tabs, Plotly visibility, history, exact
  verification, irreversible deletion disclosure/status, and renderer failure.
- Review reconciliation: all **98** items across requirements, security,
  runtime, UX, and integration checklists are checked; no clarification,
  placeholder, or checklist-error marker remains.

The only Python warning is the repository's pre-existing Starlette `httpx`
compatibility deprecation. The live installed-release Playwright case remains
tagged `@live` for the later system-gate phase and is intentionally excluded by
the default Playwright configuration.

## Red-to-green defects closed

- Stable logical identity initially used execution identity, which would create
  a new tab on every file rerun. It now uses stable task identity and maps a
  fresh process revision safely.
- The development-only feature override assumed local-storage access; opaque
  documents could throw and crash unrelated web tests. Access is now guarded.
- Updated Plotly hosts could collapse to zero height. The responsive host now
  has an explicit minimum height and is covered by unit and Chromium tests.
- The first mocked UI journey used a synthetic browser event. It now consumes
  the real authenticated surface SSE client backed by post-commit service
  publication.

See [us1-red.md](us1-red.md) for the deliberately observed failing state.
