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
- projected EPP-F02C recovery is `proposed`, unregistered, 51/60 through the
  approved T051 exact subject, with T052–T060 open.

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
