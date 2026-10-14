# Actual desktop editor walkthrough — after approved installation

In a fresh conversation on the existing GB10 execution host, paste:

> Use the Wright plugin. First read connection status. Open the shared Workflows
> editor for workspace `c54dabc1-b560-4dfb-8197-f922e9ff6edf`, session
> `desktop-abbb5c26-d460-4a5c-a52b-ff905156c6ed`, saved path
> `workflows/native-editor.workflow.wflow` using `wright_workflow_open`.
> This is isolated UI test state. Do not start a workflow, call a model worker,
> change configuration, or open a browser URL. Report missing tools explicitly.

Expected: one actual native panel showing the same neutral Wright canvas.
The current test source title is “Other saved edit”; it is not engineering work.

1. Confirm the canvas renders. Record the actual desktop build if available.
2. Use Source, change the workflow name, Apply checked edit, then Save. Observe
   any host tool permission prompt separately from Wright process reviews.
3. Close and reopen the same saved path. Verify the name and block positions.
   Save before closing; unsaved restoration/close interception is unqualified.
4. Resize the panel and change host theme. Check Add step, inspector, Undo/Redo,
   Source/Side by side and keyboard focus. Do not start a run from this editor.
5. Capture the actual desktop panel with clean data for a progress image.

Describe native rendering, save, reopen, theme, resize and permission outcomes
separately. A browser screenshot or passing mock test is not this acceptance.
The broader workspace-create and actual desktop reasoning/checkpoint journey
follows this first edit/save/reopen check.
