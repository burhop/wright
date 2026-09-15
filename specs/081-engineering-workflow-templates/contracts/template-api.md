# Template Catalog and Instance Contract

The engineering template catalog is a canonical-workflow resource. It does not extend the existing Rivet template format or endpoint.

## List templates

`GET /api/workspace/workflow-source-templates`

Response:

```json
{
  "catalog_version": "1.0.0",
  "templates": [
    {
      "template_id": "printed-replacement-part",
      "version": "1.0.0",
      "title": "3D Printed Replacement Part",
      "discipline": "Additive manufacturing",
      "summary": "Create and verify a printable replacement from an image.",
      "preview": {
        "asset": "templates/previews/printed-replacement-part.webp",
        "alt": "..."
      },
      "provided_inputs": [],
      "requested_inputs": [],
      "expected_outputs": [],
      "external_effects": ["printer_transfer"],
      "readiness": {
        "state": "setup_required",
        "definition_valid": true,
        "configured": false,
        "qualified": false,
        "available": false,
        "verified_run": false,
        "facts": [],
        "blocking_reasons": []
      },
      "source_digest": "64 lowercase hex characters"
    }
  ]
}
```

List is side-effect free, offline, stable in catalog order, and contains exactly ten active entries. It exposes no source bytes, credentials, absolute paths, stored approvals, or historic run state. The server derives readiness from current evidence/configuration.

## Get one template

`GET /api/workspace/workflow-source-templates/{template_id}?version=1.0.0`

Returns the list metadata plus the read-only canonical source preview, presentation preview, operation/capability details, assertion summary, provenance, and input-rights record. Unknown ID/version returns 404. Invalid packaged source makes the catalog fail closed rather than returning a partially trusted template.

## Instantiate

`POST /api/workspace/workflow-source-templates/{template_id}/instances`

Request:

```json
{
  "session_id": "current workspace session",
  "template_version": "1.0.0",
  "expected_source_digest": "digest read during preview",
  "workflow_path": "workflows/printed-replacement-part.workflow.wflow",
  "request_id": "idempotency identifier"
}
```

Response `201`:

```json
{
  "workspace_id": "...",
  "workflow_id": "fresh identity",
  "path": "workflows/printed-replacement-part.workflow.wflow",
  "revision": 1,
  "etag": "...",
  "source": "fresh canonical source",
  "layout": { "revision": 1, "positions": {} },
  "template": {
    "template_id": "printed-replacement-part",
    "version": "1.0.0",
    "source_digest": "..."
  }
}
```

The operation checks workspace/session/RBAC, exact preview digest and requested version, validates source/layout, replaces semantic identities, and atomically creates source, layout, and provenance. Existing target returns `409 workflow_source_exists`. A retry using the same request ID and exact request returns the same response; reuse with different content returns `409 idempotency_conflict`. It never overwrites, runs, approves, contacts a tool, or performs an external action.

## Readiness refresh

`POST /api/workspace/workflow-source-templates/{template_id}/readiness`

Request contains session ID and template version. This may inspect configured catalog/tool state with read-only operations. It may not install, authenticate, invoke mutating tools, create files, or promote qualification. The response uses the same readiness shape as list and records observed-at time and evidence links.

## UI contract

- Entry is **Start from template** beside existing New/Open actions inside the active workspace Workflows surface.
- The closed control shows its label, not a preselected template.
- Keyboard and pointer users can open the list, move among ten options, read each detail panel, enter a safe editable name, create, cancel, and return focus.
- Readiness and external effects use text plus icon/shape; color alone is insufficient.
- Required stable test IDs: `workflow-start-template`, `workflow-template-list`, `workflow-template-option-{id}`, `workflow-template-details`, `workflow-template-readiness`, `workflow-template-name`, `workflow-template-create`, and `workflow-template-cancel`.
- A created instance opens in the same established editor. The menu does not reduce or replace existing authoring controls.
