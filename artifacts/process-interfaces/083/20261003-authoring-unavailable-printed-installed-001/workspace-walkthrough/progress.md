# Heat workspace entry walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T12:35:26.285Z UTC â€” Updated installed workspace

URL: http://wright.localhost:54524/workspace/083-printed-repeat-015
Action: Open the isolated workspace.
Controls: Workflows, Workspace Files
Expected: Existing workspace navigation visible.
Actual: Normal Workflows and Files controls are available.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T12:35:35.017Z UTC â€” Saved and common results retained

URL: http://wright.localhost:54524/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-authoring-unavailable-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Click Use common working view.
Controls: Use common working view, Create or choose interface
Expected: Exact original outputs in both views.
Actual: 20 exact results retained; run 5c3a84a335854e88aa8bbe48a591ce0d.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T12:35:35.600Z UTC â€” Clear creation limit and usable saved interface

URL: http://wright.localhost:54524/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-authoring-unavailable-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Open interface controls and enter a description.
Controls: Create or choose interface, How should this interface help the user?, Create interface, Update selected interface, Saved interface, Saved revision, Open saved interface
Expected: Visible actionable reason; Create/Update disabled and exact saved interface enabled.
Actual: Reason: The qualified interface compiler is unavailable.

Configure the local qualified toolchain; existing saved interfaces and the common view still work.

Technical details. Exact saved interface and revision retained; no creation is submitted.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T12:35:36.566Z UTC â€” Compact authoring and keyboard access

URL: http://wright.localhost:54524/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-authoring-unavailable-printed-001&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Resize to480px, focus Saved interface and press Tab twice.
Controls: Saved interface, Saved revision, Open saved interface
Expected: No outer overflow, zero scoped automated violations, exact keyboard focus order.
Actual: Document 432px/432px; zero WCAG A/AA violations; keyboard reaches exact saved revision and Open saved interface.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T12:35:42.645Z UTC â€” Saved interface opens while creation is unavailable

URL: http://wright.localhost:54524/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=93d2b5b0-9593-4d78-bf03-ddec0c4c8d89&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=working&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73
Action: Press Enter on Open saved interface.
Controls: Open saved interface, Working tab
Expected: Exact UI/revision/run with all original outputs and no generation.
Actual: Exact backend binding and 20 result identities verified; no creation, process start, review or action submitted.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## Report metadata correction

The inherited compact-navigation title/checklist was corrected to this authoring journey. Original metadata/source remain privately retained. Recorded actions, screenshots and outcomes are unchanged.
