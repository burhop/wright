# Implementation Plan: Chat Composer Commands

**Branch**: `020-chat-composer-commands` | **Date**: 2026-06-08 | **Spec**: [spec.md](file:///home/burhop/repos/wright/specs/020-chat-composer-commands/spec.md)

**Input**: Feature specification from `/specs/020-chat-composer-commands/spec.md`

## Summary

Add a modern chat composer UI that includes a "+" action button, dynamic autocomplete for slash commands (`/`) and mentions (`@`), and drag-and-drop/paste support for images. This requires creating a new file vault backend route for handling local image uploads, a backend endpoint to expose agent capabilities, and a new `CommandMenu` React component in the frontend.

## User Review Required

> [!IMPORTANT]
> The backend will be updated with a new `vault.py` router to handle local file uploads. These files will be stored in a `.vault` directory locally. Does this align with the project's offline-first mandate and storage preferences?

## Open Questions

> [!WARNING]
> Is there a specific styling preference for the `CommandMenu` floating popup beyond following the existing `index.css` tokens? Should it use a glassmorphism effect?

## Proposed Changes

### Backend (FastAPI)

#### [NEW] [vault.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/vault.py)
- Create a new router for file uploads.
- Implement `POST /api/vault/upload` to accept `multipart/form-data` and save the file to a `.vault` directory.
- Implement `GET /api/vault/files/{file_id}` to serve the uploaded files back to the frontend.

#### [MODIFY] [agent.py](file:///home/burhop/repos/wright/apps/api/src/api/routers/agent.py)
- Implement `GET /api/agent/commands` to return the statically defined capabilities of the agent (e.g., `/plan`, `/clarify`, `/tasks`, `/implement`).

#### [MODIFY] [main.py](file:///home/burhop/repos/wright/apps/api/src/api/main.py)
- Include the new `vault_router`.

---

### Frontend (React)

#### [NEW] [CommandMenu.tsx](file:///home/burhop/repos/wright/apps/web/src/components/chat/CommandMenu.tsx)
- Create a floating autocomplete menu component that takes a `filter` prop.
- Render a list of commands fetched from `GET /api/agent/commands`.
- Allow keyboard navigation (Up/Down) and selection (Enter).

#### [MODIFY] [MessageComposer.tsx](file:///home/burhop/repos/wright/apps/web/src/components/chat/MessageComposer.tsx)
- Add a "+" button adjacent to the chat input to toggle a context menu.
- Listen to `onChange` events to detect `/` or `@` and render the `<CommandMenu>`.
- Replace the selected command into the input state when clicked/entered.
- Add `onPaste` and `onDrop` event handlers.
- When an image is pasted/dropped, call a new `uploadFile` API and render an `AttachmentPill`.
- Modify the `onSend` callback to include `attachments` alongside the `message` string.

#### [MODIFY] [agent-service.ts](file:///home/burhop/repos/wright/apps/web/src/services/agent-service.ts)
- Add `uploadFile` method to POST to `/api/vault/upload`.
- Add `getCommands` method to GET from `/api/agent/commands`.

## Verification Plan

### Automated Tests
- N/A for this phase (component-level local testing).

### Manual Verification
1. Run `npm run dev` and `uv run ... uvicorn`.
2. Open the UI, type `/` in the chat input, and verify the menu appears and filters.
3. Select a command with the keyboard and ensure it prefixes the input.
4. Drag and drop an image into the chat window and ensure it uploads to the `.vault` directory and renders a preview pill.
5. Click the "+" button and verify the context menu triggers correctly.
