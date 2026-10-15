# OASiS Open FEM Agent usage guide

Updated 15 October 2026. Status: historical Linux x64 protocol/backend/gateway
qualification retained; GB10 ARM64 installation/protocol verified, bounded scikit-fem backend checked; desktop engineering use unverified.

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

## GB10 ARM64 installation attempt, 15 October 2026

A fresh selected ARM64 container used the existing recipe with Python 3.12.12,
source 7c184d5b, MCP 1.28.1 and scikit-fem 12.0.2. After adding the documented Git
prerequisite inside that container, the resolver selected oasis-mcp 1.1.0 and
adios2 2.12.1.1001. The latter attempted a source build and failed at CMake
configuration because a C/C++ compiler was absent. No MCP initialization, tool
call or solver job occurred. The first missing-Git attempt and second build
failure are retained at `/tmp/wright-desktop-oasis-arm64-20261015-01` on GB10.

This is a missing selected-environment prerequisite, not a proved provider defect
or universal ARM64 incompatibility. Next is a bounded compiler-prerequisite test
inside a fresh selected container. Do not remove required dependencies, relax
pins or add compilers to the Wright base image to conceal the failure. The base
image remained unchanged. Historical Linux x64 results above remain separate.

## GB10 ARM64 corrected installation and protocol

The selected-container attempts established additional native-build prerequisites
for resolved adios2 2.12.1.1001: `build-essential`, `libssl-dev`,
`libcurl4-openssl-dev` and `pkg-config`. With these confined to the provider
container, the pinned installation completed on ARM64. OASiS source, MCP 1.28.1
and scikit-fem 12.0.2 were unchanged; NumPy resolved to 1.26.4 and meshio to 5.3.5.
The full dependency freeze is retained with the local attempt evidence.

Selected image: `sha256:a9df706fe1be647725b5101e68adf6fce11bcb34da19200eabd1a9848abf485d`.
A separate network-disabled container initialized OASiS 1.28.1 over MCP protocol
2025-11-25 and listed 17 tools. No tool execution or solver job was performed.
Backend registration messages are not evidence that every optional solver works.
The absent optional SPARTA knowledge file was logged; SPARTA is not selected.

Next qualification is the actual selected scikit-fem backend, independent field
checks and Wright gateway. Desktop enrollment and the original heat-spreader
engineering process remain unverified. Earlier failed attempts are retained.

## GB10 ARM64 scikit-fem backend, 15 October 2026

The retained 3D conduction script ran through actual MCP `run_simulation` for
synthetic fixed-temperature and total-resistance Robin fixtures. Keep outputs
inside the provider job directory: an initial absolute `/workspace/direct` output
root produced files but OASiS did not discover them and returned
`completed_unverified`. That attempt is retained. A fresh job with output root
`.` returned `completed` with four coarse/fine VTU fields. No submission replay
was used, and the original physics/script were unchanged.

Independent CSV checks covered all 135 coarse and 765 fine nodes per case,
finite values, 50 × 30 × 2 mm bounds, pointwise linear temperature and 1 W
conductive heat. Maximum pointwise error was below 3e-11 °C. Hot ends were
25.55555556 °C (fixed) and 25.65555556 °C (Robin). These compare the numerical
fields to the specified synthetic model, not physical validation. Recorded
CSV/VTU hashes matched; the independent checker did not decode VTU content.

OASiS correctly retained `trustworthy_result:false` and `critic_approved:false`:
its mandatory independent critic review has not occurred. The local evidence is
`/tmp/wright-desktop-oasis-arm64-20261015-01`, including both tool receipts and
`independent-field-check.json`. Containers exited normally. Wright gateway and
full desktop heat-spreader execution remain unqualified on this host.

### ARM64 gateway transport proof (2026-10-15)

A fresh synthetic conduction job (`1ed23738`) also completed through Wright’s
real `GatewayService` and `StdioRunner`, with a private fixture catalog and
workspace. The audit recorded one started and one succeeded tool call; the four
coarse/fine fields passed the same independent CSV analytical checks. This does
not qualify live enrollment or the desktop engineering workflow. Provider
`trustworthy_result` remains false and no critic approval was supplied. Evidence:
`prototypes/desktop-harness/oasis-arm64-gateway-evidence.json`. The initial
sandbox attempt could not reach Docker and dispatched no provider call; its
log is retained separately from the successful authorized host execution.
