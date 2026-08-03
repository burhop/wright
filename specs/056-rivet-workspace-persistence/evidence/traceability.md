# Requirements Traceability

| Requirement | Evidence |
|---|---|
| FR-001, FR-004 | `WorkspaceWorkflowStore`, `WorkflowRepository`, index rebuild test |
| FR-002 | `WorkspacePath` confinement plus slug and symlink checks; unsafe-slug tests |
| FR-003 | staged same-directory write with `fsync` and `os.replace`; stale-save trials |
| FR-005, FR-009 | delete/recovery storage tests and rollback evidence |
| FR-006, FR-007 | default-off API configuration and feature-flag tests |
| FR-008 | metadata-only `WorkflowIndexRecord` fields and repository test |
| FR-010 | this evidence set and documented Windows directory-fsync limitation |
