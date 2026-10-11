# Installed workflow authoring continuation

Prepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.

## 2026-10-03T11:00:36.970Z UTC â€” Normal workspace editor entry

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical
Action: Click Workflows.
Controls: Workflows, Workflow files
Expected: Existing editor opens within the workspace.
Actual: Existing editor and workflow file menu are visible.
Status: pass
Screenshots: screenshots/raw/S01.png; screenshots/annotated/S01.png

## 2026-10-03T11:00:37.496Z UTC â€” Accurate new-workflow instructions

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical
Action: Open New workflow.
Controls: Workflow name, Create workflow
Expected: Instructions describe a blank workflow.
Actual: The installed dialog describes blank-workflow creation and readiness.
Status: pass
Screenshots: screenshots/raw/S02.png; screenshots/annotated/S02.png

## 2026-10-03T11:00:38.743Z UTC â€” Fresh blank source

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Create Editor verification 083 009 and open Source.
Controls: Workflow name, Create workflow, Source
Expected: A new, separate workflow has no prefilled engineering steps.
Actual: The scratch workflow source contains its name and no task/input/connection/item declarations.
Status: pass
Screenshots: screenshots/raw/S03.png; screenshots/annotated/S03.png

## 2026-10-03T11:00:39.368Z UTC â€” Direct input configuration

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Create Text input and enter engineering text.
Controls: Create, Text input, Text
Expected: Input inspector edits the same workflow.
Actual: Text input and its direct inspector field are visible and configured.
Status: pass
Screenshots: screenshots/raw/S04.png; screenshots/annotated/S04.png

## 2026-10-03T11:00:39.810Z UTC â€” Undo and redo

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Undo the text edit, then Redo.
Controls: Undo, Redo
Expected: Both controls restore accepted editing state.
Actual: Undo removes the entered value and Redo restores it.
Status: pass
Screenshots: screenshots/raw/S05.png; screenshots/annotated/S05.png

## 2026-10-03T11:00:40.480Z UTC â€” Individual AI steps

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Create two AI prompt steps.
Controls: Create, AI prompt
Expected: Both new steps appear in the established canvas.
Actual: Two separate AI prompt steps appear; no model work is started.
Status: pass
Screenshots: screenshots/raw/S06.png; screenshots/annotated/S06.png

## 2026-10-03T11:00:40.908Z UTC â€” Typed connection in source

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Connect the first Response to the second Prompt using Enter.
Controls: Response output, Prompt input, Source
Expected: A type-compatible connection appears in the same source.
Actual: The keyboard-created connection appears in canonical source.
Status: pass
Screenshots: screenshots/raw/S07.png; screenshots/annotated/S07.png

## 2026-10-03T11:00:42.181Z UTC â€” Actual pointer socket connection

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Drag the Text input Design text output to the first AI prompt Prompt input; inspect Source.
Controls: Design text output, First Prompt input, Source
Expected: The typed pointer connection changes the accepted graph and appears in source.
Actual: The semantic digest changes and source records two connections, including the exact input/output keys.
Status: pass
Screenshots: screenshots/raw/S07a.png; screenshots/annotated/S07a.png

## 2026-10-03T11:00:43.385Z UTC â€” Pan changes only the viewport

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Drag empty canvas 90 pixels right and 45 pixels up.
Controls: Empty diagram canvas
Expected: The viewport moves; source and node layout remain unchanged.
Actual: The viewport transform changes while both semantic and layout digests stay identical.
Status: pass
Screenshots: screenshots/raw/S07b.png; screenshots/annotated/S07b.png

## 2026-10-03T11:00:44.707Z UTC â€” Editor accessibility scan

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Inspect active editor WCAG A/AA semantics and contrast.
Controls: Diagram, Source, Save, Canvas controls, Connection sockets
Expected: No detected A/AA accessibility violations in the active editor.
Actual: Automated axe WCAG 2/2.1 A/AA scan reports no violations; manual/assistive-technology acceptance remains separate.
Status: pass
Screenshots: screenshots/raw/S07c.png; screenshots/annotated/S07c.png

## 2026-10-03T11:00:46.782Z UTC â€” Saved source reopens

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Save and reload the workspace.
Controls: Save, Source
Expected: The exact saved workflow reopens without execution.
Actual: Reload restores the saved input, two AI steps and connection exactly.
Status: pass
Screenshots: screenshots/raw/S08.png; screenshots/annotated/S08.png

## 2026-10-03T11:00:47.153Z UTC â€” Invalid draft stays isolated

URL: http://wright.localhost:64695/workspace/083-heat-live-005?workflow=canonical&workflowPath=workflows%2Feditor-verification-083-009.workflow.wflow
Action: Enter a source draft containing managed revision: 99 and Apply.
Controls: Source, Apply, Run
Expected: Invalid source leaves accepted revision intact and blocks Run.
Actual: Managed-field diagnostic is visible, accepted revision is unchanged and Run is disabled.
Status: pass
Screenshots: screenshots/raw/S09.png; screenshots/annotated/S09.png
