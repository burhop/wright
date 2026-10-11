# Fresh common-view original-input walkthrough

Prepared before navigation. Read-only continuation after the retained harness expected Completed instead of the actual Process completed label. The original common-view start and completed run are preserved; this continuation never starts or changes the process. Private authenticated trace is not published.

## 2026-10-04T02:05:22.503Z UTC — Same completed digital run

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?processView=view-common-digital-083-091&processPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processDigest=88edffded48c36532efc8c49d7e1a78206753d3b52d658d8d3b9d18b1684eb06&processRun=8c042141e6c7422aa58ca1bbab14d86e
Action: Open the exact-run workspace link
Controls: Open the exact-run workspace link
Expected: Actual common view and backend agree on completion
Actual: The same common-view-started run has five actual outputs and no generated interface or review. The UI correctly says Process completed.
Status: PASS
Screenshots: screenshots/raw/C01.png; screenshots/annotated/C01.png

## 2026-10-04T02:05:23.103Z UTC — Reconcile completion without replay

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?processView=view-common-digital-083-091&processPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processDigest=88edffded48c36532efc8c49d7e1a78206753d3b52d658d8d3b9d18b1684eb06&processRun=8c042141e6c7422aa58ca1bbab14d86e
Action: Click Refresh view
Controls: Click Refresh view
Expected: Same completed run and accepted source
Actual: Refresh reads the same completed digital mesh process without starting it again.
Status: PASS
Screenshots: screenshots/raw/C02.png; screenshots/annotated/C02.png

## 2026-10-04T02:05:23.553Z UTC — Inspect actual result cards

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?processView=view-common-digital-083-091&processPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processDigest=88edffded48c36532efc8c49d7e1a78206753d3b52d658d8d3b9d18b1684eb06&processRun=8c042141e6c7422aa58ca1bbab14d86e
Action: Scroll to Results and checks
Controls: Scroll to Results and checks
Expected: Exact native source STL, repaired STL, preview and native responses
Actual: Five exact backend-recorded result cards are available. Native geometry remains digital preparation, without manufacturing release or physical acceptance.
Status: PASS
Screenshots: screenshots/raw/C03.png; screenshots/annotated/C03.png

## 2026-10-04T02:05:27.132Z UTC — Reload preserves the completed run

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?processView=view-common-digital-083-091&processPath=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&processDigest=88edffded48c36532efc8c49d7e1a78206753d3b52d658d8d3b9d18b1684eb06&processRun=8c042141e6c7422aa58ca1bbab14d86e
Action: Reload the workspace
Controls: Reload the workspace
Expected: The same durable run returns with no new start
Actual: The exact completed run restores after reload; no generated interface is required.
Status: PASS
Screenshots: screenshots/raw/C04.png; screenshots/annotated/C04.png
