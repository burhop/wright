# SteveCAD saved process in Wright

Actual isolated workspace; inspection only. No engineering acceptance.

## 2026-10-11T17:17:53.033Z UTC — 00
URL: http://wright.localhost:8891/
Action/control/value: Open Wright and unlock it with the existing private local access token. Do not share the token.
Expected: Normal local access succeeds without exposing credentials
Actual: Normal local access succeeds without exposing credentials Verified in the served UI.
Diagnostics: []
Raw: screenshots/raw/00-after.png
Annotated: screenshots/annotated/00-after.png
Status: PASS

## 2026-10-11T17:17:54.111Z UTC — 01
URL: http://wright.localhost:8891/
Action/control/value: Open Wright on port 8891.
Expected: The exact isolated workspace card is visible
Actual: The exact isolated workspace card is visible Verified in the served UI.
Diagnostics: []
Raw: screenshots/raw/01-after.png
Annotated: screenshots/annotated/01-after.png
Status: PASS

## 2026-10-11T17:17:55.273Z UTC — 02
URL: http://wright.localhost:8891/workspace/225aca34-3ae9-4557-85d6-0d8defd90a86
Action/control/value: Click SteveCAD engineering demonstrations.
Expected: The workspace opens with its Workflows control
Actual: The workspace opens with its Workflows control Verified in the served UI.
Diagnostics: []
Raw: screenshots/raw/02-after.png
Annotated: screenshots/annotated/02-after.png
Status: PASS

## 2026-10-11T17:17:56.584Z UTC — 03
URL: http://wright.localhost:8891/workspace/225aca34-3ae9-4557-85d6-0d8defd90a86?workflow=canonical&workflowPath=workflows%2Funtitled-workflow-072768b5-78f.workflow.wflow
Action/control/value: Click Workflows.
Expected: The preserved workflow editor opens in the workspace
Actual: The preserved workflow editor opens in the workspace Verified in the served UI.
Diagnostics: []
Raw: screenshots/raw/03-after.png
Annotated: screenshots/annotated/03-after.png
Status: PASS

## 2026-10-11T17:17:57.272Z UTC — 04
URL: http://wright.localhost:8891/workspace/225aca34-3ae9-4557-85d6-0d8defd90a86?workflow=canonical&workflowPath=workflows%2Funtitled-workflow-072768b5-78f.workflow.wflow
Action/control/value: Open the workflow file menu, then click Open workflow.
Expected: The saved thermal process is listed
Actual: The saved thermal process is listed Verified in the served UI.
Diagnostics: []
Raw: screenshots/raw/04-after.png
Annotated: screenshots/annotated/04-after.png
Status: PASS

## 2026-10-11T17:17:58.453Z UTC — 05
URL: http://wright.localhost:8891/workspace/225aca34-3ae9-4557-85d6-0d8defd90a86?workflow=canonical&workflowPath=workflows%2Fstevecad-heat-spreader-native-003.workflow.wflow
Action/control/value: Click stevecad-heat-spreader-native-003.workflow.wflow.
Expected: The exact saved heat-spreader process opens with its authoring and working-view controls
Actual: The exact saved heat-spreader process opens with its authoring and working-view controls Verified in the served UI.
Diagnostics: []
Raw: screenshots/raw/05-after.png
Annotated: screenshots/annotated/05-after.png
Status: PASS
