# Review inspector usability correction

Task: find the proposed print-package review, understand its checklist, and
return to the same workflow. Uses accepted candidate 036 revision 9; no run or
results were fabricated and no review decision was submitted.

The independent reviewer found the upstream list displaced the actual checklist.
The 480px screenshot additionally showed only 242px allocated to the inspector.
Collapse upstream context by default, retain its complete list on demand, label
the existing return control Close details, and reuse the existing temporary
inspector sheet at widths below 650px. The canvas and its selection remain intact.

Actual compiled browser checks passed at 1100x900 and 480x900: find/focus the
review node, open details, close details, verify saved revision/digest unchanged.
77 affected component tests pass. A first test failure caught a missing stable
interactive-control ID; corrected before the passing test. Before/after and
return screenshots are retained here. Runtime engineering review, Windows panel
rendering and end-to-end engineering execution remain unverified. The inspected
source checklist is authoring content, not an approval action.

Private drivers and receipts: `.local-run/experience-review/candidate-036/`
`focus-review-narrow.mjs` and `focused-review-narrow-01` through `-04`.
Installed 0.33 is unchanged. The new compiled resource is a local candidate.
