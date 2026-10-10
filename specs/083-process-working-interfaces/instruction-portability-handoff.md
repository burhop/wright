# Portable workflow instructions and deliberate input - test handoff

**Status: saved technical goal implemented and qualified locally, 8 October 2026.**
This handoff records exact final run/build identities. Earlier Feature083
acceptance is separate; the current user has not accepted these changes.

## Start here

Open the [isolated authoring workspace](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba).
Its companion [import workspace](http://127.0.0.1:5248/workspace/46354f7c-1428-48a1-b6b3-175cf7eee49e)
is for portable reuse. Authentication is required and has been exercised securely
in browser tests; no token belongs in a link or report. The original user workspace
and services remain separate. No browser-tab opener is available to this agent.

## Human test checklist

1. Use **Workflows -> New workflow**. Confirm a genuinely empty graph. Add text
   and an AI/MCP task, draw a connection, edit the prompt, save and reopen.
2. Inspect **Workflow instructions** and **Step instruction settings**. Check
   effective policy, custom text and origins. Editing a default must not change
   an existing saved definition; an explicit update shows a diff and creates a
   revision. Export/import should retain its instruction bodies.
3. Run a declared **Request input** example. Confirm the diagram shows a normal
   wait, opens the exact same run in a working tab, and restores it after reload.
   An answer continues the same run. Input is separate from engineering approval.
4. Open a completed result from both diagram and working view. The exact indexed
   output filename belongs to that run. Its content should become visible and
   focused, rather than remaining below the page. Reopening must not run again.
5. Inspect documented CAD choices and native measurement evidence. Compare the
   strict negative with the exhaustive strict positive. A rendering is a visual
   result; native dimensions, validation and engineering acceptance are separate.
6. Export a saved workflow, import it into the companion workspace, change its
   declared inputs and run it. Compare source/instruction identities and the new
   numerical outputs. An imported UI remains an inactive candidate requiring
   local compatibility/rebuild/review; it carries no run or approval authority.
7. Open the labelled missing-output negative. Check a specific failure and its
   retained actual tool response, with no invented result or opportunistic dialog.

## Useful saved workflows

[Exact workflow and result links](evidence/instruction-portability-workflow-links.md)
identify each accepted source revision and recorded run. The listed interaction
snapshots were verified through the authenticated normal API; links contain no
credentials or action grants.

| Job | Workflow | Observed software/numerical evidence |
|---|---|---|
| Native CAD to realistic image, documented design choices | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Fshape-to-realistic-image-portable-documented-choices.workflow.wflow) | Completed e333f6183c704380bac48be20b402ccb. Native PSM, actual JPEG and generated PNG; independent203.2 x50.8 x3.175mm native readback. |
| Exhaustively specified strict CAD to realistic image | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Fexhaustive-strict-shape-9663f682.workflow.wflow) | Completed e3a2f56a090f4e9cb765582b42cb21d8 with no assumed choices. Separate read-only run d19cdff0c7df40ab8d34bd2fc203db81 verified native flat203.200003487 x50.8 x3.175mm, thickness/radius3.175mm and K0.5; explicit floating-point tolerance is retained. |
| Strict underspecified CAD, expected failure before geometry | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Faction-intent-shape-strict-unspecified-e998b58e.workflow.wflow) | Run9ccec0d193204bb193aeeb6e6cc2de11 rejected its geometry proposal before gateway dispatch; read-only server observation only. |
| Numerical heat-spreader sizing | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Fheat-spreader-numerical-sizing-portable.workflow.wflow) | Completed189a2fea1a944a588b7b7f520769602d; actual mesh -> temperature fields -> sizing decision, independently checked at every node. Idealized numerical model, not physical acceptance. |
| Original Robot floor-seam data regression | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Frobot-floor-seam-portable-regression.workflow.wflow) | Completedfc012b84347142828ae64066d021ac53; original CSV -> ROS2 bag -> metrics/plots. Association is not a causal finding. |
| Declared first input with same-run restart | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Ffrozen-first-question-portable.workflow.wflow) | Completed d2381e55fb9946b39bfca8df47275774 after an attributed synthetic test answer and service recreation; invalid/stale/duplicate cases retained. |
| Conditional input after actual upstream work | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Fdeclared-question-needed-portable.workflow.wflow) | Completed c996ca8b361d4e2b8ceab30a3ba05ce9 after the declared wait; typed condition evidence, not an AI-created question. |
| Conditional input already resolved upstream | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Fdeclared-question-already-resolved-portable.workflow.wflow) | Completed79aeae6e30eb4b7bbbb36aa57b759be0 with a recorded skip and no fabricated checkpoint. |
| Actual provider response but missing required output, expected failure | [Open](http://127.0.0.1:5248/workspace/ddc70e4f-da62-4d6f-ac4b-4d116eca10ba?workflow=canonical&workflowPath=workflows%2Fexpected-failure-readonly-missing-artifact-bfa40cf8.workflow.wflow) | Run2eb73fce79464521b745f9bd9c8bc775 retains the actual read-only response and reports WORKFLOW_OUTPUT_INVALID. |

The final independent-provider chain71811e15501344d084c5fd261c3060be completed:
native CAD -> Blender topology/unit inspection -> actual offline slice. Its six
output identities were independently hashed; separate native observation confirms
203.2x50.8x3.175mm flat geometry. All28 mesh vertices match the observed unit
conversion, with numerical residuals explicitly separated from engineering
tolerances. The package has254 actual G-code layer changes. Its exact workflow
and results are in the curated link index. No physical dispatch occurred.
Two fresh post-last-fix UI journeys completed in the companion workspace:
steel comparison45253e1f826d465e96e976860000bb9c and aluminum
comparisonba8b9b6208054956956d3283cbea8605. Their actual47.1g/16.2g and
75.36g/25.92g results retain saved A instructions under different defaults B,
with loaded/focused readers and same-run reload. Defaults A are restored by CAS.
Synthetic decisions belong only to new digital test subjects
and retain integration_test attribution; no physical or supplier effect is allowed.

## Evidence and qualification limits

- [Implementation tasks](instruction-portability-tasks.md), [progress](instruction-portability-progress.md)
  and [bug ledger](instruction-portability-bug-ledger.md).
- [Instruction inventory and packaged-resource audit](evidence/instruction-invocation-inventory.md),
  [routing/capture/authority audit](evidence/frozen-model-routing-and-assumption-invalidation.md),
  [input/review live proofs](evidence/instruction-interaction-live-proofs.md),
  [portable dependency qualification](evidence/workflow-bundle-transfer.md),
  [independent modern invocation audit](evidence/instruction-modern-invocation-final-audit.md),
  and [served UI evidence](instruction-portability-ui-evidence.md).
- [Complete saved test-definition index](evidence/instruction-portability-all-workflows.md)
  includes exploratory drafts, negative fixtures and superseded failures. Use the
  curated collection first; a saved definition does not establish successful execution.
- Complete workspace regression after the last typed CAD-export fix:2399 passed,
  24 host-specific skips. Final
  core/adapter/API regression:1464 passed,1 skip. Final exact-value gate tests
  pass30 checks; common-view/reader checks pass106 and web type checking passes.
  Reports retain earlier failures separately; these counts are different scopes,
  not a count of independently accepted engineering jobs.
- API8065 PID41316 and production UI5248 PID13592 remain available, authenticated
  and loopback-only. UI build is `artifacts/process-interfaces/083/instruction-portability-20261008/web-dist-06`;
  served file hashes were checked. Fresh CAD, Blender and offline-slicer providers
  remain available and idle. Original services/workspaces were not restarted.
- The test drive reached capacity. Only goal-owned evidence was compressed or
  moved to the writable C: proof root with byte hashes verified and original D:
  paths preserved by directory junctions. No old/shared evidence was deleted.
- No push, merge or release. Task-owned changes share files with131 pre-existing
  dirty entries; no broad staging or partial checkpoint commit was made.

The multi-provider chain is an isolated digital mockup using existing native CAD,
Blender inspection/unit conversion and an offline slicer. Its fixed CAD output
folder is deliberately unique to this definition. Current run-path/1 does not
template CAD bindings; repeat this example through a new explicitly named copy
and output folder rather than overwriting its evidence. Blender safe mode remains
enabled and requires its export directory to exist from declared upstream work.
These are visible capability limits, not a general reusable CAD-folder claim.

Actual native analytic volume was unavailable in that provider; zero/stale physical
property fields are not used as measurements. Two slicer estimate anomalies
(first-layer time and volume units/value) remain untrusted external metadata.
The verified files, geometry/units handoffs and embedded toolpaths do not establish
material calibration, supports, strength, physical printability or engineering release.
The final invocation audit also distinguishes the text bridge's `hermes` alias,
accepted frozen model lock, redacted uncalled schemas and unobservable provider
instructions. Packaged-resource checks do not claim a published release.

These are implementation/software and scoped numerical proofs. They do not
constitute user acceptance, released-package qualification, physical performance,
manufacturing release, or general support for every provider/schema/graph.
