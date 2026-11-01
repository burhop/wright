# Codex UI preservation checkpoint — 28 October 2026

Start the next design discussion with the
[engineering-experience plan](../../../../docs/design/codex-engineering-experience-plan.md).
This checkpoint preserves the first attempt. It is not a completed UI, an accepted
engineering journey, a release, or authorization to resume engineering work.

## What is preserved

The feature branch is `codex/desktop-usability-journeys`. Before this checkpoint,
its tip was `5b7c065ef1fbce1e23609a16d9dc0a19d28559b3`; the fetched `origin/dev`
was `1514ea25a63e8e330f86dcac3ccf05f73bc0403b`. The branch retains the source,
tests, generated panel, prior implementation commits and dated evidence notes.
The separate Feature 084 checkout and other worktrees are outside this cleanup.

[checkpoint.json](checkpoint.json) records exact installed/candidate resources,
retained-output identities and the limits of the observations. The two screenshots
here are **simulated desktop-host tests**, not Windows captures:

- [Narrow image preview](simulated-image-480.png)
- [Visible host download refusal](simulated-download-declined.png)

Private evidence, the user's screenshots, runtime state and frozen source copies
are preserved locally under
`/home/burhop/repos/wright/.local-run/codex-ui-preservation-20261028/`.
Its manifest and checksums describe the copies. Credentials, private configuration,
raw state and conversation screenshots are deliberately not GitHub artifacts.
Local preservation is not an off-machine backup of that private data.

## Actual state and unfinished work

| Item | Status and evidence boundary |
|---|---|
| Installed prototype | **0.33.0**, source `290f8c12969783ce7dcd3046a0a0f3c4253921df`; unchanged by this checkpoint |
| Actual Windows image | **PASS**: user screenshot shows retained block PNG in the native panel |
| Actual Windows download in 0.33 | **FAIL**: user reports no visible response |
| Download correction | **Locally verified, uninstalled 0.34 candidate**; public host-mediated SDK path, exact bytes, visible failure, no automatic retry |
| Download correction tests | **PASS**: 136 focused checks; subsequent browser-compatible CSV fixture fix passes 15 affected tests and TypeScript |
| Real retained run through simulated host | **PASS**: image visibility, producer navigation, Results 1/1, matching source, same-run return, narrow layout and reopen |
| Candidate packaging | **Incomplete**: first verifier accidentally changed a digest during broad version substitution; backend rejected it. Corrected script retained, successful protocol requalification still pending |
| Candidate Windows delivery/open | **UNVERIFIED**; a simulated acknowledgement is not saved-file evidence |
| Actual chat-switch restoration | **UNVERIFIED** |
| End-to-end new design, reviews and full rerun | **NOT ESTABLISHED** by the retained-model inspection journey |
| Usability | **NOT ACCEPTED**: navigation, unnecessary controls/text, raw JSON, repeated filenames, results and return paths remain the plan's priorities |

The existing backend remains the frozen 0.30 source at
`/tmp/wright-desktop-native030-source-20261028`, with state at
`/tmp/wright-engineering-run-journey-state-20261028`. This checkpoint does not
restart it, change credentials or install 0.34. Do not assume the editable source,
installed plugin, backend source and already-open panel all have one version.

## Evidence index

- [Engineering run and limitations](../../engineering-run-journey-20261028.md)
- [Bitmap correction and actual Windows confirmation](../../bitmap-preview-20261028.md)
- [Download correction and protocol boundary](../../host-download-20261028.md)
- [Native file-tab investigation](../../native-document-tabs-proof.md)
- [UI observation limits](../../panel-observation-20261028.md)
- [Earlier usability qualification](../../usability-qualification-20261025.md)
- Raw local checks: `.local-run/engineering-run-journey-20261028/host-download/`,
  including `local-checks.json`, `preflight-findings.json`,
  `candidate-034-final/report.json` and `host-download-evidence.json`.

The recorded 136 tests precede the final test-only raw CSV import correction.
That correction replaces Node-only imports in a browser TypeScript test, with no
runtime or dependency change. The exact-image candidate contains the unchanged
runtime code. Four existing UI-kit React lint findings are recorded in the earlier
focused baseline comparison; that comparison is not a full repository gate pass.

## Repository qualification

This is a preservation push to a feature branch without a pull request. No
full-gate, CI, merge or release pass is implied. Before proposing integration,
run the normal dev-push gate and cumulative full merge-gate bootstrap required
by the runbook; this checkpoint does not establish a green incremental baseline.

The checkpoint's focused checks pass: 145 tests across the shared preview and
native download/preview/observation suites, app TypeScript, native-panel ESLint,
formatting of all corrected files, and strict MkDocs. Initial formatting and
three documentation-link findings were corrected without changing runtime
behavior. The browser test's raw fixture import is the only non-format source
correction in this checkpoint. The public-alpha current-file leak scan passes;
the final history-scan receipt and push identity are retained in the private
preservation directory. Local check logs are under
`.local-run/preservation-checkpoint-20261028/`.
