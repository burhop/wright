# Engineering-first workflow inspection

The working surface is for an engineer evaluating a process and its evidence,
not for an operator of Wright's test infrastructure. Present recorded facts and
use the workflow's authored purpose. Do not invent an engineering interpretation
of a filename, a successful tool call, or an opaque result payload.

## Questions each surface answers

| Surface | Engineer's question | Information and action |
| --- | --- | --- |
| Input block | What information am I supplying? | Authored purpose; full selected path; hover path; open the exact file in a workspace tab. Selection and inspection are separate actions. |
| Task block | What does this do and what does it use? | Purpose; upstream block names; declared outputs separately from files actually produced in the recorded run. |
| Result block | What did I get, and where can I see it? | Teal read-only RESULT card connected to its producer; recorded availability separately from review state; plot preview and direct workspace-tab opening. |
| Connection | What passes along this line? | Named source and destination; information carried for data connections; sequencing, review, or revision meaning for the other connection types. A connection is not evidence of execution. |
| Run details | Where did we get to, and what needs me? | Recorded status; pending decision or stopping reason; step progress; results and direct file access. An expandable reading area preserves access to the diagram. |
| Review | What must I check before accepting this result? | Recorded review files, exact requirement text, decision scope, review note, approve/request-changes actions. |
| Technical record | Which exact version or service was involved? | Optional, initially closed identifiers, source references, file fingerprints, settings, and execution telemetry. |

## Evidence and authority rules

- A finished step is not an engineering pass. Produced files are not necessarily
  reviewed, validated, released, or safe to act upon.
- A pending local review is “Awaiting your review,” never “Completed.” Approved,
  stale, expired, changes-requested, and already-used reviews remain distinct.
- Evidence links come from the recorded review package and its file fingerprints,
  not output filenames configured for a future step. The workspace viewer opens
  the current file at that path; the UI does not claim it is an immutable preview.
  Existing server-side version checks remain the authority at decision time.
- Requirement wording and its source record are retained exactly. Repository
  source references are not represented as clickable workspace files.
- Incomplete requirement records still disable approval. Feedback is required
  for a changes request. Existing authenticated decision requests are unchanged.
- A managed review records the decision without exposing an independent manual
  continuation control. No UI inspection automatically approves or resumes work.
- Results from another source revision or an edited draft are not attached to
  the currently selected block. They remain inspectable in the recorded run.
- External-action destinations, proposed actions, and settings stay visible as
  labelled information. Their exact authorization record remains available.

## Deliberate limits of this iteration

Robot 008's saved definition, authored block descriptions, evidence, and decision
are not rewritten. Some authored names therefore still reflect its test origin.
The generic UI does not translate unknown engineering quantities or claim a
numerical check passed by parsing arbitrary prose or JSON.

The next artifact-presentation layer should consume explicit result contracts:
quantity, value, unit, tolerance, frame/time range, method, uncertainty, acceptance
status, and evidence reference. That enables trustworthy measurement tables and
plots. Missing fields should say “not provided,” not be guessed. Large input
libraries also warrant a searchable picker; the current selector is retained
with a separate readable selection and Open file action.

## Verification

Use the normal workspace Workflows control and Robot 008 at 944 × 791. Inspect
an input, open the report and plot in workspace tabs, expand Run details, inspect
step progress and a connection, and reveal the optional technical record. Compare
the recorded source, review, and artifact identities before and after. Do not
submit a live approval or continue the attempt during this UI walkthrough.

The repository walkthrough saves raw and annotated screens, browser diagnostics,
an execution trace, an HTML report, and unchanged-run evidence. Failed runs are
retained separately. Browser verification is not user acceptance.

## First-class result blocks (2026-09-21)

Results are derived visual objects, not executable tasks or changes to the
canonical workflow. They are not written into the source or layout and cannot be
connected, deleted, or dragged as authoring objects. Dashed teal lines associate
each result group with its producing step. Inputs have blue accents and an inward
arrow; results have a teal rounded card, outward arrow, and explicit RESULT label.
The distinction does not depend on color alone.

Group files by the recorded producer. Prefer plots, documents and models over
supporting technical files. Keep related evidence together instead of making a
block for each log. The Results navigator beside Inputs selects and reveals the
same cards; it complements rather than replaces the diagram. The result viewer
puts the selected file, Open in tab, and verified image preview first. File
locations and the producer explanation are available on demand.

Expected paths come from authored saved-output and expected-file settings. They
remain disabled placeholders until the same run actually records those paths.
No filesystem scan, filename substitution, or directory guessing grants
availability. Review membership requires the recorded path and digest to match
the checkpoint; availability is never presented as a check passing. Image bytes
are checked before rendering; an opened workspace tab displays the current file.
When the workflow has changed, saved-run results are explicitly labelled and
detached from current step connections.

Robot 009 exposes five groups: plots/supporting data, diagnosis, the expected
evidence index, and two groups of supporting files. Four groups contain produced
files; the evidence index has not been produced. This UI does not repair the
separate named-output runtime handoff defect or supply engineering approval.
