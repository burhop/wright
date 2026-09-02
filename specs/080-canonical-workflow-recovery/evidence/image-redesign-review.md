# Image-led native authoring: internal review

Status: early integrated review completed; final acceptance pending.

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
| Collapsed agent pane left unused horizontal space | Workspace page fills its flex parent | Pending fresh screenshot |
| Initial selection opened Inspector unnecessarily | Start with no selection and Inspector closed | Pending fresh screenshot |
| Inputs popover inherited trigger width and horizontal button layout | Explicit bounded width and stacked rows | Pending fresh screenshot |
| Company context was excluded from input editing by execution-kind heuristic | Use canonical input classification | Host test passed, browser pending |
| Fitting the graph reduced 14px titles to about 10px | Readable initial viewport, explicit Fit overview action | Pending fresh screenshot |
| Selecting offscreen nodes did not pan into available space | Selection visibility adjustment after Inspector resize | Pending interaction evidence |
| Idle component address appeared as “1 issue” | Only failed/blocked/needs-input states create issue targets | Renderer regression test pending |
| Input-preview help and bottom run details ran together | Explicit content-card/footer spacing | Pending fresh screenshot |
| Short viewport cuts the lower rail categories | Internal keyboard-scroll path; review a more compact launcher | Open visual refinement |

The 768×512 image is a reduced viewport, **not** evidence of actual browser 200%
zoom. Actual zoom remains required. All failures and earlier artifacts are kept.

## Final independent review

Pending exact implementation subject and full authoring walkthrough.
