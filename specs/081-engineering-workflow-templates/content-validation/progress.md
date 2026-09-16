# Content-validation checkpoint

**State:** Planned / deferred until all 30 process flows produce data.
**Updated:** 2026-09-13 UTC.
**Current authority:** Define and save the implementation plan for a future agent.
**Implementation:** Not started. **Validation results:** None created by this planning task.
**Preferred future agent:** Sol, selected by the user at handoff.

## Next action

On a later implementation assignment, read [quickstart.md](quickstart.md) and execute **CV01: G0 read-only cohort audit**. If all 30 current completed flows and stable output identities are not established, leave the implementation deferred and report precise missing prerequisites.

## Milestones

| Milestone                          | Tasks                               | Status      |
| ---------------------------------- | ----------------------------------- | ----------- |
| Activation and acceptance baseline | CV01–CV05                           | Not started |
| Contracts and engine               | CV06–CV11                           | Not started |
| Two real pilots                    | CV12–CV15                           | Not started |
| All family profiles/readers        | CV16–CV25, checkpoints A–E per task | Not started |
| Evidence surfaces and corpus       | CV26–CV30                           | Not started |
| Reliability and final handoff      | CV31–CV34                           | Not started |

## Planning decisions to preserve

- Independent content verification and design compliance are distinct.
- Validate retained current artifacts before considering generator repair.
- All 30 profiles and all mandatory requirements receive explicit dispositions.
- Profiles live outside generation packs so generation fingerprints stay unchanged.
- Historical execution `valid_data=0` remains a historical fact; new validation uses separate records/projections.
- Reuse existing assertion/normalizer logic through an explicit status adapter; canonical workflows do not run through legacy Rivet orchestration.
- Current selected Modelica derivative/hysteresis/numerical controls must be rechecked at activation.
- The parent AGENTS plan pointer remains the active campaign context; this deferred plan is linked from the parent.

## Planning verification

The saved seven-document bundle was checked for 34 unique sequential task IDs,
coverage entries for all 30 current scenario IDs and resolvable local Markdown
links; no missing task, case or local target was found. Scoped Git whitespace
checking passed. Independent architecture and acceptance reviews were
incorporated, including terminal retry/resume, append-only late-review reports,
mixed failure/unresolved verdicts and deterministic current-result selection.
These are documentation checks, not implementation or engineering-validation tests.

## Resume record template

After implementation starts, append a concise dated entry containing:

- Exact completed task/checkpoint and evidence/report paths.
- Checkout/commit and modified files relevant to the task.
- Selected cohort/profile/reader versions and currentness changes.
- Tests run, outcome and scope; generator failures vs validator defects.
- Owned native sessions/working copies and cleanup state, if any.
- Unresolved source questions, pending reviews or capability blockers.
- One concrete next task and its prerequisites.

Do not prefill pass counts, reader qualification or gate evidence before performing the work.
