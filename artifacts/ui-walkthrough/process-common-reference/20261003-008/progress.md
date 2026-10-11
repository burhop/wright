# Common process UI walkthrough

Prepared before navigation. Controlled HTTP fixtures; no real backend, model, MCP or physical operation.

## 2026-10-03T22:53:26.149Z UTC — Normal workspace and accepted process

URL: http://127.0.0.1:62133/workspace/ws-recovery?workflow=canonical
Controls: Workflows
Action: Open the isolated workspace and click Workflows.
Expected: The accepted process opens in the existing editor.
Actual: The normal workspace editor opens; no run is submitted.
Status: PASS
Raw: screenshots/raw/S01.png; annotated: screenshots/annotated/S01.png; result: screenshots/raw/S01-result.png
Diagnostics: [{"kind":"response","detail":"404 http://127.0.0.1:62133/api/settings"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"},{"kind":"response","detail":"404 http://127.0.0.1:62133/api/agent/chat/stream/status?session_id=session-recovery"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"}]

## 2026-10-03T22:53:26.924Z UTC — Common working tab

URL: http://127.0.0.1:62133/workspace/ws-recovery?workflow=canonical&processView=dffa0895-8146-4a7f-8264-cf4780932f40&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Use saved process
Action: Click Use saved process.
Expected: Inputs and preparation controls open in a workspace tab.
Actual: The common view shows Design request and Reference image; starting is disabled.
Status: PASS
Raw: screenshots/raw/S02.png; annotated: screenshots/annotated/S02.png; result: screenshots/raw/S02-result.png
Diagnostics: [{"kind":"response","detail":"404 http://127.0.0.1:62133/api/settings"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"},{"kind":"response","detail":"404 http://127.0.0.1:62133/api/agent/chat/stream/status?session_id=session-recovery"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"}]

## 2026-10-03T22:53:27.326Z UTC — Provide the design request

URL: http://127.0.0.1:62133/workspace/ws-recovery?workflow=canonical&processView=dffa0895-8146-4a7f-8264-cf4780932f40&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Design request (required)
Action: Enter Make a small test part using the reference image in Design request.
Expected: The draft is entered without starting or editing source.
Actual: The typed draft stays in the working view and no dispatch occurs.
Status: PASS
Raw: screenshots/raw/S03.png; annotated: screenshots/annotated/S03.png; result: screenshots/raw/S03-result.png
Diagnostics: [{"kind":"response","detail":"404 http://127.0.0.1:62133/api/settings"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"},{"kind":"response","detail":"404 http://127.0.0.1:62133/api/agent/chat/stream/status?session_id=session-recovery"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"}]

## 2026-10-03T22:53:27.888Z UTC — Uploaded bitmap and pending transfer

URL: http://127.0.0.1:62133/workspace/ws-recovery?workflow=canonical&processView=dffa0895-8146-4a7f-8264-cf4780932f40&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Reference image
Action: Choose reference.png in Reference image.
Expected: A decoded thumbnail and file-transfer progress are visible; preparation/start remain disabled.
Actual: The 96 by 96 bitmap decodes, Preparing file is visible and no process can start while upload is pending.
Status: PASS
Raw: screenshots/raw/S04.png; annotated: screenshots/annotated/S04.png; result: screenshots/raw/S04-result.png
Diagnostics: [{"kind":"response","detail":"404 http://127.0.0.1:62133/api/settings"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"},{"kind":"response","detail":"404 http://127.0.0.1:62133/api/agent/chat/stream/status?session_id=session-recovery"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"}]

## 2026-10-03T22:53:28.271Z UTC — Transfer finishes before preparation

URL: http://127.0.0.1:62133/workspace/ws-recovery?workflow=canonical&processView=dffa0895-8146-4a7f-8264-cf4780932f40&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Prepare and check inputs
Action: Wait for the file upload to complete.
Expected: Preparation becomes available after the scoped upload reply.
Actual: The upload's original SHA-256 and process scope are retained; the thumbnail stays visible.
Status: PASS
Raw: screenshots/raw/S05.png; annotated: screenshots/annotated/S05.png; result: screenshots/raw/S05-result.png
Diagnostics: [{"kind":"response","detail":"404 http://127.0.0.1:62133/api/settings"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"},{"kind":"response","detail":"404 http://127.0.0.1:62133/api/agent/chat/stream/status?session_id=session-recovery"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"}]

## 2026-10-03T22:53:28.969Z UTC — Check all supplied inputs

URL: http://127.0.0.1:62133/workspace/ws-recovery?workflow=canonical&processView=dffa0895-8146-4a7f-8264-cf4780932f40&processPath=workflows%2Fmounting-bracket.workflow.wflow&processDigest=f5a13afad2c11e65c591ed52bb8531769ef5bcd7c946030960f1511c1d64ba9d
Controls: Prepare and check inputs
Action: Click Prepare and check inputs.
Expected: The exact prompt and file binding are prepared, then start becomes permitted.
Actual: Error: [2mexpect([22m[31mreceived[39m[2m).[22mtoMatchObject[2m([22m[32mexpected[39m[2m)[22m

[1mMatcher error[22m: [31mreceived[39m value must be a non-null object

Received has value: [31mundefined[39m
Status: STOPPED
Raw: screenshots/raw/S06.png; annotated: screenshots/annotated/S06.png; result: screenshots/raw/S06-result.png
Diagnostics: [{"kind":"response","detail":"404 http://127.0.0.1:62133/api/settings"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"},{"kind":"response","detail":"404 http://127.0.0.1:62133/api/agent/chat/stream/status?session_id=session-recovery"},{"kind":"console","detail":"Failed to load resource: the server responded with a status of 404 (Not Found)"}]
