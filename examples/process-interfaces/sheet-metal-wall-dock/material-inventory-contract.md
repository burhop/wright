# Native material inventory handoff — version 1

This workflow input contract resolves a reproduced R5 preparation defect: an AI
summary used `material_query.materials`, while the old profile expected
`materialsQuery.materials`. Neither field is the native provider's contract.

For this selected provider, bind the existing **cad.list_materials** MCP tool
directly with providerId=`solid_edge`, query=`5052`, offset=0 and limit=10.
Preserve its structured result as the inventory document. The currently observed
provider schema has `providerId`, `materials`, `totalMatches` and `hasMore` at
the root. Do not ask a model to rename or restructure that evidence.

Before intent or CAD, the existing validator must establish:

- providerId is `solid_edge`;
- totalMatches is1 and hasMore isfalse, so this particular bounded query has a
  complete, unambiguous result;
- materials[0].name is exactly the R1-permitted label, including its trailing
  space: `Aluminum Alloy:3.3523 , AlMg2.5, EN-AW 5052 `.

A changed provider schema or larger/ambiguous inventory requires explicit
rebinding or pagination before continuing. Missing fields cannot pass. This
contract does not grant material certification, H32 equivalence, density/strength
values or permission to manufacture. Actual material assignment is verified
again on the created native document. The final engineering review remains
required. Supplier stock selection continues to follow R1, separately.

This is configuration for an existing external tool and Wright's existing
validator, not a vendor protocol implementation. Earlier reports and profiles
remain unchanged. Use a new accepted source and run for the corrected handoff.
