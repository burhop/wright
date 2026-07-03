# Quickstart: Workspace Session Model Validation

## Goal

Verify that a workspace owns multiple sessions, session switching is chat-only, and MCP status follows workspace tool configuration.

## Scenario 1: Multiple Sessions In One Workspace

1. Start Wright API and web app.
2. Open an existing workspace.
3. Create a new chat session.
4. Send a short message.
5. Create a second chat session.
6. Confirm the session dropdown lists both sessions for the same workspace.
7. Switch between sessions.
8. Confirm only the chat transcript changes; file tree, open tabs, and viewer remain unchanged.
9. Refresh the page and confirm the same workspace lists the same sessions.

## Scenario 2: Sessions Are Workspace-Scoped

1. Create or open Workspace A.
2. Create two sessions in Workspace A.
3. Create or open Workspace B.
4. Create one session in Workspace B.
5. Return to Workspace A.
6. Confirm the dropdown shows only Workspace A sessions.
7. Return to Workspace B.
8. Confirm the dropdown shows only Workspace B sessions.

## Scenario 3: MCP Status Is Workspace-Scoped

1. Enable Onshape MCP for the Onshape workspace.
2. Enable a different tool set for another workspace.
3. Open the Onshape workspace.
4. Confirm MCP status references only Onshape workspace requirements.
5. Switch between sessions in the Onshape workspace.
6. Confirm MCP status remains tied to the Onshape workspace.

## Scenario 4: Legacy Data Migration

1. Start from a database with one existing `engineering_workspaces.session_id` value.
2. Run Wright after migration.
3. Open the workspace.
4. Confirm the legacy session appears in the workspace session selector.
5. Confirm enabled tools remain available for the workspace.

## Automated Validation

Run focused backend and frontend tests covering:

- workspace-to-session association migration
- workspace-scoped session listing
- session creation without overwriting workspace identity
- workspace-scoped MCP status
- chat session switching without resetting workspace panel state
