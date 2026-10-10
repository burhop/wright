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
