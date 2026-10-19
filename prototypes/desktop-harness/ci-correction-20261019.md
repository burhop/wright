# Desktop integration CI correction — 19 October 2026

The first updated PR #159 candidate (`7e603294`) passed the Linux and Windows
frontend checks, the complete browser report (179 passed, five skipped, no
unexpected/flaky outcomes), package/platform checks and native lifecycle proofs.
All first-cycle checks are now terminal: 26 passed, three failed and one
intentional deployment skip. Windows backend tests passed too. GitHub's Actions
incident delayed status publication. No job was restarted because observation lagged.

Three failures were collected before the consolidated correction:

- CodeQL classified the public `remote_oauth_flow` discriminator as a password.
  Exact SARIF flows start at that parameter/default/CLI attribute, never at a
  credential or token owner. The internal name is now `remote_signin_mode`;
  the existing CLI flag, serialized key, two supported values, validation and
  authentication route stay the same. The synthetic delivery fixture uses
  `hmac.compare_digest` for its exact canary. No CodeQL rule/alert is suppressed.
- Gitleaks matched two `credential_sha256` receipt values. Both were independently
  recomputed from this workstream's isolated loopback HTTPS fixture canaries.
  `.gitleaksignore` identifies only the two exact introducing commit/path/rule/line
  findings. The current receipt calls those values `fixture_value_digest`.
  Actual pinned-scanner probes found zero matches in the current receipt and
  still detected both original fields plus a neighboring API key in a new commit.
  Existing scanner rules and other evidence allowances are unchanged.
- Trivy exited before producing a usable vulnerability report. The published
  projection provides no exact cause, so that failure remains unclassified rather
  than a clean inventory or a claimed transient error. Command failures now expose
  only a finite reported category; raw details stay local. No retry, database
  validity extension, severity change or security-policy waiver was added.

The normal merge gate now collects the existing desktop-owner suite as its own
pytest root and runs the existing pinned history scan. The fast gate selects
those owners/history for prototype changes and history for fingerprint changes;
existing allowlist contract selection is unchanged. A broader helper experiment
exposed unrelated unpublished historical fixtures and was not selected. Its old
rules, assertions, source and evidence remain unchanged.

The normal updated gates and complete current-head CI must pass before integration.
The installed plugin remains 0.15.0. The 0.16 native resource remains byte-identical;
its final runtime/profile and exact merged-dev served journey still need recording
before the named update and Windows/personal sign-in acceptance.

Evidence is retained under `/tmp/wright-desktop-resume-evidence-20261019/`:
`codeql-7e603294.sarif.json`, `ci-gitleaks-fixture-hash-classification.json`,
`desktop-exact-fingerprint-contract.json`, `ci-7e603294-browser-artifact-result.json`,
the original job logs, and actual-source correction checks. These receipts describe
observed boundaries; they do not grant workflow review or external-action authority.

Actual-source correction checks passed: 300 desktop-owner tests and 110 targeted
gate/scanner/setup tests (including all 66 image-scanner unit cases). The one
fixture formatter correction changes only whitespace. These affected checks do
not replace the updated full/push gates or the next current-head CI cycle.

The first expanded local history gate found a fixture in an unrelated local
branch, not an ancestor of this candidate. Its full failed receipt is retained.
Both history-clone implementations now retain only the candidate branch and omit
unrelated tags. A real Git regression first failed for both implementations, then
proved that all candidate and merged ancestors remain while the sibling branch/tag
is excluded. No exception was added for that finding, and the other worktree was
not changed. History-runner impact selection now runs this regression/history;
existing allowlist-rule contracts remain selected for changes to their subjects.

The scope reproduction and gate results are retained as
`history-scope-failure-bc9584aa.json`, `history-scope-before-fix.log`,
`history-scope-after-fix-v2.log`, and `normal-full-gate-bc9584aa-receipt.json`
in the same evidence directory. The failed gate remains failed; its image scan
passed, while its temporary history clone included the unrelated branch.
