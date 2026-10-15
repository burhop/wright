# Native workflow creation slice

Implementation under qualification; not installed or user accepted.
Baseline: a7083736, a separate descendant of PR 154. Installed 0.9 stays frozen.

Journey: choose/create a workspace, select Workflows, choose New workflow, name
it, and enter the existing shared editor. Return to Workspaces and reopen the
exact saved source. Conversation-driven authoring remains available.

Reuse `blankWorkflowSource` and the existing source POST owner through
`wright_workflow_create`; expose this scoped tool to the app as well as the model.
No new executor, process-UI generator, storage, run or permission grant. The
single-panel host retains the shared canvas, source and working-view contracts.

The source owner materializes versioned instruction defaults. Its returned
workspace/path/digest identifies the saved source; raw blank-template bytes are
not that authority. Opening reads through the existing owner. A confirmed save
followed by navigation failure offers Open saved workflow without another write.
An uncertain creation disables repeat submission and names the attempted path for
Refresh/reconciliation. Workspace changes are disabled during the pending action.
Opening/reopening never starts a run. Existing draft protection remains unchanged.

Qualification includes duplicate clicks, lost acknowledgement, wrong-scope
receipt and reopening after navigation failure. Existing home navigation and
bridge denial checks remain required. Reuse the actual MCP/browser home harness;
no simulated owner result counts as source persistence. Actual Windows acceptance,
complete engineering demos and the broader repository gates remain separate.

Retained failures: state `wright-desktop-new-workflow-state-20261015-01` saved the
source successfully but the UI initially rejected owner-added instructions.
Readback reconciled the exact identity without replay. Corrected UI was checked
in fresh state `wright-desktop-new-workflow-state-20261015-02`. Its first browser
attempt proved creation/reopening but exposed the same raw-template assumption
in the text-preview fixture. Corrected fixture expectations use actual owner
readback. Both failed attempts remain preserved; no storage contract was weakened.
