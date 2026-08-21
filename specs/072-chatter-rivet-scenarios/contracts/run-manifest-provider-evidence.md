# Contract: Rivet Run Manifest Provider Evidence v2

## Versioning

- New runs write Run Manifest `schema_version: 2`.
- Existing version 1 manifests remain inspectable and comparable as legacy MCP-shaped evidence.
- A version 1 binding cannot be silently upgraded to model evidence; reproduction requires a new review and version 2 run.
- The Loop 069 `capability-binding.schema.json` and `run-manifest.schema.json` resources remain byte-for-byte unchanged. Version 2 uses new `capability-binding-v2.schema.json` and `run-manifest-v2.schema.json` resources, selected strictly by the declared version.

## Binding evidence

Every binding contains the existing node, qualified tool, schema, validation and binding digests plus:

```json
{
  "provider": {
    "schema_version": "1.0",
    "provider_kind": "mcp | engineering_model",
    "provider_id": "stable provider identity",
    "capability_id": "stable provider-local capability identity",
    "resource_class": "small | medium | large | external",
    "evidence": {}
  }
}
```

For `mcp`, `evidence` requires server ID/revision, tool name, validation evidence ID and workspace grant digest.

For `engineering_model`, `evidence` requires model ID, package revision and manifest digest, variant and artifact-set digest, installation ID/digest, adapter ID/version, runtime version, mandatory-test evidence ID/material digest, workspace model-binding digest, task ID, input/output schema digests, threshold and resource declaration digest.

The union is closed and discriminated. Provider evidence participates in the capability binding digest, binding-set digest, review digest and Run Manifest digest.

## Child-call evidence

Every child call copies the provider kind and exact provider evidence digest from its reviewed binding and correlates:

- run, generation, authority, node, request, call and trace identities;
- child receipt and terminal state;
- input/output digests but not private values;
- authorized artifact references;
- cancellation acknowledgement and cleanup/residue facts.

A late provider response after authority revocation cannot change terminal state or publish artifacts.

## Reproduction comparison

Material differences include workflow/scenario, provider kind/evidence, package/runtime/vector, MCP validation, schemas, threshold, fixtures, inputs, results, artifacts, assertions, policy and cleanup state. Non-material differences include timing, observed RAM/CPU, request/trace IDs, timestamps and bounded host diagnostics.

Missing provider evidence, a kind mismatch, or any changed material digest returns `reproducible: false` with a stable review/retest recovery action.
