# Campaign efficiency review and proposed next execution plan

**Reviewed:** 2026-09-14, approximately 11:34 America/New_York.
**Status:** Recommendation for the next execution cycle; no campaign or validation run is started by this document.
**Scope:** Existing feature 081, ten engineering workflow families, three human-input datasets each.

**Follow-up:** After this review the user reported D: had been offline and was
restored. The real Windows user's TEMP/TMP and all 25 inspected Codex/Hermes/
Python/uv processes already use D:\TEMP; the user settings were reapplied and
verified. Initial C: registry values belonged to the separate sandbox account.
See [the storage note](storage-headroom-guard.md). The user subsequently resolved
the immediate disk shortage: C: now has approximately 9.95 GiB free and C:\tmp
is absent. Treat disk cleanup as addressed, while retaining measured preflight
and future workspace-capacity planning. Prioritize protocol, context and contract
fixes below rather than spending another cycle on disk cleanup.

## Evidence baseline

The live dashboard responds at <http://127.0.0.1:8771/?view=recovery>.
Its cumulative counters are **30 / 30 / 20 / 0**. The ledger contains 140
distinct accepted run IDs: 118 failed, 20 completed, one cancelled and one
outcome-unknown. These are actual accepted runs, not inferred from attempt
directory numbers. No run is currently recorded as running; this is not an
OS-level assertion that every worker/application has exited.

Only **19 scenarios have a completion matching the currently registered input
and template fingerprints**. PCB02 attempt020 completed all required stages
and has a retained 32/32 output hash verification, but its dataset digest is
`555f8d0b87ac7093a0c92ab39fe2564c46516a7fc4e915db95ed1c5e4b4e33a2`;
the registered current digest is
`8190f0fe207fcd3d83351ab0a33a704409b49be08a057639e88b5247025d2d00`.
Reconcile the intended input revision before either scheduling another run or
claiming PCB02 is ready for validation. Do not rewrite history or revert inputs
merely to recover a passing count. Current-revision projection is also not the
full G0 audit of intended definition identity, hashes and lifecycle evidence.

| Family                   |         Current-revision completions | Accepted attempts in ledger |
| ------------------------ | -----------------------------------: | --------------------------: |
| Heat spreader            |                                  3/3 |                          12 |
| Drill jig                |                                  3/3 |                          15 |
| Robot tracking           |                                  3/3 |                           8 |
| Sensor/fan harness       |                                  3/3 |                           3 |
| Water heater             |                                  3/3 |                           6 |
| Sensor-interface PCB     | 2/3; third has historical completion |                          33 |
| Pi enclosure and CFD     |                                  2/3 |                          36 |
| Printed replacement part |                                  0/3 |                          14 |
| Equipment bracket        |                                  0/3 |                           4 |
| Sheet metal              |                                  0/3 |                           9 |

Additional observations:

- C: has approximately **0.25 GiB free**; D: has approximately **233 GiB free**.
  Repeated storage-guard failures are documented. Reducing a guard from 512 to
  256 MiB does not establish enough capacity for CAD/solver work.
- The recovery journal's Pi next action still refers to attempts033/034, while
  the current ledger records failed attempt044. Several other narrative fields
  also retain older counts. Recovery decisions need a generated current index.
- Sheet01 retains a `runtime_owner_missing` outcome. PCB03's completion has a
  documented lifecycle snapshot discrepancy. Neither should be hidden by output
  counts, and neither proves that its application is currently running.
- None of the 140 ledger receipts contains a nonempty `usage` field. The ledger
  cannot quantify token consumption, dollar cost or which model caused it.

**Separate measured coordination usage:** The subsequently resumed CAD review
task reported 537,267 input tokens, of which 446,208 were cached, plus 3,401
output tokens (434 reasoning output). This is one multi-round coordination turn,
not historical workflow usage. The CLI selected current Astra instead of that
task's prior Sol setting. [The handoff](solid-edge-agent-handoff.md) records the
actual result and provenance. Explicit model selection and compact context are
therefore concrete efficiency priorities; do not equate a short response with
low input processing or infer a dollar charge from these counts alone.

Sources: live `/api/status` and `/api/diagnostics`,
`artifacts/engineering-workflow-datasets/status.json`, read-only queries of
`campaign.sqlite3`, `recovery-state.json`, PCB02 attempt020 `run.json`,
`.local-run/feature-081-live/campaign-execution/pcb020-output-verification.json`,
and [execution-state.md](execution-state.md). This review did not independently
rehash all successful output trees or validate their engineering contents.

## Diagnosis

The engineering scope is feasible in substantial part: seven families have
produced at least one complete output set. It is not yet established that all
remaining integrations can meet the required contracts. The present recovery
method spends too many full runs discovering defects that can be exercised
without model inference or without repeating earlier stages.

The [approved recovery plan](focused-recovery.md) already prescribes narrow
probes, compact context, fixed operations and bounded retries. The main change
needed is to enforce those rules in software and qualify adjacent stage
boundaries together. Another longer autonomous prompt alone will not do that.

**Additional observed service issue:** The dashboard's September 14 restart
outlasted its launcher's 60-second readiness timeout before eventually becoming
healthy. `scripts/engineering_dataset_campaign.py` performs a full `campaign.scan()`
before serving requests. Subsequent scans begin after a two-second wait following
each completed scan, ingest every receipt, and hash recorded artifact bytes while
holding the campaign lock. Unchanged-receipt detection happens after output checks.
This is a concrete source of repeated disk work and delayed dashboard responses;
its share of CAD/solver latency has not been measured. Start the read-only view
from persisted state with an explicit reconciliation status, then reconcile in
the background. Use incremental change detection for normal updates and explicit
full integrity audits, with freshness/invalidation evidence rather than silently
claiming cached bytes were freshly rehashed. Do not weaken final output/G0 audits.

| Recurring problem                            | Concrete evidence                                                                                  | Reusable response                                                                                                                                                                                                      |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unstable host/runtime prerequisites          | Pi storage stops, stale imported compiler, missing qualified fan library after volume changes      | Preflight the live process/build identity, mounted resources, required binaries and available storage before any model task; invalidate readiness on restart or mount change.                                          |
| Model controls routine protocol              | PCB duplicate save/tool calls; Pi044 malformed Hermes tool-decision JSON; printing null completion | Test the adapter protocol separately. Give fixed save/export/solver operations explicit completion semantics and persisted receipts. Preserve unknown-mutation and replay protection.                                  |
| Large cross-stage context                    | Pi037/039 context rejection after successful CAD; inspection/tool-call timeouts                    | Pass typed summaries and artifact references. Keep full files on disk; make bulk hash/export inspection deterministic. Bound context before dispatch, not after expensive stages.                                      |
| Repeated reconstruction of known formats     | Pi evidence aliases/list versus named fields; filename and API mismatches                          | Generate stable contract serialization and native measurements in code. Validate model-owned source/parameters against the pinned interface before native execution.                                                   |
| Unclear design authority                     | Bracket source authoring refuses underdefined pocket/fillet geometry                               | Separate mandatory human constraints from permitted design variables and model-selected candidates; review the concrete candidate before manufacture/analysis. Do not require humans to supply executable CAD recipes. |
| Local proof fails to cover the next boundary | A CAD fix is followed by compiler, mount or reporting failure                                      | Qualify the failing operation and downstream consumers with retained evidence in a disposable project before a fresh full pilot. Diagnostic reuse earns no campaign credit.                                            |

Solid Edge's repeated `AddFlangeByFace` E_POINTER failure needs a native provider
investigation. Prompt revisions cannot establish that the COM operation works.
Printing has qualified fixed mesh repair and lifecycle cleanup, but model source
construction remains unbounded; a full repair/slice chain is not yet proven.
Bracket CAD/FEA coupling also remains unproven for these three datasets.

## Proposed execution sequence

Use the existing canonical executor, campaign runner, ledger and dashboard.
Implement shared changes in their owning packages; do not create a replacement
workflow engine, scenario-ID recipes, or another monitoring system.

### 1. Establish a trustworthy, stable starting point

- Reconcile PCB02's intended input revision, Sheet01's unknown outcome and the
  PCB03 lifecycle discrepancy. Preserve all retained successes and failures.
- Establish storage headroom from observed case sizes plus reserve. Move
  configurable disposable work/cache locations to D: where supported, preserving
  workspace identities, grants and mounts; verify copies before removing any
  source. Do not move active native projects or merely lower disk guards.
- Extend existing preflight to verify the actual loaded runtime/build, fan
  library, selected volumes, tool contracts and owned application state.
  A static schema pin alone is insufficient. Recheck after lifecycle changes.
- Generate a compact current checkpoint from receipts plus explicit decisions;
  link to historical notes instead of requiring agents to read their full history.

**Exit:** one reproducible readiness command detects the observed infrastructure
failures before an LLM request, and the exact current cohort is recorded.

### 2. Remove expensive sources of avoidable failure

- Keep image interpretation, requirement interpretation and design decisions
  with the model. Move fixed serialization, measurements, hashes, save/export,
  mesh repair and solver dispatch into existing generic operations as applicable.
- Qualify Hermes decision parsing and terminal behavior in a tiny disposable
  workflow, including malformed/null responses and duplicate requests. Never
  turn a parser failure into unverified engineering success.
- Replace repeated prompt instructions to stop calling tools with explicit
  task-boundary/terminal-operation behavior where the task contract permits it.
  A recorded successful mutation must not be replayed to obtain a nicer answer.
- Apply compact stage-input contracts and context budgets across families.
  Retain full evidence externally and retrieve only the required portions.
- Exercise retained failing inputs and their downstream handoff contracts before
  new full runs. Reuse existing focused regressions; do not test prompt wording
  as a substitute for actual native/contract behavior.

**Exit:** the relevant retained failures pass through the real affected boundary
within a measured call/time budget, with terminal cleanup evidence.

### 3. Complete families in evidence-led order

1. Reconcile PCB02, then qualify Pi03's source-to-CFD chain before one fresh
   canonical pilot. Two completed Pi cases make this the strongest near-term
   opportunity. Pi044's malformed decision must be covered by the protocol probe.
2. Printing: qualify bounded source authoring, preferably a complete generated
   construction program rather than many interactive model edits, then exercise
   fixed repair and slicing. Preserve image-derived design and declared features.
   Run one full pilot; only then expand to its two siblings.
3. Bracket: define legitimate design discretion, then prove source construction
   and the CAD-to-FEA handoff for one pilot before sibling expansion.
4. Sheet metal: give the native provider a separate bounded feasibility task:
   minimal sheet, required flange, native save, STEP export and flat-pattern DXF,
   followed by the retained failing recipe and cleanup. If this fails after the
   allowed repairs, record the precise provider gap and an explicit adapter
   repair/replacement proposal. Any alternative must preserve genuine sheet-metal
   and bend/flat-pattern capabilities; a mesh approximation is insufficient.

   Per the user's September 14 instruction, coordinate this provider work with
   the existing **Review CAD accuracy and speed** task in `D:\repos\SolidEdgeMCP`.
   [The handoff](solid-edge-agent-handoff.md) defines evidence and ownership.
   The initial request is read-only coordination, preserving that task's separate
   accuracy/speed milestone and Sheet Metal 100 exclusions.

The sheet-metal diagnostic may move earlier when its isolated resource is ready.
Do not hold ready work behind an unchanged provider failure. Preserve all ten
families; any reduction of engineering requirements needs an explicit scope
decision rather than quiet changes to make tests pass.

### 4. Make spending and retries bounded

- Start the next goal with **shared stabilization plus one additional complete
  pilot**, rather than an unlimited instruction to keep trying until 30 succeed.
  Queue subsequent bounded milestones automatically when their exit gates pass.
- Persist a repair episode keyed to the root failure and affected boundary.
  Enforce the existing maximum two safe corrections; fresh prompts, grants or
  attempt IDs do not reset it. Require a demonstrated material fix before a full
  retry. Add an overall episode time/call budget so novel errors cannot extend
  the same investigation indefinitely.
- Let ordinary processes wait for solvers, persist events and update the
  dashboard. Model activity should resume on actionable state changes. Local
  polling itself is not an LLM token expense; repeatedly asking agents to inspect
  unchanged polling results is avoidable work.
- Capture workflow inference usage and available orchestration usage separately,
  including actual model identity, input/output/cache/reasoning counts when
  provided, and duration. Unknown usage remains unknown. Enforce request/time
  budgets when the provider cannot expose token totals; do not invent billing.
- Explicitly select the intended model when launching authorized work; a CLI
  resume can use current configuration rather than the saved task's model.
  Use compact bounded handoffs instead of repeatedly reloading long campaign
  histories. Do not create new user tasks without the user's instruction, or
  duplicate a still-running agent's work.
- Keep the four cumulative chart lines. Clearly expose current-revision
  completions, accepted attempts, failure classes, last new completion, cleanup
  state and measured usage. Extend the existing diagnostics; do not rebuild it.
- Fix one shared defect, run its relevant tests, then one eligible pilot.
  Preserve unaffected successes. Do not run the full regression/campaign after
  every prompt edit, or keep an agent active solely to fill waiting time.

No numeric savings guarantee is supported by the present telemetry. Evaluate
progress using added current completions per measured usage and per elapsed hour,
alongside blocked boundaries resolved. A cheaper model alone does not address
the number of inference requests or repeated native workflow attempts.

## Subsequent output-content validation

Keep [content validation](../content-validation/plan.md) deferred until separately
assigned and its **all-30 G0 gate** passes. This review does not activate it or
change `valid_data=0`.

The saved plan already proposes shared readers/validators and 30 data profiles,
not thirty independent validation implementations. Follow that architecture:
common geometry/mesh/DXF checks; common thermal/CFD/FEA field and balance checks;
electrical/connectivity checks; and trace/time-series and requirement checks.
Use its heat-spreader and drill-jig pilots, then expand by reusable capability.

Validate retained outputs without regenerating CAD or rerunning solvers unless
specific missing evidence or an authorized design repair requires it. Freeze
requirements independently of generated results, and qualify validators using
known-good and deliberately defective fixtures. Existing operational geometry,
safety, integrity and native-tool gates remain in the generation workflows.

## Scope and constitutional consistency

The proposed changes retain thin API routes, core/application/storage ownership,
canonical source authority, selected MCP host isolation, immutable evidence,
input provenance and existing approval/replay guards. No constitution amendment
is proposed. Test-auto approval remains limited to its enrolled local/test
authority; physical printing and supplier transactions are separate qualification
and authorization work. Full campaign credit still requires every declared step
and same-run expected outputs. Dashboard availability and historical counters
must survive restart. This review changes documentation only.
