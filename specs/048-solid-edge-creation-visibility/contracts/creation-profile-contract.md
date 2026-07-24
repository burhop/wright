# Contract: Solid Edge Creation Profile

## Session selection

A host that intends Solid Edge creation opens its existing explicit Wright gateway session with profile `solid_edge_creation_v1`. The profile is immutable with the session's principal, workspace, and transport binding. A reconnect to the same gateway session must present the same profile.

Non-Solid-Edge sessions retain the standard profile. This feature does not define a general Solid Edge inspection profile.

## Tool projection

The v1 production allowlist uses exact SolidEdgeMCP child names:

| Class | Tool | List condition | Call condition |
| --- | --- | --- | --- |
| Validation | `cad.validate_recipe` | Allowed | `providerId=solid_edge`; no mutation |
| Creation | `cad.create_part_from_recipe` | Allowed | New document, confined output, visible/open result |
| Validation | `cad.validate_sheet_metal_recipe` | Allowed | `providerId=solid_edge`; no mutation |
| Creation | `cad.create_sheet_metal_from_recipe` | Allowed | New document, confined output, visible/open result |
| Validation | `cad.validate_assembly_recipe` | Allowed | `providerId=solid_edge`; no mutation |
| Creation | `cad.create_assembly_from_recipe` | Allowed | New document, confined output, visible/open result |
| Follow-up | `cad.rebuild_document` | Allowed only after creation | Target matches current session's created-artifact binding |
| Follow-up | `cad.export_document` | Allowed only after creation | Source matches binding; destination is confined |
| Follow-up | `cad.export_screenshot_views` | Allowed only after creation | Source matches binding; destinations are confined |

Wright-owned passive service health may be exposed separately and must not return active-document, feature, face, dimension, variable, measurement, capability, or semantic inventory.

Every other SolidEdgeMCP tool is hidden from `tools/list` and rejected by `tools/call`, including direct calls that guess a hidden name. Examples include document list/open/close/active-document operations, body/face/feature/variable/dimension lists, measurements, capability inventories, semantic reference discovery/resolution, observed-design preparation, and repair operations. Newly discovered or unknown Solid Edge tools are denied until reviewed into a new policy version.

## Creation call invariants

Before delegating a creation call, Wright validates:

1. The gateway session uses `solid_edge_creation_v1` and the target server is the configured SolidEdgeMCP server.
2. `providerId` equals `solid_edge`.
3. `outputPath` is explicit and its resolved canonical path is inside the bound Wright workspace and the configured SolidEdgeMCP allowed root.
4. `visible` is `true`.
5. `closeAfterSave` is `false`, unless the user explicitly requested closure of this new document.
6. `overwrite` is false unless the user explicitly authorized replacement of this exact output path.
7. The recipe mode is `commit`, represents a new document, and does not select an existing/active document.
8. A simple-part smoke has at most one validation call, exactly one creation call, and no follow-up or inspection call.

Any failed invariant returns an actionable policy or input error without starting the child operation. A provider validation or execution error is returned as-is after redaction and terminates the creation workflow. Wright must not switch to inspection or unrelated recovery.

## Canonical box request

The canonical 20 mm x 20 mm x 10 mm smoke recipe is:

```json
{
  "providerId": "solid_edge",
  "outputPath": "<absolute path under the bound workspace>/box-20x20x10.par",
  "visible": true,
  "closeAfterSave": false,
  "overwrite": false,
  "recipe": {
    "mode": "commit",
    "units": "mm",
    "document": "new",
    "steps": [
      {
        "type": "create_sketch",
        "plane": "top",
        "profile": {
          "type": "centered_rectangle",
          "center": {"u": "0", "v": "0", "unit": "mm"},
          "width": {"value": "20", "unit": "mm"},
          "height": {"value": "20", "unit": "mm"}
        }
      },
      {
        "type": "extrude",
        "distance": {"value": "10", "unit": "mm"},
        "direction": "positive_normal"
      }
    ]
  }
}
```

The provider's discovered JSON Schema remains authoritative for exact serialization. Wright's semantic checks are additive and fail closed if a required field cannot be proven.

## Successful result

A successful creation result must provide or permit Wright to derive:

- success outcome;
- provider/document identity when available;
- canonical saved output path;
- new-document evidence;
- visible/open-at-return evidence;
- provider issues/warnings in redacted form.

Wright creates a session-scoped `CreatedArtifactBinding` only from this successful result. File existence alone is insufficient for live visibility evidence.

## Errors

| Condition | Required behavior |
| --- | --- |
| Hidden/unknown tool | Return not-found or policy-denied without child call |
| Path outside workspace/root | Return confined-path error without child call |
| Existing file without exact overwrite authorization | Return conflict without child call |
| Invalid recipe | Return exact redacted validation issue; stop |
| Solid Edge unavailable | Return child-unavailable status; stop |
| Provider timeout | Return timed-out status; stop |
| Creation result lacks visible/open/new-document proof | Treat as failed verification; do not inspect ambient documents |

## Independent acceptance probe

For a bounded simple-part turn, record the projected tool list and gateway audit. Acceptance requires one `cad.create_part_from_recipe` terminal success, zero inspection/inventory calls, the requested confined file, a new visible/open document, and no state change to any document that was open before the turn.
