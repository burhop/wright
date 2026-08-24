# Prototype Quickstart and Checkpoint Workflow

## Status

This document is the planned operator workflow. The prototype code and candidate dependencies do not exist until the plan is approved and their checkpoints are started.

## Safety boundaries

- Work only on `076-engineering-workflow-prototype`.
- Treat the branch as disposable learning evidence, not a production migration.
- Do not modify Rivet or convert saved Rivet projects.
- Do not add CAD-, FEA-, manufacturing-, procurement-, or supplier-specific services/executors.
- Route all real MCP calls through the existing generic Wright catalog and governed gateway.
- Keep the prototype feature flag off by default and use a direct prototype route.
- Do not begin the next major checkpoint until its evidence is reviewed.

## Proposed route and flag

- Route: `/prototype/engineering-workflow`
- Flag: `VITE_ENGINEERING_WORKFLOW_PROTOTYPE=1`
- Initial navigation: direct URL only; no production sidebar entry.
- Persistence: deterministic fixtures plus optional browser-local ephemeral drafts. No database migration.

## Inner development loop

Run the smallest relevant test first. The exact file list is created with each checkpoint.

```powershell
npm run test --workspace apps/web -- --run <changed-test-files>
```

Then run the prototype model tests:

```powershell
npm run test --workspace apps/web -- --run src/prototypes/engineering-workflow/domain
```

For a UI slice, run only its component tests, then the prototype set. Formatting and targeted type checks run before broader suites. Browser automation is not part of ordinary edit/save feedback.

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

## Expected deliverables by checkpoint

| Checkpoint | Deliverable                                                                                    |
| ---------- | ---------------------------------------------------------------------------------------------- |
| CP0        | Rivet/current-code postmortem, timings, reference fixture, decision rubric.                    |
| CP1        | Three shallow read-only canvas harnesses and scored recommendation.                            |
| CP2        | Selected canvas with production-like engineer-readable static UI and usability evidence.       |
| CP3        | Typed manual editing, validation, semantic diff, undo, and local draft behavior.               |
| CP4        | Generic MCP catalog binding and governed fake/real call path with three conformance tools.     |
| CP5        | Deterministic LLM command proposals, preview, accept/reject, and invalid-response handling.    |
| CP6        | Integrated reference story, limited browser journeys, comparative usability/timing evidence.   |
| CP7        | ADR recommending retain Rivet, hybrid, replace, or stop; production roadmap and deletion plan. |

## Cleanup

If the recommendation is stop or the branch is no longer needed, preserve the accepted spec/evidence through the agreed documentation path before deleting the remote branch. Prototype dependencies, route, local drafts, and harness code have no production compatibility guarantee.
