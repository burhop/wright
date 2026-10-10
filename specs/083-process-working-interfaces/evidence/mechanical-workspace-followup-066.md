# Workspace usability follow-up, 10 October 2026 (066–067)

This extends the [full-goal audit](mechanical-completion-audit-065.md).
It does not close the goal or replace engineering acceptance. The preceding
goal turn made progress through the 064/065 artifacts and reconciliation;
this turn reproduced and repaired a shared settings defect and completed
additional current-state checks.

## Ordinary workspace journey

An engineer opens the saved wheel workflow, inspects Workspace Settings and Git
Version Control, reopens its recorded working view, chooses **Prepare another
run**, and returns to the previous exact result. No workflow source, settings,
Git repository or engineering run is changed by this browser journey.

- [Initial retained attempt, 166](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-166-workspace-shell/report.html):
  settings/Git/result entry worked. The recorder stopped after preparing another
  case because it expected a heading named `Prepare`; the actual heading is
  `Inputs`. This was a recorder error. The failed pre-run selector edit is also
  retained; it did not change the executed script.
- [Production continuation, 167](../../../artifacts/ui-walkthrough/mechanical-engineering/20261010-167-workspace-shell-current/report.html):
  seven steps pass, empty console/page/HTTP error diagnostics, no recorded
  engineering/configuration/Git action requests. Both report structures validate.
- Actual settings return HTTP 200. The workspace repository reports branch
  `master` and 2,559 changes; refresh succeeds. These are the isolated workspace's
  Git facts, not the Wright source repository's branch or change count.
- New-case preparation clears the selected run and exposes its inputs.
  Reopening the original run restores its exact sliced package and review hold.
  Neither opening preparation nor passive reopening submits Start.

The browser tests loading, refresh and navigation. It does not commit, switch
branches, push, pull, save credentials or claim those external effects succeeded.
Providers are stopped; readiness of a newly submitted run was not tested here.

## Reproduced settings defect and repair

The database default and API value are **10,485,760 bytes**, but the form previously
displayed that integer under an MB label, with a maximum of 100. Besides showing
the wrong units, this made the default form invalid to submit. Older UI fixtures
incorrectly used values of `10` and `25` directly in the byte field.

The existing WorkspacePanel now converts bytes to **MiB** when loading and
converts the edited value back to integer bytes when saving. It preserves
fractional MiB and small stored byte values, keeps blank input editable, rejects
nonpositive/invalid submission, and associates the label with its field.
There is no inferred migration of old values: a stored `10` remains ten bytes.
The API's field description and service parameter document the existing byte
contract. No API behavior, execution policy or instruction asset changes.

Five focused tests failed on the original UI. The final workspace session and
Git component suites pass **46 tests**, including load/save round trips for
10 MiB, 25.5 MiB, one byte and the null default, plus edited fractional values
and rejection of empty input. Two intermediate test attempts are retained; the
final test refers to the reloaded form and matches the error's warning prefix.
The existing mocked navigation fixture now uses actual byte values; that wider
Playwright suite was not run in this turn.

Type checking and production build 33 pass. Only the owned UI preview was
replaced; the API remained running. Current settings, Git and preparation
screens were visually inspected. Save conversion is covered by component tests;
the live browser journey deliberately did not submit a settings save.

## Preserved evidence and saved interface

`workspace-shell-audit-066.json` independently checks all **52** run records,
**198** earlier wheel files, **64** latest wheel files and the accepted source.
All hashes and the run-file set remain unchanged. It records build identity,
test/source hashes, screenshots, observations and limits.

The separate read-only `imported-ui-source-audit-current-067.json` reconciles
the retained authoring request, imported candidate, actual response, local save
and database records. Its saved interface has 22 bindings and still matches
the accepted source. Interaction schema `wright.process-interaction/1`, UI schema
`wright.process-ui/1`, client 1.0.0 and kit 1.0.0 match their current declared
versions. Earlier 41 recorded runs remain unchanged. This establishes retained
identity/provenance; it does not claim a new UI generation, fresh browser reuse
test or behavioral compatibility from version numbers alone. Earlier actual
saved reuse/fallback walkthroughs remain separately cited in audit 065.

## Remaining issues made visible by this check

1. **Preparation is too verbose.** The new-case screen shows many saved input
   files individually, including duplicate concept-image references and provider
   configuration. Required-input resolution must remain with the backend, but
   the common form should distinguish inputs needing an answer from inspectable
   saved defaults. Do not drop dependencies or change the accepted workflow to
   simplify the screen. Functional new-case/reopen evidence does not close this
   ergonomics requirement. Use screenshot `06-prepare-after.png` in 167 as the
   before state for a shared presentation repair.
2. **The large-file threshold's consumer is not established.** Code inventory
   found the settings field, byte storage and API, but no current warning consumer.
   The unit correction does not prove that large files generate warnings.
   Reconcile this exposed setting with its actual Git/file-list owner before
   claiming the complete warning feature works.
3. **Required goal deliverables remain open:** dock engineering decision and
   native outputs, actual existing swim-lane ownership/integration, final
   presentation/handoff and remaining qualification/evidence audits in 065.

The next independent implementation work is the shared preparation form. The
dock and swim-lane decisions remain pending separately; no synthetic review
response can supply their missing authority.
