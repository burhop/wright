# Record engineering reviews with providers closed (071)

10 October 2026. Follow-up to the measured-correction walkthrough in
[070](mechanical-correction-followup-070.md). This advances M3 status/reviews and
M4 regression coverage. The complete mechanical-engineering goal remains open.

## User journey and reproduced defect

An engineer reads the completed drawing, measurements and assessment, then
records a decision on that exact evidence. The application that produced the
files may already be closed. Recording a decision does not start that application
or continue the process.

Walkthrough 170 exposed disabled Approve and Request changes controls because the
completed CAD step's server had no available tools. Five fresh isolated tests
reproduced the same coupling through the real approval service: whole-workflow
execution preflight ran before decision recording and even obscured a changed
artifact diagnostic. These tests use a controlled gateway and synthetic documents;
they are software authority tests, not live engineering qualification.

## Shared correction and preserved boundaries

- The existing source preparer has a review-only mode. It still reads the exact
  source, compiles its declarations/instructions, loads pinned validation criteria,
  resolves confined paths and checks the saved input snapshot. Its returned plan
  is explicitly inert; the executor rejects it.
- Review preparation reads recorded provider choices and routing identities.
  It does not refresh a choice catalog, reopen a CAD document, contact an image
  or model provider, or require an inspection reader to remain installed.
- The existing approval owner recomputes the exact action/settings/input identity
  and rehashes all reviewed input/artifact files. Its canonical lease, checkpoint,
  scoped actor, request identity and decision persistence remain authoritative.
- Locally enrolled test decisions retain source/dataset/output confinement,
  declared tool identities, grant expiry/revocation and exact-subject attribution.
  Missing capabilities do not create automatic review authority.
- Continue process still uses full execution preparation: live tools/schemas,
  validation readers, option freshness, CAD/application capabilities, frozen model
  revalidation, one-shot dispatch and uncertain-outcome handling remain required.
- Common and saved working interfaces consume these backend-permitted actions
  through the existing contract. No new endpoint, client authority, UI schema,
  vendor integration or process executor is introduced. Existing UI compatibility
  and common-view fallback remain unchanged.

Source, requirement, input and artifact changes still invalidate a review.
Provider disconnection affects execution readiness without changing the bytes
an engineer is reviewing. A recorded approval is not provider acceptance,
manufacturing release or evidence of a physical outcome.

## Verification status

306 affected tests pass, including 20 new cases. Controlled negative and recovery
cases include changed/deleted files and source, stale subjects, expired or revoked
grants, missing automatic authority, idempotent decisions, saved choices, model
replacement on continuation, an inert preparation rejected by the executor,
the actual scoped process interaction contract, and same-run continuation without
repeating the completed producer. The two warnings are existing test-library
deprecations.

[Walkthrough 171](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-171-review-offline/report.html)
passes five steps on production UI build 34 with the reloaded API on 8067:
open the retained correction review; inspect the decision controls and temporary
reason field; read the failed assessment; open the regenerated drawing; reload
the same unanswered run. Approve is enabled with CAD closed. Request changes is
enabled only after a reason is entered; the temporary text was cleared and no
decision was submitted. Continue process remains disabled before approval.
The actual scoped-service fixture separately proves that an approved decision
still cannot continue while its provider is unavailable.

Browser diagnostics and review/execution requests are empty. Screenshots were
visually inspected, and the walkthrough structure validates. A read-only audit
confirms all 52 run-record hashes and 28 reviewed source/artifact copies still
match, and the exact checkpoint remains pending with no actor or external action.
FreeCAD and Blender are closed. API PID 84296 and UI PID 27764 are live; this was
an API reload only, without a frontend rebuild or changed UI contract. The audit
receipt is `review-availability-audit-071.json` in the private control root.

The initial sandbox test attempt could not create its temporary directory. A
second sandbox attempt was interrupted without a result. The reproduction then
ran in the authorized isolated C: test area. New test-fixture mistakes (tuple
return handling, JSON filename and unbound input port) were corrected without
changing product acceptance criteria; the earlier reports remain preserved.

Private receipts are in the increment's control root under
`tests/review-offline-*-071.xml`; the final combined receipt is
`tests/review-offline-regression-071.xml`. Pre-edit copies of the five existing
production files retain the inherited dirty work.

No protected review has been answered or resumed. The saved wheel and thermal
engineering runs remain distinct from these software fixtures. Final acceptance
still needs the other open audit items, accepted dock resolution, actual existing
swim-lane integration and the final engineer-readable presentation/handoff.
The earlier wheel/thermal end-to-end journeys remain valid historical evidence;
M4's two fresh different engineering journeys must be repeated after the final
implementation fix, including this later shared change.
