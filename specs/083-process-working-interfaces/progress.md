# Feature 083 progress

**Date:** 2026-09-30.
**State:** Goal submitted; implementation active on
`codex/083-process-working-interfaces`. Planning history remains below. No physical
action or protected campaign execution is authorized.

## Authority and context

- User selected complete experience, AI UI creation through Wright/default coding
  role and preflighted long-running processes with declared interaction points.
- Latest instruction authorized preparing this technical plan and saved goal.
- Prepared on `codex/prompt-to-3d-printed-part-demo`; proposed implementation branch
  is `codex/083-process-working-interfaces`.
- Existing `.specify/feature.json` and managed 082 AGENTS block are preserved until
  T001 activation after goal submission. Prior runtime/prototype edits are retained.
- Goal submission approves this package and the explicit local/test authority in
  [implementation-goal.md](implementation-goal.md); saving it does not activate it.

## Planning work

Prepared spec, technical plan, research, data model, three contracts, acceptance
cases, quickstart, 57 ordered tasks and saved goal. Read current architecture/
constitution/vision/editor/demonstration/MCP guidance. Three read-only research
subtasks inspected runtime, hosting and coding role/provider proof seams.

Resolved material gaps: per-run input overlay, observer-independent execution,
structured response barriers, neutral approved MCP operation, public kit/client
packaging, effective scoped coding instructions, fixed app build, presentation-bound
process authority and existing document-tab integration. These are proposed work,
not already supported capabilities.

Spec Kit plan/tasks templates applied directly. Bash setup returned access denied;
no PowerShell equivalents exist. Optional pre/post `speckit-git-commit` hooks
(commit plan/tasks) and `speckit-agent-context-update` hook (refresh pointer) were
left unused; no mandatory plan/tasks hook was registered. Context activation
remains an explicit implementation step rather than an incidental planning write.

## Implementation milestones

| Milestone | Task coverage | State |
|---|---|---|
| M0 Baseline/preflight | T001–T004 | Complete; live qualification remains later work |
| M1 Inputs/runtime/interaction | T005–T016, T022–T028 | In progress; contracts/persistence/service boundary complete |
| M2 Client/kit/common tabs | T017–T021 | Pending |
| M3 Wright AI authoring/hosting/reuse | T029–T042 | Pending |
| M4 Different processes/migration | T043–T049 | Pending |
| M5 Distribution/verification/handoff | T050–T057 | Pending |

## Implementation entries

### 2026-09-30 — M0 setup complete (T001–T004)

Created feature branch and activated 083 context after preserving dirty-file hashes
and prior pointer/guidance. Inspected current editor/runtime/agent/hosting boundaries;
normal UI ports are down, so no browser verification is claimed. Git Bash prerequisite
check and completed planning checklist pass. Python/frontend tooling and Docker are
available. Existing Hermes health/authenticated models checks pass without exposing
credentials; actual generation and scoped role remain pending. Blender host is not
listening; provider qualification is later work. Frozen proof inputs/profile digests
and test-policy constraints are saved, without enrolling or executing campaign work.

Evidence: [baseline](evidence/baseline.md), [resources](evidence/prerequisites.md),
[proof scope](evidence/proof-scope.md). Next: T005 strict versioned domain contracts
and shared schema fixtures, followed by additive persistence.

### 2026-09-30 — Foundation contracts/storage/boundaries (T005–T007)

Added strict versioned process/input/response/UI/role/build shapes and packaged
generated schema fixtures. Added migration 22 with immutable snapshots, exact
start/response receipts, saved revisions, active-revision CAS and bounded durable
authoring jobs. No competing run table/lifecycle authority was introduced.
Application service composition reuses the accepted source owner, checks scoped
workspace/capabilities/digests, and supplies readable redacted bounded errors.

The first contract run was intentionally red before implementation. A huge
parameterized test ID caused an initial test-fixture error; explicit IDs fixed
the test setup. Storage and service tests were likewise written and run red
before their modules existed. Foundation/regression checks now pass. Workspace
regressions require temporary roots outside the application checkout; the first
inside-checkout run was rejected by the existing protected-path guard and the
corrected outside-checkout run passed. Evidence: [foundation](evidence/foundation.md).

Remaining: projection/API, input readiness/overlays, run supervision, declared
responses, client/kit/tabs, actual AI authoring, both engineering proofs and
distribution/browser acceptance. No UI or live engineering proof is claimed.
Next: T008 projection/currentness negative tests and T009 authority composition.

Local milestone commit: `c417eca0` (contracts, persistent metadata, service boundary,
approved plan and vision guidance). Runtime/prototype files remain outside this
commit. A subsequent document-format cleanup fixes intentional Markdown trailing
spaces that the first staged whitespace check reported; no runtime scope changed.

### 2026-09-30 — Projection tests and pure fold (T008; T009 partial)

Added 24 pure interaction/result/currentness tests and the presentation fold.
Cases retain exact run/port/hashed representation, distinct recorded waiting/
cancellation/unknown states, backend blocking reasons and restricted scopes.
Two tests obtain real 082 structured-output assessments/currentness from the
existing validator; changed bytes do not acquire their old assessment reference.
A passing assessment does not grant a blocked action. Attached runs use their
own frozen snapshot; legacy unknown inputs are not filled from a newer preparation.
History keeps its original accepted source identity and blocks changed-source
mutations. Evidence: [projection](evidence/projection.md).

T009 remains pending for composition with source/input readiness, exact recorded
run loading, checkpoint/review/current-action owners and paged runtime facts.
This pure fold is not a served API or a replacement execution/status authority.

Combined contracts/storage/service/projection and affected workspace/082/v2
continuation/event-fold regressions: **187 passed, 1 host symlink skip**.
Exact command is recorded in projection evidence. No live service handle is left
running by these tests. All required runtime/UI/model/MCP/distribution work remains
in the unchecked tasks; no goal completion or engineering acceptance is claimed.

Projection/document cleanup commit: `1c67af61`. The staged whitespace check and
new-module Ruff check pass. Next task is full T009 owner composition, followed by
T010 thin API routes and T011/T012 readiness and input overlays.

### 2026-09-30 — Exact recorder attachment and owner composition (T009 partial)

The preceding user status turn verified the active goal and saved commits but
made no implementation change. This turn resumes concrete work: exact read-only
recorder attachment, shared ownership reconciliation, run input receipt lookup,
scoped paged assessment identities, canonical approval permission inspection,
terminal review evidence checks and attached-run interaction composition.
Pure projection now pages large views with references bound to actual scoped
facts. No new execution/review/status authority was introduced.

The new tests were run red before implementation. Combined affected regressions
pass: **272 passed, 1 host symlink skip**. Details, exact command, fixture repairs
and limits are in [owner composition evidence](evidence/owners.md). No test
process remains running. T009 stays unchecked for source-input/readiness
composition; next work connects that implementation and thin authenticated API
routes. All runtime/UI/live-model/live-MCP/distribution finish requirements remain.

Local owner-composition milestone commit: `d1020aa5`. Only its 14 owned files
were staged. Pre-existing runtime/prototype and protected campaign/binding hashes
remain unchanged. No services or test handles remain running from this increment.

### 2026-09-30 — Inputs and preparation composition (T009, T011, T012)

The preceding user status turn checked the active goal and saved work. It made
no implementation changes. This turn completed the shared source-default/run-input
conversion, immutable overlay execution, generic read-only provider choices,
schema/file/freshness/provenance checks, known MCP argument preflight and service
preparation/readiness composition. Accepted source and recorded-run input ownership
remain unchanged. T009, T011 and T012 are now checked; T010 remains next.

Affected recorder/review/storage/continuation/082/input regressions: **354 passed,
one host symlink skip**. Source/CAD/application checks: **75 passed**. Current
contracts and public-option-freshness checks: **78 passed**. Exact commands,
metadata format, corrections and limits are in [input evidence](evidence/inputs.md).
The input checks and service behavior use controlled fixtures, not live engineering
providers or generated interfaces. No test handle remains running after completion.

No API/browser/common UI/model-generation/live-MCP/distribution proof is claimed.
The full goal remains active. Next work wires authenticated source/input/readiness
routes and the existing executor's backend-owned lifetime with durable identities.

Focused local input/readiness commit: `db06be6a` (18 owned files). Ruff/format
and staged whitespace checks pass. The 11 preserved runtime/prototype files and
three protected review/binding files still match the recorded baseline hashes.

API reconnaissance confirms the existing persisted `_workflow_source_scope`,
engineer/admin validation-role gate and shared error handler in the workspace
mount. T010 should compose these; the process-interfaces prefix needs bounded,
non-echoing validation errors and no-store responses. No API source was changed
by this reconnaissance. Existing native gateway sessions are scoped to the
persisted workspace session; no client-supplied principal/capability is accepted.

### 2026-09-30 — Authenticated process transport (T010)

Previous goal turn made concrete progress and saved input/readiness commit
`db06be6a`. This turn added the thin native snapshot/input/readiness routes and
request envelopes, retained persisted workspace binding/engineer-admin role
authorization and existing control-plane authentication/origin checks, bounded
request bodies and removed value/tag/context echoes from new-prefix errors.
Recorded-run attachment retains its exact checkpoint and never replays work.

The new tests were observed red before implementation. Focused checks: **11
passed**; combined source/run/review/continuation/082/security API regressions:
**73 passed, one existing skip**. Exact command and scope are in
[API evidence](evidence/api.md). T010 is checked; foundation T005–T010 now exists.
No UI, live model/MCP or distribution completion is claimed. The full goal remains
active, with T013/T014 backend-owned task/receipt/attachment/cancellation work next.

Focused local API commit: `5a8f2ea0` (eight owned files/hunks). UTF-8 comparison
confirms the original nine-line main.py prototype addition remains exactly
unstaged. Main patch staging required LF normalization; a preservation check
initially used the Windows default text encoding and was corrected to explicit
UTF-8. Source/prototype contents were not rewritten by those checks.

### 2026-09-30 — Backend-owned run identity, observation and local cancellation

The prior status turn produced evidence: 35 run/record recovery tests passed,
confirming the interrupted chat connection did not lose the existing changes.
This implementation turn completes T013/T014 and the native transport portion of
T015. T015 stays unchecked until the old source-start stream is migrated; its
request-owned disconnect behavior is still present and is not claimed fixed.

The new bounded supervisor composes the existing preparation/executor/recorder,
retains exact receipts/log locators, survives observer loss and reconstructs
recorded terminal/waiting/interrupted facts without replay. Recorded cancellation
commands also retain backend ownership; storage/runtime cleanup and initial
start publication races have focused tests. Workspace shutdown closes run owners
before file workers, including its error path. Exact source/actor/run-bound event
pages expose progress metadata rather than engineering/tool payloads.

Native start/attach/SSE/cancel routes preserve current scope/auth/origin/RBAC and
no-store errors/responses. Final focused checks: **26 passed**. Broader affected
checks before two final added cases: **256 passed**. Tests were observed red for
missing APIs/events, a cancellation observer race and immediate attachment, then
green after implementation. Exact commands/limits are in
[run evidence](evidence/run-supervision.md). Ruff passes; no live model, MCP,
browser, engineering acceptance or distribution completion is claimed.

Next: migrate the legacy source-start stream onto the same durable supervision,
then provider observation/cancellation and the public client/common UI. The full
M0–M5 goal stays active. No push/merge/release or physical dispatch is authorized.

Final affected/security rerun: **272 passed, one existing skip**, 33.19 seconds.
All checked handles reached completion. Twelve preserved runtime/prototype files,
three protected review/binding files and the original main.py prototype patch
match the baseline. T013/T014 are checked; no later task is checked prematurely.

## Implementation progress format

Append dated entries: task IDs, branch/commit/build, owned files, exact commands,
run/subject/artifact identities, observations/evidence links, failed/pending scope,
resources required and next task. Keep task checkboxes aligned. Do not replace
this log with optimistic stage labels or claim user acceptance without user feedback.

At the planning checkpoint, validation passed: 13 feature documents, 39 resolved local links,
57 sequential task IDs/paths and complete FR/SC coverage. All 12 preserved-file
hashes match; managed 082 context equals HEAD, and `git diff --check` passes.
See [checklists/requirements.md](checklists/requirements.md). Current implementation
and test status is recorded in the dated entries and task checkboxes above.
Served browser checks, live engineering qualification and distribution proof remain pending.
