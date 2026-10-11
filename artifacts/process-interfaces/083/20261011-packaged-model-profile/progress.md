# Production workflow proof

Started 2026-10-11T02:08:00.252Z UTC. Isolated workspace. Follow the current digital engineering run through the normal workspace; no process action is submitted by this browser.

## 2026-10-11T02:08:01.617Z UTC â€” 01-entry Open a blank workflow
URL: http://127.0.0.1:18087/workspace/d45bcf4f-1336-4cf1-bace-a01db359cf5b?workflow=canonical&workflowPath=workflows%2Funtitled-workflow-0182a1ff-e5e.workflow.wflow
Action: Open Packaged UI verification and click Workflows.
Expected: The ordinary workspace control opens the current editor with no existing blocks.
Actual: Expected state verified.
Diagnostics: []
Raw: screenshots/raw/01-entry-after.png
Annotated: screenshots/annotated/01-entry-after.png
Status: PASS

## 2026-10-11T02:08:02.497Z UTC â€” 02-input Add an input block
URL: http://127.0.0.1:18087/workspace/d45bcf4f-1336-4cf1-bace-a01db359cf5b?workflow=canonical&workflowPath=workflows%2Funtitled-workflow-0182a1ff-e5e.workflow.wflow
Action: Click Inputs, then Text input.
Expected: One editable text input appears in the flowchart and inspector.
Actual: Expected state verified.
Diagnostics: []
Raw: screenshots/raw/02-input-after.png
Annotated: screenshots/annotated/02-input-after.png
Status: PASS

## 2026-10-11T02:08:03.477Z UTC â€” 03-save Save the draft
URL: http://127.0.0.1:18087/workspace/d45bcf4f-1336-4cf1-bace-a01db359cf5b?workflow=canonical&workflowPath=workflows%2Funtitled-workflow-0182a1ff-e5e.workflow.wflow
Action: Click Save.
Expected: The workflow is saved through Wright with captured instructions; no execution is started.
Actual: Expected state verified.
Diagnostics: []
Raw: screenshots/raw/03-save-after.png
Annotated: screenshots/annotated/03-save-after.png
Status: PASS

## 2026-10-11T02:08:04.302Z UTC â€” 04-reopen Reopen the saved workflow
URL: http://127.0.0.1:18087/workspace/d45bcf4f-1336-4cf1-bace-a01db359cf5b?workflow=canonical&workflowPath=workflows%2Funtitled-workflow-0182a1ff-e5e.workflow.wflow
Action: Refresh the workspace tab.
Expected: The same saved workflow and its input block are restored without running it.
Actual: Expected state verified.
Diagnostics: []
Raw: screenshots/raw/04-reopen-after.png
Annotated: screenshots/annotated/04-reopen-after.png
Status: PASS

## 2026-10-11T02:08:06.511Z UTC â€” 05-model Inspect the configured model
URL: http://127.0.0.1:18087/workspace/d45bcf4f-1336-4cf1-bace-a01db359cf5b?workflow=canonical&workflowPath=workflows%2Funtitled-workflow-0182a1ff-e5e.workflow.wflow
Action: Open the Agent pane if needed and inspect Model.
Expected: The observed configured model is shown; remote switching is disabled and Model Setup is explained.
Actual: Expected state verified.
Diagnostics: []
Raw: screenshots/raw/05-model-after.png
Annotated: screenshots/annotated/05-model-after.png
Status: PASS
