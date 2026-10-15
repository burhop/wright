# OASiS Open FEM Agent usage guide

Updated 15 October 2026. Status: historical Linux x64 protocol/backend/gateway
qualification retained; fresh GB10 ARM64 and desktop engineering use unverified.

## Identity and sources

Independent provider: [Hereon OASiS](https://github.com/Hereon-InstituteMS/OASiS).
Use the existing [setup recipe](../mcp-server-setup-recipes.md#oasis-open-fem-agent-oasis-open-fem-agent).
The pinned source is `7c184d5b7ca5cda6086f3912d1c7923c58307780`.
[9 September evidence](../evidence/curation-2026-09-09/oasis-linux.json) records
clean Wright Linux x64 qualification, MCP SDK/server 1.28.1 and 17 tools.
These are historical observations, not current hosted-service or ARM64 claims.

## Installation and readiness

Keep OASiS and its selected solver in an isolated provider environment. Do not add
solver software to Wright's base image. The recorded recipe uses Python 3.12,
MCP 1.28.1 and scikit-fem 12.0.2. Preserve the pins: the recorded source permits
incompatible MCP 2.x resolution and requires NumPy below 2. Clear child PYTHONPATH
because its generic `core`, `tools` and `server` packages collide with Wright.

Install only the selected backend. The lightweight scikit-fem conduction case
must not require every optional FE engine. Native CalculiX/Gmsh composition is a
separate selected-provider environment. Its example Dockerfile has an
installation-specific Python path; rediscover the actual path on a fresh install.
The provider must see the intended isolated workspace at `/workspace` for the
existing heat-spreader example. No credentials are specified by the retained
local recipe. SteveCAD authentication remains an independent prerequisite.

## Verified workflows and successful calls

Historical direct MCP initialization/tool discovery and `run_simulation` with
`solver=skfem` completed three fixed unit-square Poisson probes. Retained direct
and Wright gateway outputs were byte-identical VTU files, 237,184 bytes and 2,113
nodes. The independent oracle checked [0,1] square bounds, zero Z extent, finite
values, zero Dirichlet boundary and maximum phi 0.0735750773202. The Hermes-facing
gateway was also exercised. Use the exact retained probe and discovered schemas;
this result does not qualify an arbitrary solver script.

[Conduction evidence](../evidence/campaign-2026-09-12/oasis-conduction.json)
records separate 3D fixed-temperature/Robin probes. Nonempty fields alone did
not establish numerical correctness. A later
[native readiness fixture](https://github.com/burhop/wright/blob/dev/artifacts/stevecad-demonstrations/qualification/oasis-native-fea-002/provenance.json)
used OASiS's Python backend to invoke CalculiX 2.21 on a synthetic one-element
block. Its force reaction was observed; `critic_approved` and
`trustworthy_result` remained false. Do not call that a scikit-fem solve or an
accepted equipment-mount result.

## Pitfalls and recovery

Keep job IDs, raw result files and hashes. After uncertain submission, inspect the
same job before any retry. Historical controlled invalid Python produced no VTU;
a one-second Wright deadline retired the provider process group without an
orphaned solver. That bounded Linux x64 result is not a universal cancellation
guarantee. Native `ccx -v` returned 201 despite printing its version; a version
string alone is not solve qualification.

## Validation, authority and limitations

For the existing SteveCAD heat-spreader comparison, retain the original 40/60 mm
widths, 4 W conduction model, assumptions, genuine basis/result reviews and 082
exact-output validation. Its FE mesh is a dimensional rectangular idealization,
not arbitrary STEP meshing. Preserve coarse/fine fields and independent checks;
mesh agreement in a linear P1-representable field does not validate device physics.

Do not set `critic_approved:true` without the actual independent review. Neither
provider success nor this guide grants Wright tool permission or human approval.
The protected original waiting run remains untouched. Fresh GB10 provider use,
desktop task enrollment and the complete CAD-to-analysis chain remain open.

## Bugs and follow-ups

No new provider defect or report is asserted here. Compare exact inputs and
current discovered contracts before proposing a minimal redacted report through
the provider repository. Preserve uncertain outcomes and avoid duplicate reports.

## Maintenance

This guide indexes existing evidence without rerunning or upgrading the provider.
Next: qualify the pinned recipe in a fresh selected ARM64 environment, then the
actual backend and Wright gateway, recording platform-specific results before
using it in a new engineering run. Keep the historical evidence intact.
