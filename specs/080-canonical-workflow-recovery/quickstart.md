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
- 20/20 conformance tests pass and every treatment rejects 8/8 invalid controls,
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

Expected: 28/28 focused recovery/config/routing tests pass and the
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

Stop on the first ambiguity. Do not treat this concept as production authority, merge it, or release it before explicit product approval.

## Recorded exact-subject gate — 2026-08-31 EDT

| Gate | Result |
|---|---|
| Strict JSON/YAML/DSL and graph conformance | **PASS · 20/20** |
| Focused model, command, config, and route tests | **PASS · 28/28** |
| Production TypeScript/Vite build | **PASS** · recovery remains a lazy route chunk |
| Chromium recovery journey | **PASS · 4/4** · includes pointer/keyboard handles, axe, reduced motion, 390×844 containment, run recovery, output popup, and download |
| `npm ci --dry-run` | **PASS** · lockfile is reproducible; the existing `jsdom` Node-engine warning remains visible under local Node 25.2.0 |

The Vite native-config-loader and existing large-chunk warnings are recorded,
not introduced or hidden by this recovery concept. No push, merge, release,
external execution, or customer action occurred.

## Inspect the digest-bound walkthrough

- Passing report: `artifacts/ui-walkthrough/workflow-recovery/20260901T012043Z-continuation-2/report.html`
- Passing manifest SHA-256: `3b7aec8fbf5d4c4f33c108a47906def7be883259a13425a11ce297aa366ca594`
- Exact subject: `4c717e22c812f2d1dc3bb6618229371561ba5aaa`
- Exact tree: `9c1d044b26d90cf5763578d3c9410878bafb1d52`

```powershell
python C:\Users\markb\.codex\skills\playwright-ui-walkthrough\scripts\validate_walkthrough.py `
  artifacts\ui-walkthrough\workflow-recovery\20260901T012043Z-continuation-2
```

Expected: `Walkthrough artifact structure is valid.` The two preceding blocked
roots are intentionally retained as harness-stop evidence; the linked passing
continuation is the product-approval subject.

## Verify the recovery dashboard

Open `http://127.0.0.1:8765/`. The server is launched against this recovery
worktree and presents two deliberately separate ledgers:

- governed EPP-F02B remains `BLOCKED`, 27/38, with T028–T038 open;
- projected EPP-F02C recovery is `proposed`, unregistered, 49/60 after T049,
  with T050–T060 open and T051 the mandatory approval stop.

The live recovery gallery serves only the exact frozen and passing recovery
walkthrough roots. Report, status, manifest, frozen screenshot, and all five
recovery thumbnails return HTTP 200; raw encoded and plain `..` evidence-mount
traversal attempts return HTTP 403. Headless Chromium verifies the recovery
ledger, governed-truth warning, pending approval, incomplete customer readiness,
six loaded gallery images, no console/page errors, and no horizontal overflow at
1440 or 390 pixels. Local captures are in
`artifacts/dashboard-recovery-verification/desktop-goal.png` and
`artifacts/dashboard-recovery-verification/mobile-goal.png`.
