# Image-led native authoring: internal review

Status: two independent visual passes completed; the exact-subject pass found one final output-preview overflow to repair.

This is an independent AI-agent screenshot/code review, not a human usability
study, benchmark, engineering validation, or product-owner signoff on a final
subject. Authorization comes from the user's 2026-09-02 goal, not this review.

## Early browser checkpoint

Artifact root: `artifacts/ui-walkthrough/image-redesign/20260902T220022Z-early-shell-continuation-1/`.
Working tree above `7e95b0c748975df247effb4bc70f1f67f92a8e81`; not an exact
committed implementation subject. Real workspace/API, no route mocks.

The primary implementer inspected raw 1537×791, 1070×791 and 768×512 screens.
A separately delegated reviewer inspected the primary selected image and seven
raw states (shell, Create menu, Inputs navigator, Inspector, three viewport states).
Browser shell assertions passed, but visual review found material issues:

| Finding | Correction | Verification |
|---|---|---|
| Collapsed agent pane left unused horizontal space | Workspace page fills its flex parent | Verified in exact 4cfab9ba image-reference-match |
| Initial selection opened Inspector unnecessarily | Start with no selection and Inspector closed | Verified in exact image-reference-match and independent read-only pass |
| Inputs popover inherited trigger width and horizontal button layout | Explicit bounded width and stacked rows | Verified by navigator capture and independent review |
| Company context was excluded from input editing by execution-kind heuristic | Use canonical input classification | Host regression and full authoring journey passed |
| Fitting the graph reduced 14px titles to about 10px | Readable initial viewport, explicit Fit overview action | Matched-image review passed; graph is not automatically shrunk to fit |
| Selecting offscreen nodes did not pan into available space | Selection visibility adjustment after Inspector resize | Independent review and keyboard authoring journey passed |
| Idle component address appeared as “1 issue” | Only failed/blocked/needs-input states create issue targets | Expanded 14-test renderer suite passed; exact default image has no invented issue |
| Input-preview help and bottom run details ran together | Explicit content-card/footer spacing | Main editor/bottom details verified; separate output modal finding below |
| Short viewport cuts the lower rail categories | Internal keyboard-scroll path and compact launcher | Short-viewport keyboard journey and actual 200% controls passed |

The 768×512 image is a reduced viewport, **not** evidence of actual browser 200%
zoom. Subsequent actual Chromium tab-zoom evidence is recorded below. All failures and earlier artifacts are kept.

## Subsequent independent review

`20260902T223502Z-independent-readonly-review` performed seven read-only browser
checks, recorded no mutations or unexpected diagnostics, and compared the
1536×1024 editor with the selected primary image. The independent reviewer
accepted the hierarchy but found four concrete polish issues: file input and
MCP document input icon distinctions, unstyled New/Open workflow controls, and
the delete dialog's unstyled/abutting Keep step button. All four were repaired
before commit `4cfab9ba8091b766805e00157739204675385c0c`.

The reviewer then inspected the exact 32-step report
`20260902T225850Z-committed-acceptance-4cfab9ba-continuation-2`, including the
primary editor, text/file/tool settings, connections, delete dialog, proposal,
simulation/output and responsive/actual-zoom states. The four prior polish
findings were confirmed resolved. Actual 200% images show the Inspector Apply
control reachable through internal scrolling, minimap collapsed on entry, and
a usable canvas after optional Inspector collapse. This is real tab zoom 2.0,
not just a small screenshot or CSS zoom.

One additional P2 finding prevents zero-issue acceptance: the output-preview
sidebar uses an auto min-content grid track. Long filenames/checksums widen its
children beyond the fixed sidebar, clipping the report action and simulation
qualification. The next continuation must prove wrapping, no horizontal
overflow and reachable full action labels, including narrow/zoom states.
After wrapping was repaired, the strengthened narrow screenshots revealed
workspace chrome painting above the nested modal. A body portal retaining
the recovery theme and existing focus behavior is required; simply raising an
inner z-index does not escape the retained-tab stacking context. This is a
second scoped P2 modal finding, not a change to the approved product direction.
The reviewer is
now implementing this small repair; its regression rerun must not be described
as independent author review. The integration writer and separate walkthrough
owner will inspect the repaired result before closing acceptance.

## Modal repair follow-up

The integration writer separately inspected the repaired 1537×791, 830×791 and
768×395 screenshots in `output-preview-final-green-20260902`. Filenames,
simulation qualification, checksum, lineage and both full action labels wrap
inside the card; the modal header and Close remain above the host chrome. The
narrow captures intentionally scroll the modal's own content to the actions,
not the document. All 13 existing Chromium journeys pass, including added text
range bounds, unobscured header/action targets, keyboard trapping, Escape and
backdrop dismissal with focus return. The unchanged focused active-run lock
test passes in 3.03s; a resource-bounded full suite and the exact-subject actual
200% continuation remain separate closing checks.
