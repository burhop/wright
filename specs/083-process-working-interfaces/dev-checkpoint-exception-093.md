# Approved development checkpoint exception — 11 October 2026

## User decision and boundary

The user needs the current work on `dev` as the base for a separate Codex-agent
project. After being offered a one-time override of full pre-merge gates, delayed
full CI qualification and narrowly scoped scanner exceptions, the user replied:
“That sounds good. Proceed.” This authorizes this checkpoint through a feature
PR into `dev`; no direct `dev` push, `main` integration or production release.

For this checkpoint, repeated full local merge and changed-branch push gates are
replaced by the completed suite evidence, affected scanner checks and a short
packaged workspace smoke. Full browser/platform CI and development deployment
qualification follow integration. They remain unverified until their actual
results are inspected. The repository's standing gate scripts and policy remain
unchanged; this record is a one-time user exception, not a passing full gate.

## Completed evidence

- Product candidate: `bf09fb609395f64dd74f9e75ab9f9681bd253d9e`.
  Clean Git-archive image:
  `sha256:a059597d35129aade1fda23a23c821582e91fb4e1015c3191f1045dad8d1b0a8`.
- Exact image scan passed with no blocking findings on 11 October, using pinned
  Trivy 0.70.0 and the unchanged image vulnerability policy. Local public receipt:
  `test-results/docker-image-security/20261011T135609Z-9545c092/public/scan.json`.
- Gate 10 passed the backend suites, coverage, blocking static checks, native
  packaging and clean installs before its one frontend timing assertion failed.
  Corrected full frontend suite: 1,790 tests in 198 files passed. Strict docs passed.
  See [delivery evidence](dev-delivery-checkpoint-090.md). Gate 10 remains failed.
- Fresh candidate-image smoke 05 passed five normal workspace steps: blank
  Workflows entry, add text input, save, reload the same workflow, and inspect the
  configured model. No browser diagnostics or process/review/dispatch actions.
  The configured inference endpoint is a deliberately unavailable fixture;
  model discovery is verified, actual inference is not. Local walkthrough:
  `.local-run/dev-delivery/packaged-ui-walkthrough-05/report.html`.
- User-approved scanner exceptions match only the exact rule, path, field and
  public value. All 47 positives and 124 negative detections passed; eight
  configuration tests and affected Ruff checks passed. See the
  [approval and classification](scanner-findings-proposal-090.md).

## Deferred browser failures and CI

The full browser diagnostic was deliberately stopped at test 61 of 183 after
the user approved the deferral. Fourteen failures had been reported, affecting
engineering-template entry (2), live MCP directory preview (1), common process
view (4), declared interactions (3), input inspector (2), and review actions (2).
They are unresolved; this checkpoint is not fully qualified. The template tests
expect the old `?workflow=canonical` entry URL. The broader failure set has not
been classified as product defects versus stale fixtures/contracts. Preserve
the original local log `.local-run/dev-delivery/remaining-browser-phase-01.log`.
Collect the full CI result and resolve failures together in follow-up work.

Before publication, record the terminal history scan. After creating the PR,
record its URL, commit and the approved pre-CI merge status. Track eventual CI
and deployment outcomes separately; do not call skipped/failed checks passed.

## Remaining engineering goal

The full goal remains active and incomplete. Native 130 mm dock deliverables,
the editor port-type finding, reviewed swim-lane integration and final fresh
engineering journeys are follow-up work. The existing 130 mm intent review is
not answered or resumed. Requirements and exact-output verification stay intact.
Documentation and examples may be polished later; PPT work remains deferred.
