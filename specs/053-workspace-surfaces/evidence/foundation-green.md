# Phase 2 foundation verification

Recorded 2026-07-30 on branch `053-workspace-surfaces`.

## Implemented scope

- Side-effect-neutral domain IDs, source discriminators, lifecycle transitions,
  generation provenance, stable redacted errors, and trace correlation values.
- Contiguous migration 6 plus exact user/workspace/session-scoped descriptor,
  preference, grant, runtime, provenance, diagnostic, outbox, and content-vault
  persistence. Optimistic writes reject stale revisions without mutation.
- Explicit application ports, service authority/state machine, bounded diagnostic
  history, and bounded descriptor events scoped to the complete
  user/workspace/session tuple.
- Thin authenticated FastAPI projections/routes and default-off mounting with
  startup/shutdown ownership in the composition root.
- Strict TypeScript descriptor/capability parsing, deterministic presenter
  registration, stable version-2 state, exact-once presenter disposal, the
  legacy file-viewer adapter, and default-off frontend mounting.

## Automated evidence

```text
uv run pytest <Phase 2 Python foundation suite> -q
77 passed, 1 warning in 8.37s
```

The only warning is the existing FastAPI TestClient notice that Starlette's
`httpx` integration is deprecated in favor of `httpx2`; it does not originate
from Workspace Surfaces behavior.

```text
npx vitest run <Workspace Surfaces foundation specs>
5 files passed; 24 tests passed

npm run lint
passed

npm run build
passed; 473 modules transformed
```

The production build retains the existing advisory for a JavaScript chunk
larger than 500 kB. Plotly and presenter lazy loading are scheduled in later
feature tasks and are not loaded by this foundation implementation.

```text
uv run ruff check <all Phase 2 Python implementation and test paths>
All checks passed
```

The Python suite includes migration rollback/compatibility, import boundaries,
installed-wheel contents and import side effects, API/legacy file-content
compatibility, every foundational SQLite/vault trace, cross-scope denial,
Last-Event-ID bounded replay, and composition lifecycle ownership.
