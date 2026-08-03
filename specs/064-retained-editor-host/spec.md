# Feature Specification: Retained Rivet Editor Host

**Feature Branch**: `064-retained-editor-host`  
**Created**: 2026-08-03  
**Status**: Draft  
**Umbrella base**: `9c0c19b` (`054-rivet-workflow-integration`)

## User Scenarios & Testing

### User Story 1 - Open a retained manual editor (Priority: P1)

A workspace user opens Rivet in an isolated retained workspace tab.

**Independent Test**: Opening the tab twice reuses the same workspace-bound retained editor and cannot open a second workspace's editor.

### User Story 2 - Use temporary browser import/export (Priority: P2)

A user opens and exports a project through Rivet's normal browser controls with a visible statement that Wright workspace files are not changed.

## Edge Cases

- A disabled, missing, corrupt, or conflicting editor artifact never starts a process.
- Closing the presentation does not grant file, gateway, secret, or execution authority.

## Requirements

- **FR-001**: Wright MUST expose the verified pinned editor only as an isolated retained workspace surface.
- **FR-002**: Wright MUST keep manual browser import/export non-authoritative and visibly disclose that it does not save into the workspace.
- **FR-003**: The editor MUST receive no workspace file, gateway, secret, or execution authority.
- **FR-004**: Disabled or unavailable editor behavior MUST leave Wright healthy and launch no process.
- **FR-005**: The slice MUST consume existing workspace-surface and editor-adapter contracts without changing authored workflow persistence.

## Success Criteria

- **SC-001**: A verified editor opens as an isolated workspace tab in a lifecycle test.
- **SC-002**: Reopening the workspace tab reuses the retained instance in automated coverage.
- **SC-003**: Automated checks prove that unavailable/disabled cases start no editor and manual mode offers no workspace save path.

## Assumptions

- This corrective slice starts from the latest umbrella commit and supersedes the out-of-order `063` candidate; it does not merge that candidate.
- Workspace-authoritative editor persistence remains the already-approved adapter/persistence path, not this temporary manual mode.
