# Generic file transfer through mcp-shell-server

Observed 12 October 2026: independent provider
<https://github.com/tumf/mcp-shell-server>, version 1.1.12, source commit
`b71b694b463883fae4ae12dfb111d28a72c405da`. Provider source is unmodified.
This is a supporting file capability; CAD creation, measurement, mesh export
and rendering remain owned by their engineering providers.

## Verified boundary and setup

The native Windows Wright gateway initialized, listed and proxied the actual
`shell_execute` tool in a fresh minimal Linux container. A jq backend probe
returned 42. A durable connected-input canary passed in 3.440 seconds. This is
not a full clean-Linux-Wright catalog qualification or a production release.
See `artifacts/stevecad-demonstrations/qualification/generic-transfer-001/` and
`qualification/transfer-privacy-canary-002/` for exact arguments and receipts.

Selected image `wright-stevecad-transfer-clean:001`, image SHA-256
`963478d283a142f63b7cb377865a74eded05760b5d0ecfa80f685c80196ffbcc`, contains
Python 3.12, MCP SDK 1.30.0, h11 0.16.0, curl and jq. The container runs as UID
10001, with a read-only root, bounded tmpfs, no capabilities, no privilege
escalation, resource limits and only one fresh workspace output directory
mounted writable. No credentials or Docker socket are mounted. Entry point:
`python -c "from mcp_shell_server import main; main()"`. There is no `__main__`
module. Allow only the needed executable names: `curl,jq,sha256sum`.

The provider explicitly documents trusted execution: its command allowlist
does not constrain what allowed programs can do. OS isolation supplies those
boundaries. The selected internal network has no direct external DNS/route;
the explicit proxy allows HTTPS CONNECT only to `stevecad.studio:443`.
The disallowed-domain probe returned 403; direct external access failed.
The proxy has no published host port and does not log transfer requests.

## Successful calling conventions

`shell_execute` takes `command` as an argv array, optional `stdin`, optional
`directory`, and bounded integer `timeout`. Tool output is MCP text content. Wright's ordinary document output
port carries the MCP envelope; decode `.content[0].text | fromjson` when the
next jq operation needs JSON produced by a previous jq call. Output format and
output-port kind are separate declarations. Compile and inspect bindings before
dispatch; use `mcp_argument_ports` and actual item connections.

Use separate jq and curl tasks connected by a **text** output port. A literal
`"|"` argv entry selects the provider pipeline path, which ignores supplied
stdin in version 1.1.12 (verified in source and failed attempt 004). Do not use
a pipeline to carry a transfer credential. The validator also rejects literal
newlines in argv: keep jq programs on one line and encode embedded newlines as
JSON escapes. Semicolons are forbidden; for fixed-string substitution use
`split(marker) | join(value)` instead of a two-argument function with semicolon.
These are qualified calling constraints, not changes to provider source.

Native Blender safe mode rejects `bpy.data.texts.load`. Keep it enabled. A jq
step can read a declared nonsecret metadata artifact and return ordinary native
tool arguments from a fixed template with validated literals. Connect these
through `mcp_arguments_source: connection`; never add eval, exec, unrestricted
file reading or raw add-on socket calls.

**Observed limitation:** a program can exit nonzero and return stderr without
the provider setting MCP `isError`. A completed Wright run is therefore not
proof that the intended shell computation passed. Check exact output content,
fresh required artifacts and the downstream engineering producer's validation.
The first canary (`445963e66443498bb63a37ecf120eedf`) preserves this observation.
The corrected source unwraps the envelope; its exact output asserts that the
unredacted synthetic value was received, without returning that value.

## Transfer and privacy

Do not execute a returned shell command. In the accepted workflow, parse only
the documented HTTPS URL and header, check the pinned resource/revision/build,
and pass a curl configuration through stdin. Keep the one-use header out of
argv, source, prompts and saved outputs. The original export-instruction step
must not save its response. Use the exact scoped output destination, no redirect,
bounded transfer time/size, `--fail` and `--remove-on-error`. Downstream use must
depend on the freshly hashed actual file, not a written success claim.

Before real credentials, repeat the retained synthetic canary against any
changed persistence boundary. It proved current-run in-memory usability,
redacted run/event/API evidence, and no raw value in 265 scanned files including
runtime logs/database. This is a scoped observation, not a general secret-store
guarantee. Credential-bearing durable human-interaction continuations fail
closed; arrange expiring transfers within an uninterrupted declared section.

One-use transfers must not be replayed after an uncertain outcome. Inspect the
existing run, destination and provider response first. Do not stop an active
renderer or rebuild CAD because an observation request timed out. A new ticket,
fresh destination or source revision must be deliberate and identifiable.

## Remaining work

The actual SteveCAD export-to-three-view proof **passed in 62.007 seconds** in
run `646d7a74c124431e8979c3acea4b01de`, retained under
`qualification/automatic-native-render-chain-007/`. HTTP 200, exact STEP/GLB/PNG
hashes, native mesh validation and all 110 instance matches are verified. No
credential-bearing intermediate artifact is saved. Attempts 001–006 remain as
failure/recovery evidence, including pending native work observed to completion.
The generic per-design bindings subsequently completed inside main block v16,
including exact private STEP download, mesh validation and three native images.
See `prompt-to-reviewed-cad/block-native-003/native-run-audit.json`. Its final
review rejected the renderer's fallback appearance, so passing transfer is not
overall engineering acceptance. Full catalog clean-container qualification,
assembly main-process reuse, broader shell operations and physical actions remain
unverified. Changed-prompt block reuse now has actual same-source v19 evidence:
`block-native-006` and `six-hole-native-001` both complete exact private transfer,
mesh matching and six-image production. The latter retains an unrelated generated
intermediate-stock requirement as UNVERIFIED. See
`qualification/generic-render-binding-001/v19-reuse-audit.json` for source,
input, model-routing and producer-order checks.
No provider bug has been submitted. Investigate documented behavior and a small
reproduction before treating the nonzero-exit observation as a provider defect.

## Feature 084: native Orca capability probe, 23 October 2026

**Verified scope:** the same unchanged independent provider 1.1.12 at
`b71b694b463883fae4ae12dfb111d28a72c405da` initializes, lists `shell_execute`
and actually invokes official ARM64 OrcaSlicer 2.4.2 on a new 10 × 10 × 5 mm
fixture. This is direct isolated MCP evidence, not the current native
Hermes/Wright gateway, a complete handle process or clean Intel catalog proof.

Selected image `wright-084-orca-shell-selected:001` has digest
`71ac2d857b0aebcd4f5bfa76bfc26b6e9c380fe9d0eb5eecdaa6e94101c871af`.
The independent provider is installed in a separate Python 3.11 environment
with MCP 1.30.0 and h11 0.16.0. Native Orca is the official checksum-verified
ARM64 AppImage, extracted and mounted read-only. OpenGL/GLU and WebKitGTK are
installed only in this selected provider image; neither the host nor Wright's
base image changed.

The fresh container runs as the workspace user's UID/GID, has no network,
read-only root, dropped capabilities, no privilege escalation, 1 GiB memory,
2 CPUs, 128-process limit, bounded temporary space, and one feature-local output
mount. `ALLOW_COMMANDS` contains only `/opt/orca/AppRun`; no credentials or
Docker socket are mounted. The exact command, initialization, schema and
response are in
[`orca-shell-mcp-001.json`](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/orca-shell-mcp-001.json).

For multiple Orca profiles use repeated `--load-settings` flags, one path per
argument. The native parser supports the list, and the exported effective
settings prove both profiles applied. Do not put semicolons in a single argument
or change the provider's validator. With `--outputdir /work/out`, pass a basename
to `--export-3mf`: the failed direct attempt prepended the output directory to an
absolute export path. Its partial G-code and explicit package-export failure
were retained before a new destination was used.

The historical Bambu profile requires an **explicit candidate mapping** of
`tree_support_wall_count=-1` to Orca's `0`: both mean automatic in their pinned
engine definitions. Original profile bytes are retained. This single-field
candidate is not a silent engine substitution or accepted process revision.
The effective native output preserves P1S, 0.4 mm nozzle, PETG, 0.20 mm layers,
five walls, 40% infill and automatic tree supports. See
[`orca-candidate-profile-diff.json`](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/orca-candidate-profile-diff.json).

The MCP success response contains only an `XDG_RUNTIME_DIR` warning and
`isError:false`; it does not return the original slicer's `ok/source/output/plate`
receipt. Independent checks therefore require native `result.json` return code
0, fresh package bytes, intact ZIP, actual G-code motion and exact effective
settings. They are retained with the real files in
[`mcp-viability-001-output/`](../../../artifacts/first-contact/084/provider-readiness/mcp-viability-001-output/).
Read actual `OrcaSlicer` metadata: this engine also writes Bambu-compatible
application metadata, which is not evidence Bambu Studio executed.

The package's `support_used:true` metadata does not establish generated support
contact: the tiny fixture has no support extrusion segments and its filament
metadata says `used_for_support:false`. Native `--rotate-x 90` on the same tiny
input exited 139 before producing an artifact. One fresh diagnostic with Xvfb,
XDG runtime setup and debug logging also exited 139 before output. Rotation is
unqualified and no provider bug was submitted. These probes cannot stand in for the handle's two
orientations or support-contact evidence.

A retained bed-temperature warning accompanies 70 °C Textured PEI bed settings
and 230/245 °C nozzle settings. Those temperatures lie within the manufacturer
[PETG HF technical data sheet](https://store.bblcdn.com/s6/default/20423d7f839c4a66b9712508549c68b4/Bambu_PETG_HF_TDS.pdf)
ranges (65–75 °C bed, 230–260 °C nozzle, specified plate preparation). Preserve
the warning; this comparison does not validate material condition, adhesion,
strength, actual printing or external-action authority.

## Standard 3MF build-transform handoff, 23 October 2026

The first bounded standard-3MF candidate succeeds through the same `shell_execute`
boundary with the same candidate profiles and no `--rotate-x` option. Upstream
OASiS Python preparation writes the original tiny fixture mesh in its original
millimeter coordinates and an ordinary Core build-item rigid transform. This
uses [3MF Core matrix/build semantics](https://github.com/3MFConsortium/spec_core/blob/997b385e06f3181cf9aae0c578e0b45ccd48ccb2/3MF%20Core%20Specification.md#33-3d-matrices),
without Bambu-specific input extensions or provider implementation changes.

Evidence: [`orca-standard3mf-mcp-001.json`](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/orca-standard3mf-mcp-001.json)
and [`standard3mf-001-output/independent-checks.json`](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/standard3mf-001-output/independent-checks.json).
Original STL bytes/hash are unchanged. All 12 oriented source triangles agree
with the generated 3MF exactly. Orca recenters the exported mesh and records a
separate build rotation/translation. Composing its actual component/build
matrices, then applying the inverse source mapping, agrees with the original
oriented triangles within `8.89e-16 mm` against a declared `1e-6 mm` tolerance.
Keep raw and composed transforms; comparing raw native mesh coordinates alone
would incorrectly treat the slicer's recentering as altered source geometry.

Actual G-code contains 50 layers from 0.2 to 10 mm, compared with the unrotated
fixture's 25 layers from 0.2 to 5 mm. For this candidate all positive-extrusion
object paths are straight segments; their checked endpoint bounds cover the
centerline bounds. Native travel arcs are tracked as travel, not support.
The baseline contains five positive-extrusion arcs; its reported endpoint
bounds do not claim complete arc-extrema bounds. Preserve that reader limit.

G-code XY coordinates subtract the configured tool offset `[0,2] mm`; the
[pinned native conversion](https://github.com/OrcaSlicer/OrcaSlicer/blob/v2.4.2/src/libslic3r/GCode.cpp#L8123)
and actual profile support adding that offset for build-coordinate comparison.
Corrected candidate extrusion centerlines lie inside the transformed mesh
bounds. This is digital lineage/layer evidence, not bead-volume or physical proof.
The box has no support extrusion; support-contact capability remains unproved.

The exported native `source_file` names the intermediate `source-model-side.3mf`.
Preserve an explicit original-STL digest → prepared-standard-3MF digest → native
package digest chain, with geometry and transform checks at both handoffs. This
is not the original slicer's direct repaired-STL receipt and cannot silently
satisfy its unchanged operation/source-identity validator. The actual handle,
accepted binding amendment and side-to-final correction remain separate work.

## Installed native discovery, 23 October 2026

The pinned independent shell MCP now initializes through the isolated installed
Wright Tool Registry and exports its actual `shell_execute` schema. The final
command retains the qualified `HOME=/tmp/orca-home`, executable allowlist
`/opt/orca/AppRun` and 60-second provider limit. The original prepared mount
manifest's 360-second value was never adopted. A first unused registration that
omitted the HOME setting was replaced through the normal API; final identity and
exact command are in the [native configuration evidence](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/native-runtime-001/README.md).
The host workspace is mounted at the identical absolute container path and the
extracted official Orca image remains read-only. Discovery did not execute Orca;
it does not qualify handle slicing, support contacts or physical printing.

## Completed Printed02 source8 slicing handoff, 23 October 2026

**Verified:** installed native Wright run `f45755b659114ec6a746ceaa4f23b773`, source
revision 8, used this unchanged independent `shell_execute` provider to invoke
Orca 2.4.2 twice. Upstream standard 3MF build instances preserve the same repaired
STL in original model coordinates: identity for pads-down and +90 degrees X for
side. No native rotation workaround or new vendor protocol was added. The
[actual comparison](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/run-evidence/outputs/orientation-comparison.json)
binds pads-down package
`d19eedff7ee1131902fede4c0b3364968a8bae2e1ed75d5d35c8ecb7ee0acdeb`
and side package
`9133a77444971a5aca9b2b5ef55bbb4d1ffce074148c0023cd2bcd0e8b016ec9`
to exact source, prepared-model, G-code and support-view hashes. Pads-down is the
selected final package in this revision; side remains an actual comparison.

Check both native `result.json` return codes and the
[effective settings](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/run-evidence/outputs/effective-settings.json),
not MCP `isError` alone: P1S, 0.4 mm, PETG, 0.20 mm layers, five walls and 40%
infill are retained. The explicit support-wall -1 to 0 mapping remains visible.
Nominal support paths and interface locations inform review; counts, firmware
metadata and the conditional tool-offset interpretation do not prove physical
contact, removability or printing.

The [completed receipt](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/native-handle-final-019/final-validation/receipt.json)
records 43 passing checks over 17 subjects after the user's exact final review,
with physical validation `not_assessed`. The retained transfer receipt is only
an integration-test simulation with `network_dispatch:false`. Earlier source7's
[correspondence failure](https://github.com/burhop/wright/blob/dev/artifacts/first-contact/084/provider-readiness/handle-orca-correspondence-001/README.md)
was a shared-reader pairing error, not an established Orca defect; its failed run
stays failed. A new selected orientation requires an accepted revision and fresh
package/review/receipt bindings. Never replay an uncertain shell/native action
based solely on a timeout or reuse this run's authority for another package.

## Prepared ARM64 guest: scoped transfer connection, 28 October 2026

The first-hour campaign reused unchanged provider1.1.12 at the pinned commit
above without installing Docker or local CAD software. Existing bubblewrap,
curl and jq plus the immutable Wright118 runtime support a workspace-scoped
stdio binding. Native installation, initialize, tool discovery and workspace
enablement passed. An actual gateway call hashed the retained handle STL.
Remote download and saved-process handoff through this binding remain unverified.

The VM denies unprivileged UID mapping. Its existing sudo starts the mount
sandbox; setpriv drops to guest UID/GID1000, clears groups and prevents privilege
acquisition before provider execution. Generated `/opt` needs explicit0755
inside the sandbox: the private launch umask otherwise makes runtime config
inaccessible and misleadingly produces `ModuleNotFoundError: mcp`. Source/runtime
are read-only, only the target workspace is writable, and credentials are absent.
The guest network remains available; no domain-filtering qualification is claimed.
Exact scoped command, failed attempts and native receipts are retained in
[transfer setup125](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/workflow-transfer-125/RESULT.md).
This is a prepared candidate binding tied to runtime118, not out-of-box customer
setup. Preserve private-ticket handling and require actual artifact handoff before
claiming a saved CAD workflow is runnable.

### Actual saved STEP handoff in the ARM64 guest

The corrected binding completed a real saved Wright export→private-transfer→file→hash
chain in1.914seconds on28October. It retained621,468bytes with SHA256
`91b169b188c4c64534bd41e919adfc1f4a7994485c5ec4fd39aba094a86a5856`, matching
the existing unapproved handle revision5 export. No CAD redesign or engineering
approval occurred. [Actual run and failed attempts](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/cad-handoff-127/RESULT.md).

In addition to `/opt`, explicitly create sandbox `/etc` with0755 before its
read-only SSL/resolver mounts. Otherwise private umask prevented curl DNS even
though initialize/list and local hashing passed. The required-file runtime gate
caught the absent output; do not rely on this provider's MCP error flag alone.
Rediscover `workflow_tool_contracts` after changing registered provider identity:
Wright's binding digest includes the server identity, unlike the input schema alone.
The first corrected-source launch was rejected before starting a run because its
digest still named the old provider. The final corrected source and all failed
attempts are retained. This qualifies STEP transfer only, not ZIP extraction,
mesh repair, full first-contact usability or print readiness.

### Actual exported STL handoff, 28 October 2026

The same unchanged independent provider with dedicated `unzip` completed an
actual saved mesh export→download→member extraction→hash chain in2.597seconds.
It retained the real2,918,184-byte STL, SHA256
`d84a4f339e8c18272c7010da8fe4eea45b05972c70b5382cfa4912caa0403123`, matching
the existing unapproved preview. Archive and STL are distinct declared outputs;
extract only the expected body member into the run-owned destination. Do not
rename a ZIP to STL or substitute its hash for the mesh identity.

The guest lacked unzip. Installing the standard Ubuntu ARM64 package required
171kB download/503kB disk. A proposed general Python allowlist expansion was
rejected by automatic approval review and was not performed. The accepted narrow
configuration admits curl,jq,sha256sum,unzip inside the existing scoped sandbox.
[Actual evidence and integrated draft status](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/mesh-handoff-128/RESULT.md).
The full handle draft now declares CAD→exact export→STL and retains its original
mesh port and downstream requirements. This dynamic integration is saved but not
executed; geometry measurement/repair, analysis and print qualification remain.

## Prepared ARM64 guest connection,28October2026

Cached qualified Orca2.4.2 and independent shell1.1.12 now initialize through installed native Wright in the isolated handle workspace. Validation69e996769a3e49af9566ecd9bda73bcd passed; actual `/opt/orca/AppRun --help` returned OrcaSlicer2.4.2 through the public gateway. No model was sliced. Original profile preparation, independent inspection and full saved bindings remain pending.

Retain networknone, read-only root/application, scoped workspace, AppRun-only allowlist and the explicit60-second provider limit. No general Python executable was added. Guest image OCI manifestf451b7d4… has the same layers and meaningful configuration as retained source71ac2d85…. See [setup evidence](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/slicer-setup-136/RESULT.md).
