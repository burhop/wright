# Canonical Workflow Recovery Quickstart

Run commands from the repository root on the recovery branch.

## Image-led native authoring

Use the integration checkout `D:/repos/wright/.local-run/epp-f02b-writer/wright`
on `codex/080-canonical-workflow-recovery`. The separate root checkout contains
reference images/planning; it is not the served implementation.

Running editor: `http://127.0.0.1:5227/workspace/85cbd6b3-e9d1-474d-add2-36f6e95a7b51?workflow=canonical`.
This opens **Wright workflow evidence** with the preserved original example.
The separate acceptance document records authored objects and connections without
overwriting that example. The current subject and report are recorded in
`evidence/image-redesign-delivery.json`.

1. Open a real engineering workspace and choose **Workflows**. Its first entry
   creates the default only if missing; existing source is preserved.
2. Use **New workflow** for a separate named document, or **Open workflow** for
   an existing one. Creating an existing name never overwrites it.
3. Choose a group in **Create**, then an object template. Nothing executes.
4. Select an input, open **Settings**, enter text or choose a permitted workspace
   file, and **Apply settings**. **Inputs** is a temporary navigator, not another
   value editor. Configured means configured, not approved or executed.
5. Select a step to edit its prompt/instructions and parameters. Generic tool,
   checker, and document templates remain clearly labeled unbound drafts.
6. Connect exact output/input sockets. Keyboard users focus an output and press
   Enter, then focus the intended input and press Enter; Escape cancels. Selection
   reveals each named endpoint. **Focus path** emphasizes dependencies.
7. Edit **Source** and apply valid edits. Invalid candidates retain the last
   accepted diagram. Use **Undo**/**Redo** and **Save**, then reopen to verify both
   authored configuration and positions.
8. **Example suggestion** is a reviewed fixture, not live AI. **Simulate** only
   replays the unchanged supported example. Authored/new topologies are not
   executable here; disabled simulation is an honest limitation.

The canvas starts at a readable scale. Use zoom/pan or **Fit workflow to view**
for an overview; hide the Inspector/minimap when more canvas space is useful.
Run details expand below the canvas, never over it. The Create rail and details
scroll internally on short windows; the document stays inside the viewport.

Tests, failed continuations and review findings are recorded under
`evidence/image-redesign-*`. The final32-step committed authoring journey passes
on `af069122`, including repaired previews, actual200% zoom and multi-tab saves.
The local API responsiveness repair preserves configuration/authentication
semantics; it does not make unbound templates executable.
The older web/correction counts and reports below are historical, not evidence
that the new redesign is complete.

## Verify the capability and syntax evidence

```powershell
python scripts/recovery/audit_capability_coverage.py
python scripts/recovery/evaluate_workflow_syntaxes.py --write-fixtures
python -m pytest tests/recovery/test_workflow_conformance.py -q --basetemp .test-tmp/recovery-kernel
```

Expected evidence:

- 890/890 source rows mapped into 33/33 capabilities using the generated CAP labels;
- 11/11 product gates, 100/100 stories, and 25/25 lessons covered;
- strict JSON, YAML, internal IR, and friendly engineer source rehydrate one accepted semantic identity;
- 36/36 conformance tests pass and every internal treatment rejects its complete invalid-control matrix,
  including graph cycles, feedback ownership/order, duplicate endpoints,
  cardinality, reciprocal phase/port ownership, binding-map, and component
  interface violations.

## Verify the web concept

```powershell
npm run test --workspace=apps/web -- --run `
  src/config/workflow-recovery.spec.ts `
  src/prototypes/workflow-recovery/model.spec.ts `
  src/prototypes/workflow-recovery/recovery-authoring.spec.ts `
  src/prototypes/workflow-recovery/command-system.spec.ts `
  src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.spec.tsx `
  src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx `
  src/components/pages/WorkflowRecoveryPage.spec.tsx `
  src/services/workspace-service.spec.ts `
  tests/WorkspacePanelSessions.spec.tsx `
  src/__tests__/App.test.tsx

uv run pytest -q `
  packages/workspace_service/tests/test_workflow_sources.py `
  apps/api/tests/test_workflow_sources_api.py

npm run build --workspace=apps/web
```

Expected: all focused source, command, canvas, workspace routing, persistence,
conflict, and absence-of-global-route tests pass, followed by a production web
build. Existing Vite chunk-size and config-loader warnings are not introduced
by this feature.

The final combined workspace-owned tree passed 116/116 Vitest files and
585/585 tests, followed by TypeScript and production Vite build. The bounded
workflow-source/API/security/trace slice passed 90 tests with three retained
Windows symlink-privilege skips; the broader service/API/security compatibility
regression passed 286 tests with seven skips for the same host limitation.

## Run the real-browser journey

Choose an unused local port if 5173 is already occupied:

```powershell
$env:WRIGHT_PLAYWRIGHT_PORT = "5195"
npx playwright test tests/ui-integration/workflow-recovery.spec.ts `
  --project=chromium --workers=1
```

The managed server enables `VITE_WRIGHT_WORKFLOW_RECOVERY=1` only for the test. The journey supplies a stateful mock workspace and workflow-source API but does not mock React Flow or concept behavior.

## Inspect manually

Use an explicit database path in the recovery worktree. Do not let a relative
API launch silently select an empty database from another branch, and do not
point this review at the user's real Wright database.

In API terminal 1:

```powershell
$reviewRoot = Join-Path (Get-Location) ".local-run/workflow-recovery-review"
New-Item -ItemType Directory -Force $reviewRoot | Out-Null
New-Item -ItemType Directory -Force (Join-Path $reviewRoot "workspace") | Out-Null
$env:DATABASE_PATH = Join-Path $reviewRoot "state.db"
$env:WRIGHT_API_MCP_AUTOSTART = "0"
uv run --extra runtime uvicorn api.main:app --host 127.0.0.1 --port 8000
```

In web terminal 2:

```powershell
$env:VITE_WRIGHT_WORKFLOW_RECOVERY = "1"
$env:WRIGHT_WEB_API_PROXY_TARGET = "http://127.0.0.1:8000"
npm run dev --workspace=apps/web -- --host 127.0.0.1 --port 5195
```

Open `http://127.0.0.1:5195/`. If the isolated review database is new, create
one workspace using the existing directory above; `Wright workflow review` is
an example local-review name, not a production workspace. The dashboard must
list it. Select the workspace and confirm the ordinary workspace URL contains
the actual ID returned by the API (`/workspace/<real-id>`). Then choose
**Workflows** inside that workspace; only that explicit action adds
`?workflow=canonical`. If the default workflow file is missing, this action is
explicit creation intent: Wright must idempotently create the validated default
inside that workspace and open the editor immediately, with no missing-file
confirmation screen. Re-entering **Workflows** must open the existing source
without replacing its bytes or advancing its identity. Merely selecting the
workspace creates no workflow. This setup neither copies nor claims to modify
the user's real database.

Then verify:

1. first Workflows entry bootstraps and immediately opens the compact
   `mounting-bracket.workflow.wflow` file/status bar, including version,
   validation, `PROVISIONAL`, and `SIMULATION` state; leave and re-enter once to
   verify that the existing source and identity are preserved;
2. reference images, design intent as text/common document, and approved
   company context feeding one reviewed design specification;
3. tolerance inspection appearing only after CAD or downstream work is selected;
4. live drag before mouse-up and layout-only commit on release;
5. concrete file/model/report names, mixed AI-draft plus engineer-review
   provenance, and technical IDs only behind disclosure;
6. Diagram/Source/Side by side correspondence and invalid-source containment;
7. AI proposal assumptions, warnings, diff, preview, reject, and accept;
8. queued → running → needs-input → recovered → succeeded simulation;
9. STEP preview, report, download name, and full three-source lineage.
10. overview-first graph density: all nine step titles and the left-to-right flow are readable without persistent edge labels or per-port metadata; focus a socket or relationship and select a step to verify the complete accessible details remain available.

Diagram, Source, and the inspector are synchronized views of one visible
`workflows/mounting-bracket.workflow.wflow` file. Groups are optional, and the
short example does not require phases. Host-managed revision, digest,
compare-and-swap, and integrity records stay outside engineer-authored source
and appear only as technical details. Referenced engineering files remain
separate workspace items; layout and immutable workflow-test/run records are
also separate. The current Add/View/Replace input control, simulation state,
demo report, and demo STEP download are not persisted by saving the workflow
source.

At 1070×791, verify no document/page scrolling. The bounded source list or
inspector may scroll internally. The nine-step workflow has no Find control;
search appears only for graphs with 26 or more steps.

At both 1537×791 and 1070×791, verify compact blocks, small connection points,
hidden-by-default relationship labels, and a one-line reusable review-group
summary. Keyboard focus, selection, the **Details** action, and inspector tabs
must reveal the full typed contracts without expanding the default graph.

Stop on the first ambiguity. Historical approval remains bound only to its exact
subject below; the workspace-owned correction needs a fresh committed
walkthrough before any new exact-subject claim. Neither subject is production
authority, and neither authorizes merge or release.

## Historical recorded exact-subject gate — 2026-08-31 EDT

| Gate | Result |
|---|---|
| Strict JSON/YAML/internal DSL and graph conformance | **PASS · 23/23** on the historical subject |
| Focused model, command, renderer, and host tests | **PASS · 36/36** on the prior correction |
| Production TypeScript/Vite build | **PASS** on the prior correction |
| Chromium recovery journey | **PASS · 5/5** · includes pointer/keyboard handles, axe, reduced motion, 390×844 containment, run recovery, output popup, and download |
| `npm ci --dry-run` | **PASS** · lockfile is reproducible; the existing `jsdom` Node-engine warning remains visible under local Node 25.2.0 |

The Vite native-config-loader and existing large-chunk warnings are recorded,
not introduced or hidden by this recovery concept. No push, merge, release,
external execution, or customer action occurred.

## Inspect the digest-bound walkthroughs

The original direction-approval baseline remains immutable at commit
`f9237763d6fa6e9748dfb7b713e753a7fc4b4d17`, tree
`aeca6ab8294dd54112d3e9ac10148537af32b0f0`, and manifest
`f2b4964ec1f599b55a8a8d53704147d2133674baa5db9a28072d4a2808c57347`.
Its 50/50-step package remains historical approval evidence.

The prior mechanical-engineer correction is bound separately:

- Passing report: `artifacts/ui-walkthrough/workflow-recovery-usability/20260901T151651Z-continuation-5/report.html`
- Passing manifest SHA-256: `e661bf45ff1449abc87399b928156fc336f367f260368a2966645a0026afd96e`
- Exact subject: `c5fb7d8e4a722f84956ebe22085e7fdf38b1b1d5`
- Exact tree: `148a935edd38e9abe91b9ed284cd04882acf59c6`
- Result: 12/12 steps at 1070×791, 12 raw and 12 annotated
  screenshots, 30 manifest-bound files, a 16,542,037-byte trace, and zero
  browser diagnostics. The compact workflow-file/status bar measured 65 px.

```powershell
python C:\Users\markb\.codex\skills\playwright-ui-walkthrough\scripts\validate_walkthrough.py `
  artifacts\ui-walkthrough\workflow-recovery-usability\20260901T151651Z-continuation-5
```

Expected: `Walkthrough artifact structure is valid.` Earlier stopped roots are
intentionally retained as failure-and-repair evidence. The prior package
verifies material equivalence to the approved direction after the requesting
engineer's corrections; it does not invent a second human approval.

The workspace-owned engineer-source correction is bound to commit
`38b409bf149a1241cc87cdedd48f83fed16b5050`, tree
`452c1ab82b12fe94ba743e3dfe612c8cd4b9dac6`, and continuation 14. Its validated
package passes 24/24 steps with 26 raw and 26 annotated screenshots, 59
manifest-bound files, zero unexpected diagnostics, and manifest SHA-256
`b8764a02ef83dfc52b65714de0cdbb05071feb9c0ebf4f5fde4995a2870cf335`.
Continuation 5 remains prior formative correction evidence, not current proof.

## Verify the recovery dashboard

Open `http://127.0.0.1:8765/`. The server is launched against this recovery
worktree and presents two deliberately separate ledgers:

- governed EPP-F02B remains `BLOCKED`, 27/38, with T028–T038 open;
- projected EPP-F02C recovery remains `proposed` and unregistered; consult the
  refreshed task ledger for its current numerator/denominator because the
  workspace-owned correction adds new dependency-ordered work after
  continuation 5.

The live recovery gallery separates the frozen checkpoint, original approval
baseline, prior continuation-5 correction walkthrough, and current validated
workspace-owned continuation-14 subject.
Existing report, status, manifest, and selected screenshots return HTTP 200;
raw encoded and plain `..` evidence-mount
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
with no search through 25 steps, then enables fit, minimap, stable-ID search,
and selection at 26 or more. The final
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

Expected: 14/14 pass across the complete workflow and accessibility files. The focused accessibility file proves keyboard activation
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

## Verify T059 local release-candidate hardening

Run from a clean detached worktree at exact commit
`fe6140d85f0598454394d7b7105d756c3794a7dd` (tree
`8df2b19c94926c8fe922870de4bbad92bb285720`):

```powershell
python scripts/release-preflight.py --dry-run --tag v0.1.9 `
  --source-commit fe6140d85f0598454394d7b7105d756c3794a7dd `
  --output test-results/release-candidate/t059/preflight.json

bash scripts/build-python-distributions.sh `
  --dist-root test-results/release-candidate/t059/python .

python scripts/test-native-hermes-install.py `
  --wheel <exact-wheel> --previous-wheel <fixture-predecessor> `
  --wheelhouse <platform-wheelhouse> --hermes-home <external-temp-home> `
  --wright-home <external-temp-home> --plugin-source hermes-plugin-wright `
  --hermes-command <hermes-0.19.0> --codex-command <codex-0.144.1> `
  --evidence test-results/release-candidate/t059/native-lifecycle-windows.json

$env:WRIGHT_DOCKER_IMAGE = "wright:t059-fe6140d8"
bash scripts/docker-smoke-test.sh

python scripts/release-rehearsal.py --dry-run --tag v0.1.9 `
  --python-dist test-results/release-candidate/t059/python/wright-engineering `
  --native-build-evidence <native-build-evidence.json> `
  --native-lifecycle-evidence <native-lifecycle-windows.json> `
  --output test-results/release-candidate/t059/rehearsal
```

Expected: the wheel/sdist clean-install and retain SHA-256
`53a48234...a77d` / `988c95f8...b9a3`; Windows native lifecycle and direct
Codex MCP profile pass; Docker smoke ends with `ALL SMOKE AND RECOVERY TESTS
PASSED`; local OCI manifest is `sha256:666ed2de...ab76a`; and the rehearsal
digest is `0130502a...3bf6` with zero external mutations. See
`evidence/release-candidate-hardening.md` and
`artifacts/t059-release-candidate/`.

This completes only T059's authorized local scope. Do not interpret the
rehearsal's simulated `release_ready` state as public or customer readiness.
T060 still requires separate authorization for dev-push/merge/release gates,
Linux/macOS and public-artifact verification, registry promotion, docs, tag,
and GitHub Release.

## Recompute the full recovery completion audit

```powershell
python scripts/recovery/audit_recovery_completion.py `
  --output specs/080-canonical-workflow-recovery/evidence/recovery-completion-audit.json

python -m pytest -q -p no:cacheprovider `
  tests/recovery/test_recovery_completion_audit.py
```

Expected: audit status `PASS`, locally provable objective requirements passed,
historical approval, prior continuation-5 integrity, and current continuation-14
integrity intact; the 77/80 task ledger reproduced exactly; prohibited actions
empty; and customer readiness false. A passing audit does not convert T056,
T058, or T060 into completed work.
