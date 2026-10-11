# Independent geometry preparation in existing examples

The printed-replacement-part preparer requires `--repair-binding` as well as its
[independent slicer binding](external-slicing-bindings.md). It proposes an accepted
process for Wright's existing compiler/runtime; it does not launch native software,
run repair locally or stage the retired native implementation.

The original three assignments, source stages, full validation profiles, material
and process basis, review identities and controlling inputs remain. The original
repair constraints are retained as
[configuration](https://github.com/burhop/wright/blob/dev/examples/process-interfaces/printed-replacement-part/original-repair-policy.json).
The 256 mm envelope belongs to this historical reference policy, not to generic
Wright inspection or a universal manufacturing requirement. A different process
declares its own requirements and qualified capabilities.

## Resolve the binding before staging

Supply one exact scenario, fresh workspace and attempt. The binding identifies:

- `schema_version: 1`, `scenario_id`, resolved absolute host `workspace_root` and
  relative `output_root` for this attempt.
- `provider`: actual registered `server`, original `tool` name and current gateway
  `schema_digest` from discovery/qualification.
- `arguments`: a regular bounded JSON object file identified by `path` and exact
  SHA-256. The independent provider owns native operation semantics and host paths.
- `machine_profile_sha256`: the exact selected machine profile from the separately
  qualified slicer configuration.
- `policy`: the original configuration, retaining JSON types. Exclude policy-file
  metadata `schema_version`, `basis`, `archived_operation_sha256` and
  `handle_triangle_limit`. For case 02 use that handle limit (24,000 triangles) and
  `planar_cleanup: true`; other original cases retain 80,000 and `false`.

Use [the declaration example](https://github.com/burhop/wright/blob/dev/examples/process-interfaces/external-mesh-binding.example.json)
as a field reference. Its placeholder paths/digests are not ready to execute.
Native arguments must already name the actual source and expected repaired STL
and geometry PNG paths under the provider's explicitly configured workspace.
This helper does not rewrite opaque argument code, infer mount equivalence,
generate a native recipe, install a provider or create a new MCP server.

Missing configuration, type changes, different attempts/profiles, changed argument
bytes, missing/ambiguous schemas and the retired bundled provider fail before
preparer staging. The retained policy plus supplied arguments alone do not prove
that a provider applies those semantics. Independently qualify that operation and
verify its actual outputs. The preparer retains provenance rather than granting
engineering acceptance.

Run the existing preparer with explicit `--scenario`, `--repair-binding`,
`--slicer-binding`, fresh `--attempt`, `--workspace-root`, `--draft-root`, and the
normal API/session/original-template source options. Accept the proposed source
through Wright. Staging does not enroll a test policy, approve a human checkpoint,
start a campaign or authorize a physical operation. The old private native campaign
launcher and `--repair-server` path are retired; there is no native fallback.

## Actual artifact handoff and measurement

The original repair block invokes the independent provider with exact connected
JSON arguments and declared source/policy dependencies. That producer owns
`repaired_mesh.stl` and `mesh-preview.png`.

A separate passive operation through the existing independent inspection provider
reads those actual bytes and the source STL. The staged inspection module is pinned
by SHA-256. Its configured workspace mount is explicit. The inspector produces
only `mesh-inspection-evidence.json`, preserving native artifact ownership.
An existing 082 validator step then measures the exact repaired STL again and
checks the pinned passive report. Its workspace profile is derived from the
original declared policy and content-pinned with its baseline. It directly checks
manifold integrity, connected components, signed volume, triangle count and
envelope using the existing bounded STL reader. Report-specific checks and the
original handle measurement remain explicitly labelled structured evidence.
Declared ordering holds the actual slicer until this backend gate passes.
Source, repaired geometry and package retain their original full validator roles.

A live negative control exposed why this explicit gate is necessary: a failed
inspection job can be returned inside a successful MCP transport response.
Transport success and the existence of a report do not authorize downstream work.
The gate uses exact artifact subjects through the existing validator and recovery
mechanisms. It does not infer global provider success from arbitrary status fields
or create another validator/executor. Missing evidence, failed measurements or an
unavailable required reader keep downstream work held with the actual assessment.

Passive measurements include finite binary-STL coordinates, exact shared edges,
connected components, degenerate faces, signed volume, bounds and the declared
triangle/build-volume limits. A positive signed volume is the original outward
orientation diagnostic; it is not proof of every facet's winding. The original
handle triangle clipping, 25 mm clearance and independent bore-section measurements
are retained unchanged. Bore diagnostics remain review evidence, not invented
acceptance tolerances. Mandatory failures retain available evidence and fail the
declared step. Invalid/truncated/over-limit inputs may fail before report creation.

Source inspection is bounded to one million triangles; repaired limits come from
the declared policy. Preview inspection is bounded to 16 MiB and 16,384 pixels per
axis. It verifies the PNG header/dimensions and file identity, not complete image
content, supports or slicer simulation. A native geometry preview and the actual
slicer package/toolpaths have distinct scopes. Human engineering review and physical
verification remain separate.

Historical correction qualification hashes refer to the exact archived operation.
They preserve the original construction history; they do not qualify a changed
provider recipe or approve current repair. Current independent operation, passive
measurements and full validation must establish the current artifact evidence.
