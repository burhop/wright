# Contract: Workspace Document Artifact and Requested Deliverable

This contract defines the narrow Wright-owned path for a Rivet workflow that
promises a text document. It does not grant general filesystem access and it
does not replace domain MCP tools for CAD, mesh, drawing, or other native
engineering formats.

## Typed requested effect

Every Graph Builder request carries one host-owned `requested_deliverable`
selection. The user confirms this value before generation; free-text model
inference is not an authority boundary.

```json
{
  "kind": "value_only | workspace_document | native_cad | stl_mesh",
  "label": "Design review notes",
  "suggested_relative_path": "reports/design-review.md"
}
```

Rules:

- `kind` is mandatory. The Graph Builder UI MUST NOT silently default a request
  to `value_only`.
- `label` is a bounded human description, not a path or authority token.
- `suggested_relative_path` is allowed only for `workspace_document` and is
  still validated by the artifact producer.
- The selected effect is retained with the Graph Builder preview and committed
  workflow revision so save and run validation use the same immutable intent.
- A model may propose a different effect, but only an explicit user selection
  changes the authoritative requested effect.

## Artifact-producing capability declaration

Tool bindings used as producers expose a Wright-owned declaration:

```json
{
  "effect_kind": "workspace_document",
  "artifact_output": true,
  "native_format": false,
  "required_approvals": ["workspace_write_approval"]
}
```

The declaration is part of the reviewed capability/binding projection. Graph
Builder MUST NOT infer producer authority from a tool title, description, path
string, or model-authored node title.

For `workspace_document`, the approved qualified tool is
`wright-workspace-files__write_text_document`. Native CAD and STL effects must
resolve to reviewed domain capability declarations and cannot be satisfied by
the generic document tool.

## Wright document tool

The in-process gateway capability is exposed through an ordinary Rivet MCP Tool
Call node.

Qualified name:

`wright-workspace-files__write_text_document`

Input:

```json
{
  "relativePath": "reports/design-review.md",
  "content": "# Design review\n...",
  "mediaType": "text/markdown",
  "overwrite": false
}
```

Rules:

- `relativePath` is UTF-8, bounded, relative to the bound workspace, and passes
  `WorkspacePath.resolve` containment.
- Absolute, drive, UNC, device, URL, traversal, alternate-data-stream,
  symlink/reparse, hidden, `.git`, and `.wright` paths are rejected.
- The extension and media type must be on the reviewed text allowlist. CAD,
  STL, PDF, archive, image, executable, and other binary/native extensions are
  rejected.
- `content` is valid UTF-8 text within the configured byte limit.
- `overwrite` defaults to and must remain `false` in the first contract
  version. Existing targets produce a stable conflict without mutation.
- Parent directories may be created only after every component passes the same
  path and hidden/reparse checks.
- Publication is atomic and fail-if-exists. A crash or cancellation cannot
  leave a partial target, and temporary residue is cleaned within the same
  confined directory.
- The tool requires `workspace_write_approval`; client hints and MCP
  annotations never satisfy it.

Successful result:

```json
{
  "content": [
    {
      "type": "resource_link",
      "uri": "wright://artifact/workspace-123/artifact-123",
      "name": "design-review.md",
      "mimeType": "text/markdown",
      "sha256": "<sha256>",
      "bytes": 2048
    }
  ],
  "structuredContent": {
    "artifactId": "artifact-123",
    "relativePath": "reports/design-review.md",
    "mediaType": "text/markdown",
    "sha256": "<sha256>",
    "bytes": 2048
  }
}
```

The resource link is emitted only after the file and its immutable artifact
record have both committed. Compensation removes a newly published file if its
record cannot be committed; it never deletes or overwrites a pre-existing file.

## Workspace artifact record

Each created document has an immutable SQLite record containing:

- `artifact_id`, `workspace_id`, and normalized relative path;
- SHA-256 digest, byte count, media type, and created timestamp;
- producer provider/tool, request/correlation identity, principal, and session;
- optional run ID linkage attached after the workflow run accepts the child
  evidence.

Artifact IDs are opaque and do not expose a filesystem path. Reusing an
artifact ID with different identity or bytes is rejected.

## Authorized read/open

- Gateway `resources/read` resolves an artifact only within the bound workspace.
- The Run Inspector uses a scoped, `Cache-Control: no-store` API read/download
  route keyed by run ID and artifact ID.
- The route requires the existing workspace/session identity, proves that the
  run manifest references the artifact, resolves the immutable artifact record,
  and verifies the current file digest before returning content.
- Missing, cross-workspace, cross-session, changed, expired, or unverified
  artifacts return a bounded not-found/integrity response without revealing
  another workspace's existence.
- Text may open in the existing safe workspace viewer. Attachment download uses
  a sanitized filename and the registered media type. No arbitrary path is
  accepted from the browser.

## Graph Builder, save, and run validation

For a non-`value_only` requested deliverable, the exact committed graph must:

1. contain a reviewed producer whose declared `effect_kind` matches the request;
2. retain its exact qualified binding and required approval;
3. supply every required producer input, including a valid relative path for a
   workspace document;
4. connect the producer's authoritative artifact result to the graph's declared
   output path; and
5. use domain producers for native CAD/STL effects.

Graph Builder blocks preview acceptance when these facts are missing. Save and
run preflight repeat the same model-free validation against the exact immutable
revision so editor or historical drift cannot bypass it. Diagnostics name the
requested deliverable, missing producer/dependency/approval fact, affected box,
and corrective action.

A successful scalar, object, LLM response, path string, or Graph Output value
without a registered artifact reference does not satisfy a file deliverable.
