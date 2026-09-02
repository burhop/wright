# Image-redesign implementation validation

Status: image-led UI and modal repairs verified; a confirmed shared API event-loop stall is being repaired before fresh final acceptance.

## Latest checkpoint: repeated multi-tab save delay under investigation

Commit `629de4f2dd4d7eb33f295f3fd6771d329c5b2373`, tree
`db4f6fde60f22f3cc4f1791404fe9b6fe8cd572f`, contains the preview wrapping,
body-portal and backdrop-focus repairs. All **643 web tests pass** with
`npm run test -- --maxWorkers=4` (177.42s), preserving every five-second test
timeout; all **13 Chromium journeys**, current TypeScript/Vite build and the
exact committed program validator pass. The controlled API restart preserved
all seven workflow files and verified new listener57804 and the same subject.

The fresh full walkthrough
`20260902T232911Z-committed-acceptance-629de4f2-continuation-1` stopped at the
second-tab save in step21 after 21 preceding grouped checks passed. It retained
the unchanged five-second deadline and all stopped evidence. The save click was
23:30:51.664Z; the browser stopped at23:30:57.205Z; journal/head publication
occurred at23:30:57.896–57.931Z. The later stored revision is correct, but the
response was not captured as successful in the stopped walkthrough.

The publication span was about36ms; the unexplained delay preceded it. Other
unrelated API requests also waited multiple seconds. A read-only frontend audit
found no SSE connection leak and confirmed existing in-flight polling guards.
The next check compares direct API versus browser/proxy timing to distinguish
request queuing from server-side waiting. No timeout increase, dropped conflict
assertion, fabricated success or blind acceptance rerun is authorized by this
record. Final UI acceptance remains open until this recurring delay is resolved.

### Confirmed shared event-loop cause

The read-only two-tab timing probe recorded simultaneous independent direct
API8018 and proxy5227 health requests taking 7.408/7.413s, versus earlier
48–78ms reads. Explicit tab activation did not remove the delay. This rules out
browser connection slots or the proxy as a sufficient explanation. It made no
workflow changes and retained its trace and four raw/annotated diagnostic states.

An isolated py-spy0.4.2 installation under `.local-run/api-profiler` then sampled
API listener57804 for60s at25Hz, including idle threads, nonblocking and without
local variables. Raw evidence: `.local-run/api-shared-stall-20260902.raw`.
There are9,336 samples and7 nonblocking stack-read errors. The API MainThread
was sampled128 times in `check_llm_backend_health` → `_llm_settings_from_config`
→ `hermes_config_path` → `_hermes_config_command` → `subprocess.run` →
`communicate`/`join`, plus5 samples during subprocess creation. This establishes
real synchronous command discovery on the request event loop. It is not a
precise continuous-duration measurement. The second diagnostic probe actually
started after the profiler; no overlap between those runs is claimed.

Code inspection finds the same synchronous discovery family called from async
setup/status and model-option paths. The authorized repair preserves the public
synchronous library APIs and all explicit-path/profile/environment/auth rules,
but offloads discovery at async callers. No cache, credentials override, timeout
increase, or fabricated health state is introduced. Event-controlled concurrency
tests must prove health/ticker progress while discovery is still blocked.

### Repair and startup-identity checks

The initial offload implementation passed 55 focused compatibility/concurrency
tests after six new cases failed before the repair. Independent code review
then found a stale-write race: the offloaded setup status snapshot could write
an older active-agent selection back to the runtime and database. Two actual
endpoint regressions reproduced that race. The read-only status endpoint no
longer writes selection state; startup and explicit configuration/selection
retain that authority. Final regression and live timing outcomes follow below.

The final five-file setup/model/health/config compatibility suite passed
**57/57** (29.23s; 142 existing deprecation warnings), including both selection
race cases. Independent read-only review reports no remaining actionable
findings. Command: `.venv/Scripts/python.exe -m pytest
apps/api/tests/test_setup_api.py apps/api/tests/test_agent_model_gateway_auth.py
apps/api/tests/test_agent_health.py
packages/agent_adapters/tests/test_hermes_gateway_adapter.py
packages/agent_adapters/tests/test_hermes_config.py -q --basetemp
.test-tmp/image-redesign-config-offload-race-green-20260902`.

The separate source/layout/API/operator suite passed **125 tests, 5 explicit
platform skips** (17.80s; 143 existing warnings), using the same four-file
command recorded in `image-redesign-storage-review.md` and basetemp
`.test-tmp/image-redesign-storage-offload-final-20260902`. No frontend code
changed after the 643-test/13-browser/build checkpoint.

The restart helper now fingerprints setup/model routes and Hermes configuration
modules, and rejects untracked adapter source. Its module-origin probe resolves
nested packages without importing application code. All **27 provenance tests**
passed (0.42s), and Ruff/diff checks passed. A process-sandbox denial happened
before the first test launch; the permitted identical local command passed.
No API restart or repaired live-service success is claimed by these tests.

Integration worktree: `D:/repos/wright/.local-run/epp-f02b-writer/wright`.
Branch: `codex/080-canonical-workflow-recovery`. Baseline: `7e95b0c7`.
Working-tree commands and exact-commit observations are distinguished below.

## First committed-subject authoring checks (visual follow-up required)

Commit `4cfab9ba8091b766805e00157739204675385c0c`, tree
`93bc29cabb266f454efa5f6157e31fd302789ce1`: walkthrough
`20260902T225850Z-committed-acceptance-4cfab9ba-continuation-2` passes **32/32**.
All 184 manifest hashes verify; 83 raw/83 annotated images and a 115,639,279-byte
trace are retained. Report image loading, Escape and Close controls pass.
Frontend served-source provenance covers 14 unique modules with no missing or
mismatched normalized source; raw hashes remain separately recorded. Controlled
API restart provenance binds the same commit, source paths and hashes. No
unexpected console, page, failed-request or HTTP diagnostic remains; the
intentional conflict 409/resource error is recorded, not suppressed globally.

The first exact-subject continuation stopped at the unchanged five-second
second-tab save deadline. A later read verified that the write committed; its
response completion is unavailable in that stopped trace. The next unchanged
continuation passed. No product fix or increased timeout was claimed.

The committed-source program validator reports `verdict: passed` for this
subject; program tree stays `047a330be53cd7565895dbc6eb7a4fadc012f2dd`. It reports
the preserved untracked scratch/note as not globally clean, while all tracked
implementation files were clean for the walkthrough. Historical approval and
correction manifests were rehashed: 204 and 59 files respectively, no omissions
or mismatches. Frozen historical 079 tasks are unchanged from `b4a7e996`.

| Check | Command / scope | Observed result |
|---|---|---|
| Authoring helpers and boundaries | `npm run test -- src/prototypes/workflow-recovery/authoring-objects.spec.ts src/prototypes/workflow-recovery/recovery-authoring.spec.ts src/prototypes/workflow-recovery/command-system.spec.ts` in `apps/web` | 65 passed / 3 files; exit 0 (helper agent) |
| Host authoring | `npm run test -- src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx` | 15 passed; exit 0 (host agent) |
| Renderer before added selection/trace tests | `npm run test -- src/prototypes/workflow-recovery/ReactFlowRecoveryCanvas.spec.tsx` | 7 passed; exit 0 (integration writer); expanded suite pending |
| Build | `npm run build` | Passed; 858 modules (host agent); existing Vite native-config and bundle-size warnings |
| Early real browser shell | `node scripts/recovery/capture_image_redesign.mjs --label=early-shell-continuation-1 --viewports=all --url=http://127.0.0.1:5227/workspace/85cbd6b3-e9d1-474d-add2-36f6e95a7b51?workflow=canonical` | 4 shell actions and 4 viewport captures; assertion pass, material visual findings recorded separately |
| Full web suite | `npm run test` in `apps/web` | 117 files / 623 tests passed; exit 0; 82.97s (integration writer). Later changes require focused rerun and final broad checkpoint. |

## Failures preserved

- Tests-first helper suite initially failed because the module did not exist.
- A stronger collection-narrowing case initially failed because collection
  outputs could feed one-valued inputs. Source and command paths now reject that
  atomically; existing single-value fan-in to collection inputs is retained.
- First Chromium launch failed with `spawn EPERM` in the sandbox before
  navigation. Separate permitted continuation captured the actual application.
- Early screenshots passed basic assertions but failed visual acceptance; see
  `image-redesign-review.md`. Passing a screenshot harness is not visual approval.

## Remaining checks after first exact capture

The full authoring journey, actual zoom, storage/source/security regressions,
broad web/build, freeze and Spec Kit consistency checks now have evidence below.
The independent reviewer found long-text clipping in the output-preview sidebar
that the first passing browser journey did not detect. The new range/hit-target
regression failed before the scoped wrapping fix and passed afterward (20.7s).
The narrow screenshots then exposed host chrome painting above the modal;
a portal/stacking repair and header-occlusion assertion are in progress.
Fresh exact-subject capture and dashboard handoff remain.

The final modal repair now passes **18/18 Concept tests**, including body portal,
focus cycle/return, Escape, backdrop dismissal and unmount cleanup. The full web
suite was rerun after that repair: **118 files / 643 tests passed** (122.10s).
TypeScript and Vite production build also pass (858 modules). A Chromium rerun
retained a 30-second context-teardown failure while writing passing-test traces;
its product assertions had completed. A fresh run uses the previously successful
retain-on-failure trace mode with unchanged assertions and timeouts. The full
final walkthrough still records a continuous trace.

That browser pass also exposed an actual backdrop-click focus return failure:
the mousedown handler restored focus, then the browser's default focus action
cleared it. The handler now prevents that default only for a click on the bare
backdrop. The strengthened unit test covers both the cancelable event and a
complete user click; **18/18 Concept tests passed** again (12.56s). Final full
web and 13-journey Chromium reruns follow this last handler change. Red traces
and the preceding passing-but-incomplete visual states remain preserved.

Final Chromium rerun `output-preview-final-green-20260902`: **13/13 passed**
(2.1m), with unchanged assertions/timeouts and retain-on-failure tracing.
Current TypeScript/Vite build passed again (858 modules, 8.84s Vite). A parallel
full web run reported 642 passes and one default-five-second active-run-test
timeout, not an assertion mismatch. That test does not open a modal and passes
unchanged in isolation (3.03s). The complete suite is being rerun with four
workers and the same five-second timeout to bound concurrent host pressure.

The complete `tests/recovery` suite passed **56/56** in 7.10s with
`--basetemp .test-tmp/image-redesign-audit-final`. This includes safe selection
of new dashboard evidence (17 focused audit tests) without overwriting historical
dashboard artifacts or treating the three external gates as completed. The
capability audit was rerun: **890/890 rows, 33/33 capabilities, no omissions**.
Frozen historical T028–T038 remain unchanged through Git comparison.

### Later working-tree checkpoints (supersede the earlier pending observations)

Final pre-commit broad rerun: **118 web files / 642 tests passed** (97.76s),
followed by a successful TypeScript/production build (858 modules, 5.03s).
Existing Vite native-config and bundle-size warnings remain warnings, not hidden
failures. Final storage/API/operator suite: **123 passed, 5 skipped, 143 warnings**
(22.90s), including all 25 pure provenance-helper tests. Final Chromium regression
rerun: **13/13 passed** (1.2m), output `test-repair-final-20260902`.
Frozen historical spec079 tasks are byte-equivalent through Git to `b4a7e996`.

| Check | Observed result |
|---|---|
| Complete real-browser functional journey | `20260902T223458Z-functional-continuation-6`: 30/30, including exact save/reopen source/layout, stale-tab 409 conflict/compare/reload, bounded proposal/run, four viewport sizes and actual Chromium tab zoom 2.0. Raw/annotated/trace/manifest/report validator passed. |
| Independent read-only visual review | `20260902T223502Z-independent-readonly-review`: seven checks, zero mutations and unexpected diagnostics; primary 1536×1024 hierarchy accepted internally, four concrete polish findings repaired. |
| Actual 200% controls | `20260902T224417Z-zoom-continuation-1`: five checks, real 768×395 effective viewport at DPR2; Settings Apply reached by internal scrolling without applying values; Inspector/minimap collapse restores canvas space. |
| Workspace Console/maximize | `20260902T223851Z-workspace-controls-continuation-1`: separate center hit targets and open/collapse/maximize/restore pass. |
| Existing Chromium integration suite | `test-repair-20260902-run5`: 13/13, 59.2s; typed pointer/keyboard, live drag, <1s feedback, history, proposal/lineage, accessibility and mobile containment. |
| Expanded renderer | 14/14 (5.04s), plus TypeScript check exit 0; operation-aware icons and short-height minimap included. |
| Layout hash and host | 19/19 in canonical-wire + host suites: nested key order does not alter identity; changed coordinates and authority still do. |
| Broad web checkpoint | 118 files / 637 passed (97.07s). Subsequent build found two unsupported Testing Library `exact` options in test code; corrected to the library's already-exact string-name matcher. Final broad/build rerun follows. |
| Backend storage/API/operator tests | 113 passed / 5 genuine platform skips; see `image-redesign-storage-review.md`. Later provenance-helper additions have separate focused results. |
| Conformance | `python -m pytest tests/recovery/test_workflow_conformance.py -q --basetemp .test-tmp/image-redesign-conformance-final`: 36 passed, 2.52s. |
| Capability audit | 890/890 source rows, 33/33 capabilities, zero unexplained omissions. |
| Syntax fixture evaluator | JSON, YAML and engineering-source round trips/schema checks and 5/5 edit candidates each pass. Fixed fixture SHA `04cc79dad3b8177e52ab46d0c994d5d48b39f63d7483ccf504eb8d665b902b2d`; not a benchmark. |

Additional failed continuations are retained: missing favicon; retained-tab
selector ambiguity; newly named document identity rejected by cold roundtrip;
order-sensitive layout checksum; proposal overlay intercepting the Inspector.
Each repair was followed by a separate continuation, not a rewritten passing
history. Save/reopen checksum failure was not coordinate loss: captured PUT and
GET positions matched exactly; canonical key sorting fixed evidence identity.

The read-only Spec Kit prerequisite command completed through the permitted WSL
Bash process: `.specify/scripts/bash/check-prerequisites.sh --json --require-tasks
--include-tasks`. It returned the correct `080-canonical-workflow-recovery`
feature directory and all prerequisite artifacts. WSL did not detect the Windows
worktree Git metadata, so its branch validation was skipped; native Git inspection
independently identifies `codex/080-canonical-workflow-recovery`.
