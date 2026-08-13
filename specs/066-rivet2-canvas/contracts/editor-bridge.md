# Editor Bridge Contract v2

The Wright parent and Rivet 2 frame communicate only through `window.postMessage` using their exact configured origins. The frame receives no workspace credential, filesystem path, tool capability, or execution authority.

## Parent to Frame

### `wright-rivet:set-project`

```json
{
  "type": "wright-rivet:set-project",
  "requestId": "uuid",
  "project": "serialized .rivet-project text"
}
```

The frame parses and normalizes the project, then opens or replaces the active Rivet project through the hosted workspace API.

Terminal responses:

- `wright-rivet:project-set` with the same `requestId`
- `wright-rivet:error` with the same `requestId`, a stable error `code`, and a user-safe `message`

### `wright-rivet:get-project`

```json
{
  "type": "wright-rivet:get-project",
  "requestId": "uuid"
}
```

The frame serializes the latest active project from hosted lifecycle state.

Terminal responses:

- `wright-rivet:project` with the same `requestId` and serialized `project`
- `wright-rivet:error` with the same `requestId`

## Frame to Parent

### `wright-rivet:ready`

Sent once the hosted workspace bridge is ready to accept commands. The parent queues at most one latest project while the frame starts and sends it after readiness.

### `wright-rivet:project-set`

Acknowledges that the requested project became active. An acknowledgement for a stale request does not change Wright's selected workflow.

### `wright-rivet:project`

Returns the current serialized project for a matching pending save request. The parent ignores unknown, duplicate, expired, or wrong-origin responses.

### `wright-rivet:error`

```json
{
  "type": "wright-rivet:error",
  "requestId": "uuid",
  "code": "invalid-project",
  "message": "The workflow could not be opened in Rivet 2."
}
```

Allowed codes include `not-ready`, `invalid-project`, `open-failed`, `no-active-project`, `serialize-failed`, and `request-rejected`.

## Bounds and Security

- Both sides compare `event.origin` with the exact configured target origin.
- Both sides accept messages only from the expected peer window.
- Project text uses the existing workspace workflow size limits.
- Pending requests time out and are removed; late replies are ignored.
- The frame does not persist a global project catalog and does not open browser file dialogs.
