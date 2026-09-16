# Approved focused recovery amendment

Approved by the user September 12, 2026 (recorded September 13 UTC), following
the campaign review and the report of Solid Edge/Blender remaining open.
This amends execution order and recovery in the existing testing cycle.
The target stays **30 datasets / 30 accepted pairs / 30 complete output sets /
0 content-validated sets**. These are real engineering workflows.

## Evidence and decisions

At 2026-09-13 00:39:45 UTC the persistent ledger showed 30/29/9/0, with 57
accepted run IDs: 47 failed, 9 completed, and one historical run recorded as
owner-missing. The ninth completion was at 21:41 UTC; almost three hours of
later attempts had added no complete scenario. Attempt numbers also include
preparations and cannot be interpreted as dispatch counts.

| Workflow family | Current-revision completions at review |
| --- | --- |
| Sensor-and-fan harness | 3/3 |
| Robot tracking diagnosis | 2/3 |
| Water-heater sizing | 2/3 |
| Heat-spreader sizing | 2/3 |
| Printed replacement part | 0/3 |
| Raspberry Pi enclosure/CFD | 0/3 |
| Sheet-metal supplier handoff | 0/3 |
| Parametric drill jig | 0/3 |
| Lightweight equipment bracket | 0/3 |
| Sensor-interface PCB | 0/3 |

Sources: `artifacts/engineering-workflow-datasets/status.json`, the matching
`output/<scenario>/<attempt>/run.json` records, and [execution-state.md](execution-state.md).
Treat these as a dated baseline; inspect current state before resuming.

Decisions supported by that evidence:

- Pi failures discovered build123d API mismatches after successful research,
  design and review. Qualify exact imports, signatures, entrypoint, shape
  normalization, source paths and export contracts before another full pilot.
- Sheet02 attempt006 cleared input gaps and recipe validation, then failed
  native flange creation with `E_POINTER`. Investigate the retained recipe and
  selected native session directly. A passed schema check does not prove the
  CAD operation works; do not assume this error is caused by a leftover process.
- Jig03 attempt009 produced every expected file role before a later context
  limit failure. Preserve the files and fix the observation/reporting stage;
  that failed workflow still earns no full-completion credit.
- KiCad save/reload and aggregate read behavior, Modelica capacity and native
  import startup have required integration fixes. Probe those exact seams.
- User-reported application shutdown problems require explicit native process
  ownership and cleanup. An open application is not by itself a leak; distinguish
  intentional leased reuse, user sessions and orphaned campaign processes.

## Work sequence and exit criteria

1. **Reconcile once.** Read the compact current checkpoint and ledger; discover
   actual workers, native sessions and resource owners. Keep all nine valid
   current-revision completions. Reconcile the historical owner-missing run
   without claiming it succeeded or replaying its mutation. Produce a concise
   pending matrix with family, failing stage, evidence, resource and next action.
2. **Make native lifecycle observable and bounded.** Implement
   [native-application-lifecycle.md](contracts/native-application-lifecycle.md)
   before dispatching affected CAD families. Independent read-only analysis,
   software fixes and isolated non-CAD work may continue.
3. **Prove one failed seam.** Reproduce the retained failure in a disposable,
   owned diagnostic project under the pinned provider version. Apply the
   smallest reusable fix and run its focused regression. Tests exercise actual
   imports/exports/native calls where relevant, not only text in a prompt.
4. **Run one full pilot in that family.** Use the normal canonical executor,
   complete input pack and declared output roles. A full runtime-backed success
   is the exit criterion before expanding that binding revision to siblings.
   Prioritize ready Pi and sheet-metal pilots, then printing when its outstanding
   guard decision or an authorized compatible solution makes it ready. Resolve
   independent near-complete follow-ons while a flagship resource is blocked.
5. **Expand and regress selectively.** Run the other two datasets with the proven
   binding; retain their distinct images and engineering requirements. Re-run an
   already complete case only if a changed dependency affects it. Finish all
   remaining families; a pilot or a diagnostic can never replace the thirty cases.
6. **Close the campaign.** Verify 30/30/30/0, normal served flagship journeys,
   output links, restart/continuation, and native teardown receipts. Every owned
   native session must be exited or deliberately released; no unresolved owned
   process may be hidden behind an otherwise successful output metric.

## Efficient execution and repair

Use the selected **Sol** model for orchestration and supported workflow inference.
Record the actual provider/model returned by the runtime; verify supported
configuration before dispatch and report unavailable choices rather than silently
substituting a model. The goal text does not select a model in the Codex UI.

Keep AI for image interpretation, requirements and engineering design. Bind
fixed exports, schema checks, file inspection and solver dispatch directly to
tested generic operations. Preserve canonical source authority and tool pins;
do not add scenario-ID recipes or a second executor. Check generated imports,
syntax and declared contract keys before expensive native execution. Generate
SDK/schema guidance from the selected implementation where practical.

For the printed-part family, the model owns interpretation of the supplied
image, dimensions and human context and authors the source mesh. Routine repair,
measurement, triangle limiting, build-volume checking, bed placement, repaired
STL export and preview rendering use a reviewed fixed operation through the
same lifecycle-owned Blender socket. Supports and slicing remain in the fixed
Bambu operation. Both configured operations validate same-attempt paths and
staged operation bytes and reject replayed outputs. Qualify each fixed native
operation in a disposable owned session before using a fresh canonical attempt.
The mesh-repair operation passed disposable qualification-repair-004 on the
retained attempt013 source: 754,726 triangles and 92,657 nonmanifold edges were
converted by two bounded voxel passes to 53,092 triangles with zero boundary or
nonmanifold edges, one component and positive volume while retaining the exact
26 x 38 x 17 mm envelope. Both nonempty outputs are hashed in the qualification
receipt. Cleanup removed the owned Blender PID and deactivated both temporary
servers, so fresh attempt014 may exercise the full canonical graph.
Attempt014 produced a new source mesh through three successful native calls but
Hermes then returned the exact `None.rstrip` null completion on all three normal
and all three tool-free recovery decisions. Repair and slicing did not run;
terminal cleanup removed the owned Blender process and both server bindings.
The adapter now emits a minimal format-aware completion envelope derived only
from Wright-recorded successful call numbers after those six exact failures;
concrete downstream file and engineering gates remain authoritative. Its focused
suite passes 41 tests. Attempt015 did not hit that transport fault: it used nine
source calls and reached a valid intermediate with the envelope, two through
bores and two counterbores, but timed out before the pad recess and final export;
an earlier rebuild had left an empty 84-byte STL. No repair or slice ran, and
cleanup succeeded. Attempts014/015 consume the two-attempt source-stage budget.
Quarantine new printing runs until a retained-source probe proves a materially
bounded authoring contract.

Add at most **two local repair attempts per failing stage and accepted authority**.
Retain each generated source/recipe version, diagnostics, hashes and outcomes.
Count corrections across source revisions and replacement grants in the same
repair episode; issuing a fresh grant cannot reset this budget. A new full retry
requires a material fix demonstrated against the retained failure.
Repair may proceed only when the prior outcome proves no mutation or a safe,
owned diagnostic state; reconcile uncertain native operations first. Exhaustion
quarantines that family/binding until a material fix passes the failed probe.
Never repeat identical rejected arguments. This bound does not authorize a
retry of an unknown operation or override existing sheet-metal revision limits.

Reuse verified research/design evidence during diagnostic development with
explicit provenance. A source/input/tool change requires fresh enrollment and
appropriate reapproval, invalidating dependent results. Final countable runs
still execute their entire canonical graph and collect same-run engineering
outputs. Do not import old output files to claim a new full run.

Pass compact typed summaries, file IDs/digests and relevant sections between
stages; keep complete originals available through bounded paging. Avoid sending
large topology reports repeatedly or asking the model to reconstruct known SDK
conventions. Use small, bounded independent agent tasks only when they reduce
elapsed work; avoid duplicating the full campaign context. No automatic upgrade
to another model or invented dollar-cost estimates.

## Scheduling and visibility

Separate mutable queue scheduling from immutable attempt manifests. Track
exclusive resources by actual application session/device/container, acquiring
all required leases in a stable order. Initially permit **two independent lanes**
only after proving host, tool and storage isolation; otherwise remain serial.
A family-local error quarantines that binding/resource, not the whole queue.
Global integrity or shared-runtime deployment issues may require a global
between-case pause. Respect CPU, memory, disk and provider limits.

Preserve the four requested cumulative lines and current-revision status.
Add last successful stage, failure class, pilot/sibling readiness, actual accepted
attempt count, attempts since the last fix, queue age, last completion timestamp,
stage/native/model duration, and token usage when available. Unknown usage is
unknown, not zero; show estimated cost only with an explicit dated rate source.
Expose application leases, owned/borrowed status, health, idle deadline and
cleanup outcome. Update on persisted changes rather than manufacturing progress.

Use bounded event waits and a compact checkpoint instead of repeatedly reading
entire transcripts or rebuilding eighteen-case queues. Persist every material
fix, run outcome and cleanup result before proceeding. Continue unaffected work
when a case is blocked. Report a remaining external blocker only after recording
its exact evidence and needed action; do not poll an unchanged blocker forever.

## Scope and constitution check

This cycle checks full execution, nonempty expected files and same-run identity.
Keep operational geometry/mesh requirements needed to run real tools and
existing safety/integrity gates; do not add certification, convergence studies
or a new engineering-correctness program to the completion condition.
Only explicitly enrolled external handoffs are simulated. Actual CAD, mesh,
supports, slicing and solver outputs remain real. Validity stays zero.

## September 13 PCB attempt008 result and material revision

PCB02/03 attempt008 ran serially through the normal canonical API with automatic
local review and the exact isolated KiCad server. The split symbol and net stages
resolved the attempt007 call-budget bottlenecks in both cases. PCB02 completed
the native board build and all placement work, then stopped before autorouting:
its first native pre-route DRC retained two non-unconnected blocking errors,
courtyard overlaps between fixed J2/H4 and J3/H2. The workflow correctly refused
to mutate immutable fixed geometry or call autoroute. The fictional case02 human
context now supplies feasible connector geometric centers, J2=(34,19.5) mm and
J3=(34,10.5) mm, explicitly distinguished from footprint origins. The first
disposable retained-board probe rejected an earlier candidate with six blocking
errors. The second used actual native courtyard extents and also repositioned
the two unconstrained test points that conflicted with the new connectors;
native DRC then reported zero non-unconnected errors and zero courtyard overlaps.

PCB03 completed component and net authoring, project setup, one-time board build,
all fixed geometry and all remaining placement. It performed bounded distinct
corrections for TP2 and TP5, passed to design-rule application, and then exceeded
the 600-second combined finish-board stage before its final get-constraints and
footprint-list checks. Infrastructure and the KiCad server stayed healthy. The
future graph now separates remaining placement from a short rule/seal stage, so
the latter owns rule application, the final two read-only checks and capture of
the immutable unrouted PCB/project. This is a 16-stage graph and its focused
tests pass 3/3 with Ruff and diff checks clean. A read-only retained PCB03 probe
also returned the persisted 40 x 30 mm outline, 0.25 mm track/clearance, 0.60 mm
via diameter and all 19 footprints through the proposed seal observations in a
few seconds. Both attempt008 runs remain
immutable and receive no output credit. A new full run requires fresh source and
input digests, enrollment, mounts and live preflight; case01 stays preserved.

The dashboard remains live at `http://127.0.0.1:8771/?view=recovery` and reports
`30 / 30 / 18 / 0`. Content validation remains disabled.

## September 13 PCB attempt009 terminal results

PCB02attempt009 stopped at the connection seam after a successful connected-file
save, a later in-memory correction, and an attempted second save. Wright's
completed-operation replay guard rejected the repeated mutation. The future
connection contract now performs all read-only inspection and in-memory
correction before exactly one final save, with no post-save mutation or re-save.
The focused 16-stage graph tests pass 3/3.

PCB03attempt009 cleared every earlier schematic, board-build, placement and seal
bottleneck. It passed pre-route native DRC after excluding only expected
`unconnected_items`; its one FreeRouter operation produced 70 tracks, four vias
and zero unconnected items. Final native DRC found six real copper-to-edge
errors, so Wright blocked fabrication and preserved the routed board unchanged.
The first disposable retained-board route proof moved J3 and J4 inward and
removed all six edge errors, but revealed a J3/TP3 courtyard overlap. The second
bounded proof also moved TP3, then passed pre-route DRC, one autoroute and final
native DRC with zero errors. The case03 human input now fixes the proved
J3=(36,16.46) mm and J4=(20,25.5) mm connector centers and TP3=(32,14) mm pad
center. Receipt:
`.local-run/feature-081-live/campaign-execution/pcb03-route-edge-clearance-qualification-002.json`.
Both attempt009 runs remain immutable and receive no output credit. The
dashboard remains `30 / 30 / 18 / 0`; content validation stays disabled.

No constitution amendment is needed. Product lifecycle logic belongs in existing
application/gateway services with SQLite persistence, thin routes and CLI/MCP
access. Development scheduling remains under scripts and cannot become a
template-ID executor. MCP-specific software stays outside the base image.
Existing authentication, RBAC, approval identities, immutable history, native
isolation and UI acceptance obligations remain in force. Normal local milestones
are already authorized; real printer/vendor writes, purchases, publication and
push/merge/release remain outside this campaign.

## September 14 PCB attempt010/011 terminal results

PCB03 attempt010 reached the bounded “Place remaining footprints” task and
terminated with `TASK_TIMEOUT` after the model had successfully placed through
C2. The compiler correctly caps each agent task at 600 seconds, so the repair
does not raise that limit. The preparer now emits a 17-stage graph: one 600-second
pass places only remaining R/C references, and a second 600-second pass places
remaining test and miscellaneous references before the existing rule/seal stage.
Focused budget tests pass 3/3 and Ruff is clean.

PCB02/03 attempt011 used that split graph, a fresh enrollment, the exact pinned
no-network KiCad image and a 2/2 read-only batch preflight. The runtime replacement
was verified at 56 mounts (52 retained plus four fresh attempt011 mounts) and
reactivated after correcting a wrapper assertion. PCB02 reached the native
`pending_approval` build boundary, but the extracted board had five nets rather
than the approved six: every required `GND` member was merged into `5V`, including
J2.3 and C3.2. The workflow blocked before fixed placement and routing, preserving
the failed native files. The next PCB02 attempt requires a disposable source/build
probe that proves the representation/order of `5V` and `GND` before a full run.
PCB03 was then held by the shared 512 MiB workspace guard and did not dispatch.

No output credit was issued. The dashboard remains live at
`http://127.0.0.1:8771/?view=recovery` with `30 / 30 / 18 / 0`, and content
validation remains disabled. Three bounded run-log archives moved only
size/SHA-256-verified copies to the D: evidence store; active runtimes and the
current KiCad rollback archive were preserved. No additional stopped backup
container was deleted.

## September 14 PCB attempt011 diagnosis and next repair

The PCB02 attempt011 five-net result was reproduced in two disposable native
qualifications. Reordering the GND operations before 5V did not change the
result. A second qualification using neutral labels (`GROUND` and `VCC5`) also
merged the two rail groups, proving that the failure is geometric rather than a
KiCad power-name alias. The generated symbol layout placed C2 pin 2 and C4 pin
1 on the same x coordinate with their 2.54 mm label stubs touching; KiCad’s
authoritative XML exporter therefore treated the intended six-net design as one
power net. A direct-label probe that placed each label at its exact pin tip and
removed the stubs produced six native nets with the approved memberships.

The authoring prompt now requires planning the complete symbol grid before the
first mutation, leaving each 2.54 mm stub disjoint and separating adjacent
vertical passives laterally or beyond their combined stub reach. The normal
connect stage remains label-based, so a fresh attempt must regenerate symbols
from this revised prompt and then rerun the native netlist boundary. Probe
receipts are in `.local-run/feature-081-live/campaign-execution/`, including
the original order test, neutral-label test and direct-label XML qualification.
No campaign output credit was issued. The dashboard remains `30 / 30 / 18 / 0`;
content validation stays disabled.

## September 14 PCB attempt012 route result and repair qualification

PCB03 attempt012 completed authoring and stopped at route-and-inspect. The
single allowed autoroute left one J2 GND connection unrouted, so native DRC
reported one blocking `unconnected_items` error and no fabrication export was
created. PCB02 was held by the shared 512 MiB free-space guard before dispatch.

Retained-board qualification004 proved a bounded repair with the existing
J3/J4/TP3 geometry: set J2 footprint origin to (5.0,19.0) mm and TP1 footprint
origin to (10.0,14.0) mm. Both native DRC checkpoints then had zero blocking
errors, zero unconnected items and zero copper-edge errors. These exact origins
are in the PCB03 context for the next fresh source run. Attempt012 and all
qualification receipts remain immutable and uncredited; the dashboard remains
`30 / 30 / 18 / 0` and content validation remains deferred.

## September 14 PCB attempt013 placement retry result and guard

Attempt013 proved the source-side PCB03 repair through native build: seven nets
were loaded and the fixed J2/TP1 origins were honored. It then stopped in the
R/C placement stage with `WORKFLOW_NOT_READY` after the model replayed the
completed `pcb` operation following its final move. This was a task termination
retry, not a native geometry or DRC failure; no output credit was issued. PCB02
was held before dispatch by the shared 512 MiB disk guard.

The R/C and remaining-placement prompts now require an immediate final report
after the last successful mutation or audit and prohibit any further tool call.
Focused stage-budget tests pass 3/3. Preserve attempt013, restore disk
headroom with verified inactive-evidence archiving, then stage attempt014;
dashboard remains `30 / 30 / 18 / 0` and content validation remains deferred.

## September 14 PCB attempt014 terminal results and connect guard

PCB03 attempt014 stopped in schematic connectivity with `WORKFLOW_NOT_READY`
because the model replayed the completed `schematic` operation after its final
save. PCB02 completed its six-net authoring and one autoroute, but final native
DRC retained three ADC_B `copper_edge_clearance` errors at 0.6069 mm versus the
1.0000 mm rule, plus eight silkscreen warnings. Neither case received output
credit.

The connect prompt now terminates immediately after the single final save and
coverage report. Qualify PCB02’s route-sensitive geometry on a retained board,
then stage the next fresh attempt with that exact repair. Dashboard remains
`30 / 30 / 18 / 0`; content validation remains deferred.

## September 14 PCB attempt015 launch and retained-board qualification

A disposable retained-board proof exercised PCB02 through FreeRouter and native
DRC. The qualified geometry is J1 origin `(4.5,18.81)` mm at 180°, C3 origin
`(8.0,23.0)` mm at 90°, and C4 origin `(12.0,23.0)` mm at 0°; all three
variants routed all nets with zero final native DRC errors. Receipt:
`pcb02-placement-qualification-003.json`. The exact origins are now included
in PCB02 context and board-build guidance.

Attempt015 was staged and passed read-only preflight for both PCB cases. The
72-mount pinned KiCad runtime is running, and hidden runner PID 37732 is
dispatching PCB03 then PCB02 serially with auto approval and the 512 MiB disk
guard. Durable state is under
`.local-run/feature-081-live/campaign-runner-state/pcb-attempt-015-live`; the
dashboard remains live at `http://127.0.0.1:8771/?view=recovery` and was
`30 / 30 / 18 / 0` at launch.

## 2026-09-14 PCB attempt015 PCB03 completion and PCB02 handoff

PCB03 attempt015 completed all required workflow stages and produced the expected native KiCad package: schematic, project, PCB, BOM CSV, Gerber ZIP, ERC and DRC reports, evidence records and run metadata. Native ERC and DRC completed with zero errors (warnings are retained in the reports), and the output tree contains 203 nonempty files whose recorded export hashes were verified before the dashboard incremented `processes_with_outputs` from 18 to 19. The runner recorded a lifecycle snapshot mismatch after completion; the raw run, exported evidence and lifecycle records are preserved for diagnosis and no content-validity credit was assigned.

The same hidden serial runner immediately dispatched PCB02 attempt015. PCB02 is currently running under the 72-mount identity-verified KiCad runtime with the 512 MiB disk guard. Dashboard is live at `http://127.0.0.1:8771/?view=recovery` and currently reports `30 / 30 / 19 / 0`; content validation remains disabled. Persistent recovery state records the live dashboard metrics and PCB02 handoff.

## 2026-09-14 PCB02 attempt016 recovery dispatch

Attempt015 stopped at the build approval boundary after the native audit reported H3-C2 and TP1-J3 courtyard overlaps. A disposable KiCad qualification proved a bounded repair: C2 footprint origin `(23.0,18.5)` mm, rotation 0°, and TP1 origin `(10.0,14.0)` mm, rotation 0°. The PCB02 context and prompts now carry those exact fixed references.

Attempt016 was prepared from the API instance after removing stale preparation sections while preserving the instance task IDs. Read-only preflight passed with 17 stages, 9 inputs, 14 granted tools and no output files. The pinned network-isolated KiCad runtime now has 74 mounts with the same image and 18 tool schema pins. Worker PID 38860 is running with auto approval and the 512 MiB guard. Dashboard: `http://127.0.0.1:8771/?view=recovery`, metrics `30 / 30 / 19 / 0`; content validation remains disabled.

## 2026-09-14 PCB02 attempt016 C3 geometry stop and attempt017 recovery

Attempt016 completed authoring, connectivity and native project initialization, then stopped at the expected build approval boundary. The native build returned 14 components, 6 nets and 27 assigned pads, but reported C3 at origin `(8.0,23.0)` mm, rotation 90 degrees as off-board/overlapping. The run received no output credit and remains preserved as a terminal failure.

A disposable KiCad qualification copied the failed board and tested five C3 candidates. C3 origin `(8.0,23.0)` mm at rotation 0 degrees returned zero native audit errors and zero courtyard overlaps. The board-build prompt and PCB02 context now require that qualified rotation. Attempt017 passed fresh preflight with 17 stages, 9 inputs, 14 granted tools and an empty output tree. The pinned network-isolated KiCad runtime was extended to 76 mounts with unchanged image and tool pins; worker PID 10464 is running under auto approval. Dashboard remains live at `http://127.0.0.1:8771/?view=recovery` and synchronized at `30 / 30 / 19 / 0`; content validation remains disabled.

## 2026-09-14 PCB02 attempt017 duplicate-operation stop and attempt018

Attempt017 passed the native placement audit with all 14 footprints clear and zero overlap or pad-clearance issues, but the model requested `pcb` again after the final silkscreen label mutation. The runtime rejected the completed operation and stopped the case without output credit. The source prompt now requires immediate termination after the final mounting-hole or silkscreen-label mutation, forbidding any later `pcb`, audit, load or inspection call.

Attempt018 passed fresh preflight with 17 stages, 9 inputs, 14 granted tools and an empty output tree. The pinned KiCad runtime was extended to 78 mounts with the same image, network isolation and 18 tool schema pins. Worker PID 4956 is running under auto approval. Dashboard remains live at `http://127.0.0.1:8771/?view=recovery` and synchronized at `30 / 30 / 19 / 0`; content validation remains disabled.

## 2026-09-14 PCB02 attempt018 schematic duplicate and attempt019

Attempt018 completed the native authoring task but stopped in schematic connectivity
after the model repeated the completed `schematic` operation following the final
connected-file save. The runtime rejected the duplicate operation; no output
credit was issued and the run/evidence remain preserved. The connect prompt now
states that the successful save is the terminal event, requires the next response
to be the final report, and explicitly forbids using the save result to trigger
any further tool call.

Attempt019 was staged from a fresh source with the repaired prompt and passed
read-only preflight (17 stages, 9 inputs, 14 granted tools, empty output tree).
The pinned network-isolated KiCad runtime was extended from 78 to 80 mounts with
the same image and tool pins. Worker PID 30096 is running under auto approval;
dashboard remains live at `http://127.0.0.1:8771/?view=recovery` with metrics
`30 / 30 / 19 / 0`, and content validation remains disabled.

Attempt019 cleared schematic connectivity and native project initialization, but
the board-build response reported `placement_hint_offboard` for the qualified C4
origin `(12.0,23.0)` mm at rotation 0°. No footprint mutation or output credit
was issued. A disposable KiCad qualification on the preserved attempt019 board
tested five C4 positions; the original `(12.0,23.0)` origin returned zero audit
errors, as did the bounded alternatives. The build prompt now treats this
specific contradiction as an initial observation and permits the one first
`move_footprint` call at the already-qualified C4 coordinate before continuing.

Attempt020 was staged from a fresh source and passed read-only preflight with 17
stages, 9 inputs, 14 granted tools and no outputs. The pinned runtime was
extended to 82 mounts with unchanged image and tool pins. Worker PID 39620 is
running under auto approval; dashboard remains `30 / 30 / 19 / 0` at
`http://127.0.0.1:8771/?view=recovery`, and content validation remains disabled.

Attempt020 completed all 17 required stages. Its build accepted the qualified
C4 recovery path, schematic connectivity completed without a duplicate save,
native routing and rule checks completed, and the final verification stage
exported the editable KiCad sources, ERC/DRC reports, BOM, drill file, Gerber
layers and archive. The independent verifier checked all 32 recorded output
files: 32 existed, all were nonempty, and all recorded sizes and SHA-256 hashes
matched (`missing=0`, `mismatched=0`). The dashboard advanced to
`30 / 30 / 20 / 0`; content validation remains disabled. Verification receipt:
`.local-run/feature-081-live/campaign-execution/pcb020-output-verification.json`.

## 2026-09-14 Pi03 attempts035-037 CFD compiler recovery

Pi03 attempt035 was staged with the corrected fan-face geometry contract but stopped before workflow dispatch because the workspace free-space guard measured 455,225,344 bytes against the 512 MiB requirement. The attempt and its state remain preserved without output credit.

Attempt036 ran through source research, design basis, auto approval, AgentCAD authoring and actual CAD export inspection. The inspected fluid domains recorded one 30 by 30 mm fan face at Y=12.5 and one 30 by 30 mm outlet face at Y=107.5; all same-run STEP hashes and required region identities were retained. The fixed CFD preparation task then failed before writing a mesh because the compiler rejected the CAD contract's bounded `evidence` provenance key as an unsupported declarative field. This was a contract mismatch, not a geometry or solver result. Raw run record: `runs/campaign-raspberry-pi-enclosure-03-attempt-036/20260914T094854Z-19de94a73d60.json`.

The fixed compiler now accepts only the closed, bounded CAD evidence shape and continues to reject unknown fields, source text and dictionary injection. A regression test covers both acceptance and rejection. Attempt037 was staged from a fresh API instance, passed read-only preflight (11 stages, 13 pinned tools, 17 inputs, empty outputs), and dispatched under the 256 MiB guard. Its dashboard remains live at `http://127.0.0.1:8771/?view=recovery` with metrics `30 / 30 / 20 / 0`; content validation remains disabled.

## 2026-09-14 Pi03 attempt037 context-limit stop

Attempt037 completed source research, the design-basis approval, native AgentCAD authoring and the full independent CAD/export inspection. It did not reach the CFD tool: the resume request was rejected with `workflow_context_limit` because the 32-call inspection task retained too much per-file observation and omission metadata for the next model task. No evidence was truncated and no output credit was issued. This is a workflow-context budgeting failure, not a CAD or CFD failure.

The next fresh Pi attempt must lower the scoped inspection task to 18 tool calls (the 16 expected CAD/contract files plus bounded response room) and keep the existing fixed compiler and geometry contract. Attempt037 remains immutable. Dashboard remains `30 / 30 / 20 / 0`; content validation remains disabled.

## 2026-09-14 Pi03 attempt038 AgentCAD geometry stop

Attempt038 passed staging, preflight, source research, design-basis approval and
CAD-source authoring. AgentCAD then rejected the generated source before any
expected export was committed. The preserved AgentCAD build metadata records
`Fluid outer planes differ from intended bounds` with an observed fluid zmin of
4.5 mm instead of the fixed 2.5 mm boundary. The generated source placed its
PETG floor at Z=2.0..4.5 mm, so subtracting that floor necessarily removed the
required lower air-domain plane. No output credit was issued and the dashboard
remains `30 / 30 / 20 / 0`.

The authoring contract now states the measured floor/fluid coordinates as
non-negotiable invariants (PETG floor Z=0.0..2.5; final fluid zmin=2.5 and the
other five fixed planes) and forbids a Z=2.0 floor. Attempt038 is immutable;
the next fresh attempt must regenerate the source under this tightened contract
and retain the 18-call CAD inspection budget.

## 2026-09-14 Pi03 attempt039 context-limit stop

Attempt039 regenerated a valid same-run CAD package: AgentCAD accepted both
variants, the final fluid bounds retained zmin=2.5, and the unique 30 by 30 mm
fan/outlet faces were observed. The 18-call inspection completed, but the next
CFD preparation request was rejected with `workflow_context_limit`. The two
contract JSON pages were being retained inline in the model context even though
their complete durable files were already available to the fixed compiler. No
output credit was issued; the dashboard remains `30 / 30 / 20 / 0`.

The inspection task now requests `includeText=false` for every file, records
only actual path/size/hash identities, and leaves full contract bytes on disk for
compiler validation. This is a context-budget repair; attempt039 remains
immutable and the next fresh attempt must use the compact identity-only report.

## 2026-09-14 Pi03 attempt040 stale fixed-compiler process

Attempt040 was staged from the compact identity-only inspection repair and
passed read-only preflight. Source research, design basis, native AgentCAD
authoring, actual STEP export and the 16-call identity inspection all completed;
AgentCAD again retained the required fluid zmin=2.5 mm and measured fan/outlet
faces. The CFD preparation request was then rejected with
`Unsupported declarative contract; source and dictionary injection are
forbidden`, even though the staged `pi_cfd_operations.py` contained the bounded
evidence allow-list. Investigation found the long-lived API-managed CFD worker
had imported the pre-repair compiler before attempt040 began. No mesh or output
was produced and no dashboard credit was issued.

The custom server `d044179a-bf3d-4086-b7c4-b00e8fd97f71` was stopped and
restarted through Wright's MCP lifecycle API. The new worker is running from the
same pinned container and reads the current host-bound compiler. Attempt040 is
immutable; the next fresh attempt must prove the restarted process with the
compact contract and keep the dashboard at `30 / 30 / 20 / 0` until a complete
output tree is independently verified. Content validation remains disabled.

## 2026-09-14 Pi03 attempt041 storage guard

Attempt041 was staged from fresh inputs and passed the read-only source, grant,
corpus and tool preflight. The campaign runner stopped before workflow dispatch
because the external workspace had 51,834,880 bytes free against its
268,435,456-byte minimum. No model task, engineering operation or output was
started, so no dashboard credit was issued. The attempt and state are preserved
as an infrastructure stop.

Four inactive Codex runtime rollback caches were removed from the C: volume after
path verification; the active runtime and all campaign evidence remain intact.
The volume now has approximately 391 MiB free. A fresh attempt is required after
this storage repair; dashboard remains `30 / 30 / 20 / 0` and content validation
remains disabled.

## 2026-09-14 Pi03 attempt042 bounded evidence-shape stop

Attempt042 passed preflight, auto-approved its design review, completed native
AgentCAD authoring and successfully reached the restarted fixed CFD compiler.
The compiler rejected the authored contract because
`fluid_domain_observed_bounds_mm` was emitted as a six-item list and the face
records used aliases (`area_mm2`, `matching_count`, `selected_face`) instead of
the closed named-key object shape. This is a bounded authoring-contract error;
the compiler ran and correctly refused ambiguous evidence. No mesh or output
credit was issued; attempts040-042 remain immutable and the dashboard is still
`30 / 30 / 20 / 0`.

The authoring prompt now states the exact evidence object schema, requires named
axis keys for domain and face bounds, and forbids the observed aliases and list
encoding. A regression test covers list rejection. The next fresh attempt must
use this prompt with the already restarted compiler and identity-only inspection.

## 2026-09-14 Pi03 attempt043 fixed-adapter volume stop

Attempt043 passed the repaired storage preflight, source research, design-basis
approval, native AgentCAD authoring, fixed-plane checks and the compact
identity-only CAD inspection. The named-key evidence repair therefore reached the
CFD compiler successfully. Preparation stopped before meshing because the
API-selected `wright-081-pi-runtime` used a newly recreated named `/workspace`
volume that did not contain `/workspace/pi-boundary-build` or its qualified
`libwrightPiFan.so`; the fixed compiler correctly raised
`Qualified fixed fan adapter is absent or its source changed`. No output credit
was issued and attempt043 remains immutable.

The already-qualified adapter source and library were restored into that exact
disposable runtime volume. The source hash matches the read-only operation source
(`e2265a7c7be859b72e74e923a95207a3d8da237712ff60984c06c33fb95ec184`), and the
CFD server was stopped and reactivated through the normal MCP lifecycle API.
The next fresh attempt must exercise this restored pair; dashboard remains
`30 / 30 / 20 / 0` and content validation remains disabled.
