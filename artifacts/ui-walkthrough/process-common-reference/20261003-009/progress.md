# Common process UI walkthrough

Prepared before navigation. Controlled HTTP fixtures; no real backend, model, MCP or physical operation.

## 2026-10-03T22:58:20.688Z UTC — Normal workspace and accepted process

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical
Controls: Workflows
Action: Open the isolated workspace and click Workflows.
Expected: The accepted process opens in the existing editor.
Actual: The normal workspace editor opens; no run is submitted.
Status: PASS
Raw: screenshots/raw/S01.png; annotated: screenshots/annotated/S01.png; result: screenshots/raw/S01-result.png
Diagnostics: []

## 2026-10-03T22:58:21.219Z UTC — Common working tab

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical&processView=b7f68bc7-bf2a-4f9f-ab40-16c205f17b7c&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Use saved process
Action: Click Use saved process.
Expected: Inputs and preparation controls open in a workspace tab.
Actual: The common view shows Design request and Reference image; starting is disabled.
Status: PASS
Raw: screenshots/raw/S02.png; annotated: screenshots/annotated/S02.png; result: screenshots/raw/S02-result.png
Diagnostics: []

## 2026-10-03T22:58:21.493Z UTC — Provide the design request

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical&processView=b7f68bc7-bf2a-4f9f-ab40-16c205f17b7c&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Design request (required)
Action: Enter Make a small test part using the reference image in Design request.
Expected: The draft is entered without starting or editing source.
Actual: The typed draft stays in the working view and no dispatch occurs.
Status: PASS
Raw: screenshots/raw/S03.png; annotated: screenshots/annotated/S03.png; result: screenshots/raw/S03-result.png
Diagnostics: []

## 2026-10-03T22:58:21.792Z UTC — Uploaded bitmap and pending transfer

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical&processView=b7f68bc7-bf2a-4f9f-ab40-16c205f17b7c&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Reference image
Action: Choose reference.png in Reference image.
Expected: A decoded thumbnail and file-transfer progress are visible; preparation/start remain disabled.
Actual: The 96 by 96 bitmap decodes, Preparing file is visible and no process can start while upload is pending.
Status: PASS
Raw: screenshots/raw/S04.png; annotated: screenshots/annotated/S04.png; result: screenshots/raw/S04-result.png
Diagnostics: []

## 2026-10-03T22:58:22.022Z UTC — Transfer finishes before preparation

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical&processView=b7f68bc7-bf2a-4f9f-ab40-16c205f17b7c&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Prepare and check inputs
Action: Wait for the file upload to complete.
Expected: Preparation becomes available after the scoped upload reply.
Actual: The upload's original SHA-256 and process scope are retained; the thumbnail stays visible.
Status: PASS
Raw: screenshots/raw/S05.png; annotated: screenshots/annotated/S05.png; result: screenshots/raw/S05-result.png
Diagnostics: []

## 2026-10-03T22:58:22.637Z UTC — Check all supplied inputs

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical&processView=b7f68bc7-bf2a-4f9f-ab40-16c205f17b7c&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Prepare and check inputs
Action: Click Prepare and check inputs.
Expected: The exact prompt and file binding are prepared, then start becomes permitted.
Actual: Prepared inputs contain the same uploaded reference and Start process is enabled.
Status: PASS
Raw: screenshots/raw/S06.png; annotated: screenshots/annotated/S06.png; result: screenshots/raw/S06-result.png
Diagnostics: []

## 2026-10-03T22:58:23.110Z UTC — Observe the recorded run

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical&processView=b7f68bc7-bf2a-4f9f-ab40-16c205f17b7c&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d&processRun=common-browser-run
Controls: Start process, Observation details
Action: Click Start process and open Observation details.
Expected: The returned run is attached once and the observed activity/percentage/provider are shown.
Actual: The exact run attaches; 20 percent observed completion and the controlled provider/activity are visible without guessed completion.
Status: PASS
Raw: screenshots/raw/S07.png; annotated: screenshots/annotated/S07.png; result: screenshots/raw/S07-result.png
Diagnostics: []

## 2026-10-03T22:58:24.135Z UTC — Inspect completion and keyboard access

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical&processView=b7f68bc7-bf2a-4f9f-ab40-16c205f17b7c&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d&processRun=common-browser-run
Controls: Refresh view
Action: Wait for completion, then click Refresh view.
Expected: Recorded completion and the exact result appear; common controls remain accessible.
Actual: The saved result and 100 percent last reported are shown. Scoped WCAG A/AA scanning finds zero violations.
Status: PASS
Raw: screenshots/raw/S08.png; annotated: screenshots/annotated/S08.png; result: screenshots/raw/S08-result.png
Diagnostics: []

## 2026-10-03T22:58:25.958Z UTC — Reopen without replay

URL: http://127.0.0.1:58323/workspace/ws-recovery?workflow=canonical&processView=b7f68bc7-bf2a-4f9f-ab40-16c205f17b7c&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d&processRun=common-browser-run
Controls: Close working tab, Saved run link
Action: Close the working tab, then reopen its saved link.
Expected: The same completed run reopens without a second dispatch or cancellation.
Actual: The same exact run/result reopens; one start, zero cancellations and zero accepted-source edits remain.
Status: PASS
Raw: screenshots/raw/S09.png; annotated: screenshots/annotated/S09.png; result: screenshots/raw/S09-result.png
Diagnostics: []
