# Current installed saved-interface and diagnostics walkthrough

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-04T00:30:46.309Z UTC — Reopen the recorded preview

URL: http://wright.localhost:58474/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-visible-trace-036&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73&processUIJob=job-971c977de22741b1a49cf21451b232b8
Action: Open the same recorded preview link.
Controls: Create or choose interface, Use common working view
Expected: Read-only preview on the same run and revision.
Actual: The read-only preview opens with all 20 exact output identities.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-04T00:30:47.641Z UTC — Creation details are collapsed

URL: http://wright.localhost:58474/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-visible-trace-036&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73&processUIJob=job-971c977de22741b1a49cf21451b232b8
Action: Click Create or choose interface, then scroll to Creation details.
Controls: Creation details
Expected: Saved job with collapsed diagnostics.
Actual: The actual saved job is restored and Creation details is collapsed.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-04T00:30:48.079Z UTC — All creation identities are visible together

URL: http://wright.localhost:58474/workspace/083-printed-repeat-015?workflow=canonical&workflowPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processView=view-visible-trace-036&processPath=workflows%2Fprinted-replacement-part-configured-default-016.workflow.wflow&processDigest=1fb7fb48d6579448565b28553f5b0136ed7c7e19e7c5fbd90f6d50d26493c0b7&processRun=5c3a84a335854e88aa8bbe48a591ce0d&processUIKind=preview&processUI=ui-0a09766ccdd94bfdb3dab1f5519d1628&processUIRevision=revision-d38d8f51a4674fe7816f9b00ca43ad73&processUIJob=job-971c977de22741b1a49cf21451b232b8
Action: Click Creation details and scroll its Trace text into view.
Controls: Creation details
Expected: All exact identity text inside the visible viewport.
Actual: The complete diagnostics fit in the viewport and all identities match the original actual-model authoring record.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png
