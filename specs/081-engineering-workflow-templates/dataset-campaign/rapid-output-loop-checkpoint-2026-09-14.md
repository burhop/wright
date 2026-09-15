# Rapid output loop checkpoint — 2026-09-14

The throughput-first continuation stopped after six dispatched full pilots. Two
additional Bracket03 staging launches were blocked before dispatch and did not
consume pilots. The final three dispatched pilots—PCB02 attempt021, Bracket03
attempt011, and Bracket03 attempt012—produced no new complete output set, which
triggers the goal's mandatory early-stop rule. No further work was launched.
Content validation remains disabled and no code was committed.

## Current campaign state

- Dashboard: <http://127.0.0.1:8771/?view=recovery> (HTTP 200, 41,698 bytes at
  the checkpoint).
- Reconciliation: current at `2026-09-14T17:47:44.13-04:00`.
- Metrics: 30 datasets, 30 combinations, 24 processes with complete output
  sets, 0 content-validated data.
- Six output sets remain: lightweight-equipment-bracket-01/02/03 and
  sheet-metal-part-01/02/03.

## Tested changes and focused proofs

- Printed runtime setup now uses an attempt-local lifecycle database, avoiding
  campaign-wide setup contention.
- Printed-part task guidance now requires one Blender construct/export pass,
  direct `bpy.ops.wm.stl_export`, no `hasattr` dispatch on `bpy.ops`, and no
  rebuilding of already watertight geometry.
- Printed binding/contract tests passed: 8 tests.
- Retained Printed03 source proof completed in 24 seconds; acceptance SHA-256:
  `c2d618...` (full identity is preserved with the proof artifacts).
- AgentCAD timeout remains at the constitutional 600-second maximum. The
  rejected 900-second staging experiment was fully reverted; 10 focused
  AgentCAD source-contract tests passed.
- Bracket03 recovery compilation and independent preflight passed with zero
  errors. The only review warning was the intentional same-name
  `recovery-lineage.json` hash-authenticated copy.
- Retry decisions, outcomes, approvals, hashes, and reported model request
  counts are persisted in `artifacts/engineering-workflow-datasets/` and the
  raw workspace run records.

## Actual pilot outcomes

1. `printed-replacement-part-01/attempt-003` completed with outputs in about
   3.5 minutes.
2. `printed-replacement-part-02/attempt-002` completed with outputs in about
   3 minutes.
3. `printed-replacement-part-03/attempt-016` completed with outputs in about
   3.5 minutes after the retained-source proof and compact task-contract fix.
4. `sensor-interface-pcb-02/attempt-021` completed all 17 required stages with
   32 files and 141 reported model requests. It refreshed current evidence but
   did not increase the aggregate because PCB02 was already one of the original
   21 complete cases.
5. `lightweight-equipment-bracket-03/attempt-011` restored the late successful
   AgentCAD files without replaying native CAD, preserved approval, and reached
   independent inspection. It failed because the late-result ledger itself had
   not been enrolled for complete inspection. No solver ran.
6. `lightweight-equipment-bracket-03/attempt-012` enrolled and hash-verified the
   missing ledger (`6521a04a...c93c7ec`). Inspection then succeeded and proved
   both STEP hashes equal the retained late-result ledger. The first pinned
   `calculix_mesh_preflight` call failed after about 23 seconds with
   `MCP call failed (child_unavailable)`. No solve or final report was credited.

The aggregate improvement in this continuation is 21/30 to 24/30, entirely
from the three printed-part completions. Bracket03 remains incomplete.

## Preserved Bracket03 recovery evidence

- Attempt009 late native result:
  `artifacts/engineering-workflow-datasets/diagnostics/rapid-output-loop-20260914/bracket03-attempt009-late-native-result.json`
- Attempt011 failed run:
  `artifacts/engineering-workflow-datasets/output/lightweight-equipment-bracket-03/attempt-011/run.json`
- Attempt012 failed run:
  `artifacts/engineering-workflow-datasets/output/lightweight-equipment-bracket-03/attempt-012/run.json`
- Attempt012 raw run record:
  `C:/Users/markb/wright-feature-081/engineering-workflow-demos/runs/campaign-bracket-03-attempt-012-recovery/20260914T213635Z-f8dc9b7dd105.json`
- Retry ledger episode: `bracket03-late-native-recovery`, corrections 2/2,
  both outcomes `blocked`.
- Attempt011 and attempt012 partial outputs remain intact. Do not relabel them
  complete and do not rerun this exhausted retry episode.
- Do not launch another pilot from this checkpoint: both the three-consecutive-
  no-new-output stop and the Bracket03 2/2 correction limit are authoritative.

## Remaining blockers

- Bracket03: the hash-bound geometry recovery and inspection now work, but the
  pinned CalculiX child is unavailable. Four recorded solves, four field/reaction
  expansions, and the final engineering comparison remain unexecuted.
- Bracket01: exact operation-11 blend geometry is absent; do not invent it.
- Bracket02: exact pocket/removal/fillet and bolt-keepout geometry is absent; do
  not invent it.
- Sheet-metal family: Solid Edge `AddFlangeByFace` still returns `E_POINTER` in
  both visibility and flange-before-cutout probes. The saved Solid Edge handoff
  identifies this as a separately scoped provider repair. The provider worktree
  contains other-task changes and was not modified or redeployed here.

## Next task recommendation

Run one isolated pinned-CalculiX lifecycle diagnostic, prove
`calculix_mesh_preflight` succeeds against the retained Bracket03 baseline, then
authorize one fresh downstream-only recovery attempt under a new retry boundary.
