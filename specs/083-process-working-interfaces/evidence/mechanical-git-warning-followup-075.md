# Workspace large-file warning, 10 October 2026

## Reproduced user problem

The earlier settings repair established byte/MiB conversion, but the Git panel
did not consume that setting. An engineer could configure a warning threshold
and receive no warning for large CAD, analysis or run files among their changes.
The existing Git use case already supplies `file_size`; no additional file
reader, backend policy or Git operation was needed.

In the isolated workspace, the actual saved threshold is 10 MiB and three
changed files exceed it. The [before walkthrough](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-182-git-warning-before/report.html)
stops at the missing warning. Its settings/status responses and original screen
are retained. Five newly added component cases also fail on the original panel.

## Repair and ownership

The existing `WorkspaceGitPanel` now reads the threshold alongside its normal
configuration refresh, counts changed files whose known size exceeds it, and
shows an advisory summary plus the size beside each affected file. It uses the
same 10 MiB null default as Workspace Settings, supports small byte thresholds,
and refreshes/clears the warning with settings and workspace changes.

The client type now admits the API's existing nullable size. Equal/smaller,
unknown and deleted-file sizes do not generate false oversized warnings. The
warning grants or removes no Git authority and does not disable commit. No
workflow runtime, prompt, validation, artifact identity or UI binding changed.
This is a shared workspace feature, independent of the engineering provider.

## Verification

- 54 tests pass: ten Git-panel cases, 42 workspace session/settings cases and
  two passive workflow-entry cases. The six new warning cases cover configured
  bytes, null default, size boundaries/unknown/deleted files, one-byte threshold,
  refresh and workspace switching. Existing explicit-action tests remain intact.
- Type checking and production build 35 pass. Only the goal-owned preview was
  replaced; API 8067/PID 84296 remained running. UI 5250/PID 35028 serves the new
  build. The served index and all three entry assets match its exact files.
- The [repaired walkthrough](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-183-git-warning-repaired/report.html)
  passes five steps: saved workflow entry, settings inspection, warning summary,
  exact file labels, and refresh. Both walkthrough report structures validate.
  Browser console/page/HTTP diagnostics are empty; summary and file-label
  screenshots were visually inspected.
- The three files are existing run records of 25.53, 24.22 and 29.55 MiB. They
  were read, not rewritten. No configuration save, Git mutation, review,
  continuation or new workflow execution was submitted.
- All **54** existing run records and **64** latest wheel outputs remain
  byte-identical; the accepted wheel source is unchanged.

Private receipts are under
`.local-run/process-interfaces-083/mechanical-engineering-20261008/`:
`git-warning-audit-075.json`, `ui-build-35.json`, and
`tests/git-warning-{reproduction,workspace}-075.xml`.
The initial restricted test run failed in temporary-cache setup before executing
cases. Its separate receipt is preserved; the actual host reproduction and
passing regression results are distinguished. An initial post-fix command
matched only the Git suite; the final receipt explicitly includes all three
intended suites rather than claiming an unexecuted test file.

## Completion scope

This closes the observed missing threshold consumer from follow-up 066 and
narrows M3.5's ordinary workspace gap. It does not test external Git operations,
unknown file sizes, every repository shape or physical engineering behavior.
Prior post-071 engineering runs remain their recorded scope; the full goal's
final regression gate is still separate from this UI-only proof.

The sheet-metal requirement decision/native outputs, actual existing swim-lane
capability, remaining engineering/coverage audit and final primary-job deck are
still required. No reduced objective or manufacturing acceptance is claimed.
