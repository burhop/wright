# Declared interaction implementation evidence

## Current named runtime verification

The [current runtime primary evidence](../../../artifacts/process-interfaces/083/20261003-named-runtime-checks-primary-verified/README.md)
maps all seventeen named checks to exact current test bodies and 81 fresh passing
parameterized cases. It retains same-run two-input barriers, immutable and stale
responses, lost-ack/concurrent single use, actual ASGI observer detach, safe owner
recreation, preserved uncertainty, observed cancellation and finite model/operation
budgets. Undeclared questions fail diagnostically without creating another form.
Separate current owner lookup reads two fresh persisted v2 approval records
unchanged. These are controlled digital runtime/transport fixtures; no protected
checkpoint, live engineering provider or physical action is invoked.

## 2026-10-01 — Accepted-source declaration and editor preservation

**Scope:** T022 completed; T023 is in progress. T024–T028 are pending.
This milestone implements and checks the declaration/compiler boundary. It does
not yet implement durable human-response storage or same-run resumption.

The existing JSON-valued task grammar now accepts `authoring_template=human-input`
with an explicit version-1 `human_interaction`. The compiler requires an Engineer
work step, connected upstream evidence, bounded object response schema and exactly
one single `structured_result` response port. The compiled step is a distinct
barrier descriptor, without an AI prompt, tool call or approval action. Required
evidence ports must have producers. Unsupported conditional connections, implicit
declarations, extra execution bindings and automatic correction segments crossing
the barrier are rejected. This does not expand the supported graph/rework scope.

Readiness distinguishes a consumer's `declared_human_response` dependency, pinned
to the interaction step and response port, from `upstream_produced`. A future
answer is not required as an initial run value. Source input metadata continues
to use the existing bounded conversion/default/schema owner.

The refined editor preserves both `interaction_input` and `human_interaction`
nested objects using its existing managed configuration retention mechanism.
Cold parse/format/reparse and served Source editing/save/reopen retain the schema,
required fields, additional-properties policy, port and Engineer performer.
Source storage remains opaque; the existing source store is reused unchanged.

**Current execution limit:** `prepare_prompt_workflow` rejects a workflow with
human input as `WORKFLOW_HUMAN_INPUT_UNAVAILABLE` before tool qualification or
execution. Direct executor entry also rejects such a step rather than invoking
an LLM for it. These explicit temporary capability guards must be replaced by
T024's durable v3 checkpoint implementation. They are not the completed process
experience and do not satisfy waiting/resume acceptance. No actual runtime AI
clarification policy is claimed here; that is T025.

### Shared fixture and verification

[declared-human-input.workflow.wflow](../fixtures/declared-human-input.workflow.wflow)
is an explicitly synthetic compiler/editor fixture, not an engineering proof.
Its SHA-256 is
`bc9138c226242b6a89df3e3ea0d1ea18f35acac568de123ee988628c48baeea4`.
A backend check requires the committed cross-language fixture to match the
source factory. Original campaign workflows, assignments and checkpoints are
unchanged. No human or integration-test engineering decision was submitted.

Backend command from repository root:

```powershell
.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t022-milestone packages/workspace_service/tests/test_process_human_input_source.py packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_workflow_source_execution.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_design_check.py packages/workspace_service/tests/test_workflow_sources.py
```

**185 passed, two skipped** in 13.32 s. The existing source/lock symlink checks at
`test_workflow_sources.py:468` and `:576` cannot create symlinks on this Windows
host (WinError 1314). This is not cross-platform symlink verification; retain that
obligation for the required installed/Docker checks. Private output:
`.local-run/process-interfaces-083/t022-milestone-pytest.log`.

Frontend command from `apps/web`:

```powershell
node ../../node_modules/vitest/vitest.mjs run src/prototypes/workflow-recovery/recovery-authoring.spec.ts src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx src/components/pages/WorkflowRecoveryPage.spec.tsx src/components/process-interfaces/CommonProcessView.spec.tsx --reporter=json --outputFile=D:/repos/wright/.local-run/process-interfaces-083/t022-ui-final-vitest.json
```

**126 passed** across four files. App/browser-test type checks, focused Ruff and
ESLint pass; one existing `presentedRun` hook warning remains. A fresh production
build at `.local-run/process-interfaces-083/t022-source-ui-build` passes with 927
modules in 1.81 s. Browser checks used separately served development Vite 8.2.0,
not those production assets.

### Served normal-workspace check

Used the already-qualified private system-Chrome configuration and a separately
owned Vite process on 5238, with workflow recovery/definition/composer flags set.
Entered through the normal workspace Workflows control. Installed Chrome
154.0.8037.58, 1280×720. **Four distinct browser checks pass** in 22.1 s:

- Declared metadata/schema Source edit, apply, save and cold reopen; zero starts.
- Exact 082 requirements-review subject, requirement IDs/text and source locators.
- Invalid draft containment and subsequent canvas/source/AI authoring controls.
- Typed handles and layout-only save with unchanged accepted source/revision.

```powershell
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5238'
$env:WRIGHT_PLAYWRIGHT_OUTPUT_DIR = 'D:/repos/wright/artifacts/process-interfaces/083/20261001-t022-milestone'
$env:PLAYWRIGHT_JSON_OUTPUT_NAME = 'D:/repos/wright/.local-run/process-interfaces-083/t022-milestone-playwright.json'
node node_modules/@playwright/test/cli.js test tests/ui-integration/process-declared-interactions.spec.ts tests/ui-integration/process-validation.spec.ts tests/ui-integration/workflow-recovery.spec.ts --grep 'preserves declared input schemas|exact human requirements review|keeps one accepted definition|uses real typed handles' --config .local-run/process-interfaces-083/playwright-system-chrome.config.ts --project=chromium --workers=1 --reporter=line,json --global-timeout=120000
```

Use fresh output/temp directories when reproducing. The declared-interaction
browser file currently checks source authoring only; its checkpoint-consumption
journey remains to be added in T028. HTTP contracts are controlled fixtures.
No live API, default model, MCP, engineering acceptance or hardware is claimed.
The existing React Flow attribution warnings and one unrelated surfaces-event
proxy refusal to the unstarted API on 8000 were observed; this is not a clean
live-backend integration claim.

Retained scope and screenshots:
`artifacts/process-interfaces/083/20261001-t022-milestone/`.
The scope record includes exact original/saved source hashes, saved revision,
workspace/path and zero controlled starts. No credentials are recorded.
The source screenshot depicts the reopened accepted editor; assertions, not that
viewport image alone, establish nested schema preservation. The requirements
review was repeated after expanding the existing details drawer (**one pass** in
3.4 s); that screenshot shows the actual requirements and engineering-judgment
qualification. Its private report is `t022-review-expanded-playwright.json`.

Initial failures were test assumptions: the parser base must match `workflow test`,
the formatter emits bare performer enums, and the ready editor has no
`data-surface-state=ready` attribute. Corrected those assertions while retaining
identity/schema/save/reopen checks. An initial `import.meta` fixture read was
incompatible with this repository's Playwright module configuration; use its
established root-relative file loader. One negative backend assertion incorrectly
matched correction text against exception-message text; it now checks the
separate correction field. Preliminary failed reports remain private evidence.

The owned Vite process was stopped after verification. The ten original prototype
hashes, three protected campaign hashes, two mixed API deltas and approved 083
context match their intended baselines; private report `t022-preservation.json`.
No push, merge, release or external effect occurred. The complete goal remains active.

## 2026-10-01 — T023 runtime barrier / T024 durable backend

This supersedes the earlier temporary runtime guard for normal WorkspaceService
instances. The guard remains only when the owning process interface capability is
missing. Before any unattended execution, declared-input processes require an
already persisted immutable input snapshot. The canonical executor now stops at
the declared cursor and its existing recorder creates a v3 input checkpoint.
The original source store/parser and port validation remain authoritative.

Implemented backend scope:

- `process_interfaces/interactions.py` pins the source, frozen inputs, declaration,
  schema and connected upstream values; retains exact typed answer provenance.
- The existing continuation repository attaches immutable response evidence and
  its cursor reference in one SQLite transaction. Failure rolls both back.
  Duplicate identical response retries return the original identity; different
  actors/requests/reasons/values cannot replace it. Concurrent consumption is one-shot.
- Input checkpoints remain `pending` while an answer is retained, and become
  `consumed` on exact response consumption. They have no approval state or external
  action receipt. The approval service rejects input checkpoints.
- Existing recorder `resume_segments` claims govern resumed work, including
  read-only completed retries and refusal to replay an uncertain started segment.
  Execution records the real typed answer at its declared port, not “Approved.”
- New approval checkpoints with frozen run inputs use v3 and the existing approval
  dispatcher reloads that exact overlay. Original v2 checks and records are retained.

**T023 is complete. T024 remains pending** for public scoped response orchestration,
backend-owned continuation task lifetime and projection/currentness integration.
No response route or end-user input form is claimed here. T027/T028 require the
served common/tailored journey; this backend milestone is not that completion.

### Checked backend evidence

Windows, Python 3.13.5, branch `codex/083-process-working-interfaces`, base
`6d449f60`. Root command:

```powershell
.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t024-final packages/workspace_service/tests/test_process_interface_continuation.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_external_action_execution.py packages/workspace_service/tests/test_workflow_source_execution.py packages/workspace_service/tests/test_process_human_input_source.py packages/workspace_service/tests/test_process_run_supervisor.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_approval_resume.py packages/workspace_service/tests/test_workflow_approval_review_settings.py packages/workspace_service/tests/test_process_approval_inspection.py packages/workspace_service/tests/test_process_input_execution_overlay.py packages/workspace_service/tests/test_process_preparation_service.py packages/data_vault/tests/test_workflow_continuation_repository.py packages/data_vault/tests/test_process_interface_migrations.py
```

**184 passed, no skips, 58.45 s.** Private output:
`.local-run/process-interfaces-083/t024-final-pytest.log`. Reproduction needs a fresh
temp directory. Focused Ruff checks/formats and `git diff --check` pass.

Retained scope:
`artifacts/process-interfaces/083/20261001-t024-backend/checked-scope.json`.
It records actual test run/subject/schema/input/answer identities and provenance:

- `same-run`: two successive input barriers, service recreation between them,
  three synthetic model calls total, same original run file, two completed claims;
  neither completed retry calls the model. Both answers appear as structured results.
- `d4c67b00803d499a99d7a641b7c3bbb9`: declared input followed by v3 local review;
  the existing dispatcher restores distinct run inputs and completes the same run.
- `fa619d81b06b4e6fbc17820684e379c2`: injected backend failure after resumed model
  dispatch; the retained claim is `outcome_unknown` and retries are rejected.

These are real SQLite, workspace-file, compiler, source-executor and recorder
checks with synthetic model/reviewer fixtures. Input responses retain
`integration_test=true`; the local review retains an explicitly labelled
`isolated-unit-reviewer` and synthetic decision reason. No real human reviewed
engineering output, no campaign checkpoint was touched, and no external effect
occurred. This is not a default-model/live-MCP/HTTP/browser/distribution proof.

Initial fixture failures exposed the distinction between runtime JSON binding
values and separately published EngineeringResult evidence, and JSON tuple/list
normalization on retained retry payloads. The binding now follows existing typed
JSON response semantics; retry checks compare canonical wire content. Expanded
fixtures also needed globally distinct port IDs before accepted-source preparation;
all new source fixtures now undergo the existing authoring-shape validator.
Earlier failed runs remain private diagnostics, not passing evidence.

Preservation was rechecked: ten original prototype hashes, three protected campaign
hashes, two mixed API deltas and approved 083 context all match their baselines.
Private report: `.local-run/process-interfaces-083/t024-preservation.json`.
No owned server was launched. No push, merge, release or physical/supplier operation
was performed. All later UI-authoring, live engineering, migration and distribution
requirements remain in the active goal.

## 2026-10-01 — Scoped responses and supervised continuation

Base commit `9ac221a0`, branch `codex/083-process-working-interfaces`, Windows,
Python 3.13.5, Node 25.2.0, system Chrome. **T024 is complete.** T027/T028 remain
open for review/action controls, authoring and their full recovery/policy proofs.

### Implemented authority and currentness

- `POST /api/workspace/process-interfaces/interactions/{checkpoint_id}/response`
  accepts the existing source/session scope, exact subject, bounded typed value
  and request identity. Run and actor come from authorized context/checkpoint.
  Caller-supplied actor, run, reason, destination or integration-test authority is
  rejected. Existing role checks run before workspace resolution.
- The supervisor freshly prepares the accepted source with its retained input
  overlay and original run ID. Inspection verifies the exact declaration,
  connected upstream values, result/file inventory, actual file hashes and
  execution policy before an answer is accepted/consumed. Incomplete retained
  inventories cannot skip evidence hashing. Reading a pending input performs
  qualification only: it invokes no model and cannot accept/consume a response.
- The atomic answer is consumed, then an owned task invokes the existing source
  executor and `record_workflow_resume` on the same record. There is no suspension
  between consumption and retaining that task. Recorder claims precede effects.
  The observer lifetime remains separate; closing/disconnecting never cancels.
- Concurrent identical requests, completed retries and service recreation retain
  one immutable answer. An accepted/consumed response without an execution claim
  can finish its handoff after reopen; an unfinished claimed segment is unknown
  and cannot be replayed. Different values/actors/request identities conflict.
  Existing v2/v3 approval and 082 preparation/review regressions remain passing.
- Recorded projection exposes only the declared response schema, exact evidence,
  checkpoint and subject. Changed/expired evidence disables the action with a
  correction. Read-only capability scopes cannot respond.

### Implemented input controls

The public native client checks request bounds and acknowledgement identity/value,
retains uncertainty on a lost acknowledgement, and never retries automatically.
The shared `CheckpointCard.response` uses the existing schema editor and permitted
actions. The common view sends explicit responses, follows the same run and keeps
an uncertain answer frozen for explicit same-request reconciliation. Missing values
explain what to provide. Read-only, stale, busy and consumed controls stay disabled.
This milestone implements input controls; review/action controls remain pending.
Broader reload/tailored-host response recovery is still part of T028.

### Backend/API verification

Root command, with a new writable temp directory for reproduction:

```powershell
.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t024-response-final packages/workspace_service/tests/test_process_input_supervision.py packages/workspace_service/tests/test_process_interface_continuation.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_external_action_execution.py packages/workspace_service/tests/test_workflow_source_execution.py packages/workspace_service/tests/test_process_human_input_source.py packages/workspace_service/tests/test_process_run_supervisor.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_approval_resume.py packages/workspace_service/tests/test_workflow_approval_review_settings.py packages/workspace_service/tests/test_process_approval_inspection.py packages/workspace_service/tests/test_process_input_execution_overlay.py packages/workspace_service/tests/test_process_preparation_service.py packages/data_vault/tests/test_workflow_continuation_repository.py packages/data_vault/tests/test_process_interface_migrations.py apps/api/tests/test_process_interface_checkpoints.py apps/api/tests/test_process_interfaces_api.py apps/api/tests/test_process_interface_run_lifecycle.py
```

**231 passed, no skips, 96.76 s**, with two existing TestClient dependency
deprecations. Private log: `.local-run/process-interfaces-083/t024-response-final.log`.
Final focused inspection rerun follows the last defensive dictionary guard;
its exact output is `.local-run/process-interfaces-083/t024-response-inspection-final.log`.

Actual run `f93dc4dbe28449be85f521414306cb91` completes two supervised input barriers
with service recreation and three total synthetic model calls. Checkpoints are
`checkpoint-1c2b5ec1c8dcf8486fd879ed` and `checkpoint-cef2e51f8434995dbb1a6db4`.
The checked-scope artifact retains both subject/answer hashes and claims, plus
lost-ack, interrupted-claim and unclaimed-handoff examples. These tests exercise
real source storage, SQLite, executor and recorder. Models and input actors are
controlled fixtures. Ordinary API responses correctly retain server-derived actor
and `integration_test=false`; those transport fixtures are not live proof-policy
decisions or human engineering acceptance. The earlier expressly labelled internal
integration fixtures remain separate.

### Client/kit and served browser verification

From `apps/web`:

```powershell
node ../../node_modules/vitest/vitest.mjs run src/services/process-client.spec.ts src/components/process-interfaces/CommonProcessView.spec.tsx src/components/common/ProcessUIKit.spec.tsx --reporter=json --outputFile=D:/repos/wright/.local-run/process-interfaces-083/t027-input-kit-final.json
```

**135 passed**, no failed or pending tests. Backend/API/client schema guards,
read-only forms, explicit response, same-run follow and exact lost-ack retry pass.
TypeScript passes for client, kit and application. Contract generator `--check`
matches core. Focused Ruff/ESLint and `git diff --check` pass. For the shared
client, ESLint uses `--rule 'no-control-regex:off'` for its two pre-existing
intentional control-byte exclusion expressions; neither expression was changed.

Owned Vite source server: `127.0.0.1:5239`, recovery/definition/composer flags all
`1`; installed Chrome is selected by the private system-browser configuration.

```powershell
$env:PLAYWRIGHT_BASE_URL='http://127.0.0.1:5239'
$env:WRIGHT_PLAYWRIGHT_OUTPUT_DIR='D:/repos/wright/artifacts/process-interfaces/083/20261001-t027-input-browser-final'
$env:PLAYWRIGHT_JSON_OUTPUT_FILE='D:/repos/wright/.local-run/process-interfaces-083/t027-input-browser-final.json'
node node_modules/@playwright/test/cli.js test tests/ui-integration/process-declared-interactions.spec.ts tests/ui-integration/process-common-view.spec.ts --config .local-run/process-interfaces-083/playwright-system-chrome.config.ts --project chromium --workers 1 --global-timeout 120000 --reporter json
```

**Five passed, no skips/flakes, 27.0 s**, through the normal workspace Workflow
entry and document tabs. Existing common-view source-draft preservation,
input/readiness/start/follow/exact evidence and lost-start reload journeys pass.
Declared source edit/save/reopen still preserves its schema. New input journeys
close/reopen a waiting tab without start/cancel effects, show only the declared
form, and explicitly submit/reconcile the same exact subject/run. Final screenshots
are at 1440×1000 for the input controls and include explicit no-alert assertions.
The reporter's retained scope contains Chrome version, URL, process identity,
fixture run/subject, counts and viewport. These are served frontend/controlled HTTP
proofs; real API behavior is covered separately by TestClient, not this browser.

Initial service fixtures lacked the actual file-hash port and a committed source
head; they were corrected to use the source store and real file identity service.
Initial API assertions assumed FastAPI's default error envelope rather than
Wright's owning handler; final assertions use its actionable structured envelope.
The first browser run passed assertions but visual inspection revealed a malformed
fixture SSE frame (missing cursor ID) and cropped form. The fixture now has valid
cursor frames, a realistic larger viewport and clean-view assertions. A misleading
missing-value button reason was also corrected. Preliminary outputs are private
diagnostics, not final evidence.

Fresh production build command:
`npm run build --workspace apps/web -- --outDir D:/repos/wright/.local-run/process-interfaces-083/t027-input-production-final`.
**927 modules**, TypeScript and build pass with the existing large-chunk notice.
Its hashes are retained; browsers served the Vite source build, not those assets.

### Preservation and remaining scope

`artifacts/process-interfaces/083/20261001-t024-response/checked-scope.json`
retains exact run/response/claim, test/browser/build scope and preservation.
Ten original prototype hashes, three protected campaign hashes, two original mixed
API deltas and approved 083 HEAD context match. The initial 082 feature-pointer
hash is historical; approved T001 activation is checked against current HEAD.
No protected campaign was resumed or modified. No push/merge/release, physical or
supplier operation occurred. The owned source server is stopped after these checks.

T025/T026 policy/neutral operation work, full T027/T028 review/action/recovery,
actual default-model UI authoring, both live digital engineering demonstrations,
vendor migration and installed-native/Docker proof remain required. This milestone
does not establish live default-model/MCP behavior, engineering or user acceptance.

## Recovery qualification — resumed 2026-10-01

T027/T028 are complete within their declared interaction scope. **141 focused
backend/API tests pass** (144.34 s, zero skips) across continuation, scoped
checkpoint routes, input/action supervision, unattended policy and shared
contracts. They extend the earlier real file/SQLite two-barrier restoration,
duplicate/race/stale/schema/expiry and v2 history checks recorded above.
One additional check proves the served two-input source fixture equals the
actual backend continuation fixture and compiles to the same five steps.

The served serial group passes **16 browser tests** (1.7 min, zero skips/flakes):
common view (3), declared interactions (3), inspector (2), review/action (4),
and two-input recovery (4). The new two-barrier journey preserves one run through
close/reopen, a lost accepted acknowledgement and explicit reconciliation with
the identical request body/ID. Schema rejection stays at the first barrier and
requires a new explicit submission. Stale evidence remains blocked. Accepted
responses are retained after reload. Unknown action submission remains unknown
after refresh/reopen with no duplicate action or enabled continuation.

Command (repository root, existing private installed-Chrome configuration):

```powershell
$env:PLAYWRIGHT_BASE_URL='http://127.0.0.1:5242'
$env:WRIGHT_PLAYWRIGHT_OUTPUT_DIR='D:/repos/wright/artifacts/process-interfaces/083/20261001-t028-ui-serial'
$env:PLAYWRIGHT_JSON_OUTPUT_FILE='D:/repos/wright/.local-run/process-interfaces-083/t028-ui-serial.json'
node node_modules/@playwright/test/cli.js test tests/ui-integration/process-common-view.spec.ts tests/ui-integration/process-declared-interactions.spec.ts tests/ui-integration/process-input-inspector.spec.ts tests/ui-integration/process-review-actions.spec.ts tests/ui-integration/process-two-input-recovery.spec.ts --config=.local-run/process-interfaces-083/playwright-system-chrome.config.ts --project=chromium --workers=1 --reporter=json --trace=retain-on-failure --global-timeout=180000
```

Preliminary checks remain diagnostic: a new fixture referenced the wrong helper
property (corrected); another failed before workspace entry; the first full group
had two 30-second stalls, one before input preparation and one after a response.
Both passed in a traced diagnostic run (49.6 s), and the full unchanged serial
group then passed. Heavy backend tests were concurrent with the failed group;
contention is possible but is not established as the cause. No timeout increase
or production workaround was used. These stalls remain a browser reliability
limitation, not silently discarded evidence.

The [checked-scope manifest](../../../artifacts/process-interfaces/083/20261001-t028-recovery/checked-scope.json)
retains reports, source/code hashes, browser request scope and baseline checks.
HTTP/browser/model responses here are controlled fixtures. The saved-source
interoperability uses actual compiler/storage, and backend recovery uses actual
SQLite/file services. Live default-model/MCP engineering and distribution remain
M3–M5 work. T021's outstanding editor Run regressions remain pending.
