# Workflow Storage Contract v1

All calls receive a server-derived workspace identity. Paths are never client-supplied beyond validated workflow slug and sidecar name.

`create(title, initial_project) -> WorkflowSummary`  
`read(workflow_id) -> WorkflowDocument`  
`save(workflow_id, expected_revision, project, datasets) -> WorkflowSummary | RevisionConflict`  
`rename(workflow_id, expected_revision, title) -> WorkflowSummary | RevisionConflict`  
`delete(workflow_id, expected_revision) -> RecoveryRecord | RevisionConflict`  
`recover(recovery_id) -> WorkflowSummary`  
`rebuild_index(workspace_id) -> RebuildReport`

Validation failures are typed; no operation follows a symlink or escapes its workspace root. `RevisionConflict` includes current revision and digest, never project content unless the caller separately reads it.
