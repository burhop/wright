# Printed02 handle geometry proposal

These are **unexecuted provider operation proposals**, not retained engineering
outputs or a qualified handle. `basis.json` preserves the original scenario,
six input hashes and unchanged full validation profile. `construction.json` and
`repair.json` contain separate, bounded `{"code": "…"}` arguments for the
independent Blender MCP. No original input was rewritten. Historical model
reports informed review only; no old geometry or image is supplied as new proof.

The intended provider is Blender MCP 1.9.1 at source
`5f8ddaf6e987c4aa0c3467fcc548838b28f64477`, with native Blender 4.3.2. Read its
[usage guide](../../../../docs/mcp-catalog/usage-guides/blender-mcp.md) and
[setup recipe](../../../../docs/mcp-catalog/mcp-server-setup-recipes.md#blender-mcp-blender-mcp-ahujasid).
The selected ARM64 readiness probe established discovery and a factory-scene
read; it did **not** qualify these operations, booleans, repair or preview.

## Geometry and review choices

The original 25 mm finger clearance and nominal 9 mm grip thickness consume the
entire 34 mm projection over the central 65 mm. The proposed bow therefore keeps
that span at Z=25…34 and places its curved shoulders outside X=15.5…80.5. Its
12 × 9 mm oval sections, modest Y arch and smooth 1.5 mm thumb depression retain
the requested intent within the original envelope. The depression occupies
X=28…68, with maximum depth at X=48; interpretation as a smooth depression,
rather than a flat-bottom pocket, needs the declared basis review.

The swept shoulders use a slightly conservative inner polygon radius
`3/cos(pi/96)` mm so their 24 quarter-circle facets stay at or outside R3.
Their centerline radius is about 7.501607 mm. Both original 18 × 24 × 5 mm pads
remain centered at X=0/96, Y=0, with planar contact at Z=0. Circumscribed
96-sided through cutters retain at least 4.5 mm clearance across their flats;
the largest vertex diameter is about 4.502411 mm. These are proposed numerical
constructions, not observations from an exported STL.

Native exact booleans join the pads and bow. Root bevels request R3 with native
overlap clamping; remaining sharp exposed edges request R1 without reducing the
requested width. **Neither setting proves an achieved radius.** Exact exported
sections must establish touched-edge rounds and identify any space-limited root
blend exceptions. Topology success alone cannot establish those requirements.

The legs' Y offset gives roughly 5.01 mm radial bolt access before blending.
Root blends can consume it. A proposed 10 mm washer seating/access reserve is
an explicit assumption, because the supplied context does not state washer OD
or thickness. It is not a measurement of existing hardware or a fit claim.
Observe the hardware and inspect the continuous postfillet seat and tool access;
do not shrink pads, widen holes or discard the blend requirement to invent a
pass. Sparse ray samples in the native report are diagnostic observations only.

## Bind and execute through the existing process

Both generic operations intentionally stop while `WRIGHT_HANDLE_OUTPUTS` remains
unconfigured. Before pinning a selected proposal, copy each asset and replace
only its `OUTPUT_ROOT` assignment with the reviewed absolute provider output
mount. The proposed host and provider share
`/tmp/wright-first-contact-084-native-777akcxz/wright-home/data/workspaces/handle-workspace`; the proposed
relative root is
`process-proofs/printed-replacement-part/printed-handle-084-first/outputs/{{wright.run_id}}`.
Keep the existing run token, distinct filenames and owned names. Pin the newly
configured bytes, retain the original assets and submit a visible new proposal
through normal preparation and source acceptance. The source runtime resolves
its declared run token; there is no implicit vendor-code or path rewrite.

The actual caller supplies the original `prompt.txt` as `user_prompt` without
paraphrasing or normalizing its CRLFs. That field belongs to the caller's
configured arguments; these generic assets remain code-only as required by the
existing preparer. Retain actual submitted arguments and provider responses.
Do not infer success from `isError:false`, output filenames or a partial file.

Use a fresh owned helper scene and fresh output directory. Operations refuse an
active native render or an owned-name collision; they do not clear unrelated
objects, add handlers/timers, access raw files, start subprocesses or bypass safe
mode. Source/export/preview paths must be within the explicitly writable mount.
An interrupted or timed-out operation requires inspection of durable run/native
state and retained files before any explicit new attempt. Do not replay an
uncertain export or render.

Construction emits the source STL and native observations. Repair imports that
actual source, merges only within 0.001 mm, removes degeneracy within 0.000001 mm,
recalculates normals, exports a distinct STL, then imports that exported file
again for measurement. It applies no build rotation or translation. The
geometry-only preview renders that reimported repaired STL in a separate owned
scene. Only after the render completes does it emit the existing
`W083_FINAL_REPORT` completion shape consumed by the passive repair reader.
It adds no runtime authority or success state.

Both operations inspect finite coordinates, topology, connectedness, positive
volume, triangle count, the full clipped central span, envelope, label keepout,
mounting-plane contact, sampled bore geometry, grip sections and shoulder
sections. Failures retain the attempted state and stop downstream work. These
checks are proposed code until a native run executes them successfully. The
0.00005 mm comparison bound handles floating-point representation; it is not a
manufacturing tolerance or permission to relax the original dimensions.

## Exact-output inspection and acceptance

Retain source/repaired hashes and the exact operation/response identities. Before
any slicing, independently inspect mesh intersections, pad and bore sections,
rounds, root blends, continuous washer seating/access and the requested visual
intent. The detailed measurement plan is in `basis.json`; unresolved features
stay visible at the declared persisted dimension/preview review. Native samples
and a completion marker do not replace that review or the original validation
profile.

After that review, compare real pads-down and side slices with unchanged P1S
0.4 mm PETG, 0.20 mm layer, five-wall and 40% infill profiles. Actual support
contacts and removability need separate evidence. This preview is not a support
or toolpath preview. Keep the original-frame repaired mesh as the validation
subject. Final transfer remains a labelled, digest-bound local simulation.
Physical fit, strength, fatigue, shrinkage and printing remain unverified.

## Local checks

Run only the bounded static/mathematical checks with:

```bash
.venv/bin/python -m pytest examples/process-interfaces/printed-replacement-part/handle-geometry/test_recipe.py -q
```

Seven checks passed on 23 October 2026. They validate original bytes/profile,
the exact pinned provider AST policy, code-size/run-token boundaries, pure sweep
topology and finite bounds, full central-span clearance, conservative shoulder
facets, thumb section and bore polygon. They do not import Blender or execute
native modeling code. The pure sweep has 23,164 triangles before pads, bores and
rounds; native output must still satisfy the unchanged 80,000-triangle limit.
Native construction, repair, export, preview and engineering acceptance remain
pending.
