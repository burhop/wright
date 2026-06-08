# Feature Specification: Chat Composer Commands

**Feature Branch**: `020-chat-composer-commands`

**Created**: 2026-06-08

**Status**: Draft

**Input**: User description: "We need a small + button to be able to upload files, list and run @ commands or / commands. Also, when typing @ or / we should get a pop up menu of the commands. What the commands are depends on the underlying agent system (Hermes, OpenClaw, Pi) so we need to be able to get this from the agent system to populate. We also have to be able to paste or drop images in the panel."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Context via Action Menu (Priority: P1)

Users need a visual entry point to add context, media, or run agent commands without memorizing keyboard shortcuts. A "+" button next to the chat input opens an action menu containing these options.

**Why this priority**: It establishes the foundational UI element for adding complex context and executing commands, making the feature discoverable.

**Independent Test**: Can be fully tested by clicking the "+" button and verifying the popup menu appears with options like "Add Context", "Media", "@ Mentions", and "Actions".

**Acceptance Scenarios**:

1. **Given** the user is viewing the chat composer, **When** they click the "+" button, **Then** a popup menu opens showing context addition and command execution options.
2. **Given** the popup menu is open, **When** the user clicks outside the menu, **Then** the menu closes.

---

### User Story 2 - Keyboard-Driven Auto-Complete (Priority: P1)

Power users need to quickly insert commands or mentions while typing without breaking their flow. Typing `@` or `/` in the input should trigger a dynamic autocomplete popup.

**Why this priority**: This is a core interaction pattern for modern chat applications and heavily relied upon by power users.

**Independent Test**: Can be tested by typing `@` or `/` and verifying the correct menu appears, populated dynamically from the currently active agent backend.

**Acceptance Scenarios**:

1. **Given** the user is typing in the composer, **When** they type `@` followed by a character, **Then** an autocomplete list of agents/mentions appears.
2. **Given** the user is typing in the composer, **When** they type `/` followed by a character, **Then** an autocomplete list of agent-specific actions appears.
3. **Given** the autocomplete list is visible, **When** the active agent changes (e.g. from Hermes to OpenClaw), **Then** the list dynamically updates to reflect the new agent's supported commands.

---

### User Story 3 - Paste and Drag-and-Drop Media (Priority: P2)

Users need a seamless way to add image context to their prompts by dragging images into the chat window or pasting them directly from their clipboard.

**Why this priority**: Enhances the user experience significantly, preventing the need to manually browse for files via the "+" menu every time.

**Independent Test**: Can be tested by pasting an image from the clipboard into the chat input, or dragging an image file from the OS into the chat panel.

**Acceptance Scenarios**:

1. **Given** the user has an image copied to the clipboard, **When** they paste (`Ctrl+V` / `Cmd+V`) while focused on the composer, **Then** the image is added as an attachment to the current prompt.
2. **Given** the user drags an image file over the chat panel, **When** they drop it, **Then** the image is added as an attachment to the current prompt.

### Edge Cases

- What happens when the agent backend is disconnected or errors out when fetching the list of available commands? (Should fail gracefully, showing an empty list or cached list)
- How does the system handle unsupported file types being pasted or dropped? (Should show a clean validation error to the user)
- What happens if the user pastes multiple images at once? (Should handle them sequentially or enforce a limit)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST render a "+" button adjacent to the chat input.
- **FR-002**: Clicking the "+" button MUST open a context menu with options for Media, Mentions, and Actions.
- **FR-003**: The chat composer MUST detect when the user types `/` or `@` at the start of a word.
- **FR-004**: The system MUST query the active agent backend (Hermes, OpenClaw, Pi) to fetch the list of supported slash commands and mentionable entities.
- **FR-005**: The system MUST render a dynamic popup menu filtered by the user's input following the `/` or `@` trigger.
- **FR-006**: The chat composer MUST intercept paste events and handle image data from the clipboard.
- **FR-007**: The chat panel MUST support HTML5 drag-and-drop events for image files.
- **FR-008**: Attachments MUST be visually represented in the composer before sending.

### Key Entities

- **AgentCommand**: Represents a slash command (e.g. `/plan`) supported by an agent, including its name, description, and execution context.
- **ComposerAttachment**: Represents a media file or context item attached to the current draft message.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can trigger the slash command menu via the `/` key or the "+" button.
- **SC-002**: The popup menu dynamically reflects the capabilities of the currently active agent.
- **SC-003**: Users can successfully drop an image file into the chat panel to attach it.
- **SC-004**: The feature is accessible using keyboard navigation (arrow keys to select commands, Enter to confirm).

## Assumptions

- The backend APIs for retrieving agent capabilities (`/api/agent/commands` or similar) will be implemented as part of this feature if they do not exist.
- Image uploads will be temporarily stored in the frontend state until the message is sent.
- We are only supporting image media for drag-and-drop/paste initially, not general files like PDFs or videos, unless explicitly supported by the backend.
