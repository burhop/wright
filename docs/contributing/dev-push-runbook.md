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

The fast gate selects Python, frontend/browser, and documentation checks from
the changes since the branch's last pushed tip, plus staged, unstaged, and
untracked files. A new branch falls back to `origin/dev`; the full merge gate
validates the whole pull-request diff. Gate or workflow changes run all slices.
It uses dedicated browser-test ports, so the normal Wright UI on
5173 and API on 8000 can remain running. Python checks use the cached,
Git-ignored `.venv-dev-gate` environment instead of modifying the environment
used by a running Wright process.
The fast browser slice is a Chromium smoke; the full merge gate retains
cross-browser coverage.

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
