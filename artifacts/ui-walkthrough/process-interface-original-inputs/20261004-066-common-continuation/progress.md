# Fresh common-view original-input walkthrough

Prepared before navigation. API start uses an exact locally enrolled integration-test policy. This browser does not start/approve/resume the run. Private authenticated trace is not published.

## 2026-10-04T01:26:09.096Z UTC — Same durable run in the common view

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?processView=view-fresh-prompt-common-055-066&processPath=workflows%2Fprinted-replacement-part-prompt-default-055.workflow.wflow&processDigest=17afd12596d230d549d0ff38d16834f994a07c41092576d3231f5e17597fb6f8&processRun=b12008ec35a14bc39b3d63ff6a8f3f18
Action: Open the supplied exact-run link
Controls: Open the supplied exact-run link
Expected: Actual owning run response and progress without generated UI
Actual: The corrected collector and common view agree on the accepted running run with 2 actual outputs; no generated UI is mounted.
Status: PASS
Screenshots: screenshots/raw/C01.png; screenshots/annotated/C01.png

## 2026-10-04T01:26:09.790Z UTC — Refresh preserves the run identity

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?processView=view-fresh-prompt-common-055-066&processPath=workflows%2Fprinted-replacement-part-prompt-default-055.workflow.wflow&processDigest=17afd12596d230d549d0ff38d16834f994a07c41092576d3231f5e17597fb6f8&processRun=b12008ec35a14bc39b3d63ff6a8f3f18
Action: Click Refresh view
Controls: Click Refresh view
Expected: Same source/run readback without another execution
Actual: Refresh reads the same running run and 2 outputs. It does not start, approve or resume work.
Status: PASS
Screenshots: screenshots/raw/C02.png; screenshots/annotated/C02.png

## 2026-10-04T01:26:14.432Z UTC — Reload restores the durable run

URL: http://127.0.0.1:5246/workspace/083-fresh-prompt-055?processView=view-fresh-prompt-common-055-066&processPath=workflows%2Fprinted-replacement-part-prompt-default-055.workflow.wflow&processDigest=17afd12596d230d549d0ff38d16834f994a07c41092576d3231f5e17597fb6f8&processRun=b12008ec35a14bc39b3d63ff6a8f3f18
Action: Reload the workspace tab
Controls: Reload the workspace tab
Expected: Same backend-owned run; no generated UI or replay
Actual: The common working tab restores the exact run after reload.
Status: PASS
Screenshots: screenshots/raw/C03.png; screenshots/annotated/C03.png
