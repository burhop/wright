# Dataset campaign cross-artifact analysis

## Approved recovery review, September 12 (recorded September 13 UTC)

The user approved the results review and requested better Solid Edge/Blender
shutdown management. [focused-recovery.md](focused-recovery.md) and tasks
DC012–DC025 now define the approved remediation. This documentation change
does not claim those tasks are implemented. The measured baseline remains
30/29/9/0; 57 accepted run IDs produced nine full current-revision completions.

| ID | Severity | Evidence/problem | Approved plan response | Implementation coverage |
| --- | --- | --- | --- | --- |
| R1 | High | Full Pi runs discover unsupported native APIs after research/review | Exact-version failed-operation probes before pilots | DC018, DC020 |
| R2 | High | Failed source has no bounded local repair; jigs hit context limits after native outputs | At most two safe repairs, versioned diagnostics, direct fixed calls and bounded context | DC019–DC020 |
| R3 | High | Broad family retries and queue pauses delay unrelated ready work | One complete pilot per family, sibling eligibility, per-resource quarantine | DC021, DC023–DC024 |
| R4 | High | Native application lifetime is not equivalent to MCP transport/run lifetime; user reports applications left open | Explicit app/document ownership, leases, health/reuse and bounded graceful shutdown with restart reconciliation | DC012–DC017, DC025 |
| R5 | Medium | Four cumulative lines conceal repeated attempts and stage/cleanup progress | Add diagnostic stage, age, usage and application status without changing counters | DC022 |
| R6 | Medium | Parent-first execution wording and stale checkpoint next actions conflict with current recovery needs | Supersede broad sequencing, refresh current entry, retain dated historical evidence | Updated parent/campaign plans, DC010A, execution-state and goal |

Coverage: all six review findings map to named tasks and acceptance; fourteen
new recovery tasks are unchecked. No constitution amendment is needed. Current
file-presence acceptance remains separate from parent engineering qualification;
existing safety, artifact identity and unknown-mutation protections remain.
Lifecycle cleanup cannot close user-owned sessions or disable Blender safe mode.
Neither isolated diagnostics nor partial graphs can inflate completion counts.

## Historical analysis and implementation evidence

2026-09-12. Read-only analysis was performed before the following authorized
remediation. Prerequisites passed through Git Bash; optional commit hooks were
not run because the checkout contains unrelated dirty work. The parent spec,
plan, tasks, campaign plan/tasks/goal, runtime findings and constitution were
reviewed. Coverage was nominally complete, but task descriptions alone were
not execution evidence.

| Finding | Severity | Remediation and remaining evidence |
| --- | --- | --- |
| I1: T033/T036 claimed durable continuation despite the documented missing actual resume | High | Reopened those tasks; preserved older partial evidence. DC006A/B now explicitly require the same run to traverse two approvals and a final real operation, including crash boundaries. Still open until runtime tests and a real run prove this. |
| I2: parent human-only decision contract did not define the automatic actor exception | High | Added the bounded campaign extension to `approval-resume.md` and the exact immutable policy contract. Policy tests derive the test actor and reject manual auto-decisions; API integration remains DC007A. |
| I3: campaign notes prohibited every provider write despite accepted disposable CAD/solver access | High | Aligned campaign configuration with the goal: existing authorized access may run real engineering jobs in configured disposable projects; purchases, unapproved paid access, real printer/supplier writes and publication stay outside scope. |
| U1: integration readiness lacked exact evidence and failure semantics | High | Added `contracts/integration-execution.md` and policy/repository implementation. Tests cover exact/stale source, inputs, workspace, tool schemas, output confinement, expiry and revocation. API/gateway binding and actual host preflight remain separately required. No public qualification promotion is performed. |
| U2: observer receipt booleans could not independently establish runtime execution | High | Defined runner proof obligations below and DC009A/B negative tests. The observer remains an evidence/file auditor; a complete runtime-backed collector is required before run counts may rise. |
| U3: continuation restart ownership and state transitions were underspecified | High | Defined immutable accepted-plan/input/result/policy context and same-run continuation in the integration contract and DC006A/B. Unknown mutation outcomes require read-only reconciliation; actual implementation evidence remains open. |
| I4: legacy simulation wording conflicted with the explicit campaign scope | Medium | Added a narrow FR-011 campaign cross-reference. Only external handoffs may be simulated; real engineering operations and safety/integrity checks remain required. |
| C1: broad DC tasks lacked actionable paths and test ordering | Medium | Added DC004A–DC011A subtasks with paths, ownership boundaries, negative tests and dependency order. Foundation tasks cannot close complete runtime requirements. |

## Runner evidence acceptance

Before setting `accepted_by_runtime`, the runner must read the durable run
record and retain its real `run_started` event, run ID, accepted source digest,
dataset identity and attempt association. An HTTP success, preflight result or
client-created ID is insufficient.

Before setting `all_required_steps_succeeded` or `terminal_step_reached`, derive
the required step set from the accepted full canonical source, reconcile it
with durable step outcomes and verify the actual terminal operation. A
checkpoint's dispatched status cannot substitute for later steps. Indexed
corrective attempts remain recorded; only successful required final step
states satisfy completion. The runner must not truncate a definition.

Copy only files identified by that attempt's runtime artifact records, verify
recorded path/size/digest and the predeclared output role, and retain source,
input, operation, tool/schema, model and approval lineage. Input copies,
precreated files, other-run artifacts, empty files and diagnostics cannot
replace engineering output roles. Preserve partial real outputs without
incrementing full-process completion. Validity remains exactly zero.

## Constitutional and scope audit

The user explicitly authorized ordinary campaign plan/implementation/test
continuation. No new routine approval pause or constitution amendment is
needed. Existing thin routes, domain/application/storage ownership, local
authentication, RBAC, workspace path authority, SQLite WAL, structured tracing
and canonical workflow execution remain required. Selected MCP software must
stay outside the base image. UI changes require the established three-tier
checks and a served normal-workspace journey.

The target remains 30 complete human input packs, 30 actual unique pairs run,
30 entire integration graphs producing their expected files, and zero
content-validated results. Neither this analysis nor passing foundation tests
establishes that target or public/live engineering qualification.

## Execution-cycle evidence update, September12 16:38 UTC

The initial table records findings at planning time. The following evidence
supersedes its statements that implementation/API tests are still absent:

- I1/U3: DC006A/B now have durable continuation implementation and43 focused
  checks including five normal API-handler tests with a real private MCP child.
  Two sequential approvals reach the actual final file/hash; fresh services
  reopen SQLite/source/files between phases. Duplicate decisions/resumes,
  cancellation on either side of actual dispatch, lost child response and a
  completed persisted outcome do not replay the mutation. See
  durable-multicheckpoint-acceptance.md. This does not claim forced OS-crash,
  authentication or complete flagship qualification.
- I2: DC007A is complete. New API negatives reject revoked/expired grants,
  wrong workspace, changed inputs/artifacts and manual-only authority; a
  manual changes-requested decision cannot dispatch. Existing exact digest
  checks and ordinary manual actor behavior remain.14 API checks passed after
  the final additional case, with25 API/application checks immediately before.
- U1/U2: DC005C and DC009A/B have actual normal API/recorder/runner evidence
  and40 exporter/observer/runner regressions. Eleven distinct real pairs have
  started; zero entire workflows have all expected files. Preflight failures
  and late native success after a failed task earn no completion credit.
- Runtime latency: discovery now persists its complete per-tool audit in one
  transaction before returning; no policy check, failed decision or ordinary
  dispatch audit is omitted.20 direct and21 related tests plus independent
  review passed, including rollback, redaction, failed enumeration and failed
  audit persistence preventing native dispatch. No authorization cache exists.
- Selected-host correction: Windows cold native-library imports can block
  behind pending MCP stdin reads. A qualified immutable AgentCAD bootstrap
  preloads NumPy/build123d/SciPy first; actual open-stdin Gateway CAD succeeded.
  Changed command authority requires new tool pins/fresh attempts. Old grants
  are retained and naturally stale; public readiness is unchanged.

Current open execution issues are concrete per-family bindings/inputs:
Modelica direct nodes need qualified names plus schema pins; sheet-metal
generated intent falsely attributed a supplier temper to human input and needs
explicit stock-selection revision authority. Original human files and earlier
attempts are retained. The Pi/robot/thermal/jig/PCB/harness/bracket batch runs
independently while those corrections proceed. Printing still awaits the
separate pending Blender guard choice. DC005D/DC010A/DC011A remain open; neither
new test evidence nor prerequisite solvers close the30/30/30/0 goal.

## Execution-cycle evidence update, September12 17:34 UTC

DC005D preparation is complete: all30 enrolled definitions preserve original
semantic stages and declared output roles, with exact source/input/tool grants.
DC004/DC004A remain open for complete per-file normalization and image lineage;
seven confirmed UTF8 context corruptions have fresh corrected attempts. Existing
grants, original datasets and failed runs remain unchanged.

Two entire robot workflows have now completed with22 total actual files; live
dashboard downloads verify nonempty bytes, hashes and same-run identity. Current
counters are30/12/2/0. API deployment preserves all212 previous tool pins and
adds only the exact-grant file inspection capability. Real MCP image observations
and initial-upload local review are loaded and covered by focused regressions.
The fresh25case batch007 has started Pi01 research successfully, including actual
primary drawing image observations; later design/CAD/solver steps remain pending.

The fresh queue addresses confirmed family failures without replaying old
mutations: explicit sheet-metal R3 company design choices; Pi visual source
observations and thermal inputs; Modelica exact operation pins and initial review;
CAD export file inspection; corrected UTF8 human contexts. Shared engineering
operations remain serialized, and only declared external handoffs are simulated.
No geometric/numerical correctness program or public qualification flag is used
to increase campaign progress. The remaining open work is full execution,
normalization acceptance and final served-workspace acceptance.
