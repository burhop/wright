# Preregistered Native Usability Protocol v1

**Frozen protocol date:** 2026-09-04. Recruitment and execution are pending; no participants or results are claimed. Freeze the candidate commit/tree, served asset identity, browser/OS, study fixture digests and dashboard answer sheet before the first measured trial. Changes to this protocol require a dated amendment preserving prior trials.

## Participants and conduct

Recruit five independent engineers who did not implement or design this feature. Record anonymous participant ID, engineering experience and prior Wright/process-editor exposure. A user pilot is useful feedback but separate from the five-participant acceptance cohort. No participant sees answer keys or another participant's trial. Explain the controls only through the product's ordinary help; use the same two-minute unscored orientation for everyone: open the application, show navigation, and explain that the participant may stop at any time. Do not demonstrate a task solution.

Use a fresh workspace and reset definitions/run history for each participant. Tasks run in order H1–H5. Read the exact quoted instructions. Start each timer after instructions are read and the specified start page is visible; stop when the participant declares completion, the limit expires, or the participant stops. Record elapsed time, actions/errors, assistance verbatim, outcome and evidence location. Facilitators may repeat the instruction or handle an unrelated device emergency; any task-solving hint or takeover makes that task unsuccessful. Think-aloud comments are permitted and are not hints.

A started task that fails, times out, encounters a product defect or is abandoned counts as unsuccessful. Never replace its result to improve the score. Withdrawal after any measured task retains completed results and makes remaining tasks incomplete/unsuccessful for acceptance. Replace only a person who withdraws before the first measured task; retain the recruitment record. A demonstrably external interruption can be marked inconclusive only with independently documented reason; repeat the full session, retain both attempts, and state the effective denominator. If it cannot be resolved, acceptance stays inconclusive. Product failures are never external interruptions.

## Frozen tasks and scoring

### H1 — Read exact data flow (four minutes)

Start with saved, never-executed `examples/study-trace.json` open on the canvas. Permit its readable-text view.

Instruction: "Identify the three source inputs and their configured values. Explain which inputs contribute to Full brief and which contribute to Base summary. Show the exact connection that supplies the first input of Add revision. Tell me whether either output has actually been produced."

All answers required: Design need = Design a desk bracket.; Mass constraint = Maximum mass: 200 g.; Revision note = Revision: A. Full brief depends on all three; Base summary depends only on need and mass. The exact connection is base-compose-output-text to full-compose-input-first. Both files are declarations only; there is no run/output evidence yet. Naming labels alone without identifying the endpoint is insufficient.

### H2 — Author, undo and preserve (eight minutes)

Start at the native process list with no document open.

Instruction: "Create a new process titled Study note. Add two text inputs, containing Part: BR-001 and Revision: A. Join them in that order with a newline. Write the joined text to study-note.txt and declare it as an output. Rename the revision input to Revision label, undo that rename, and show the original label again. Save the process, return to the list, and reopen it. Show that the configured text and exact connections were retained."

All conditions required: runnable two-input/join/file document, exact order/newline/file name/output declaration; rename successfully undone; save committed and reopened from list; values/IDs/endpoints retained without lost work. Independent observer checks saved definition and compares before/after semantic identities. Generated IDs need not match a fixed string. No execution speed comparison with the read-only 078 view.

### H3 — Execute and inspect actual output (five minutes)

Start with a fresh saved copy of `examples/mass-check.json`, no prior runs.

Instruction: "Validate and run this mass check. Open the actual generated report. State the calculated mass, find the inputs that produced it, and show which saved process and run produced the file."

All conditions required: actual successful run, bytes equal Mass: 135 g, source volume 0.00005 m3 and density 2700 kg/m3, artifact digest and producing run/definition identity located. A declaration or fixture label without actual accessible bytes fails.

### H4 — Correct a failed check without erasing history (five minutes)

Start with a fresh saved copy of `examples/mass-check-fails.json` (maximum 100 g).

Instruction: "Run this process. Explain what failed and why no report was produced. Correct the allowed maximum to 200 g, save, and run again. Show the successful report and the earlier failed run."

All conditions required: range failure identified at actual 135 g versus maximum 100 g; downstream report/file did not execute; correction saved; new successful run links the old run through derived_from_run_id; old evidence remains failed/unchanged; new report bytes equal Mass: 135 g.

### H5 — Understand delivered and remaining work (four minutes)

Start at the actual candidate's Program status page. Freeze its source bundle and observed quality/candidate state in the observer answer sheet before trials. This is an observation of actual records, not a fabricated production-status fixture.

Instruction: "Show the current milestone and distinguish implemented, verified and integrated work. Identify a remaining requirement and what action it needs. Find which code the latest relevant quality evidence covers. Explain whether the native milestone means all 100 benchmark cases are qualified or all existing Rivet processes have been migrated."

All conditions required: identify all three independent stages; correctly identify one pending requirement/action from the frozen bundle (if none remain, correctly establish all passed using the evidence); locate actual tested commit/coverage or explicitly recognize missing evidence; state that native milestone delivery does not establish process-100 qualification or Rivet migration/retirement. Observe missing human acceptance while the study itself is pending; do not edit dashboard results during trials.

## Acceptance, changes and accessibility

Each of H1–H5 requires at least four successful participants out of the five-person cohort. H2 must also meet its eight-minute limit. Report all results and denominators, not only successful attempts. No overall average can conceal a failing task. A changed product build after acceptance failures requires a complete fresh five-person protocol on the final candidate; preserve prior results. Unchanged covered source may carry evidence across report-only commits using the dashboard's declared scope identity. No agent can impersonate a participant or grant human-review credit.

Separately perform and record an actual manual accessibility review: complete H2 with keyboard only and with click controls without dragging; inspect 320 CSS-pixel width, 200% zoom, forced colors, reduced motion, focus order/visibility and non-color status cues. Automated axe checks supplement this review and must have no serious/critical violations. Record reviewer identity and exact build; agents may provide technical accessibility evidence but never label it independent human evidence.

Recruitment remains an external dependency. Continue implementation and technical verification while it is pending; expose the specific human acceptance gap on the dashboard.
