# Research

## Vault Uploads
**Decision**: Create a new FastAPI router `vault.py` to handle `/api/vault/upload`.
**Rationale**: Constitution Section 3 mandates a structured local file system vault. Adding a dedicated vault router keeps file handling isolated from agent session logic.
**Alternatives considered**: Adding it to `agent.py` or `workspace.py`, but files (images, STEP, STL) are agnostic to a single session and can be shared.

## Dynamic Command Autocomplete
**Decision**: Implement a floating `CommandMenu` component in the frontend using React state for the cursor coordinates to position it directly above the chat input.
**Rationale**: It provides a native IDE-like feel for typing `/` or `@`.
**Alternatives considered**: A static list below the input, but that takes up valuable vertical real estate.

## Agent Capabilities Discovery
**Decision**: Expose `GET /api/agent/commands` which returns a list of slash commands and mentionable entities supported by the currently active agent engine.
**Rationale**: Keeps the frontend agnostic of which agent is running (Hermes vs Pi).
**Alternatives considered**: Hardcoding commands in the frontend. Rejected because agent capabilities vary.
