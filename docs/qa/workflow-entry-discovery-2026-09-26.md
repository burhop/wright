# Workflow entry opens an unrelated saved workflow

**Status:** Open; recorded for a later UI pass. No behavior change in this report.

## User observation

On 2026-09-26, the user clicked the workspace **Workflow/Workflows** control expecting to create a new workflow. Wright opened the existing `mounting-bracket.wflow` editor instead. The workspace can contain several workflows, so choosing one implicitly is ambiguous. The user expects to open a particular saved workflow by clicking its file, while recognizing that finding it in a large file tree may be slow. The **Print a part demo** action is at the upper right of that unrelated editor, so the user did not see the promised **What part should Wright make?** form.

Evidence: [user screenshot](evidence/workflow-entry-existing-file-2026-09-26.png) from the local demo workspace. The served URL had `?workflow=canonical` and no `workflowPath` selection. In the current frontend, `WorkspacePanel.tsx` falls back to `/workflows/mounting-bracket.workflow.wflow` when no workflow path is supplied; it also has a separate file-click path that opens the selected `.workflow.wflow` file.

## Expected behavior for design review

- The workspace Workflow/Workflows control starts a new, empty workflow, as the user requested.
- Clicking a `.workflow.wflow` file opens that exact saved workflow. Existing work remains intact.
- Provide an efficient way to find saved workflows from the workspace, such as a searchable/recent workflow picker, so users need not search a large general file tree.
- Make the prompt-to-printed-part demo discoverable without first opening an unrelated saved workflow.

## Follow-up acceptance checks

1. In a workspace with multiple saved workflows, clicking Workflow/Workflows never silently selects a hard-coded file.
2. Clicking each workflow file opens the matching definition and tab; reopening and URL navigation preserve its identity.
3. The new-workflow action creates a blank draft without overwriting a saved workflow or discarding unsaved editor work.
4. The workflow picker or equivalent can find a named workflow quickly, and the print demo has a clear entry point.

Track this separately from the current print-demo slicing and printer work. Preserve the reviewed graphical editor and its authoring capabilities when designing the change.
