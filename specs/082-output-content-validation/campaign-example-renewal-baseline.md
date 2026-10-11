# Campaign example renewal baseline

Captured: 21 September 2026, America/New_York. Work package: R0.

## Ownership and safe boundary

- Working tree: `D:/repos/wright`
- Branch: `codex/082-output-content-validation`
- Starting commit: `5a9650522f0aa5d2e1d86d6145c12d8da52d3e2d`
- Campaign: `081-engineering-datasets-v1`
- The only identified campaign-owned runner is
  `.local-run/feature-081-live/campaign-runner-state/validator-082-pilot-robot01-attempt010`.
- Launcher PID 9212 is alive. It owns Robot 01 attempt 010, run
  `1e10a25958694ce2ab4d9454029b1fcf`.
- The attempt is `awaiting_manual_approval`; runtime status is
  `awaiting_approval`; evidence status is `exported`.
- The broad 30-case queue is not running. Awaiting manual approval is the safe
  boundary, so no pause, approval, retry, or dispatch action was taken.
- Robot 010 remains pending for the engineer who owns its review. Renewal work
  must not approve it merely to clear the queue.

## Durable campaign state

The current `artifacts/engineering-workflow-datasets/status.json` reports:

| Measure | Historical | Current revision |
| --- | ---: | ---: |
| Datasets created | 30 | 30 definitions remain present |
| Combinations run | 30 | 1 |
| Processes with outputs | 24 | 0 |
| Content-valid results | 0 | 0 |

The execution adapter is ready. Validator coverage reports 30 qualified,
30 full-scope and 0 unsupported profiles. Reconciliation is current with no
recorded error. These are infrastructure/coverage facts, not proof that the
renewed scenarios have been implemented, run, or accepted.

## Service observation

- The local campaign dashboard on port 8771 returned HTTP 200.
- The served workspace on port 5173 returned HTTP 200.
- No API-health claim is made: the attempted `/health` request returned the
  frontend document rather than an attributable API health response.

## Isolation and preservation

- Renewal records live beside the 082 specification and will use prospective
  revisions; prior scenario inputs, attempts, evidence, approvals, retry history,
  and current status remain immutable.
- The worktree already contained unrelated tracked edits and many untracked run
  artifacts. They are not owned by this renewal and must not be swept into its
  commits.
- No provider deployment, native lease, campaign queue, or physical/external
  destination was changed while capturing this baseline.

## R0 conclusion

R0 is complete. The campaign is safely stopped at a human-review boundary, its
pending review is preserved, and R1 lineup planning can proceed without a
competing broad runner.
