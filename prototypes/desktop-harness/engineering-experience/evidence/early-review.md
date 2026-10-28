# Independent navigation-study usability review

Reviewed 2026-10-28. One AI reviewer, not a human acceptance test. Headless Chromium/Playwright against the local file URL, at 1100 × 900 and 480 × 900. No engineering tools, plugins, live state, user drafts, external actions or application code were changed. Browser launch needed sandbox escalation. All journey choices were made from visible text; HTML was inspected only after completing the requested first-pass journeys. One later targeted recheck followed the author's fixes.

## Task outcomes and observed route

- Set up a replacement-handle workspace: completed using the labelled name field and Create workspace. The empty workspace made the next action clear.
- Request a workflow using existing Codex conversation: Create a workflow explicitly directed me to the conversation beside the panel and told me to attach images there. Preview sample workflow clearly substituted for a response. No second chat box competed for attention. Actual attachment and conversation transfer remain untested simulation boundaries.
- Understand review before CAD: the outline explicitly put specification review before CAD. I first clicked the review outline text expecting to inspect it; nothing happened. The outline was labelled as a stand-in for the shared canvas, so this is a documented boundary rather than a broken live editor. Prepare new run → Simulate run to design review reached the waiting screen. I understood that missing dimensions/load need review and that previewing later results does not approve anything. No outside coaching was needed.
- Inspect one step's output: results → View CAD step showed specification → CAD tool → model/STEP/drawing and retained Run 1/revision 1. Technical evidence expanded. Returning preserved Run 1. Analysis inspection likewise showed verified CAD/load → FEA → stress/displacement/checks. These are descriptions of expected artifacts, not inspectable engineering evidence; actual file opening was unavailable by design.
- Change requirements and prepare another full run while finding prior results: entered “Increase mounting-hole spacing to 128 mm; retain 100 N service load.” Save revision and prepare new run led to Run 2/revision 2. Returning to Workflow → Previous runs found Run 1/revision 1. Simulated Run 2 again went through design review; history then listed both runs. No assistance was needed, but the first pass did not let me verify that my changed requirement survived.

## First-pass findings (preserved)

1. **Material confusion: changed requirement disappeared.** Preparation did not echo the submitted 128 mm/100 N change, design review again said measurement/confirmation required, and reopening Edit requirements showed an empty field. The revision number increased, but the user could not check what changed. Evidence: 09-rerun-1100.png, 12-design-review-480.png, 16-empty-reopened-requirements-480.png. Although persistence is simulated, confirming the requirement within the current navigation session is necessary to evaluate this journey.
2. **Missing decision context:** design review did not show run or revision. This made the repeated review indistinguishable from the first one despite exact run identities on later results. Evidence: 05-design-review-1100.png and 12-design-review-480.png.
3. **Draft lost from workspace navigation:** after previewing a sample workflow, returning to the workspace showed “No workflows yet.” Confirmed in a post-journey visible check prompted by source inspection, rather than discovered unaided during the initial happy path. Evidence: 18-draft-lost-workspace-480.png.

## Targeted recheck after study-only fixes

- Confirmed the authored draft now appears as Replacement handle / Open workflow when returning to workspace before any run.
- Confirmed revised preparation displays the entered 128 mm/100 N requirement.
- Confirmed review explicitly identifies Run 2 / workflow revision 2 and displays that same requirement; assumptions now ask the user to check agreement with supplied measurements and load. Evidence: 19-recheck-review-480.png.
- Confirmed earlier Run 1 still identifies revision 1 and its expanded Requirements used for this run contains the original image-based request. Run 2's expanded section contains the changed requirement. Evidence: 21-recheck-earlier-requirements-1100.png.
- Findings 1–3 are resolved for the demonstrated navigation path. Reopening the edit field after this fix was not separately retested; the stronger preparation/review/per-run snapshot path was verified.

## Remaining limits and wording

- “Waiting for print-job review” with plain “Review required” has no review destination in this study. I can understand why the process stops, but cannot test the next review interaction. This is an intentional scope boundary, not evidence of a production failure.
- “Real CAD, FEA and slicer readiness is unqualified here” is technical wording for a first-time user. It conveys the limitation less directly than “This study does not check whether your engineering tools are ready.” Minor wording issue only.
- Original and changed requirements are now visible, but this study cannot establish that an AI incorporated them into the specification, that checks reran, or that approvals invalidate correctly in production.
- The review screen describes required design-document content but does not supply a mock document or value-by-value decision interaction. Understanding the order succeeded; completing an engineering review was not tested and must not be reported as completed.

## Width assessment and display evidence

At 1100px, content, navigation and result rows are easy to scan. At 480px, result rows and calls to action remain readable and operable; measured document width equalled 480px for results and the request handoff, with no horizontal overflow. Long context text wraps naturally. The updated review requires ordinary vertical scrolling at 480px; full-page evidence includes content below the initial viewport. This was a standalone panel study, so real desktop embedding and neighboring chat visibility were not verified.

Suggested screenshots for user discussion: `15-results-1100.png` (original result overview), `11-results-480.png` (same original narrow overview), `19-recheck-review-480.png` (updated requirement/review context), `21-recheck-earlier-requirements-1100.png` (updated retained prior-run requirements).

Assessment: the requested simulated navigation journeys are understandable without button coaching, with the three concrete context/state issues corrected in the targeted recheck. This is usability evidence for the study only, not production UI acceptance or engineering proof.
