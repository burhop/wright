# Development delivery checkpoint — 10 October 2026

## Authority and stopping point

The user authorized committing current work, pushing it to GitHub and following
the PR/check process into `dev`. They also requested current README/documentation
and screenshots where useful. No direct dev push or production release is planned.
The latest dock run remains at declared intent review; no new engineering decision
is made to deliver software. The full mechanical goal remains incomplete.

## User-visible scope

- Build and inspect workflows in the established editor; carry out the same process
  in common or saved tailored working views using shared backend authority.
- Save portable instructions and explicit assumption policy; declare input questions
  and engineering reviews as separate durable interactions.
- Inspect actual model/image/document/numerical outputs, exact validation evidence,
  previous attempts, progress and actionable failure diagnostics.
- Reopen a current-source recorded run from history, including when its diagram
  cannot be drawn, without starting or approving it.
- Update ordinary workspace navigation, provider selection, settings and Git controls.

This is the accumulated Feature 083 source and local verification work. Existing
engineering examples verify product behavior and retain their separate limitations.
Generated bulk traces, private runtime state and presentation archives stay local.
Curated screenshots and evidence descriptions may be committed after inspection.

## Remaining work

1. Complete native deliverables and validation for the separate 130 mm sheet-metal
   study after its explicit review; resolve the source's port-type mismatch in a
   visible new revision. Do not change the waiting run's accepted source silently.
2. Locate/reuse the reviewed swim-lane implementation and prove engineering handoffs.
3. Complete the remaining final fresh engineering journeys after the last shared
   repairs; preserve earlier digital verification and required human holds.
4. Treat Codex-as-agent runtime integration as a separate project. The current
   Codex MCP profile does not implement that replacement.
5. User acceptance, supplier release and physical engineering acceptance remain
   separate. Slide-deck work is deferred.

## Verification and delivery

Completed locally before the candidate commit:

- 89 focused frontend tests across navigation/history, Git controls, recovery,
  provider settings and preview routing; type checking and production build 47.
- Python Ruff checks pass. Frontend ESLint has zero errors and 12 retained hook
  dependency warnings; the required whole suites remain pending.
- Browser235: three served steps pass, exact run and 23 outputs restored after
  reload, no process mutations or browser diagnostics. Report structure validates.
  Earlier browser230–234 stopped evidence remains, including harness mistakes.
- Current README/tour screenshots visually inspected; two immutable capture hashes
  recorded. Historical Rivet documentation is labelled legacy compatibility.
- Explicit staging manifest excludes 1,896 local generated artifacts and the
  unrelated historical Studio-automation note. Staged credential scan is clean.

Full native merge gate, image build/scan, pre-push gate, GitHub CI, PR merge and
exact dev health verification remain pending. No pending check is counted as passed.

Local receipts are under `.local-run/process-interfaces-083/mechanical-engineering-20261008`
and `.local-run/dev-delivery-*`. Failures and corrected reruns are retained.

## Candidate repairs before publication

- `cd836801` records the accumulated source/docs checkpoint; `732946ac` fixes
  the clean Docker build's missing local process-client/UI-kit packages.
- `b550da6f` updates PyJWT to 2.15.1 and urllib3 to 2.8.0. The runtime dependency
  audit then reports no known vulnerabilities. The strict documentation build
  passes after repairing published-site links; repository evidence links now
  target tracked GitHub files and local-only evidence is identified honestly.
- Full gate attempt 01 stopped at the dependency audit. Attempt 02 passed that
  audit and found fixable image dependencies. The clean image built successfully;
  its scan remains blocking until the separate OS/npm/pip/Hermes repairs pass.
- The first whole frontend run recorded 1,782 passes and seven failures. A bounded
  two-worker reproduction passed 237/238 and isolated a stale route assertion.
  The correction preserves all test cases, bounds JSDOM worker contention and
  waits for two actual asynchronous readiness events. The complete rerun is pending.

These are local candidate repairs, not GitHub CI or dev integration evidence.

## Verified candidate d4156470

The complete frontend rerun passes: 198 test files and 1,789 tests. The exact clean
image `sha256:70533e9695cc104a94beb0d9ca9075dd34a76e4e9f3c01aba7478e9a2c57dd21`
built from `d4156470280de860b820753c58a9cc667be5a249` passes the current Trivy policy.
The runtime Python dependency audit reports no known vulnerabilities. Twenty
container security/packaging contracts and ten README/scanner-setup contracts pass.
The final strict docs build passes after the adapter-support/API corrections.

Full merge gate 03 stopped because port 18000 was occupied. Attempt 04 uses
verified free ports 18183/15283. It has passed the audits, Ruff/format, ESLint,
Prettier, TypeScript and the blocking release/control-plane type check, and is
running backend tests. The broad warning-mode MyPy check reports duplicate test
`conftest` modules; it is not reported as a pass.

The history credential scan found 47 public evidence fields: independently checked
file hashes, generated vault filenames and typed idempotency identifiers. Automatic
approval review rejected changing scanner configuration under delivery authority.
The [exact proposed handling](scanner-findings-proposal-090.md) awaits user approval;
no scanner policy has been changed and no push has occurred.

## Packaging follow-up

Gate 04 passed 391 control-plane tests (one skipped), then stopped on two release
contracts. The OS update is now bounded to exact PCRE2/OpenSSL packages rather
than an unrestricted upgrade. The private-package check now respects the existing
external FreeCAD provider submodule's independent publication ownership. All 212
focused release, dependency and container contracts pass after those corrections.

The exact-image smoke exposed Hermes 0.19's strict PyJWT 2.13.0 metadata pin. The
security-fixed 2.15.1 version is recorded alongside the two existing exact security
overrides. Changed versions and unrelated conflicts still fail. An additional
image-level check verifies RSA JWT signing/verification and rejection of invalid
signatures, expired tokens, wrong issuers and wrong audiences. These checks pass;
the new bounded OS package build and complete gate remain pending.

The corrected clean image from `2e3011906820` is
`sha256:d0937408b6add3f54325fed71dedc85af3bfb03e361a75891ba37af3a5fdf19c`.
Its vulnerability scan and offline API/Hermes/JWT smoke pass. Release/native
coverage passes with 323 tests, nine skips and 85.42% coverage. The independent
API suite passes 752 tests with one skip. Gate 05 again passes 391 control-plane
tests and the release suite, then exposes the same independent-provider assumption
in `test_public_python_distribution.py`. Both ownership checks are now corrected
and their four focused tests pass. A complete merge-gate pass is still pending;
the scanner-configuration approval remains pending and no publication has occurred.

## Native source-archive correction

Gate 06 passed the control-plane, release and native suites, coverage and frontend
build, then exposed a real installation defect: the source archive omitted the
shared process-client/UI-kit build inputs. Its direct wheel installed, but rebuilding
the wheel from the source archive failed. npm's local package links could be visited
before the real directories during the archive builder's whole-tree walk.

The source archive now selects the same explicit source roots directly. Its validator
also requires every declared wheel `force-include` source, with negative checks for
similarly named files and paths outside the archive. The retained failing archive is
rejected by this new check. The corrected archive validates, builds its wheel and
installs into a clean environment; both clean installations import successfully.
The direct and rebuilt wheels are byte-identical. All 192 release tests pass, along
with the focused packaging checks. These are local artifacts, not a public release.

The broader core, workspace, agent-adapter, registry and API verification passes.
Two stale storage migration assertions were updated for the already implemented
schema versions 22 and 23; the vault suite then passes 209 tests with one skip.
The native distribution now includes the freshly built current UI and runtime lock.

The corrected source needs a fresh clean candidate image and complete merge-gate
pass. Scanner approval, pre-push validation, GitHub CI and dev integration are still
pending. The 130 mm engineering run remains at its declared human review.
