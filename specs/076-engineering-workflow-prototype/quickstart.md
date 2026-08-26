# Prototype Quickstart and Checkpoint Workflow

## Status

CP2A promotes React Flow as the single feature-flagged canvas adapter over
Wright-owned fixtures. The accepted color/style contract is versioned as
`cp2a-1`. CP3 experiments now include a repeatable headless four-block smoke
run; this is discovery evidence and does not authorize production execution.

This branch was frozen as a reference-only prototype checkpoint on 2026-08-26.
Use the commands below to reproduce or inspect its evidence, not as instructions
to promote prototype code into production. New product work should begin from
`dev` after approval of the durable program plan.

## Safety boundaries

- Work only on `076-engineering-workflow-prototype`.
- Treat the branch as disposable learning evidence, not a production migration.
- Do not modify Rivet or convert saved Rivet projects.
- Do not add CAD-, FEA-, manufacturing-, procurement-, or supplier-specific services/executors.
- Route all real MCP calls through the existing generic Wright catalog and governed gateway.
- Keep the prototype feature flag off by default and use a direct prototype route.
- Do not begin the next major checkpoint until its evidence is reviewed.

## Proposed route and flag

- Selected route: `/prototype/engineering-workflow`
- Temporary CP1B compatibility alias: `/prototype/engineering-workflow/bakeoff/react-flow`
- Flag: `VITE_ENGINEERING_WORKFLOW_PROTOTYPE=1`
- Initial navigation: direct URL only; no production sidebar entry.
- The visual slice is outside authenticated backend bootstrap so deterministic UI review works offline.
- Persistence: deterministic fixtures plus optional browser-local ephemeral drafts. No database migration.

## Inner development loop

Run the smallest relevant test first. The exact file list is created with each checkpoint.

```powershell
npm run test --workspace apps/web -- <changed-test-files> --no-file-parallelism
```

Then run the prototype model tests:

```powershell
npm run test --workspace apps/web -- src/prototypes/engineering-workflow/domain --no-file-parallelism
```

For a UI slice, run only its component tests, then the prototype set. Formatting and targeted type checks run before broader suites. Browser automation is not part of ordinary edit/save feedback.

## Headless four-block smoke run

With Wright's local API running and BREP MCP installed, the following command
executes Prompt/Request → selected AI → exact BREP MCP tool → evidence-based
evaluation without mounting the workflow editor:

```powershell
node apps/web/src/prototypes/engineering-workflow/evaluation/run-brep-headless-smoke.mjs
```

The script creates and deletes an isolated Wright AI session, runs the model
with tools disabled, validates a tool-independent mounting-plate result,
deterministically compiles the exact `history` argument, mounts BREP's required
loopback application surface in headless Chromium, invokes
`brep.model.apply_history`, and requires three consistent inspections. The BREP
MCP itself is application-controlled rather than truly headless. Close other
BREP control surfaces before this experiment; any inconsistent inspection
causes an explicit failure.

## Interactive diagnostic run

Open `/prototype/engineering-workflow?scenario=diagnostic`. Wright's current
configured AI model is selected automatically; the inspector contains an
optional model override. Use **Run** to start and **Retry** after a stopped run.
The progress monitor identifies the active block. Select any block or progress
step and open **Run result** to see its status, duration, engineering summary,
and recovery guidance. Expand **Produced data** or **Technical details and
evidence** only when exact payloads, identities, or timestamps are needed.
After a successful BREP fixture run, the completion monitor shows a
**Four-hole mounting plate** output card. Use **View in BREP** to inspect the
retained live session model or **Download model definition** to save the exact
BREP history JSON. Resetting the prototype releases the session-scoped model.

These actions test a generic output-reference contract. A production document,
web model, or native CAD adapter can supply different actions without adding a
document-, Onshape-, or Solid-Edge-specific branch to the workflow runtime.

## Checkpoint verification

Before a checkpoint review:

1. Run T0 model/schema/reducer tests and record duration (target <= 5 seconds).
2. Run T1 prototype component tests and record duration (target <= 30 seconds).
3. Run T2 fake LLM/MCP contract tests when introduced (target <= 2 minutes).
4. Run only the checkpoint's relevant Chromium journey; the suite has at most three total journeys.
5. Capture the UI and update the checkpoint evidence record.
6. Classify failures as product, test, environment, or unknown.
7. Request human review and record continue/change/stop/defer.

## Push verification

Only after a checkpoint is accepted and ready to push:

1. Read `docs/contributing/dev-push-runbook.md`.
2. Run `scripts/check-dev-push.ps1` in a non-PTY process on Windows.
3. Preserve the complete result in checkpoint evidence.
4. Commit a checkpoint-sized change with the associated evidence.

The full gate is a pre-push protection, not the development watch loop.

## Reference scenario demonstration

The integrated demo should let a mechanical engineer:

1. See Define, Verify, and Manufacture as phase lanes.
2. Inspect image/context inputs and a reviewable design specification.
3. See an engineering action bound to an exact generic MCP tool.
4. See a review gate and a failed verification result feed back to design.
5. See successful verification produce artifact references used by a fabrication/quote workflow.
6. See approval and notification status with run evidence.
7. Ask the LLM to make a bounded workflow edit, review the semantic diff, and accept or reject it.

The scenario can use deterministic MCP/LLM fixtures. A configured live MCP server or model is an additional demonstration only after deterministic contracts pass.

The CP1A evidence views are `evidence/visual-slice-workflow.png` and `evidence/visual-slice-capability-library.png`.

## Expected deliverables by checkpoint

| Checkpoint | Deliverable                                                                                    |
| ---------- | ---------------------------------------------------------------------------------------------- |
| CP0        | Rivet/current-code postmortem, timings, reference fixture, decision rubric.                    |
| CP1A       | Reusable read-only visual contract plus searchable engineering capability library.             |
| CP1B       | Three shallow canvas harnesses using the visual contract and a scored recommendation.          |
| CP2        | Selected canvas adapter with interaction and comparative usability evidence.                   |
| CP3        | Typed manual editing, validation, semantic diff, undo, and local draft behavior.               |
| CP4        | Generic MCP catalog binding and governed fake/real call path with three conformance tools.     |
| CP5        | Deterministic LLM command proposals, preview, accept/reject, and invalid-response handling.    |
| CP6        | Integrated reference story, limited browser journeys, comparative usability/timing evidence.   |
| CP7        | ADR recommending retain Rivet, hybrid, replace, or stop; production roadmap and deletion plan. |

## Cleanup

If the recommendation is stop or the branch is no longer needed, preserve the accepted spec/evidence through the agreed documentation path before deleting the remote branch. Prototype dependencies, route, local drafts, and harness code have no production compatibility guarantee.
