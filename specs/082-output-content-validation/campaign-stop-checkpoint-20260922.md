# Campaign stopped for process redesign — 22 September 2026

## Controlling user direction

The user requested a good stopping point, cleanup, commit and GitHub push before
changing the process. This supersedes autonomous campaign continuation. **Do not
launch more examples, provider probes, corrections or engineering reviews until
the user gives new direction.** Finish verification and publication of this
checkpoint only. This is not achievement of the 30/30/30/30 goal.

## Implemented versus unfinished

- The runtime output validator, full-scope profiles, evidence/currentness rules,
  bounded corrections, engineer-facing results work and approved R1 example
  alignment are committed implementation, not proof that all examples complete.
- The deployed API is at `c1e9977e` (PID 49572 at the last ownership check), with
  MCP autostart disabled. The review-settings identity fix was actually exercised:
  the user's rejection of Heat 901 was recorded through the normal endpoint.
  Later preparer changes do not require an API restart. This cleanup does not
  redeploy or merge anything.
- Heat's case-specific prompt repair and explicit pinned numerical criteria are
  implemented and tested. Heat 902 still contains the mesh-limit contradiction;
  its pending review was not approved or rejected on the user's behalf. No 903
  was staged. The episode retains one used correction out of two.
- Harness native planning now preserves actual connectors and splices. Actual
  Gateway/KiCad correspondence passed for cases 01 and 02. Case 03 fails at the
  tool's rejection of `S_ZX`; no alias workaround is left half-implemented.
  See the [portable native evidence](../../artifacts/campaign-example-renewal/qualification/harness-native-20260922/README.md).
- Modelica's confined native export, composite result identity, case-specific
  water instructions and CAD source-publication fixes have retained focused
  repair evidence. They do not establish full renewed workflow qualification.

## Exact resumable boundary

| Item | State that must be preserved |
| --- | --- |
| Heat 902 | Run `a01fefe4badd4e6bb7418d4704f75a65`, checkpoint `checkpoint-875a69002c5f61ec041f3b25`, awaiting actual review; basis digest `78e2c8d1e5fe8e5e9578c0501899a6656193dee621779f15f3476c72c69463e2` |
| Printed 901 | Run `8877a99cc7054faab6b4d586b05845cb`, checkpoint `checkpoint-e4ec7f837b7f20acbc7f91df`, pending review; no inferred decision |
| Historical Robot 010 | Run `1e10a25958694ce2ab4d9454029b1fcf`, checkpoint `checkpoint-46ef3ff2d5107b0b5f55455e`, protected pending human review |
| Engineering assumptions | Water material densities and harness contact/splice resistance proposals prepared for review, not adopted |
| Retry history | Preserve terminal attempts, exhausted quarantines and the durable episode ledger; changing attempt IDs does not reset budgets |
| Solid Edge | All three examples remain in scope but deferred; do not touch its server or deployment |

Pause sentinels are recorded under the existing campaign runner state and Heat
902 observer state. The one-case Heat observer exited normally at 21:47:28 UTC,
preserving `awaiting_manual_approval`, no validations and no active POST. Its
read-only observation deadline is not a workflow failure and does not authorize
replay. Dashboards and the Wright API remain available for inspection.

The recorded counts remain historical/displayed **30/30/24/17**, with current
revision one run, zero complete packages and zero full passes. There were **11
isolated canonical qualification dispatches and zero broad waves**. Native
provider proofs, source changes and unit-test totals are not campaign credit.
R3 remains incomplete; R4/all-family campaign readiness has not passed.

## Cleanup and verification

The last harness-focused suite passed **61 tests**; Ruff passed. Repository-wide
Python lint and the 846-file formatting check pass after mechanical cleanup.
The initial dev-push gate passed the runtime dependency vulnerability audit,
then correctly stopped because an exact-candidate Docker image was missing.
Final gate and GitHub publication results will be recorded separately; neither
is implied by this initial checkpoint.

All source, tests, design decisions and curated proof files belong in Git.
Several gigabytes of generated campaign exports, diagnostics, live state,
package caches and test scratch remain on disk and are ignored, not deleted.
Native input/receipt hashes are preserved byte-for-byte in the portable bundle.
Historical evidence remains historical. No engineering limit, review authority,
case denominator or campaign metric is relaxed to make this checkpoint green.

The next process discussion should start from these completed boundaries and
explicit gaps, rather than resume the old goal automatically.

### Publication verification follow-up

Implementation checkpoint `403adca2` and the separately approved product-direction
documents `bcace4ea` are saved. The observer exit was confirmed, and the normal
API still reports the exact Heat 902 review pending with actor null. The expanded
harness/review/preparer regression suite passed 76 tests.

The clean-archive image built successfully, including TypeScript and the
production frontend. Its exact-image scan passed with zero policy findings using
the current 22 September vulnerability database. The cumulative gate then stopped
at its early occupied-port guard (18000); no unrelated listener was terminated.
Use freshly checked isolated ports for the continuation of publication checks.

Prettier found 12 frontend files needing mechanical formatting. Each resulting
file was independently checked against the formatter output of its committed
predecessor; no UI behavior change is intended. Python syntax-tree comparison
likewise confirmed the formatting-only source/test changes.

The first full-history Gitleaks scan found 15 matches. Classification identified
the exact `JIG03-KEEPOUTS` requirement label, five document-version CAS hashes in
two historical evidence representations, a reviewed browser-hook source hash,
and a byte-identical second commit of the previously classified disposable test
environment. Exact path/rule/key/value allowances preserve detection elsewhere;
the historical environment allowance is limited to the two exact commits.
Actual scanner regression: 24 integrity-value occurrences and one requirement
label accepted; 18 neighboring credential findings detected across 13 negative
contexts. Seven security-configuration tests pass. This does not itself claim
a clean rerun of the complete history or a completed cumulative gate.

The subsequent full-history Gitleaks scan passed across 1,534 commits with no
findings. Its invocation explicitly skipped TruffleHog; no TruffleHog result is
claimed. The rebuilt candidate at `fa9f1da8` also passed the exact-image policy
with no findings: image
`sha256:d649fec5efd79138b85c5c4f6723b357392db9d9eb48e9ad878dae27ed2de387`.
The image built from a clean Git archive. Public scan evidence is retained locally
under `test-results/docker-image-security/20260922T220808Z-1e43ef6f/public/`.
Focused frontend verification passed 68 tests in five files, TypeScript, and
Prettier; ESLint reported no errors and ten existing warnings.

The cumulative gate identified one additional native-build-script formatting
issue. The corrected script has an identical Python syntax tree. A full-branch
whitespace review also cleaned three older documentation/test files.

The retained structured correction proof exposed historical Git line-ending
conversion: its three top-level JSON files were originally recorded with CRLF,
while the workflow and nested evidence used LF. Recovery changed only newline
bytes, preserving the original manifest unchanged. All 11 staged evidence blobs
now match its original byte counts and SHA-256 hashes; both independent retained
proof tests pass. Pre-recovery local copies were preserved under
`.local-run/stop-checkpoint-20260922/evidence-before-eol-recovery/`. Existing
byte-preserving Git attributes protect the corrected evidence on future checkouts.
This repairs portability of historical proof; it does not create a new run or
campaign pass. Full cumulative and fast-push gates remain pending at this point.
