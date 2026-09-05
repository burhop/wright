# Development Push Runbook

Read this page before every push to a branch with an open pull request targeting
`dev`, and again immediately before making that pull request ready to merge.
Direct pushes to `dev` are not part of the supported development workflow.

## The 60-second pre-push check

1. Confirm the branch contains one reviewable outcome. If unrelated work is
   present, leave it unstaged or move it to another branch.
2. Review `git status --short` and `git diff --check`. Never use a broad
   `git add .` in a dirty worktree.
3. Run the native fast gate:

   ```powershell
   scripts/check-dev-push.ps1
   ```

   ```bash
   scripts/check-dev-push.sh
   ```

4. Do not push when any gate is red. Reproduce and fix the exact failure first.
5. Push one validated change set, then inspect all CI jobs before making another
   change. Do not use CI as a one-error-at-a-time discovery loop.

If a branch predates this runbook, has not had a green cumulative CI run, or
adopts a materially changed gate, run the full merge gate once before relying
on the last-pushed-tip fast baseline. This one-time bootstrap prevents an older
branch failure from hiding outside the latest incremental diff.

## Delivery-speed budget

- Local commits are cheap and may be created whenever they leave a reviewable
  checkpoint. A feature branch normally gets at most **two pushes**: one complete
  candidate and one consolidated correction after every first-cycle CI result is
  terminal and classified.
- Merge to `dev` once per independently useful customer capability. Do not use
  either feature-branch pushes or `dev` integration as an incremental debugger.
- A test-, CI-, or gate-only correction that cannot change shipped behavior runs
  the directly affected deterministic checks and one CI cycle. It does not restart
  a previously completed full local gate unless the correction changes product
  behavior, a public contract, dependency resolution, packaging output, security
  policy, or the merge gate's substantive coverage.
- Scheduler-sensitive microbenchmarks marked `performance` are trend evidence,
  not PR correctness gates. They run in the scheduled/manual performance workflow;
  deterministic functional, security, compatibility, and customer-journey tests
  remain blocking.
- Track pushes per feature, CI cycles, first-push green rate, runner time, local
  gate time, product-versus-infrastructure failures, and customer capabilities
  delivered. Use these measures to remove process cost, never to weaken a red
  customer, security, compatibility, or release signal.

The fast gate selects Python, frontend/browser, and documentation checks from
the changes since the branch's last pushed tip, plus staged, unstaged, and
untracked files. A new branch falls back to `origin/dev`; the full merge gate
validates the whole pull-request diff. Gate or workflow changes run all slices.
When the broad `tests` target and a nested `tests/...` target are both selected,
the fast gate excludes the nested target from the broad invocation and runs it
separately. This preserves suite-local pytest imports while preventing duplicate
collection of same-named test modules.
Container and engineering-image changes also select the Docker bundle, smoke
contract, and workflow-policy tests. Pull-request CI remains authoritative for
the native amd64 and arm64 image builds that cannot be reproduced on every
developer host; both images must build and pass their exact-image smoke tests.

It uses dedicated browser-test ports, so the normal Wright UI on
5173 and API on 8000 can remain running. Python checks use the cached,
Git-ignored `.venv-dev-gate` environment instead of modifying the environment
used by a running Wright process.
The full gate builds the frontend once with the developer's installed lockfile
dependencies, then reuses that fresh output for native packaging. It does not
run `npm ci` against the shared `node_modules`, so an active Wright UI cannot
lock a native Node binding that the merge gate tries to replace.
Before starting its long checks, the full gate verifies that both configured
browser-test ports can actually be bound. A conflict fails immediately with
the environment-variable override instead of surfacing after the test matrix.
The fast browser slice is normally a Chromium smoke. When the changed target is
a `tests/ui-integration/workspace-surfaces/*.spec.ts` contract, the fast gate
runs that selected spec across Chromium, Firefox, WebKit, and the desktop
profile because directory, iframe, and surface interactions are
platform-sensitive. Ordinary application-source fallback remains
Chromium-only; the full merge gate retains cross-browser coverage.

Engineering-process control-plane changes have an explicit focused route. Changes under `docs/programs/engineering-process-platform/**`, `specs/076-control-plane-validator/**`, `scripts/program_control/**`, the `scripts/validate-engineering-process-program.py` entrypoint, or `tests/program_control_plane/**` select `tests/program_control_plane`. Python source and tests also enter Ruff/format/MyPy scope. The full merge gate and Linux/Windows CI run the focused suite before broader test roots so contract failures remain attributable. On either Windows or POSIX, the repeatable focused command is:

```text
uv run --extra runtime python -m pytest -q tests/program_control_plane
```

The corresponding Ruff and format checks cover the entrypoint, package, and focused tests. No gate copies validator semantics; all invoke the same committed implementation and tests.

Before a program-control change can pass the fast push gate, its committed feature
state must be `PUSH_AUTHORIZATION_PENDING`, `PR_READY`, or `DEV_MERGE_READY`, its
mutating lease must be closed, and the authoritative validator must pass against
the exact `HEAD`. This mirrors the non-mutating identity used by GitHub's synthetic
merge checkout and prevents a locally named implementation worktree from hiding a
lease/worktree mismatch that would fail pull-request validation.

EPP-N01 may use the [prospective scoped implementation delivery rule](../programs/engineering-process-platform/coordinator-state-machine.md#prospective-native-implementation-delivery-revision-98-onward).
It passes through these same states and gates with an exact-candidate independent
technical review, a closed lease, and an explicit partition of delivered and
pending tasks. Human usability, actual dev deployment, and final reporting may
remain pending without being counted as passed. This does not waive tests, CI,
independent review, security/compatibility failures, or any required merge gate;
the authoritative validator enforces the scoped record and code freshness.

The full merge gate, Linux quality job, and Windows backend job fetch or retain
full Git history because the program-control tests verify immutable historical
objects. After their focused program-control and native-runtime runs, their broad
`tests` pass excludes those two already-executed roots. The gate-policy regression
and workflow-policy test selected by the fast gate enforce these requirements so
local and CI validation do not silently fall back to duplicate pytest collection
or shallow history. Pull-request runners attach GitHub's synthetic
merge commit to the governed feature branch name locally before validation. This
preserves merge-result coverage while giving branch/worktree-bound leases an
honest checkout identity; it does not update the remote feature branch. Windows
pytest steps also enable native-command fail-fast behavior so an early failing
suite cannot be hidden by a later passing command.

Committed program-status evidence also selects the scanner-configuration and
CI-route regressions in the fast gate. The Gitleaks exception is limited to the
`generic-api-key` rule, the exact three ledger/test/packaged-status paths, and a
matched lowercase, exactly 64-hex `run_key` value; other matches on the same minified
line and other key names or paths remain scannable. When Docker is responsive,
the fast gate runs both a scanner-backed positive/negative allowlist contract
and the pinned Gitleaks history scan. It reports an explicit bounded host skip
otherwise, and GitHub security CI remains authoritative. Application and
package changes select the container smoke contract because they trigger the
OCI PR build. The current Trivy database and exact image scan remain
authoritative in CI when a local Docker host is unavailable.

## Before merge to dev

1. Fetch `origin/dev` and resolve integration drift on the feature branch.
2. Run the full gate from the operating system where the change was developed:

   ```powershell
   scripts/check-dev-merge.ps1
   ```

   ```bash
   scripts/check-dev-merge.sh
   ```

3. A skipped gate requires a written host limitation in the feature quickstart
   or pull request. A real failure cannot be documented away.
4. Make the pull request ready only after the full gate passes and every current
   required GitHub check is green.
5. Merge through the pull request. Do not push directly to `dev`.

## CI failure protocol

- Collect every failed job and its first actionable error before editing.
- Classify the failure as product behavior, test contract, test isolation,
  platform/profile drift, packaging, or infrastructure.
- Reproduce the failing command locally or in the matching clean container.
- Long-running independent analysis may overlap deterministic local
  reproduction, but do not push a replacement commit until every job from the
  previous commit has reached a terminal state.
- After two failed pushes for the same cause, stop pushing. Build a deterministic
  reproducer and make one consolidated correction.
- When CI catches a failure class the local gate missed, update the gate and
  this runbook in the same correction.
- Never rerun a failed job without evidence that the cause is transient.

## Definition of development-ready

A change is not development-ready when the PR merely merges. The exact merged
`dev` commit must build the development image, deploy to the development
environment, pass service health checks, and pass a browser smoke covering the
changed user journey. Record the deployed commit/image digest so failures can
be rolled back without rebuilding.

## Maintainer expectations

- Keep pull requests small enough that one owner can state the user-visible
  acceptance outcome in one sentence.
- Keep frontend unit and Playwright CI independent so both report in one run.
- Keep test browser storage and ports isolated from other tests and developer
  services.
- Keep `scripts/check-dev-push.*`, `scripts/check-dev-merge.*`, and GitHub
  Actions commands aligned. The merge script remains the authoritative full
  gate; the push script is the fast feedback subset.
