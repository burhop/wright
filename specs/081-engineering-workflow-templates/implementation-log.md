# Implementation Log

## Baseline

- Branch: `codex/081-engineering-workflow-templates`
- Starting commit: `17f7a816e7be118e40d062f1cdb8d2508fd8e0f6`
- Canonical UI authority: `docs/contributing/workflow-ui-integration.md`
- Latest reviewed editor lineage: `codex/080-canonical-workflow-recovery`; frontend implementation `4cfab9ba`, corrections through `629de4f2`, handoff documentation `87706742`
- Current integrated entry: `apps/web/src/components/chat/WorkspacePanel.tsx` → `apps/web/src/components/pages/WorkflowRecoveryPage.tsx` → `apps/web/src/prototypes/workflow-recovery/WorkflowRecoveryConcept.tsx`
- Current semantic source/runtime: workspace `.workflow.wflow` source plus separate layout/run state in `packages/workspace_service/src/workspace_service/`

The checkout already contained unrelated MCP-catalog tracked changes and local test/discovery artifacts while this feature branch was being prepared. They are not owned by feature 081 and will not be staged, reverted, reformatted or used as passing implementation evidence.

## Ignore-rule verification

Verified before code changes:

- `.gitignore` covers Python bytecode/environments, Node modules/logs, build/dist outputs, Playwright/test output, local runtime state, databases, vault data, credentials and common editor/OS files.
- `.dockerignore` covers Git, Python/Node caches, builds, test/artifact output, environment files, credentials and local state. Feature 081 runtime assets live inside the packaged workspace-service source and are not excluded.
- `.prettierignore` exists. ESLint configuration is repository-managed; no missing feature-specific ignore was identified.
- No ignore-file edit is required for this feature setup.

## Task-generation and analysis

- Generated 72 dependency-ordered tasks across four user stories.
- Format validation: 72 distinct sequential IDs, zero malformed task rows.
- Cross-artifact analysis: 26/26 functional requirements and 10/10 buildable success criteria covered; zero placeholder, unmapped-task, critical, high, medium, low or constitution findings after correcting the core/application ownership assignment and removing push from current implementation scope.

## Implemented UI and catalog

- Added an immutable, digest-checked catalog with exactly ten ordered engineering workflow definitions, layouts, local SVG previews, rights metadata, expected artifacts, external effects, and truthful readiness facts.
- Added atomic fresh-instance creation over the canonical workflow source service. Source, layout, committed head, and immutable template origin are written under one lock and rolled back together on failure. Same-request retries are idempotent; other filename collisions fail without overwrite.
- Added list, detail, preview, readiness, and instance API routes plus typed browser clients.
- Integrated **Start from template** beside the existing New/Open actions. The dialog supports keyboard option navigation, visible focus, details, safe naming, explicit create, and read-only cancellation.
- Added original local fixtures for the printed replacement and sheet-metal examples and an attributable Raspberry Pi 5 manufacturer-reference descriptor.

Validation:

- Catalog/storage suite: `69 passed, 2 skipped` (host-dependent skips).
- Template/API focused suite: `13 passed` with one Starlette deprecation warning.
- Web component/client/source/run/approval/capture suite: `100 passed` across four files.
- Served workspace Playwright journey: final focus-aware run `2 passed (5.5s)` using the normal Workflows control.
- Production web build: passed; only existing Vite config-loader and chunk-size warnings.
- Final shared backend/storage foundation suite: `58 passed`; source/run regression suite: `40 passed`; feature API slice: `7 passed`, each with only the existing Starlette test-client deprecation warning where applicable.

## Engineering execution foundation

- Added versioned validators for additive manufacturing, sourced enclosure CFD, and sheet-metal supplier handoff outputs. The validators require measured artifacts or computed fields and can return inconclusive without promoting a result.
- Added data-vault migration 20 and durable compare-and-swap checkpoints for exact human approval subjects and one-shot continuation.
- Added get, decision, resume-authority, and reconciliation APIs. Resume records `not_dispatched` before an adapter may act; `outcome_unknown` is explicit and cannot become proof of completion.
- Canonical source execution now compiles exact external-action approval blocks, pauses before mutation, persists completed-step continuation, and resumes only after the API recomputes current definition/input/artifact digests inside the authorized workspace.
- Added rights-checked local capture packages over verified immutable artifacts. Capture records disclose fixture/simulation and external-action state and have no publishing path.
- Approval mutation/race/restart, migration, and API tests pass. No printer, supplier, purchase, payment, social publishing, or other external mutation was executed.

The first three definitions are complete reviewable engineering sequences and remain `setup_required`. Their image-to-mesh/slicer/P1S, AgentCAD/CFD, and current supplier-browser paths still require clean-environment qualification with user-provided hardware, accounts, credentials, and licensed hosts before the catalog may label them Ready or Verified. The other seven intentionally remain `reference`.
