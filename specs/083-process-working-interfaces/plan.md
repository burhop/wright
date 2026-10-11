# Implementation Plan: Process working interfaces

**Feature:** `083-process-working-interfaces` | **Date:** 2026-09-30
**Prepared branch:** `codex/prompt-to-3d-printed-part-demo`
**Implementation branch:** `codex/083-process-working-interfaces`
**Spec:** [spec.md](spec.md) | **Status:** Approved by goal submission on 2026-09-30; implementation active.

## Summary

Deliver complementary authoring and working experiences on the same accepted
Wright process and durable run. Implement a small process interaction projection,
immutable run inputs, backend-owned execution, declared human responses, a public
scoped client/UI kit, a common workspace view and AI-created reusable interfaces
generated through Wright. Prove the full experience with existing manufacturing
preparation and thermal-analysis processes, preserving engineering verification.

The complete scope includes M0–M5 in [tasks.md](tasks.md). M1/M2 are useful
increments, not the requested finish line. Submitting
[implementation-goal.md](implementation-goal.md) approves this concrete package
and authorizes implementation; saving this plan does not start it.

## Technical context

| Area | Choice |
|---|---|
| Language | Existing Python >=3.11 supported lanes; TypeScript/React19 frontend |
| Backend | FastAPI/Pydantic; canonical source compiler/execute_prompt_workflow; gateway; source-run recorder/leases/continuation; 082 validator |
| Frontend | Existing npm lockfile, TypeScript/Vite; public local/pinned client+kit packages; existing tokens, viewers and workspace tabs |
| Agent | BaseAgentEngine + optional invocation context; qualified Hermes inherited-default-model first path; separate coding role/instructions/model/platform |
| Storage | Additive SQLite WAL repositories/migrations and immutable vault source/input/build artifacts; existing run record remains authority |
| Hosting | Existing managed surfaces with generic installed static-asset runtime, isolated preview origin and presentation-bound process bridge |
| Tests after approval | pytest contracts/services/API/recovery; Vitest components; mocked Playwright journeys; served workspace + real default model/MCP proof; installed native/Docker checks |
| Targets | Supported native runtime and Docker appliance; no production need for source checkout; authoring compiler is an explicit capability |
| Initial scope | Supported canonical source data/order DAG + bounded current rework; no new arbitrary graph scheduler; two actual engineering proof journeys |
| Bounds | Contract limits for inline inputs/snapshots/UI bundles and fixed builds; gateway/reader budgets remain controlling |
| Performance | Start returns run identity without waiting for a tool/LLM; observations do not keep execution request alive. Measure progress delivery/reconnect on evidence host; use recorded events and bounded pages, not unbounded browser histories |
| Offline | Common view, saved built interfaces, result inspection and local providers work offline. AI generation uses configured available model; unavailable cloud/model/compiler is explicit, not a hidden dependency of saved UI use |

Use current lockfile versions, not arbitrary dependency upgrades. No new npm
publication, package manager, cloud identity service or database daemon is planned.

## Constitution check

Pre-design and post-contract checks against constitution v3.1.1: aligned by design.
Runtime/distribution/security/browser gates remain to be executed after approval.

| Principle | Design compliance and implementation evidence |
|---|---|
| 1 Modular/offline | Pure contracts in core; storage in data_vault; application logic in workspace_service; adapter changes in agent_adapters; thin routes; offline common/saved UI |
| 2 Execution/distribution | Same source runtime/gateway; installed public kit/client/instructions/asset runtime; qualified local authoring compiler; no provider host software added to base image to pass tests |
| 3 Embedded storage | SQLite WAL and bounded vault artifacts; no second lifecycle database/authority |
| 4 Identity | Existing local auth/origin/RBAC; presentation-derived scopes; generated JS has no admin/device credentials |
| 5 Tool isolation | Existing independent MCPs through gateway; no GUI/vendor workaround; any LLM-facing added authoring tool follows existing BaseTool boundary |
| 6 UI/testing | Tokens/primitives/patterns, test IDs and three tiers; served workspace entry preserves refined editor |
| 7 Traceability | trace_id through generation/build/run/gateway/storage; readable UI diagnostics; exact prompts/instructions/tool arguments/evidence available on demand |
| 8 Phase/branch/review | Planning only now. Submitted goal approves package and explicitly permits unattended local work between implementation milestones; actual process reviews and external authority remain intact |
| Governance | No constitution amendment. Push/merge/release runbooks apply only at separately authorized transitions |

### Planning workflow exception

The Spec Kit plan/tasks templates and hooks were read. Bash setup failed with
`Bash/Service/CreateInstance/E_ACCESSDENIED`; there is no PowerShell setup equivalent
in this checkout. Artifacts were prepared directly with explicit feature paths.
Optional commit/context hooks were left unused. `.specify/feature.json` and the
managed 082 AGENTS block remain unchanged as required by the agreed roadmap.
Feature activation is T001 after goal submission, with prior context retained.

## Workflow platform alignment

- **V1 Workflow definitions own the process:** No required manufacturing lifecycle, device/control panel,
  camera or print action. Different process layouts consume the same interactions.
- **V2 Wright owns reusable mechanisms:** Existing source/compiler/recorder/gateway/rework
  owns execution. New supervisor owns task lifetime, not graph semantics.
- **V3 Independent vendor integrations:** Existing MCPs own engineering/vendor behavior.
  Operational Bambu/Studio/camera/AMS code is migration debt, not a platform service.
- **V4 Consistent and specialised interfaces:** Existing editor plus common/tailored working tabs; same
  input/run/decision context, useful errors and exact navigation; close != cancel.
- **V5 Requirements and exact-output verification:** Existing result/assessment/review
  identities remain authoritative. UI/model success cannot validate output or
  approve a subject; missing required capability/evidence blocks rather than guesses.
- **V6 External-action evidence and uncertainty:** Exact configured authority,
  receipt and observations; submission/start/completion/cancellation are distinct;
  unknown outcomes cannot authorize replay.
- **V7 Replaceable AI and integrations:** Small versioned interaction/client/kit/UI/role contracts with
  compatibility/fallback, not universal screen language or a new agent platform.

User journey: open accepted process → common view → prepare inputs/readiness →
optional Create interface in Wright → preview/save → start/follow → declared
decision/response → inspect results/evidence → return/reuse/update. Definition
edits and run inputs are separate. No routine runtime questions are improvised.

## Architecture and ownership

```text
accepted source + immutable inputs + configured provider capabilities
                         |
            existing source compiler/preparation
                         |
 backend-owned run task -> existing executor/gateway/recorder/082 checks
                         |               |
                declared checkpoint   exact results/evidence
                         \               /
                  interaction projection/use cases
                         |
              public scoped client + shared UI kit
                  /                       \
       native common workspace tab    isolated saved UI workspace tab
                                             ^
                               Wright coding-role authoring/build/preview
```

Interaction projection is read-side composition and guarded command adaptation.
It is not a second executor, validator or status source. Generation/build is a
separate presentation-authoring job, not an engineering process run.

### M0 — Baseline and bounded authority

Create feature branch without losing dirty prototype work. Record prior pointer,
changed files, source/runtime hashes, current served editor/build/flags and owned
services. Activate 083 only there, preserving stable guidance and 082 history.
Inventory exact existing contracts and live prerequisites; freeze two isolated
proof roots/provider bindings. Capture a local capability/readiness report before
spending a long run on unavailable models/compiler/tools. Keep working on unaffected
platform tasks if a proof resource is missing; never fabricate its completion.

### M1 — Inputs, interactions and durable execution

Implement contracts in core/data_vault/workspace_service. Add immutable input
overlay to current preparation/execution/continuation. Analyze supported dependency
paths and reject unresolved required choices. Add declared `human-input` step and
v3 checkpoints while preserving v2. Bind existing reviews/082 assessments/actions
by exact subject. Enforce the unattended interaction policy.

Split start from observation with durable idempotent receipts and backend-owned
task/lease supervision around the current executor. Reopen waiting/completed
records; interrupted uncertain active work follows current reconciliation rules.
Use existing async-operation monitor with finite policies, not unlimited model calls.
Add neutral approved `mcp-operation` dispatch through current gateway/consume
authority for configured operations; qualify with a nonphysical isolated provider.

### M2 — Client, kit and common workspace journey

Create public packages with native and presentation-bound transports. Extract
tokens/accessibility/useful format viewers; fix theme/private-import assumptions.
Common schema forms include image thumbnails, units and configured option lists.
Results show representations, actual tool contributions, checks, findings and
downloads. Toolpath viewer uses actual bounded parsed package data, all supported
layers, orbit/zoom/layer control; absent support classifications are unknown, not
zero or fabricated geometry. Reuse 3D/rendering dependencies already present.

Integrate typed tabs into existing document host with exact navigation and durable
restore/fallback. Preserve flowchart/source/drag/ports/undo/save/layout/conflicts.
Native and isolated transports share backend currentness and action semantics.

### M3 — AI-created reusable UI through Wright

Introduce bounded coding role on current adapter boundary; default model inherits
actual config. Instructions and enforced scope survive every turn. Generation
does not enable every workspace MCP or mutate global Hermes configuration.

Fixed static-app builder validates paths/imports/bindings, compiles using pinned
resources and emits immutable bundles/build reports. Reuse managed hosting with
server-derived process scopes and generic asset runtime. Preview opens read-only
in a Wright tab. Save/update/rollback persists versioned source/build/compatibility
and actual generation provenance. Required stale bindings disable mutations and
offer common view; opening saved UI needs neither model nor build tool.

### M4 — Migrate/prove different engineering processes

Follow [acceptance-cases.md](acceptance-cases.md). Freshly qualify existing independent
providers with actual schemas/requirements. Preserve original assignment/material/
profile/analysis authority; configured external bindings own vendor choices.
Use actual geometry/slice artifacts and actual CAD/thermal fields, not canned UI
data. Generate both tailored UIs through Wright and verify common/tailored parity.

Migrate prompt-to-part entry/callers to accepted workflow+shared services/UI. Remove
active vendor startup/dispatch/telemetry/camera/Studio code after migration. Preserve
old links via read-only historical result adapter; no old dispatch workaround
remains as a hidden fallback. Campaign sources/evidence remain immutable references.
A missing provider blocks the applicable live proof, not core development, and
does not justify a new Wright-owned vendor project.

### M5 — Package, verify and hand off

Run targeted contract/runtime/security/UI tests, actual served-workspace browser
walkthrough and installed native/Docker checks. Ship public resources using existing
package assets/build mechanisms. Installed saved UI needs no checkout/build.
Publish reproducible operator/developer instructions, evidence index and completion
report. Reporting UI remains another branch; share result/assessment references.
Technical verification and user engineering/product acceptance remain separate.

## Concrete source structure

New filenames below are intended ownership, not a promise they already exist.
Refactor within those owners when actual code warrants it; preserve public contracts.

```text
packages/core/src/core/
  process_interactions.py               # pure versioned shapes
  process_interfaces.py                 # UI bindings/role/build contracts
packages/data_vault/src/data_vault/
  process_input_repository.py           # snapshots/start/response identities
  process_interface_repository.py       # immutable UI/job metadata
  workflow_continuation_repository.py   # additive v3 compatibility
packages/workspace_service/src/workspace_service/
  process_interfaces/                  # readiness/projection/input/run/authoring/build
  process_interfaces/resources/        # packaged role/docs/template/kit distributions
  workflow_source_execution.py          # same compiler/executor, explicit barriers
  workflow_run_preparation.py           # run input overlay
  workflow_execution_continuation.py    # same-run restoration
  workflow_approval_execution.py        # neutral bounded gateway action
  surfaces/                            # asset host/scoped process binding
packages/agent_adapters/src/agent_adapters/
  base.py / hermes.py                   # optional scoped invocation capabilities
packages/process_client/                # new public TypeScript package
packages/ui_kit/                        # new public React/CSS package
apps/api/src/api/
  routers/process_interfaces.py         # thin routes
  schemas/process_interfaces.py
  routers/surface_preview.py            # reserved scoped bridge
apps/web/src/
  components/process-interfaces/        # common view + authoring experience
  components/chat/WorkspacePanel.tsx    # current document tab host
  store/viewer.tsx                     # typed process-tab view intent
examples/process-interfaces/            # neutral bindings/reference instructions
tests/ui-integration/                   # mocked common/generated journeys
tests/e2e/                              # scoped served/live smoke evidence
```

Relevant existing seams and reasons are recorded in [research.md](research.md).
Contracts: [interaction API/client](contracts/process-interaction.md),
[runtime/source](contracts/runtime-and-source.md),
[UI/agent/hosting](contracts/ui-authoring-and-hosting.md).

## Compatibility, migration and rollback

- Keep legacy source/read/run links, source defaults, v2 approvals and historical
  result digests. Compatibility routes for old demo links are read-only.
- Additive data migrations, immutable UI revisions and explicit active-revision
  pointer allow rollback. Do not remove old campaign files or rewrite assertions.
- Unsupported UI/version/schema returns common view and focused repair. An active
  process source change invalidates affected inputs/actions/reviews as required.
- Flag new entry during integration if needed, but final acceptance uses the normal
  served workspace Workflow/Workflows control. A detached route is insufficient.
- Inspect all transitive callers before retiring vendor modules. Retained metadata,
  evidence, fixtures and external capability bindings may name vendors; platform
  execution/services must not implement their protocols or workarounds.
- Avoid unrelated native/Rivet editor takeover, all-30 campaign expansion and new
  reporting application. Nothing here adopts pending campaign decisions.

## Evidence, limits and completion

Every required task records code/build identity, exact commands/run IDs, artifact
references and observed scope in [progress.md](progress.md). Completion requires
the selected live model/UI and engineering demonstrations, not only fixtures or
schemas. Success includes honest failing engineering findings held for review;
it does not require inventing a pass.

Physical printing, supplier dispatch, public provider promotion, production
release and human acceptance are outside this implementation goal. Generic action
tests establish only the observed nonphysical scope. The first supported thermal
solver consumes measured rectangular STEP dimensions; it does not claim arbitrary
CAD-topology meshing or general FEA qualification.

No product questions remain. Missing live resources/authority and materially new
engineering assignments must be disclosed, not silently substituted. Routine
implementation choices within this package are the coding agent's responsibility.

## Complexity tracking

No constitutional deviation. Two TypeScript packages separate the reusable public
contracts/presentation from the private shell; existing Python package boundaries
remain intact. The backend supervisor and static asset host manage existing task/
presentation lifetime and do not add graph or agent execution engines.
