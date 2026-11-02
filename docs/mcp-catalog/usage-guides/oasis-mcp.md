# OASiS MCP usage guide

Last updated: 23 October 2026. **Verified:** direct isolated ARM64 MCP discovery
and one small scikit-fem solve with independently inspected output files.
Thermal-design acceptance and the current native Hermes/Wright route remain
unverified.

## Identity and sources

Independent provider: [Hereon-InstituteMS/OASiS](https://github.com/Hereon-InstituteMS/OASiS).
Read the [existing setup recipe](../mcp-server-setup-recipes.md#oasis-open-fem-agent-oasis-open-fem-agent)
and its retained qualification first. The recipe owns the earlier clean Linux
direct/gateway and timeout evidence; this guide does not replace that scope.

Selected source is `7c184d5b7ca5cda6086f3912d1c7923c58307780`, package
`oasis-mcp` 1.1.0, Python 3.12, MCP 1.28.1, scikit-fem 12.0.2, NumPy 1.26.4
and PyVista 0.49.1. The server's initialize version is its MCP SDK version,
not the package version. Cached image `wright-desktop-oasis-selected:20261015-01`
has SHA-256 `a9df706fe1be647725b5101e68adf6fce11bcb34da19200eabd1a9848abf485d`.

Evidence: [Feature 084 provider readiness](../../../artifacts/first-contact/084/provider-readiness/).
`oasis-direct-discovery-001.json`, `oasis-direct-skfem-status-001.json` and
`oasis-direct-poisson-001.json` retain actual initialization, schemas and calls.

## Installation and readiness

Run the unchanged installed module with `/selected/venv/bin/python -m server`,
empty `PYTHONPATH` and `PYVISTA_OFF_SCREEN=true`. Keep the recipe's MCP 1.x pin;
the provider imports that SDK API. No credentials or model API are required for
this fixed-script local solve.

The new selected container had no network, a read-only root, temporary `/tmp`
and a fresh writable output mount at
`/selected/venv/lib/python3.12/simulation_outputs`. No existing run directory
was reused. Initialization listed 17 tools. `discover` with
`{"query":"list","solver":"skfem"}` reports scikit-fem available; the other
backends are not installed on this image. Listing is not execution proof.

## Verified workflows and successful calls

`run_simulation` accepted the exact retained script in `input_content`, with
`solver="skfem"`, `job_name="wright084_poisson_probe_001"`, `np=1` and
`critic_approved=false`.
The script solves a dimensionless unit-square Poisson problem on 25 P1 nodes,
32 triangles, unit forcing and zero boundary values; it writes VTU and CSV.
This is a backend capability probe, not a material model or thermal design.

The provider returned job `4e7adb74`, completed in 1.24 seconds. Actual files
are retained in [oasis-poisson-output](../../../artifacts/first-contact/084/provider-readiness/oasis-poisson-output/),
including the exact script and native logs. Independent CSV checks find finite
values, bounds `[0,1] × [0,1]`, zero Z, 16 zero-valued boundary nodes and maximum
`0.07031250000000001`; hashes bind these checks to the actual output bytes.
Future downstream tools must consume those exact declared files, not a textual
completion message. Different geometry, mesh, boundary conditions, material or
script invalidates this proof for that new computation.

## Pitfalls and recovery

The result explicitly says `trustworthy_result:false` because the provider's
critic gate was not granted. Keep that value false: numerical output inspection
does not invent critic approval or Wright engineering acceptance. For actual
engineering, perform the applicable independent review and exact-output checks.

The selected read-only container reports a nonfatal session-journal save failure
under `/selected/venv/lib/python3.12/data`. Solver field files are independently
retained. If durable provider journaling is needed, declare a separate fresh
writable data mount; do not make the whole image writable. A missing optional
SPARTA knowledge file and a Pydantic annotation warning were observed; neither
prevented this scikit-fem solve. These are scoped observations, not confirmed
provider bugs. Observe the existing output/job after an uncertain timeout before
retrying; the current probe completed and was not resubmitted.

## Validation, authority and limitations

This ARM64 check did not use Wright's gateway or native Hermes, did not run the
heat-spreader example, did not exercise other solvers, coupling or visualization,
and did not qualify the current host under the separate clean Intel Linux
catalog procedure. It grants no physical or external-action authority.

## Bugs and maintenance

No provider bug report was submitted. Preserve exact schemas, arguments,
versions, native outputs and independent checks before attributing a new failure.
Recheck discovery and selected prerequisites after updating the source or image;
retain this dated evidence rather than treating it as a new version's proof.

## Standard 3MF preparation probe, 23 October 2026

Root explicitly authorized the existing Python backend for a bounded
standard-format preparation operation. The fixed script preserves the tiny
fixture's source STL bytes and oriented triangles, then writes a 3MF Core mesh
in original millimeter model coordinates with a rigid build-instance transform.
No FEM is performed or claimed. The script and exact call are retained in
[`oasis-standard-3mf-001.json`](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/oasis-standard-3mf-001.json)
and [`standard3mf-001-output/prepare.py`](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/standard3mf-001-output/prepare.py).

The Python process finishes in 0.06 seconds, but the provider warns about no
skfem import and returns `completed_unverified`, `output_files:[]` and
`trustworthy_result:false`: its FEM output recognition does not enumerate these
STL/3MF/JSON format artifacts. All three actual files are independently retained
and checked. Do not add dummy solver output, claim FEM verification, grant
critic approval or infer that its output list covers arbitrary formats.
Reusable process integration needs declared file ownership and actual file
checks, not a fabricated provider receipt.

The produced standard 3MF was consumed by the independent shell MCP and native
Orca without a native rotation flag. The actual native package preserves the
source geometry through its recorded component/build transforms within
`1e-6 mm`; details are in the [generic MCP guide](mcp-shell-server.md). This
tiny fixture proves a standard-format handoff. It does not qualify the complete
handle, its support contacts, physical printing or the native Hermes journey.

## Installed native discovery, 23 October 2026

The same selected provider now initializes with 17 tools through the isolated
installed Wright Tool Registry. The exact new command uses UID/GID 1000, network
disabled, a read-only root and the accepted workspace mounted at the identical
absolute path. Its provider output directory aliases the owned workspace's
`.provider-run/oasis-output`. See the [native configuration evidence](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/native-runtime-001/README.md)
for its registration command, schema digests and container snapshot. Initialization
does not establish script execution or writable output compatibility under this
new non-root configuration. Actual handle operations still require their declared
file checks; the earlier FEM output-recognition limitations remain applicable.

## Completed Printed02 source8 supporting inspection, 23 October 2026

**Verified scope:** installed native Wright run
`f45755b659114ec6a746ceaa4f23b773`, source revision 8, used the existing Python
backend for standard 3MF preparation, passive geometry/G-code inspection and
orientation comparison. FreeCAD and Blender supplied the actual geometry; the
independent shell provider ran Orca. **No FEM solve or FEM engineering result is
claimed for these handle operations.**

Retain OASiS's `completed_unverified`, `output_files:[]` and
`trustworthy_result:false` responses. Its FEM recognizer does not enumerate the
declared 3MF/JSON files, and no critic approval was invented. The
[pads-down inspection](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/run-evidence/outputs/inspect_slice_handoff-provider-response.json)
and [side inspection](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/run-evidence/outputs/comparison/inspect_slice_handoff-provider-response.json)
completed in reported 19.99 and 19.94 seconds; actual files are separately
digest-bound in the [run inventory](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/run-evidence/receipt.json).
The [comparison](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/run-evidence/outputs/orientation-comparison.json)
records exact source-to-prepared geometry and native/inverse error about
0.000001957154 mm, below the unchanged 0.0001 mm bound, plus both real layer views.
These are supporting inspection outputs, not provider-attested solver results.

Earlier source7 failed on a
[shared-reader sorting mismatch](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/handle-orca-correspondence-001/README.md).
The visible source8 binding uses the corrected deterministic bijection while
preserving winding, multiplicity and tolerance. Do not rerun a failed or uncertain
job blindly, waive correspondence, alter the provider's attestation or mark the
old run successful. Exact output inspection remains required even when the
provider process exits cleanly; no provider defect was established.

The [final Wright receipt](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/final-validation/receipt.json)
records 43 passing checks across 17 subjects, including six applications of the
user's exact final review; physical validation is `not_assessed`. The
[resource observation](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/final-validation/resource-observation/README.md)
retains 24,136,179 actual raw subject bytes under the cumulative 32 MiB cap.
The 1,000,000-entity limit applies to reader-supplied checkpoint counts, not a
total across all checks. A shared 120-second deadline is cooperative; the
512 MiB setting derives bounded input/measurement allocations and is **not**
an enforced process RSS/heap cap. These Wright validator limits are separate
from the external provider container's 1 GiB limit. No physical contact,
removability, hardware/strength, printing or comparative-superiority claim follows.


## Isolated handle workspace readiness, 28 October 2026

Reused the cached qualified image in the disposable ARM64 guest, with network disabled, read-only root, UID1000, 2 CPUs/1 GiB and only the selected handle workspace/output mounts. Native validation discovered 17 tools; an actual Wright gateway `discover` call reported scikit-fem available. No engineering script or FEM solve was run in this observation. Original printer/material/process profiles were hash-checked, not changed.

The image transfer took 75.614 seconds. Docker's imported OCI identity differs from the older source image identity; filesystem layers, architecture and creation match, while legacy container hostname and attachment configuration fields are omitted. Preserve this comparison rather than repeatedly transferring because the image ID differs. Receipts and limitations: preparation readiness (retained local evidence: `artifacts/first-contact/synthetic-beta-003/operator-retries/preparation-138/RESULT.md`). Engineering output and review gates still require their own evidence; discovery is not engineering qualification.

Local evidence references identify preserved operator records; they are not included in the public documentation build.
