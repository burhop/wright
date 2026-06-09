# API Contracts

## `POST /api/vault/upload`
Uploads a file to the local file vault.
**Request**: `multipart/form-data` with `file` field.
**Response**:
```json
{
  "file_id": "uuid-string",
  "filename": "image.png",
  "mime_type": "image/png",
  "size_bytes": 1024,
  "url": "/api/vault/files/uuid-string"
}
```

## `GET /api/agent/commands`
Fetches the supported commands for the active agent profile.
**Response**:
```json
{
  "commands": [
    {
      "name": "plan",
      "description": "Generate an implementation plan",
      "prefix": "/"
    },
    {
      "name": "clarify",
      "description": "Identify missing specifications",
      "prefix": "/"
    }
  ]
}
```
