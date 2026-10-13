# Blender MCP: verified CAD presentation work

Recorded 12 October 2026. Independent provider:
[ahujasid/blender-mcp](https://github.com/ahujasid/blender-mcp).
Read the existing [setup recipe](../mcp-server-setup-recipes.md#blender-mcp-blender-mcp-ahujasid)
first. This example uses package1.9.1 and native Blender4.3.2 in a fresh selected
Linux container, through the existing native Windows Wright gateway. It does
not claim a new clean-Wright-container catalog qualification or physical tests.

The owned local registration is `7c90758c-7b5d-4de8-a997-b256afb445da`, with28
discovered tools. Its command executes the selected provider's `blender-mcp`
entry point inside `wright-stevecad-blender-render-002`. Network is disabled,
workspace input is mounted read-only, and temporary outputs are on tmpfs.
Provider source/versions and actual schema evidence live under
`artifacts/stevecad-demonstrations/qualification/blender-render-selected/`.
Telemetry and safe mode remain configured respectively disabled/enabled.

## Actual engineering handoff

SteveCAD revision7/build `780f3196-07b2-4590-b102-1cdd9a73b6cf` exported STEP.
An independent standard-format reader maps110 placed solids to exact native
bounds/volume and tessellates them. Blender MCP's supported `execute_blender_code`
tool imports those110 immutable STL files with `bpy.ops.wm.stl_import`, scale
0.001 metres per input millimetre. Actual imported bounds agree with the checked
STL bounds within0.0001mm. No CAD geometry is added or reshaped; a studio floor,
camera, material shading and lights are explicitly presentation fixtures.
Native EEVEE and Cycles file renders are produced from the actual geometry.
This is a substantive CAD-to-presentation handoff, not an invented AI model.

Native inputs, source checksums and successful operator-only import code are in
`robot-rev7-safe-import.json` and `safe-import-code.py` in the qualification root.
Native rendering receipts and unchanged generated PNGs are under
`artifacts/stevecad-demonstrations/robot-arm-media/corrected-rev7/blender-renderings/`.
Capture/root filenames alone do not establish success; inspect the returned body.

## Setup and scoped code

The automatic qualification now uses registered helper 004, server
`18094520-ff0d-4647-92da-2ae2eda5419b`, with an explicit read-only mesh input
mount and writable render output mount. Run
`646d7a74c124431e8979c3acea4b01de` rendered three 1000 × 720, 64-sample Cycles
views after the actual SteveCAD download and AgentCAD mesh export. All 110
actual vertex bounds matched the native reference within 0.1 mm. Receipts are
in `qualification/automatic-native-render-chain-007/`. Safe mode also rejects
`bpy.data.texts.load`: pass validated metadata as ordinary literal tool arguments
from the declared upstream formatter. No text datablock, eval, exec or raw socket
bypass is needed. Each fresh run uses a new owned scene and checks that no native
render is active before changing the scene or camera.

Start normal Blender under Xvfb; its add-on needs the application's event loop.
In this selected environment Docker `--init` was needed: the first owned
container started Xvfb but never launched Blender. Actual process/port checks
proved that state before only that helper was stopped; the second owned
container starts the native add-on at localhost9876. No existing campaign or
Wright process was stopped. The cached image contains real ELF executables,
and no MCP host software was installed in Wright's base image.

Use the observed code schema (`code`, `user_prompt`). The provider requests the
user's actual words in `user_prompt`; keep the same quoted task for a multistep
operation. Do not replace that field with an internal subgoal. Supported scripts
can import `bpy`, `mathutils` and allowed pure-Python modules, and use Blender's
native import/export/render operators. General `hashlib`/filesystem-reading
code was rejected by safe mode before execution. That was an authoring mistake;
the supported STL import operator subsequently succeeded. Safe mode was not
disabled and rejected code was not sent through the raw add-on socket.

Check transport status AND response text: a refusal or native error can arrive
with `isError:false` and a textual `result`. Require actual successful execution,
expected geometry counts/identity and output evidence. A tool listing or empty
scene read does not qualify rendering.

## Rendering and recovery

Use native sRGB appearance metadata, converted to linear shader inputs. Correct
exposure and lighting before accepting images; the first render was overexposed.
Keep simple servo/board envelopes as those actual shapes. Surface shading and
normal effects are appearance only and do not prove physical material/finish.
For each view derive orthographic scale from projected bounds of the110 CAD
objects, excluding the floor. Blender orthographic scale and image aspect ratio
must both be considered; a fixed scale clipped the first top image. Explicit
top-camera orientation avoids unintentionally reversing screen axes.

This build has no OpenImageDenoise support. A requested denoising render failed;
the supported Cycles render with denoising disabled completed. Preserve the
failure and actual host capability rather than modifying provider protocols.
A blocking gateway render request also timed out while native Blender later
saved the unique requested PNG in46.64 seconds. The native log and output file
were inspected before the file was retained; no render was resubmitted based
only on an observation timeout.

`bpy.ops.render.render('INVOKE_DEFAULT',write_still=True)` is the supported
asynchronous application operation. In the owned scene it returned
`RUNNING_MODAL`, with `bpy.app.is_job_running('RENDER')` true and the exact view,
source-build and destination recorded. Observe native completion before changing
the camera or invoking another render. This uses Blender's own job lifecycle;
it adds no Python handlers/timers or second Wright executor. A caller's scene
tag is correlation, not a provider-issued job ID or manufacturing authority.

For temporary native image files, Docker archive copy failed to access the
tmpfs file. A read-only `docker exec ... cat` byte transfer retained the exact
PNG without image editing. Treat this as operator qualification/retention;
future reusable process bindings still need their explicit artifact ownership
and existing file/image-output contracts. Do not silently substitute old PNGs.

## Known limits and bug triage

The viewport screenshot tool currently returns an all-black PNG in this selected
environment. Its native log explicitly says `No module named 'numpy'` and falls
back to a window grab. That identifies an unmet selected-host prerequisite;
it is not a confirmed provider defect. The initial scene-control capture and
its misleading robot filename are preserved with `initial-capture-scope.json`.
Do not present those black/control images as robot renderings or count them as
successful visual evidence. Native file rendering works separately.

Cloud/asset tools remain unqualified and network-disabled; no third-party asset
was downloaded. Rendering proves presentation of the supplied digital geometry,
not dimension compliance, physical printing, servo fit, drive transmission,
strength, payload, stability or powered operation. No new Blender bug was
reported. Follow the shared bug checklist before any report, and preserve
report IDs/receipts only after an actual supported submission.

## Verified durable native-file output

At05:34UTC on12October, an actual accepted two-step qualification completed in
6.302seconds on Wright's normal source runtime. It imported the110 immutable
revision7 meshes into a fresh selected native Blender, then wrote a640×480
16-sample Cycles PNG to one explicitly mounted workspace output directory.
The existing `expected_files` and `expected_file_ports` declarations recorded
the actual fresh PNG's bytes, SHA-256 and `render_image` port; the retained
runtime output hash equals an independent byte hash, and the PNG decodes.
No `mcp_image_outputs`, new executor, new backend code or model call was needed.

Evidence: `artifacts/stevecad-demonstrations/qualification/blender-file-handoff-001/`,
run`498f6f64564445a4a8787cdab529a6d1`, accepted digest
`6079dab7422b2422590ba94248b2179c1833e4cab4980184e5585106377857a2`.
The independent verification states this is a small file-handoff proof, not a
final studio image or the complete seven-stage process. Its input meshes were
prepared earlier; automatic exact-model export/tessellation remains upstream
work before the main workflow can use this rendering path.

For a direct `mcp-tool` declaration, `mcp_tool` must be the discovered gateway
name (`server_id__execute_blender_code`) and `mcp_schema_digest` the actual
discovered digest. A bare original tool name was rejected as unavailable, then
the unpinned corrected name was rejected as a changed definition. Both readiness
rejections occurred before native work; their sources/receipts are retained.
Use the API's revision-checked PUT with expected storage revision/digest to
correct an existing saved source; POST creates a new source. These were our
declaration/API mistakes, not provider defects or extra engineering approvals.

The fresh helper003 has read-only input geometry and only one output directory
mounted writable;002 remains separate with its final rendering assets. The
selected provider source, safe mode and network-disabled configuration remain
the same. Declared output ownership does not make mutable application state a
portable model artifact: require the exact upstream files and identities when
binding another design or run.

## Connected GLB handoff and selected-host prerequisite correction

The newer selected image `wright-stevecad-blender-selected-numpy:001`, SHA
`2efd64503c1b5525ec7b4f0fb90cf50662ae0ed9338232f21cf2b9dfed3cd4cb`,
adds NumPy2.3.4 only to `/selected/blender-py313-deps`. Native Blender's actual
Python is3.13.15, distinct from the MCP entrypoint's selected Python3.12. The
checksum-pinned CPython3.13 Linux wheel matches that native ABI. The bootstrap
adds the private dependency path; the original selected image and provider
source remain unchanged. Nothing was added to Wright's base image or runtime
extra. Dependency evidence and the exact wheel hash live under
`qualification/native-mesh-render-chain-001/numpy-dependency-pin.json`.

Fresh helper004 uses read-only GLB inputs and one writable image-output directory.
Its actual startup confirms NumPy2.3.4 and the native add-on ready. A qualified
supported `bpy.ops.import_scene.gltf` consumes the real connected mesh, applies
the observed0.001m/mm conversion and maps110 objects to source geometry. Restoring
supplied sRGB presentation colors replaces only the exporter's fallback palette.
Use actual transformed vertices for bounds; transformed local bounding-box
corners caused the first failed identity comparison. The prospective correction
creates a fresh owned scene only when no native render is running; it does not
restart or replay an uncertain job.

Run`7f626fb8ae424bfd9ec9d7910ad27be4` completed this actual three-task connected
AgentCAD→Blender chain in18.269seconds. The1000×720/32-sample PNG is a quick
presentation preview, not one of the selected final512-sample images. Runtime
GLB/PNG hashes, native FINISHED, all110 unique geometry matches and decoded
image checks pass. The original failed run remains. No model calls or new
runtime implementation were used. Read the [AgentCAD guide](agentcad-mcp.md)
for producer validation and the remaining automatic SteveCAD transfer gap.

The older black screenshot evidence is still retained. NumPy now satisfies its
known native prerequisite in004, but viewport screenshot success is not yet
requalified; native file rendering is independently proved. Do not infer a
screenshot pass, OpenImageDenoise availability or a full catalog pass from this
dependency installation.
