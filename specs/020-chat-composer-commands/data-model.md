# Data Model

## VaultFile
A file stored in the local file vault.
- `file_id`: UUID
- `filename`: str
- `mime_type`: str
- `size_bytes`: int
- `path`: str (absolute path on disk)

## AgentCommand
A capability exposed by an agent.
- `name`: str (e.g. `plan`, `clarify`)
- `description`: str
- `prefix`: str (`/` or `@`)

## ComposerAttachment (Frontend)
State representing a file attached to the current draft.
- `fileId`: string
- `filename`: string
- `mimeType`: string
- `previewUrl`: string (blob URL or backend URL for images)
