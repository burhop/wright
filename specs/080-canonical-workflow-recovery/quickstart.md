# Canonical Workflow Recovery Quickstart

Run commands from the repository root on the recovery branch.

## Verify the capability and syntax evidence

```powershell
python scripts/recovery/audit_capability_coverage.py
python scripts/recovery/evaluate_workflow_syntaxes.py --write-fixtures
python -m pytest tests/recovery/test_workflow_conformance.py -q --basetemp .test-tmp/recovery-kernel
```

Expected evidence:

- 859/859 source rows mapped into 33/33 capabilities;
- 11/11 product gates, 100/100 stories, and 25/25 lessons covered;
- JSON, YAML, and DSL parse to one canonical semantic identity;
- 23/23 conformance tests pass and every treatment rejects 8/8 invalid controls,
  including graph cycles, feedback ownership/order, duplicate endpoints,
  cardinality, reciprocal phase/port ownership, binding-map, and component
  interface violations.

## Verify the web concept

```powershell
npm run test --workspace=apps/web -- --run `
  src/config/workflow-recovery.spec.ts `
  src/prototypes/workflow-recovery/model.spec.ts `
  src/prototypes/workflow-recovery/command-system.spec.ts `
  src/__tests__/App.test.tsx

npm run build --workspace=apps/web
```

Expected: 35/35 focused recovery/config/routing tests pass and the
recovery page builds into a lazy route chunk. Existing Vite chunk-size and
config-loader warnings are not introduced by this feature.

## Run the real-browser journey

Choose an unused local port if 5173 is already occupied:

```powershell
$env:WRIGHT_PLAYWRIGHT_PORT = "5195"
npx playwright test tests/ui-integration/workflow-recovery.spec.ts `
  --project=chromium --workers=1
```

The managed server enables `VITE_WRIGHT_WORKFLOW_RECOVERY=1` only for the test. The journey mocks shell APIs but does not mock React Flow or concept behavior.

## Inspect manually

```powershell
$env:VITE_WRIGHT_WORKFLOW_RECOVERY = "1"
npm run dev --workspace=apps/web -- --host 127.0.0.1 --port 5195
```

Open `http://127.0.0.1:5195/workflow-recovery` and verify:

1. the provisional/`SIMULATED` authority strip;
2. the three-treatment port lab;
3. palette add/delete/undo/redo and attachment preview/replace;
4. direct handle connection and accessible edge disconnect;
5. Diagram/Code/Split correspondence and invalid-source containment;
6. AI proposal assumptions, warnings, diff, preview, reject, and accept;
7. queued → running → needs-input → recovered → succeeded simulation;
8. STEP preview, report, download name, and lineage.

Stop on the first ambiguity. The exact subject below has product/visual-direction
approval, but it is still not production authority and MUST NOT be merged or
released under the current authorization.

## Recorded exact-subject gate — 2026-08-31 EDT

| Gate | Result |
|---|---|
| Strict JSON/YAML/DSL and graph conformance | **PASS · 23/23** |
| Focused model, command, config, and route tests | **PASS · 35/35** |
| Production TypeScript/Vite build | **PASS** · recovery remains a lazy route chunk |
| Chromium recovery journey | **PASS · 5/5** · includes pointer/keyboard handles, axe, reduced motion, 390×844 containment, run recovery, output popup, and download |
| `npm ci --dry-run` | **PASS** · lockfile is reproducible; the existing `jsdom` Node-engine warning remains visible under local Node 25.2.0 |

The Vite native-config-loader and existing large-chunk warnings are recorded,
not introduced or hidden by this recovery concept. No push, merge, release,
external execution, or customer action occurred.

## Inspect the digest-bound walkthrough

- Passing report: `artifacts/ui-walkthrough/workflow-recovery/20260901T031913Z-continuation-1/report.html`
- Passing manifest SHA-256: `f2b4964ec1f599b55a8a8d53704147d2133674baa5db9a28072d4a2808c57347`
- Exact subject: `f9237763d6fa6e9748dfb7b713e753a7fc4b4d17`
- Exact tree: `aeca6ab8294dd54112d3e9ac10148537af32b0f0`
- Result: 50/50 steps, 99 raw and 99 annotated screenshots, 204
  manifest-bound files, a 94,777,058-byte trace, and zero browser diagnostics.

```powershell
python C:\Users\markb\.codex\skills\playwright-ui-walkthrough\scripts\validate_walkthrough.py `
  artifacts\ui-walkthrough\workflow-recovery\20260901T031913Z-continuation-1
```

Expected: `Walkthrough artifact structure is valid.` Earlier stopped roots are
intentionally retained as failure-and-repair evidence. The linked passing
continuation is the exact approved product/visual-direction subject.

## Verify the recovery dashboard

Open `http://127.0.0.1:8765/`. The server is launched against this recovery
worktree and presents two deliberately separate ledgers:

- governed EPP-F02B remains `BLOCKED`, 27/38, with T028–T038 open;
- projected EPP-F02C recovery is `proposed`, unregistered, 56/60 through the
  verified T057 security/offline checkpoint; T056 and T058–T060 remain open.

The live recovery gallery serves only the exact frozen and passing recovery
walkthrough roots. Report, status, manifest, frozen screenshot, and all seven
recovery thumbnails return HTTP 200; raw encoded and plain `..` evidence-mount
traversal attempts return HTTP 403. Headless Chromium verifies the recovery
ledger, governed-truth warning, approved exact subject, incomplete customer readiness,
eight loaded gallery images, no console/page errors, and no horizontal overflow at
1440 or 390 pixels. Local captures are in
`artifacts/dashboard-recovery-verification/desktop-goal.png` and
`artifacts/dashboard-recovery-verification/mobile-goal.png`.

## Verify the T052 stable production boundary

The approved recovery definition now enters production only through the explicit
`2.0.0-recovery.1` to `2.0.0` migration in
`packages/core/src/core/workflow_definitions.py`. Definition revisions persist in
the independent `workflow-definitions.sqlite3` sidecar; legacy drafts, layout,
and runs remain separate.

```powershell
uv run ruff check packages/core/src/core/workflow_definitions.py `
  packages/data_vault/src/data_vault/workflow_definition_repository.py

uv run pytest -q packages/core/tests/test_workflow_definitions.py `
  packages/data_vault/tests/test_workflow_definition_repository.py `
  packages/data_vault/tests/test_workflow_draft_repository.py

uv run pytest -q packages/core/tests packages/data_vault/tests
```

Expected: Ruff passes; the focused suite reports 21 passed; the broad suite
reports 216 passed and 1 retained skip. Exact migration digests, rollback rules,
and deferred boundaries are recorded in
`evidence/production-promotion.md` and ADR 0002.

## Verify T053 durable layout persistence

The approved recovery layout fixture promotes explicitly to stable
`workflow-layout/1.0.0` and persists in its own append-only
`workflow-layouts.sqlite3` sidecar.

```powershell
uv run pytest -q packages/core/tests/test_workflow_layouts.py `
  packages/data_vault/tests/test_workflow_layout_repository.py

uv run pytest -q packages/core/tests packages/data_vault/tests
```

Expected: the focused suite reports 11 passed; the broad suite reports 227
passed and 1 retained skip. ADR 0003 and
`evidence/durable-layout-persistence.md` record exact digests, reopen behavior,
CAS containment, unknown-version recovery, and rollback limits.

## Verify T054 durable workflow execution

Canonical run, step, activity, and artifact records use stable
`workflow-run/1.0.0` in an independent `workflow-runs.sqlite3` sidecar. The
legacy primary run tables remain untouched.

```powershell
uv run pytest -q packages/core/tests/test_canonical_workflow_runs.py `
  packages/data_vault/tests/test_canonical_workflow_run_repository.py

uv run pytest -q packages/core/tests packages/data_vault/tests
```

Expected: the focused suite reports 16 passed; the broad suite reports 243
passed and 1 retained skip. ADR 0004 and
`evidence/durable-workflow-execution.md` record subject identity, component and
artifact lineage, cancellation, reconnect, cleanup, historical recovery-run
preservation, schema checksum, and explicit non-authority boundaries.

## Verify T055 component and large-graph behavior

```powershell
npm run test --workspace=apps/web -- --run `
  src/components/workflow-composer/component-graph.spec.ts `
  src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.spec.tsx

$env:WRIGHT_PLAYWRIGHT_PORT = "5195"
npx playwright test tests/ui-integration/workflow-recovery.spec.ts --project=chromium

npm run build --workspace=apps/web
```

Expected: component projection rejects invalid internal scopes/paths, collapsed
instances retain scoped run-lineage targets, expansion does not change revision
or semantic digest, and the 100-block renderer switches to compact presentation
while fit, minimap, stable-ID search, and selection remain available. The final
Chromium suite reports 6 passed. See
`evidence/component-large-graph-promotion.md`; its 100-block result is bounded
behavior evidence, not a production performance benchmark.

## Verify the automated portion of T056

```powershell
$env:WRIGHT_PLAYWRIGHT_PORT = "5195"
npx playwright test `
  tests/ui-integration/workflow-recovery.spec.ts `
  tests/ui-integration/workflow-recovery-accessibility.spec.ts `
  --project=chromium
```

Expected: 8/8 pass. The focused accessibility file proves keyboard activation
and focus order, modal focus containment/return, a two-times Chromium page
scale, accessibility-tree names/roles, zero serious/critical Axe findings, and
zero document overflow. See `evidence/accessibility-qualification.md`.

T056 remains open: an accessibility-tree snapshot is not a real screen-reader
session, and the representative-engineer study in
`evidence/moderated-engineer-usability-protocol.md` has not been run. Do not
mark either gate complete from automation or protocol preparation.

## Verify T057 security and offline qualification

```powershell
uv run pytest -q `
  tests/security/test_canonical_workflow_security.py `
  tests/e2e/test_canonical_workflow_offline.py

uv run --extra engineering-models pytest -q `
  packages/core/tests/test_workflow_definitions.py `
  packages/core/tests/test_canonical_workflow_runs.py `
  packages/data_vault/tests/test_workflow_definition_repository.py `
  packages/data_vault/tests/test_workflow_layout_repository.py `
  packages/data_vault/tests/test_canonical_workflow_run_repository.py `
  packages/workspace_service/tests/test_workflow_operations.py `
  packages/workspace_service/tests/surfaces/test_capability_grants.py `
  tests/security `
  tests/e2e/test_engineering_program_offline.py `
  tests/e2e/test_canonical_workflow_offline.py

uv run ruff check `
  packages/core/src/core/rivet_mcp.py `
  packages/core/src/core/workflow_definitions.py `
  packages/core/src/core/canonical_workflow_runs.py `
  tests/security/test_canonical_workflow_security.py `
  tests/e2e/test_canonical_workflow_offline.py
```

Expected: 10 focused tests pass, 88 broad regression tests pass, and Ruff
passes. The tests prove exact workspace/session and one-shot capability scope,
administrator-only authority, fail-closed secret handling before hashing or
immutable storage, command/envelope resource limits, independent sidecars,
cross-root isolation, and restart/reconnect with zero network calls. See
`evidence/security-offline-qualification.md`.

## Verify the bounded T058 benchmark preflight

```powershell
uv run pytest -q `
  tests/recovery/test_benchmark_preflight.py `
  tests/recovery/test_workflow_conformance.py

uv run ruff check `
  scripts/recovery/benchmark_preflight.py `
  tests/recovery/conftest.py `
  tests/recovery/test_benchmark_preflight.py

uv run python scripts/recovery/benchmark_preflight.py `
  --output test-results/dataset-evaluation/benchmark-preflight.json
```

Expected: 26 tests and Ruff pass, while the preflight truthfully reports
`BLOCKED`, `0/100`, zero cases, zero schema findings, and zero state violations.
It lists `DEC-P0-007`, `009`, `010`, `011`, and `012` plus `EPP-F03`, `F05`,
`F06`, and `B01` as blockers. Do not generate or count cases until the named
human decisions and roadmap dependencies are satisfied. See
`evidence/benchmark-preflight.md`.
