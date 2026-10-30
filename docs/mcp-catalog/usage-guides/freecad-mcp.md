# FreeCAD MCP usage guide

Last updated: 28 October 2026. Status: native Printed02 handle construction and
Wright gateway handoff are verified in the retained source8/source9 digital
runs. The earlier strict STEP roundtrip probes remain failed. A fresh Ubuntu
ARM64 installation starts successfully. A focused original-handle CAD → mesh →
structural solve through Wright is observed below; engineering adequacy, mesh
convergence and a complete customer journey remain unverified.

## Identity and sources

Fresh prepared customer066 also completed catalog onboarding and a real read-only
`list_documents` call returning an empty list. Its [readable retained result](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-handle-engineer-066/result.txt)
binds the matching call/result records. This establishes that connection only;
it does not establish structural qualification or a completed handle journey.
Manual Hermes reload and result-label clarity remain reported friction.
In the matched connection-only [customer068 visit](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-handle-engineer-068/result.txt),
development candidate067 supplied the native-profile restart command successfully.
Restart is still manual; discoverability of the retained call remains a Wright
presentation issue, not an established provider defect. No time saving is claimed.

In [customer070](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-handle-engineer-070/result.txt),
Wright candidate069-r2 displayed the retained real request and empty response
beside the answer. The customer found and opened it without developer hints.
This is a prepared connection/use-visibility observation only; the original
feedback is unreviewed. Manual gateway restart remains. Guest notification
preparation differed from066/068, so elapsed time does not establish a causal
performance gain. No additional CAD/FEA qualification or provider defect follows.

[Customer074](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-handle-engineer-074/result.txt)
used a technically prepared local056 connection with14 actual discovered
contracts. It confirmed the connection active, but Wright rejected a workflow
operation-assignment edit before provider selection. No CAD/analysis operation
was performed in that visit. The failure belongs to Wright's source-preservation
path; it does not establish a provider defect. Runtime Hermes reconnect remained
necessary despite the prepared registry connection.

- Independent provider: [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp),
  MIT, source `63acb305573194a011641ab13ccfb391fe95769f`, package 0.1.18.
- [Existing setup recipe](../mcp-server-setup-recipes.md#freecad-core-freecad-core-nekanat)
  pins MCP SDK 1.28.1; the upstream open dependency range can select incompatible
  SDK 2.x. Provider and addon source must match.
- [Historical clean Linux AMD64 qualification](../evidence/curation-2026-09-09/freecad-linux.json)
  proves direct and gateway creation/export of a 10 × 8 × 6 mm box, 480 mm³.
  It does not qualify every native operation or this ARM64 environment.

## Installation and readiness

The selected ARM64 investigation uses cached image
`sha256:2d410f9187e5ae1d14410df89795ab1316a37e363d1f771172e7b4b4de5c972e`.
The default Wright supervisor was bypassed. Its Python 3.13.13 environment
contained MCP 1.29.0; this child loads the exact unmodified provider source and
cached MCP 1.28.1 from read-only mounts using `PYTHONPATH=/provider/src:/sdk`.
Import paths and versions were observed before use. The FreeCAD 1.1.1 ARM64
AppImage has SHA-256
`8004e166dc5c516cc8e8d85a5f58b5d56c3836cf8652301c2e6b9e4b1fd27827`.
Use a new owned container, network none, no published ports, fresh addon settings
and home, bounded resources, read-only root, and only the declared feature
workspace writable. Do not reuse campaign services or install CAD in Wright's
base image. FreeCAD runs under Xvfb; the unchanged addon exposes localhost RPC
9875 only inside that container. No credentials are required.

## Ordinary Ubuntu ARM64 setup

FreeCAD is a desktop application required by this provider. Installing the MCP
Python package alone does not install or start it. Keep FreeCAD open while Wright
uses the provider. The following operations worked inside a fresh Ubuntu 24.04
ARM64 desktop guest; they changed only that disposable guest.

First download [FreeCAD 1.1.1 for Linux ARM64](https://github.com/FreeCAD/FreeCAD/releases/download/1.1.1/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage)
into your Downloads folder. This is the ARM64 build, approximately 756 MB;
an Intel/AMD Linux computer needs its matching build instead. The
[official release page](https://github.com/FreeCAD/FreeCAD/releases/tag/1.1.1)
lists the available platforms.

You can use that browser link, or run the following in your desktop terminal.
If the file is already present, this verifies it without replacing it:

```bash
mkdir -p "$HOME/Downloads"
WRIGHT_FREECAD_IMAGE="$HOME/Downloads/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"
if [ ! -f "$WRIGHT_FREECAD_IMAGE" ]; then
  curl --fail --location \
    --output "$WRIGHT_FREECAD_IMAGE.part" \
    'https://github.com/FreeCAD/FreeCAD/releases/download/1.1.1/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage' \
    && mv -n "$WRIGHT_FREECAD_IMAGE.part" "$WRIGHT_FREECAD_IMAGE"
fi
printf '%s  %s\n' '8004e166dc5c516cc8e8d85a5f58b5d56c3836cf8652301c2e6b9e4b1fd27827' "$WRIGHT_FREECAD_IMAGE" | sha256sum --check -
```

Continue only when the check reports **OK**. If the download failed, run the
download block again; the incomplete `.part` file is not used for installation.
If an existing file fails its check, keep it separate and download the linked
ARM64 build before continuing.

The earlier observed installation used a cached, hash-checked application. The
official URL, size and published digest were checked on 28 October 2026 in the
[download metadata receipt](../../../artifacts/first-contact/synthetic-beta-003/receipts/freecad-download-metadata-103.json).
That check does not measure a customer's download time or qualify installation.
Use a new installation directory so an existing setup remains intact:

```bash
WRIGHT_FREECAD_DIR="$HOME/wright-tools/freecad-1.1.1"
WRIGHT_FREECAD_IMAGE="$HOME/Downloads/FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"
sha256sum "$WRIGHT_FREECAD_IMAGE"
# Require 8004e166dc5c516cc8e8d85a5f58b5d56c3836cf8652301c2e6b9e4b1fd27827.
mkdir -p "$WRIGHT_FREECAD_DIR/native"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  git python3-venv xvfb xauth libgl1 libegl1 libxkbcommon-x11-0 \
  libxcb-cursor0 libxrender1 libxi6 libxrandr2 libxinerama1 libxcursor1 \
  libxcomposite1 libxdamage1 libxtst6 libfontconfig1 libdbus-1-3 \
  calculix-ccx gmsh
git init "$WRIGHT_FREECAD_DIR/provider"
git -C "$WRIGHT_FREECAD_DIR/provider" remote add origin https://github.com/neka-nat/freecad-mcp.git
git -C "$WRIGHT_FREECAD_DIR/provider" fetch --depth 1 origin 63acb305573194a011641ab13ccfb391fe95769f
git -C "$WRIGHT_FREECAD_DIR/provider" checkout --detach FETCH_HEAD
python3 -m venv "$WRIGHT_FREECAD_DIR/venv"
"$WRIGHT_FREECAD_DIR/venv/bin/pip" install 'mcp[cli]==1.28.1' "$WRIGHT_FREECAD_DIR/provider"
cp "$WRIGHT_FREECAD_IMAGE" "$WRIGHT_FREECAD_DIR/native/FreeCAD.AppImage"
chmod +x "$WRIGHT_FREECAD_DIR/native/FreeCAD.AppImage"
(cd "$WRIGHT_FREECAD_DIR/native" && ./FreeCAD.AppImage --appimage-extract)
```

Install the matching addon into a new FreeCAD profile before its first launch.
If any destination already exists, preserve it and reconcile its version instead
of copying over it:

```bash
for WRIGHT_FREECAD_PROFILE in "$HOME/.local/share/FreeCAD" "$HOME/.local/share/FreeCAD/v1-1" "$HOME/.FreeCAD"; do
  mkdir -p "$WRIGHT_FREECAD_PROFILE/Mod"
  cp -R "$WRIGHT_FREECAD_DIR/provider/addon/FreeCADMCP" "$WRIGHT_FREECAD_PROFILE/Mod/FreeCADMCP"
  printf '%s\n' '{"remote_enabled":false,"allowed_ips":"127.0.0.1","auto_start_rpc":true}' > "$WRIGHT_FREECAD_PROFILE/freecad_mcp_settings.json"
done
"$WRIGHT_FREECAD_DIR/native/squashfs-root/AppRun"
```

Run the last command in the desktop terminal. The laboratory's preparation SSH
required `env DISPLAY=:0 XAUTHORITY=/home/customer/.Xauthority` before it; a
version-only invocation without a display failed, and `AppRun --version` with a
display opened an extra GUI instead of returning. The extra process was stopped
and the version read from the original running application. Ordinary desktop
terminals already provide their display environment; do not use `--version` as
a readiness check here. The running addon listens on
localhost port 9875; do not expose it to the network.

In Wright, connect the selected provider with the absolute executable path
`<installation directory>/venv/bin/freecad-mcp` and arguments
`--only-text-feedback --host 127.0.0.1`. The provider, GUI and files must be in the
same guest. Its ordinary installation was observed; this session did not yet
exercise Wright's installation UI, gateway binding or a customer journey.

The installed native versions were FreeCAD 1.1.1, CalculiX 2.21
(`calculix-ccx` 2.21-1), and Gmsh 4.12.1
(`gmsh` 4.12.1+ds1-1.1build2). Gmsh and CalculiX are prerequisites for structural
analysis, not for every CAD operation. The pinned provider's
`run_fem_analysis` uses an existing analysis with explicit geometry, material,
mesh, restraints and loads. Its tool parameter defaults to 600 seconds, but the
pinned XML-RPC client has a 150-second socket timeout. A timeout can leave the
native solve running: inspect retained state and working files before any retry.
Do not launch parallel GUI RPC calls while it runs. Solver summary values do not
establish adequate mesh convergence, realistic support/material assumptions,
compliance or physical strength.

[Session 032 readiness receipt](../../../artifacts/first-contact/synthetic-beta-003/receipts/gh3-handle-prereqs-032-readiness.json)
retains exact identities, install timings and the display correction. No geometry,
mesh or structural solve was created in that preparation, and the clean reusable
Hermes baseline was not changed.

## Calling and verification

The documented synchronous tool is `execute_code` with one string field `code`.
Use `--only-text-feedback` for the MCP process. Actual discovery/schema hashes
must be retained before binding. Native errors can appear in text content while
MCP `isError` is false; require the explicit native success result and inspect
fresh output files. STEP uses millimetres; STL is unitless and its agreed
millimetre convention must be explicit. Keep authored source, native file,
meshing parameters, exact output hashes and independent mesh checks together.

The selected native reports FreeCAD revision
`0108fd4b4850cc46e625b60e53cea7a7bbe69f8d`, OCCT 7.8.1. Actual discovery listed
14 tools. See [exact commands, schemas and outputs](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-native-001/README.md).

The successful STL capability uses a 4 × 3 mm rectangular section swept around
a 90-degree, 10 mm radius path. Explicit longitudinal edges 1, 3, 6 and 9 receive
R0.5 fillets; resulting toroidal faces report minor radius 0.5 mm. End rims remain
sharp in this fixture. Its native solid passes validity and the full BOP check.
`MeshPart.meshFromShape` uses absolute linear deflection 0.01 mm and angular
deflection 0.1 rad. The actual binary STL has 8,708 triangles, one closed/wound
component and bounds 12 × 12 × 3 mm. Independent parsing measures 185.045317 mm³
against native 185.124601 mm³ (0.043% difference). Separate native `Mesh.Mesh`
readback reports no self-intersections or nonmanifold/invalid mesh structure.
The normal installed native Wright Streamable HTTP MCP gateway reopened this
exact digest and repeated its mesh checks in 0.422 seconds. No model call ran.

FreeCAD validity, a successful tool
call and an existing STL do not establish the handle's dimensions, radii,
self-intersection freedom, hardware access, fit or strength.

## Pitfalls, recovery and authority

At this exact revision synchronous `execute_code` waits at most 90 seconds for
the GUI-thread operation. A timeout can leave native work in progress: retain
the request and inspect the existing operation/files; never blindly replay it.
The async tool is outside this qualification. Keep physical actions, reviews
and dispatch authority separate from modeling. No physical operation is allowed
by this guide. No provider defect has been established or submitted here.

Two stricter proposed STEP roundtrip gates remain failed, with original inputs
and outputs preserved. The circular-section sweep passed native BOP validity
but its exported STEP failed the reimported curve-on-surface BOP check. The
rectangular-section sweep passed native and reimported BOP validity and preserved
volume within 8.6e-14 mm³, but `Shape.BoundBox` reported 12.988706 mm maxima after
reimport versus 12 mm native/STL maxima. That assertion remains failed; its cause
is unestablished, and no STEP correspondence claim is made. Both actual STL
files independently pass topology checks and native mesh intersection checks.
The recorded positive qualification is limited to native solid-to-STL and the
gateway readback, which are relevant to Printed02's required construction output.
These observations do not establish an upstream defect or authorize changing
engineering tolerances.

The first private Printed02 construction candidate stopped at the one-solid
gate before fillets, bores or STL export. Its caller mistakenly ignored the
return value of `TopoShape.mirror()`. This method returns a new shape: use
`right = left.mirror(base, normal)`, then inspect its actual bounds before fusion.
The shipped `Part/parttests/TopoShapeTest.py` uses this assignment contract;
readback confirmed the failed candidate's supposed right shoulder remained at
the left location. This is an authoring error, not a provider defect. Retained
[candidate evidence](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-candidate-001/README.md)
does not establish handle construction capability.

A second authorized private candidate assigned that mirror result and verified
the right shoulder before fusion. The unrounded handle then passed native BOP
checks as one solid. Reopening the actual central-loft STL measured Z25–34 mm;
its 31,058 facets were solid with no reported self-intersections. The next
operation, an R3.05 fillet on the four selected concave pad-top edges, failed
with `BRep_API: command not done`. The exact edge set, classification method,
unrounded BREP and partial STL are retained in
[candidate002 evidence](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-candidate-002/README.md).
No smaller radius, repair or replay was attempted. A successful unrounded solid
does not establish required root/touched rounds or the final handle; native
fillet arguments are not geometric evidence. The particular failed operation
does not establish a general kernel limitation or provider defect.

Read-only inspection of that exact failed BREP found the short root arcs have
at most0.168102 mm of outward pad margin, while the long arcs have substantial
R3-permitting interiors but terminate at zero margin. This is a specific
space-limited transition concern, not a proven kernel failure cause. A full
quarter-circle root extending beyond the pad would introduce an exposed
zero-thickness underside rim and can reach the bolt opening; it needs an
explicit alternate design rather than silently clipping or reducing radii.
[Edge diagnosis and unexecuted alternatives](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-edge-inspection-002/README.md)
retain native measurements separately from numerical proposal calculations.

One separately authorized candidate lowered only the proposed baseline from
CY6 to CY2.8, removing the exact upper pad tangent while preserving R3.05 and
all gates. The root operation then returned a basic-valid solid, but the full
BOP check rejected it for self-intersection and C0 continuity errors. The
[candidate003 source, failure and root BREP](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-candidate-003/README.md)
are retained. No bores, touched-edge rounding or final full mesh followed.
Basic validity is insufficient; do not promote such an output or repair away
an unverified feature. No further construction or provider-defect claim follows
from this evidence.

Candidate004 used a visible revised numerical proposal with eccentric unchanged
size pads, constant circular roots and documented variable-section upper pipes.
Native BOP checks passed through the root, holes and touched-edge rounding.
The unchanged subsequent seam guard still failed at the two grip joins
(approximately2.29263e-5 rad versus its1e-5 rad threshold), before final STL
export. The [exact source, API contract and retained final BREP](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-candidate-004/README.md)
remain a failed full-handle qualification. A C1 approximation request or native
fillet success does not replace actual continuity/radius/output inspection.

Read-only candidate004 seam inspection attributes the mismatch to the central
loft's endpoint derivative, with sampled angles up to0.001258 rad. An explicitly
unaccepted diagnostic STL also exceeds the original facet limit:255,870 versus
80,000 at0.01 mm/0.06 rad. Its actual envelope/central clearance and native root
and provisional washer-volume observations are retained in the
[diagnostic evidence](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-diagnostic-004/README.md).
No passing mesh/intersection or hardware-fit claim follows.

For an exact rational conic, native `ellipse.toShape().toNurbs().Edges[0].Curve`
returned a periodic degree2 representation, whereas `ellipse.toBSpline()`
returned a degree14 non-rational approximation. Keep the
[observed representation and tensor API contracts](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-tensor-contract-004/README.md)
with any future authored operation. API availability does not qualify that future
surface, continuity, solid or exported mesh.

The first isolated exact tensor-grip qualification built the rational surface
and reduced its internal axial knots, but the resulting capped shell/solid
failed basic validity before full BOP or mesh export. The
[unchanged proposal and failed native body](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-exact-grip-qualification-001/README.md)
are retained. The shell/cap failure cause is unresolved; no cleanup or automatic
retry followed. Successful surface/API operations do not prove a valid solid.

Read-only inspection confirmed inward cap normals and matching cap/lateral edge
orientations. A fresh standalone trial with only explicit outward cap orientation
passed basic solid validity, then failed the unchanged full BOP check with two
edge and one face `GeomAbs_C0` findings. Both
[the orientation diagnosis](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-exact-grip-diagnosis-001/README.md)
and [qualification002 failure](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-exact-grip-qualification-002/README.md)
are retained. No cleanup, continuity-gate relaxation or full-handle replay ran.

A separate homogeneous-C1 conic proposal passed the standalone grip's native
closed-solid/BOP, endpoint-tangency and actual mesh checks. At unchanged meshing
settings its29,096 facets comprise28,584 lateral and256 per cap. The
[qualification003 evidence](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-exact-grip-qualification-003/README.md)
retains an unresolved0.00782% difference between native volume and the analytic
value; no exact-volume correspondence or full-handle qualification is claimed.
`Segments=True` provides per-face mesh groups without changing deflections.
A subsequent [read-only actual-surface comparison](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-exact-grip-field-003/README.md)
found maximum point error5.91e-14 mm against the native exact conic and authored
quartic fields across30,300 samples, including the end and thumb-join stations.
The volume discrepancy remains recorded without inventing a mass requirement
or attributing its cause.

Full [handle005](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-candidate-005/README.md)
used those C1 conics and passed all native solid/BOP and remaining-sharp-edge
checks, but its252,910-facet mesh exceeded the unchanged80,000 bound. A separate
[0.02 mm/0.06 rad comparison](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-mesh-comparison-005/README.md)
on the identical BREP still had239,910 facets. Per-face groups show the rounded
toroidal/spherical surfaces dominate this count. Both remain unaccepted; no
intersection claim follows a stopped facet-budget gate. Measured barrel-plane
clearance does not establish expanded mouth dimensions or hardware fit.

One separately authorized [0.02 mm/0.12 rad diagnostic](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-handle-angular-comparison-005/README.md)
on that same BREP produced76,926 facets and passed actual mesh intersection,
topology, finite/area, envelope and full-span clearance checks. Continuous
full-height bore clearance and separate barrel/mouth contours were measured.
Complete grip/root feature-contour qualification remains separate; this
diagnostic has not replaced the failed source or granted workflow acceptance.

A [fresh canonical construction qualification](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/freecad-canonical-construction-001/README.md)
executed the exact asset with only its run/output bindings supplied. Native and
independent mesh checks passed for its76,742-triangle source; three expected
files were published only after checks using exclusive per-file hard links,
observations last. Earlier in-progress inspection found all expected files
absent. This verifies construction/publication capability, with engineering and
physical acceptance explicitly false. Independent feature/repaired-output
verification and the accepted workflow's declared reviews remain required.

The80,000-facet limit referenced in these diagnostic logs is the preexisting
configured operation/shared-reader bound, not a triangle count stated in the
original customer context or prompt. It remains enforced during qualification;
changing it would require a separate explicit operational-budget audit.

## Maintenance

Fresh evidence belongs under
`artifacts/first-contact/084/provider-readiness/freecad-native-001/`.
The tiny-probe container was stopped and retained. A separately approved fresh
private-candidate container mounts only the dedicated handle workspace at its
same absolute host path; the old container remains stopped under
`wright084-freecad-tiny-retained-001`. Its registration command is unchanged.
Actual workflow use still needs a visible versioned construction binding;
a tool name does not grant access to another output path.
This selected ARM64/native proof is not a new clean Intel catalog qualification.
Retain failed attempts and historical platform scope when extending it.

## Completed Printed02 source8 handoff, 23 October 2026

**Verified:** the selected FreeCAD provider constructed the actual handle through
the installed native Wright gateway in run
`f45755b659114ec6a746ceaa4f23b773`, accepted source revision 8. This extends the
earlier limited probes; their failures and STEP limitations remain unchanged.
The [run inventory](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/run-evidence/receipt.json)
binds source STL
`f72ccd2198ecf3a742cac74446a4c1b1bce9482539e4036655db6b59abf89962`
and the native BREP to this run. Its
[native observations](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/run-evidence/outputs/native-geometry-observations.json)
record solid/BOP, explicit rounds and continuity, actual 76,742-facet export,
topology and full central-span clearance. Use the exact accepted `execute_code`
operation and run-bound outputs; successful operator arguments alone are not
feature measurements.

Blender consumed that STL for independent repair, measurement and rendering;
Orca then produced both orientation packages from the repaired geometry, with
OASiS providing supporting format preparation and passive inspection. The
[completed-run receipt](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/final-validation/receipt.json)
records 217 events and 43 passing checks over 17 subjects, including six
applications of the user's exact final review. Physical validation remains
`not_assessed`; this proves neither hardware fit, strength, support removability,
printing nor comparative superiority. A changed construction or selection needs
fresh downstream evidence. Reconcile an uncertain native operation before any
new attempt; do not retrofit this success onto earlier failed candidates or
claim a provider defect from them.

## Disposable Ubuntu ARM64 readiness, 25 October 2026

A fresh technical VM for synthetic-beta-001 installed the pinned provider 0.1.18,
MCP SDK 1.28.1, matching addon and exact cached ARM64 FreeCAD 1.1.1 AppImage.
The actual direct MCP `execute_code` exported the predeclared 10×8×6 mm box;
independent binary STL parsing measured 480 mm³, 12 triangles and closed edges.
[Preparation and direct-call evidence](../../../artifacts/first-contact/synthetic-beta-001/technical-freecad-probe.json)
and [independent output check](../../../artifacts/first-contact/synthetic-beta-001/technical-freecad-output-check.json)
retain exact requests and identities. This preparation used an explicitly copied
native cache and is not a normal customer installation, a Wright-gateway call,
handle execution or new clean-container catalog qualification. The temporary
technical guest was stopped; its installed tools are absent from the reusable
Hermes-only customer baseline.

## Prepared customer observation —27October2026

[Attempt037](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-handle-prepared-037/details.json)
reached normal registration after the host-label correction, but protocol
validation failed and the server stayed disabled. Initialize passed; the saved
evidence records CatalogVerificationError before the tools/list fingerprint
completed. Actual provider output schemas contain finite annotation bounds0.0
and1.0; the Wright validator used catalog-signing serialization that rejects
floats. The local038 correction separates dynamic MCP evidence fingerprints
from strict catalog signing. Its [direct installed operator retry](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/schema-038/README.md)
passed initialize, initialized notification and tools/list with14tools. The
registered server stayed active; workspace enablement and a managed engineering
run were not performed. Fresh customer confirmation is pending; no provider bug
or renewed catalog/ARM64 engineering qualification is claimed.

The same customer inspected separately generated native CAD, Gmsh/CalculiX
files and an inconclusive comparison. These were ad-hoc local tool work, not
a managed Wright engineering run. Coarse meshes failed; numerical convergence,
reaction balance and original geometric compliance did not establish an improved
handle. Exact files and failed attempts are retained privately. No physical
strength, printing or human engineering approval followed.


## Original-handle preparation through Wright — 27 October 2026

The [044 focused follow-up](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/connect-044/README.md)
renewed stale protocol evidence normally and enabled the existing provider in the
isolated workspace. Actual contracts came from wright__workflow_tool_contracts.
Two UI-launched Wright preparation runs used the original native BREP. Native
solid/BOP checks passed. The first failed grip selection: this trimmed spline's
ordinary BoundBox extends beyond its actual surface. A visible source revision
using optimalBoundingBox(False, False), with unchanged geometric thresholds,
passed that selector. It then failed the solid-correspondence check when splitting
the load surface. Volume/area differences disagree with empty Boolean subtractions;
cause remains unresolved. No original-handle mesh/solve or acceptance followed.

Both failures and exact inputs are retained. Do not relax correspondence limits,
transfer historical approvals or replay an uncertain native call. This extends
actual managed tool-use evidence, not clean-container qualification or completed
engineering capability. No provider defect is established by these authored
operation failures. Fresh customer confirmation remains pending.


## Original handle CAD → native solve through Wright — 045

[Focused result and evidence](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/partition-045/README.md)
retain source3 preparation run6d06c9a3 and two-stage runb73a4604. Original CAD,
96mm interface and material/load/support assumptions are unchanged. A Boolean
surface split had inflated the maximum CAD tolerance to8.855mm; native parameter-
space trimming preserves3.535e-6mm. Adaptive OCCT integration, using the native
bundled pythonocc binding, passes the unchanged area/volume limits. Missing this
binding stops preparation; do not substitute inaccurate measurements.

The UI-launched saved workflow prepared the actual CAD, meshed it with Gmsh and
called the discovered run_fem_analysis. It completed in78.48s. The66,734-node
coarse mesh reports0.48219mm maximum displacement and13.7393MPa peak nodal von
Mises. These are preliminary fields, not strength or mesh-convergence acceptance.
Actual deck load39.960263N and native reaction−39.960260N agree to3.03e-6N.
Moment balance, integration-point region statistics, refinements and human review
remain missing. Default native plots use SI legends (Pa andm); label converted
engineering values explicitly. Preview STL usesmm and grants no printing approval.

**Established integration defect, not yet corrected or externally reported:**
the pinned provider returns its initially created freecad_mcp_fem_* directory,
but native FemToolsCcx.run calls setup_working_dir again and writes into fcfem_*.
The reported directory was empty. Actual native files were bound to this exact
run by equality of all prepared/deck node coordinates and by the imported DAT
text hash, then preserved without rerunning the solve. The installed source
excerpts/hashes and minimal actual two-step workflow are retained in045. The
provider also calls load_results after native run already loads them; duplicate
result objects were observed. A correction belongs in the independent provider,
with its identity and qualification recorded; no Wright vendor workaround was
added and no upstream issue was sent.

Default output requests only displacement, nodal stress/strain and total support
reaction. It does not establish individual reaction moments or integration-point
stress statistics. Do not silently replace required quantities with nodal
percentiles. Retain native files before retrying. An initial presentation request
lost its connection; reconciliation found no presentation outputs and confirmed
the existing result objects. A separate file-bound operation produced actual
plots, preview geometry and a new saved result document, without solving again.
Its blank CAD screenshot is retained but excluded from normal views. Earlier
failed044attempts and the unrelated surrogate study remain separate.

### Separate local correction candidate — 046, bounded engineering use observed in 048

[Correction status and retained patch](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/output-046/README.md)
record the separately installed `0.1.18+beta046` candidate. It returns the actual
final native working directory and file hashes, removes duplicate result loading,
and adds an explicit `detailed_results` option to `run_fem_analysis`. The option
preserves the native deck before requesting individual reactions and integration-
point stress/coordinate output; native FreeCAD execution remains responsible for
the solve. It requires a static, single-deck analysis and rejects unsupported
input instead of silently changing it. No Wright executor or vendor shim was added.

Normal Wright protocol validation passed and all 14 tools were discovered with
the actual existing handle workspace/session binding. Standalone observer clients
must not inherit the global `wright-native` binding for this workspace: doing so
produced HTTP 400 before tool invocation. This is observed operator configuration,
not proof of a general customer defect. Do not repeat installation to fix it.

At the initial 046 checkpoint, only protocol availability was verified; detailed
engineering use had not run. Original provider files and
completed native documents were preserved before replacing the loaded addon and
restarting FreeCAD; no VM restart or credential change was needed. The pending
collection operation was intended to save a readable note alongside native files.

**Focused engineering observation, 048:** the separately installed candidate046
completed an actual original-handle solve through Wright. The three-stage workflow
prepared CAD/mesh, requested detailed native output and retained the exact files
and a readable note in 84.32 s. Its collection step verified full node equality,
one result object and file hashes. Native DAT includes per-node reactions and
integration-point stress/coordinates plus element volumes. This qualifies that
bounded handoff, not arbitrary provider operations, mesh convergence or strength.
See [the actual result and remaining limits](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/detailed-048/README.md).
Saved-response file handoffs require a workspace-file output and explicit
publication policy; preserve the failed authoring requests rather than adding
a hidden file lookup. The corrected run used `publish_overwrite` only under its
unique reserved run path. No existing output or review was replaced.

**Regional assessment and larger-mesh limit, 050–052:** a declared passive
assessment used the retained native integration-point fields and original CAD
partitions to calculate volume-weighted regional stress values and numerical
balance checks. The saved process completed in 20.77 s; its readable tables were
observed in Wright. See [assessment and remaining checks](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/assessment-050/README.md).
This does not establish mesh sensitivity, printed strength or review acceptance.

The unchanged finer model (151,670 nodes, 94,874 quadratic tetrahedra) prepared
successfully, but the guest kernel killed CalculiX for insufficient memory. The
MCP call also reached its 120-second gateway limit; neither timeout nor empty
partial files count as a solver result. Native FreeCAD then displayed a blocking
error notification, while passive document reads timed out. Retain native files
and inspect the GUI before replaying a tool call. The notification was eventually
acknowledged; successful recovery still needs observation. See the
[failed attempt](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/finer-051/README.md)
and [guest memory repair](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/memory-052/README.md).
No provider protocol or timeout behavior was changed in this repair.

### Deadline and console-retention candidate — 056–057, 28 October UTC

The memory-repaired finer solve produced native fields after Wright's 120-second
limit, so its failed run was preserved and the exact native model copied before
restarting CAD. See [retained late results](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/input-055/README.md).
Candidate `0.1.18+beta056` extends the separate 046 installation: a FEM call uses
its explicit GUI wait plus 30 seconds for its own XML-RPC socket; native
`start_ccx` still owns execution. Actual console streams, return code and timing
are saved before native import or failure dialogs. The declared collector keeps
those distinct filenames. The existing disposable-guest maximum is configured
to 360 seconds, with this task at 330 seconds and native wait at 300 seconds.
This does not change Wright's normal operation default or qualify all workloads.

Reopening `prepared-analysis.FCStd` creates document name `prepared_analysis`;
do not assume the former in-memory name survives. A failed opening assertion was
returned as text while `isError` remained false. Inspect native outcome text and
actual identity before proceeding. The initial focused run failed before solving;
the separately saved 057 retry is under observation. Original failed attempts,
actual contracts, patch and installed identities are retained in
[the focused retry record](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/deadline-056/README.md).
No external report, publication or renewed clean-container qualification occurred.

**Observed 057–058:** the corrected native call returned success, actual exit code
0 and retained console/exit files. Its console identifies **bundled CalculiX
2.23**, whereas the separately installed apt package is 2.21. Package inventory
alone did not establish the executed solver version. The full attempt took
192.86 s and then failed because an authored expected-file declaration required
nonempty stderr; actual stderr is zero bytes. The failure remains recorded.
Saved declaration059 corrects that requirement, retaining raw stderr in the
verified inventory; its full delivery route is not yet re-observed.

A separate declared passive assessment completed in 29.74 s over those exact
fields, without another solve. Full native COORD/EVOL reconciliation checks the
quadratic quadrature against this actual result. The readable working-view table
was opened successfully. See [fine assessment](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/assessment-058/assessment.md)
and [two-mesh comparison](../../../artifacts/first-contact/synthetic-beta-003/engineering-cases/handle/mesh-comparison-059.md).
The declared regional/displacement sensitivity limits are met; the raw stress
peak remains mesh dependent near fixed bores. Coarse-run console review, exact
geometry, engineering acceptance and a justified design revision remain separate.

**Observed 060–062:** the new installed Wright default permits explicitly longer
MCP waits up to600s, while ordinary calls remain30s and administrator overrides
retain authority. The temporary guest override was removed; actual gateway audit
records330000ms for coarse061. That focused solve and complete native-file/report
delivery completed in63.15s. The zero-byte stderr remains hash-bound in its native
inventory and is not required as a nonempty deliverable. Readable report was
opened in the working view. See [completed coarse delivery](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/coarse-061/README.md).
Its DAT and noncomment deck lines match the earlier assessed coarse evidence,
allowing exact numerical evidence reuse. Current coarse and fine native consoles
both identify CalculiX2.23, return0 and show no warning/error marker. This closes
the current baseline-console gap; the original missing-console run remains
historical. Engineering review and any changed-design evidence remain separate.

## Retained handle response-timeout observation — 28 October2026

[Prepared reliability085](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/reliability-085/README.md) used the unchanged coarse40N handle study and independent0.1.18+beta056 provider. Wright deliberately stopped waiting after5.206s; the native solver subsequently ran27.192s and returned0. One original request/solve was observed; actual DAT matches the retained original coarse result. Original Wright outcome remains unconfirmed and native files were recovered separately. [Corrected editor086](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/reliability-086/README.md) restores that exact saved state on reopen and prevents a blind repeat.

For diagnosis, inspect FreeCAD’s Report view and the actual solver working directory. `fea.run()` may replace the initial `/tmp/freecad_mcp_fem_*` directory with `/tmp/fcfem_*`; an empty initial directory does not establish failure. Retain the actual execution receipt, stdout/stderr, input deck and result identities before any new execution. Do not repeatedly call the GUI RPC while native work is active.

This provider has no durable job-ID/status/result contract for FEA. Wright’s saved-status refresh cannot automatically retrieve a response that the provider did not retain. `execute_code_async` is not a substitute for a solver job monitor. No generic async-provider qualification, engineering acceptance or revised-design improvement follows from this observation.


### Prepared analysis customer089 and native result handoff090

On28October a fresh prepared engineer ran the actual saved two-stage process once and reopened the report in10m09s. Workflow67.660s, native CalculiX27.168s/exit0; report0.482098mm maximum displacement and12.693470MPa peak nodal von Mises. This visit did not assess equilibrium/refinement or a revised design. [Actual prompt/report/screens](../../../artifacts/first-contact/synthetic-beta-003/run-details/gh3-handle-analysis-089/result.md). Original feedback remains unreviewed.

FCStd is a native archive, not text. Wright090 now shows download/open guidance instead of decoding it as text. Its UI download matched the39,648,431-byte actual native file. Open it in FreeCAD; use Fit All and the appropriate FEM result view as needed. This correction does not add native CAD rendering or launch FreeCAD automatically. [Installed affected observation](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/native-file-090/RESULT.md).
