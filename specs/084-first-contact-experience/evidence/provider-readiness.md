# T003 provider readiness: native ARM host, 23 October 2026

This is isolated digital capability evidence, not completion of the native
Hermes first-contact journey. Original Printed02 requirements, historical
profiles, validation identity and protected campaigns remain unchanged.
Root implementation owns the accepted binding and live Wright run.

Evidence root: [`artifacts/first-contact/084/provider-readiness/`](../../../artifacts/first-contact/084/provider-readiness/).
The structured [inventory](../../../artifacts/first-contact/084/provider-readiness/inventory.json)
separates configured identities, installed components and actual use.

## Observed route and limits

The host is Linux ARM64. Installed Hermes reports 0.20.0 (2026.8.3), source
`91937a6d`, with Python 3.11.15. Both the root configuration and the `wright`
profile request model alias `gpt-5.5` from provider `openai-codex`. No model call
was made; actual routing and upstream revision are unobserved. The existing
`wright` command is a launcher for `hermes -p wright`, and the installed legacy
plugin is not qualification of the current native lifecycle adapter.
The modern isolated runtime still needs root's installation and proof.

Sandbox process visibility did not establish that the host was idle. Unrelated
host Hermes/Wright processes and containers were observed and left untouched.
All provider calls below use new owned containers, network disabled, no mounted
credentials or Docker socket, read-only roots and explicitly scoped temporary
or feature-local outputs. No printer, transfer, protected-campaign, upload or
paid model operation occurred. No host software was installed.

## Blender and OASiS

Blender's cached selected ARM64 image starts a fresh native 4.3.2 application
with add-on 1.6/protocol 5, provider 1.9.1 and MCP 1.30.0. Initialization,
28-tool discovery and `get_scene_info` succeed against its factory Cube, Light
and Camera. This proves the direct read boundary; it is neither a handle model
nor current rendering/gateway qualification. See the updated
[Blender guide](../../../docs/mcp-catalog/usage-guides/blender-mcp.md).

OASiS's cached ARM64 image contains package 1.1.0 at pinned source
`7c184d5b7ca5cda6086f3912d1c7923c58307780`, MCP 1.28.1 and scikit-fem 12.0.2.
Initialization and discovery list 17 tools and one installed solver, skfem.
One fresh fixed-script Poisson solve produces actual VTU and CSV. Independent
CSV checks find 25 finite values, 16 zero boundary nodes, unit-square bounds
and maximum 0.07031250000000001. Actual files, script, hashes and logs are in
`oasis-poisson-output/`. This is a backend check, not the thermal example.
The provider's `trustworthy_result:false` is retained. The optional session
journal cannot write under the selected read-only root; actual field files are
retained on the scoped output mount. See the new
[OASiS guide](../../../docs/mcp-catalog/usage-guides/oasis-mcp.md).

Neither probe is the repository's full clean Intel Linux container qualification
or an actual native Hermes/Wright gateway run. AgentCAD's required selected
image was not found in the current host cache; no current-host AgentCAD proof
has been established. Existing catalog recipes and historical evidence retain
their original scope.

## Slicer availability and explicit compatibility gap

The historically qualified Bambu Studio 2.8.2.61 Linux asset is AMD64. No matching
native installation, cached slicer image or host x86 emulation was found. No
emulation or hardware configuration was changed.

Official GitHub release metadata provides an OrcaSlicer 2.4.2 ARM64 AppImage.
The downloaded 135,469,576 bytes match the official SHA-256
`e1a07275a25f176626c55a5df39e91bc4476d8c28ee4a3192ff758e29dd5c3ba`.
Native CLI help succeeds after adding OpenGL/GLU and WebKitGTK only to new
feature-specific selected-provider images. Failed prerequisite probes and
bounded build logs are retained. Nothing was added to the Wright base image.

A new 10 × 10 × 5 mm box was used to test unchanged historical Printed02
profiles. Machine is P1S/0.4 mm; filament is PETG HF; process is 0.20 mm,
**five walls, 40% infill and automatic tree supports**. The original process
profile name contains X1C; both Orca's native process and filament presets
explicitly include P1S compatibility, so the name alone is not the decision.
The native slice rejects `tree_support_wall_count=-1` before producing a result.
The failure and exact unchanged hashes are retained in `orca-slice-001.json`
and `orca-profile-inputs.json`.

Pinned upstream definitions explain the incompatibility: Bambu's `-1` means
automatic support walls; Orca's `0` means automatic support walls. A **proposed**
new versioned binding can explicitly map that one setting, retain all original
engineering requirements, and identify the actual Orca engine. It must not
silently mutate the historical profiles or claim `actual_local_bambu_slice`.
The original validator identity remains frozen pending an explicit typed
provenance amendment. Candidate native and direct-MCP results below do not amend it.

The already checked-out independent `mcp-3d-printer-server` 1.2.8 has separate
plain Orca and FULU/Bambu project paths: plain Orca emits G-code, while the
FULU/Bambu path exports a sliced 3MF. Official FULU Linux releases observed are
AMD64. Pointing its FULU selector at plain Orca would misstate the provider
contract. A proposed existing generic shell MCP binding could invoke the native
Orca CLI explicitly, but it requires real MCP discovery, scoped executable
allowlisting, exact native output checks and a visible accepted binding. The
engine viability probe alone does not qualify that route.

## Candidate result and actual independent MCP boundary

Root authorized a new copied profile with only the documented auto mapping.
Its digest and exact semantic diff are in `orca-candidate-profile-diff.json`.
The first candidate produced G-code but failed package export because this CLI
prepends `--outputdir` to an absolute export filename. A new destination with
the documented basename produced a valid sliced 3MF in 0.633 seconds. Its
effective native settings preserve every core Printed02 slicer requirement.

The unchanged independent shell MCP was then installed into a separate venv
in a new selected-provider image. Its real `shell_execute` call produced a new
package/G-code with native return code 0 and identical core effective settings.
The fresh container has no network, runs as the workspace user, drops all
capabilities, disallows privilege escalation, bounds memory/CPUs/process count,
and allowlists only the native Orca entrypoint. Repeated `--load-settings`
arguments preserve separate machine/process files without violating the
provider's semicolon restriction. Actual schemas, request and response are in
`orca-shell-mcp-001.json`; independently checked native files and hashes are in
`mcp-viability-001-output/`. See the updated
[generic MCP guide](../../../docs/mcp-catalog/usage-guides/mcp-shell-server.md).

This provider response has no `ok/source/output/plate` receipt. Completion must
depend on native return-code evidence, actual required files, exact settings,
source identities and typed engine provenance; the original Bambu validator
cannot simply accept this different envelope. No accepted binding was changed.

The package records Orca 2.4.2 and also writes Bambu-compatible application
metadata. The latter must not be mistaken for the actual engine. The fixture
has no actual support segments; a `support_used:true` metadata field alone
does not prove support contact. The handle and its support comparison remain
unqualified.

Native `--rotate-x 90` on the byte-identical fixture exits 139 before producing
artifacts (`orca-slice-004.json`). One fresh Xvfb/XDG diagnostic also exits 139
with no produced artifact (`orca-slice-005.json`). Both are preserved; rotation is not
qualified and a documented flag alone is not proof of correct model/build-frame
lineage. No provider bug report or source patch was submitted.

The retained native warning `bed_temperature_too_high_than_filament` is not
suppressed. Actual settings/G-code use a 70 °C Textured PEI bed and 230/245 °C
nozzle, within the manufacturer
[PETG HF TDS](https://store.bblcdn.com/s6/default/20423d7f839c4a66b9712508549c68b4/Bambu_PETG_HF_TDS.pdf)
recommendations (65–75 °C bed and 230–260 °C nozzle, with specified surface
preparation). This explains that retained temperatures need not be silently
changed merely to remove the warning; it does not grant physical acceptance.

The standard-format alternative below now has a tiny-fixture proof. A separately
rotated comparison STL still must not be silently promoted as the original
repaired mesh/final package lineage.

All short-lived probe containers auto-removed. The only longer-lived helper,
`wright-084-blender-native-001`, was stopped after checking its exact feature084
ownership labels; the cleanup receipt is retained. No unrelated service was
stopped. Selected images and feature-local inputs remain for reproducibility.

## Standard 3MF orientation remedy: first candidate passes

Root authorized at most two fresh slicing candidates using ordinary 3MF Core
build transforms. The first passes; a second is unnecessary. Original tiny-box
STL bytes/hash and model-frame geometry are unchanged. An isolated OASiS Python
operation prepares a standards-based mesh and one explicit rigid Rx(+90°)
build-instance transform with translation onto the bed. Source and inverse
matrices, original canonical oriented triangles and all hashes are retained.
The operation is format preparation, not a FEM result; the provider's FEM-only
output recognizer returns `completed_unverified`/empty output list. Actual
STL/3MF/JSON files are independently retained and checked without dummy FEM files.

The existing shell MCP invokes native Orca on that actual 3MF, with the same
candidate profiles and no native rotation option. Native result is 0; the
exported ZIP has real G-code and unchanged effective core settings. The exported
mesh is recentered, so checks compose its actual component and build matrices.
All 12 oriented triangles match expected world geometry and inverse-mapped
original geometry within `8.89e-16 mm`, below the declared `1e-6 mm` tolerance.
Original model bounds remain 10 × 10 × 5 mm; build bounds are 10 × 5 × 10 mm.

Actual G-code records 50 layers from 0.2 to 10 mm, versus the retained unrotated
fixture's 25 layers from 0.2 to 5 mm. Its straight positive-extrusion object
paths, corrected for the actual `[0,2] mm` extruder offset using pinned native
conversion semantics, lie inside the transformed mesh. This proves digital
orientation/lineage for the tiny fixture; no support is generated for this box.
The comparison reader explicitly marks baseline arc-extrema bounds incomplete.
Initial reader mistakes were fixed against unchanged native outputs, with no
new slicing attempt.

Exact receipts: `oasis-standard-3mf-001.json`, `orca-standard3mf-mcp-001.json`,
and `standard3mf-001-output/independent-checks.json`. The updated
[OASiS](../../../docs/mcp-catalog/usage-guides/oasis-mcp.md) and
[generic MCP](../../../docs/mcp-catalog/usage-guides/mcp-shell-server.md) guides
record successful calls, scopes and limitations.

Native `source_file` names the prepared 3MF. A future accepted binding must
represent original-STL digest → prepared-3MF digest → native-package digest plus
geometry and transform checks. This does not amend the original frozen
`actual_local_bambu_slice` profile, qualify the handle/support comparison, prove
the native Hermes route or complete the side-to-final correction journey.

## Native installation preparation: no current build or model call

The private preparation root is
`/tmp/wright-first-contact-084-native-777akcxz` (mode 0700). It contains separate
`hermes-home`, `wright-home`, `workspace`, `manager-temp`, and `wheelhouse`
directories. The fresh Hermes config contains the already requested
`gpt-5.5` / `openai-codex` selection, an empty plugin/MCP set and disabled startup
curator. No credential, existing plugin, session, or user environment file was
copied.

The installed Hermes Python 3.11.15 has no pip. A standard venv under this private
root supplied pip for downloading 59 binary dependency wheels (35,294,596 bytes).
An offline `pip install --dry-run --ignore-installed --no-index` resolves all 19
current base/runtime requirements and 59 distributions without installing them.
Hashes, versions, requirements, source hashes and launch settings are recorded in
[`native-install-preparation.json`](../../../artifacts/first-contact/084/provider-readiness/native-install-preparation.json).
The cache contains 17 Wright 0.1.9 wheels; the three newest sampled wheels contain
no `first_contact` paths and have no verified current-feature identity. They are
not substitutes for the integrated candidate.

The initially prepared private-home alternative was the following. The user's
later existing-profile decision below supersedes its authentication and plugin
selection; its wheel/build isolation requirements still apply.

1. Build the exact current candidate and frontend in an isolated source snapshot.
   `scripts/build-native-runtime.py --output <dist> --evidence <receipt>` runs
   `npm ci` by default and stages frontend/lock files even with
   `--skip-frontend-build`; it must not race edits in the shared checkout.
2. Freeze the unchanged current `hermes-plugin-wright` directory as a local Git
   candidate. With private `HERMES_HOME` and `TMPDIR`, invoke the installed
   `/home/burhop/.hermes/hermes-agent/venv/bin/hermes plugins install
   file://<adapter-candidate> --enable`. The existing native acceptance script
   demonstrates this install interface, but importing its lifecycle handler is
   not an ordinary CLI interaction proof.
3. Launch the actual Hermes CLI interactively in the private workspace and enter
   `/wright start`, then `/wright status`. Set `WRIGHT_HOME`, the exact local wheel
   in `WRIGHT_RUNTIME_ARTIFACT`, its `WRIGHT_RUNTIME_SHA256`, the prepared
   `WRIGHT_RUNTIME_WHEELHOUSE`, `WRIGHT_RUNTIME_CHANNEL=local_candidate`, and
   `WRIGHT_MANAGER_VERSION=0.20.0`. Choose/check an owned port immediately before
   launch. Open the returned packaged workspace URL and its Workflow control.
   Do not substitute `hermes -q '/wright start'`: the installed single-query path
   proceeds through model chat. No CLI launch or install has occurred here.

The private role must explicitly select `HERMES_PROFILE=default` and
`WRIGHT_HERMES_PROFILE=default`; the Wright SDK worker otherwise selects the
named `wright` profile. Linux requires both `HERMES_ROLE_PYTHON` and
`HERMES_ROLE_RUNTIME_ROOT`, pointing to the observed installed Hermes interpreter
and source. An explicit owned Hermes API endpoint and
`HERMES_API_DISABLE_DEFAULT_CANDIDATES=1` prevent unrelated default endpoint
discovery. The candidate wheel's final requirements still need comparison with
the prepared wheelhouse.

### Authentication ownership and the resolved route decision

The [redacted auth inventory](../../../artifacts/first-contact/084/provider-readiness/native-hermes-auth-readiness.json)
records credential presence and expiry only. Existing root and `wright` profile
stores each contain an OAuth credential-pool entry with a refresh token. Their
access-token expiries are in August and July respectively. This establishes
**refresh needed**, not an unavailable account: refresh-token validity and
actual model routing remain unobserved. The presence of an `OPENAI_API_KEY` key
in existing environment files does not authorize a route change. No resolver,
refresh, authentication copy or inference request was invoked.

Installed Hermes serializes Codex synchronization, refresh POST and persistence
with the credential owner's cross-process `auth.json.lock`. A worker using the
same existing owner can use this normal refresh mechanism. The current Wright
SDK worker resolves its named profile under inherited `HERMES_HOME`; it has no
separate credential-home selector. A private `/tmp` Hermes home therefore does
not inherit the real owner's credentials. The existing HTTP gateway can retain
its auth owner and supports session model locks in installed source; Wright
does not qualify that HTTP interface as tool-free UI authoring.

A supported Hermes project-plugin option exists:
`HERMES_ENABLE_PROJECT_PLUGINS=1` loads `./.hermes/plugins/wright` ahead of an
installed user plugin with the same name. Both existing root/profile configs
already enable `wright`. This can load the unchanged current adapter from an
owned working directory while leaving existing plugin files and selection
untouched. With the existing profile as `HERMES_HOME`, a new owned adjacent
Wright `HERMES_CONFIG_PATH` can preserve the same auth-file owner and confine
Wright's gateway-config writes. This is project-plugin provenance, not a fresh
Git-install proof.

`HERMES_CONFIG_PATH` is a Wright setting; installed Hermes itself reads
`HERMES_HOME/config.yaml`. Its interactive startup discovers the profile's
existing enabled `wrightgateway` and has `curator.enabled=true`. Those startup
effects and normal session/log writes are not isolated;
safe mode also disables the plugin, so it does not solve this distinction.
No supported separate Hermes user-plugin/config-file location was found beyond
project-plugin discovery.

The bounded follow-up establishes that the existing loopback gateway at port
8642 answers authenticated health and capability GETs as Hermes 0.20.0. Its
actual capability response reports `server_agent`, `tool_execution=server`, and
`split_runtime=false`. Installed `_create_agent` chooses toolsets and iteration
limits from gateway config rather than the request's `tools=[]`. Frozen provider
locks and Wright's observed HTTP request evidence do not remove that independent
executor. Root rejected this route for confined workflow intent calls. The
`/api/model/options` request was deliberately skipped: `refresh=false` controls
catalog caching but does not guarantee that an expired credential will not be
refreshed. See
[`native-existing-http-readiness.json`](../../../artifacts/first-contact/084/provider-readiness/native-existing-http-readiness.json).

The user explicitly selected **normal startup of the existing Wright profile**.
The selected route therefore uses the original `wright` profile and its normal
locked credential resolver, including refresh if needed; it does not copy an
OAuth grant or require a separate sign-in. Actual refresh success and upstream
routing remain unobserved until startup/model qualification.

The unchanged current 1.2.0 thin adapter's 13 tracked files are copied into
`/tmp/wright-first-contact-084-native-777akcxz/manager-project/.hermes/plugins/wright`.
From that owned working directory, the actual installed CLI is launched with
`-p wright` and `HERMES_ENABLE_PROJECT_PLUGINS=1`. Both `HERMES_PROFILE` and
`WRIGHT_HERMES_PROFILE` are explicitly `wright`; `HERMES_HOME` is the existing
`/home/burhop/.hermes/profiles/wright`. This is supported project-plugin discovery,
not an assertion that a fresh Git install has been exercised.

A new exclusive-create, mode-0600 adjacent file,
`/home/burhop/.hermes/profiles/wright/.wright084-native-config-777akcxz.yaml`,
contains only the existing model alias/provider and an empty Wright-owned MCP
mapping. `HERMES_CONFIG_PATH` points to it so Wright gateway configuration writes
remain separate while auth lookup has the same owner. The original profile
configuration hash is unchanged, existing plugin code fingerprints are retained,
and no credential file was opened or copied by this preparation. Hermes itself
still reads its original profile config and performs the normal startup effects
the user authorized. No existing environment key collides with the explicit
launch settings.

[`native-existing-profile-launch.json`](../../../artifacts/first-contact/084/provider-readiness/native-existing-profile-launch.json)
records the complete sanitized environment, unchanged plugin file digests,
original/new config fingerprints and pre-start process/container identities.
`WRIGHT_WORKFLOW_MODEL_TRANSPORT=hermes-model-sdk` explicitly selects the confined
model transport; the rejected existing HTTP executor is not the workflow route.
The launch manifest sets the unused HTTP surface explicitly to loopback 18642,
which was checked closed, and clears HTTP fallback candidates. It does not start
an HTTP Hermes service; incidental HTTP-only UI features may report unavailable.
Root subsequently built the integrated candidate at
`/tmp/wright-first-contact-084-native-777akcxz/dist-first/wright_engineering-0.1.9-py3-none-any.whl`.
Its verified digest is
`266a158a86997f439d77f9ec1c35b7f975cbb7e3f724239d58d1be494841f962`
and size is 17,519,664 bytes. An offline dry-run against this actual wheel resolves
60 distributions including Wright, without installing anything; see
[`native-candidate-dependency-readiness.json`](../../../artifacts/first-contact/084/provider-readiness/native-candidate-dependency-readiness.json).
Loopback port 18084 was bindable and released; the launch helper checks again
immediately before startup. Root owns actual CLI launch and runtime installation.
There has been no CLI startup, refresh or model call in this preparation task.

After root's authorized CLI startup and runtime installation, two probes of the
actual installed SDK worker failed before inference. The requested alias is
`gpt-5.5`, provider `openai-codex`, API mode `codex_responses`; the auxiliary client
and resolved model are null. The worker reports
`SCOPED_INVOCATION_UNAVAILABLE`. This is an authentication readiness failure,
not demonstrated model incompatibility. The sole original-owner OAuth pool
entry is exhausted and its access token expired; a refresh token is present.
Runtime resolution's token-present result is insufficient because the auxiliary
client performs normal pool selection and finds no available entry.

The installed `hermes auth` parser has no refresh command. Normal selection,
already exercised by the probes, excludes this entry during its default
one-hour cooldown. No targeted force refresh, status reset, copied grant,
provider change, HTTP bypass or inference request was performed. Immediate
supported recovery requires interactive `hermes -p wright auth add
openai-codex --type oauth --no-browser` using the original profile owner;
that flow has not been started. Cooldown expiry may permit a later normal
refresh but does not establish that the grant will recover. See the redacted
[`native-sdk-auth-readiness.json`](../../../artifacts/first-contact/084/provider-readiness/native-sdk-auth-readiness.json)
and its two installed-worker diagnostic references. These observations supersede
the earlier preparation-stage expectation that existing credentials might
avoid a new sign-in.

The user subsequently confirmed fresh Codex sign-in. Root's one installed
`/api/agent/models` check returned HTTP 200 and the configured
`openai-codex::gpt-5.5` option, with no inference request. The auth readiness
blocker is therefore resolved; the failed probes above remain historical
evidence. See
[`native-sdk-after-signin-001.json`](../../../artifacts/first-contact/084/provider-readiness/native-sdk-after-signin-001.json).

### Isolated locked frontend build

Root authorized a fresh `git archive` snapshot of commit
`9c874899a5cf5c191f7b1862fe1d8439754ceee3` at
`/tmp/wright-first-contact-084-native-777akcxz/locked-build-9c874899/source`.
`npm ci` ran at that snapshot's repository root, preserving the workspace layout,
local `process_client`/`ui_kit` dependencies and cross-package test fixtures.
The authoritative root lock digest remains
`0611297dd45b77001f7f3c2d25dce87c4b79bf21b9ceda3eff44060baa598c12`.
The nested `apps/web/package-lock.json` still pins SDK 1.30.0 and was not selected.
The isolated installed SDK is 1.32.1. No shared `node_modules` was replaced or
linked into the snapshot.

Installation passed in 9.391 seconds and the existing TypeScript/Vite production
build passed in 24.504 seconds with all four native frontend flags enabled.
The 15 output files and installed dependency manifest digests are retained in
[`native-locked-frontend-001/build.json`](../../../artifacts/first-contact/084/provider-readiness/native-locked-frontend-001/build.json).
No output was promoted to the repository or running native installation, and no
broad tests or native packaging ran in this task. Node 22.22.0/npm 11.10.1 were
used. The preserved install warning states that locked `jsdom` 30.0.1 needs
Node `^22.22.2 || ^24.15.0 || >=26.0.0`; a compatible isolated Node is required
before claiming the full test gates. The production build also retains its
existing large-chunk warning. Neither warning was suppressed.

The client error-envelope correction was independently reviewed against the
actual installed thermal 422 response and the API's shared handler: validated
`details.reason` now reaches the common view alongside the existing
`detail.reason` form. Arbitrary diagnostics remain hidden, and uncertain-action
handling/retry behaviour is unchanged. After the owner's seven focused passing
tests, only `packages/process_client/src/client.ts` and
`apps/web/src/services/process-client.spec.ts` were copied into the isolated
snapshot, with their base and changed hashes retained. One incremental build
passed in 26.309 seconds without repeating installation; SDK 1.32.1 and the root
lock digest remained unchanged. Its exact 15-file inventory digest is
`90e9e899dc834f893265ecf00ac339350277593e14ab3b00c541c49e99cee6c1`;
see
[`native-locked-frontend-002/build.json`](../../../artifacts/first-contact/084/provider-readiness/native-locked-frontend-002/build.json).
The current isolated `apps/web/dist` contains this second build. Root owns
whether to package/promote it; the running candidate was not changed here.

### First model failure and bounded diagnostics

Root's fresh run `38442f873e6440cab541927b64f97eec` failed at
`define_geometry_basis_printed_handle_084_first` with `MODEL_UNAVAILABLE`, before
any MCP call. Its primary and SDK request captures survive. The SDK capture is
immediately before the auxiliary-client call; it does not prove an HTTP request
was sent. The installed worker deliberately discarded raw exception text and
stderr, and did not retain a safe failure category/class/status receipt. The
historical exception cannot be recovered from the owned logs.

An offline reconstruction matched the exact captured request digest, including
both original inline images. Installed Hermes/OpenAI 2.24.0 converted that request
and consumed a synthetic SSE response successfully, with no authentication
resolver or network call. The first synthetic fixture omitted the required
`response.output_item.done` event; both attempts are retained and the corrected
fixture passes. This establishes request-conversion viability only. It does not
identify the original live failure or justify a model/authentication change.

The existing worker/evidence helper now retains an optional finite failure receipt
on the already captured invocation: known category and exception class, integer
HTTP status within 100–599, and a finite allowlist of provider codes. Unknown
names/codes and exception messages, bodies, headers, arguments and tracebacks
remain excluded. The generic public result and existing sidecar forwarding are
unchanged. Thirty-eight focused worker/evidence tests passed in 1.53 seconds,
including safe metadata persistence, parent forwarding and hostile attributes;
focused Ruff/diff checks passed. Independent review found no actionable issues;
root committed the fix as `3e18db6b` and owns candidate build and any live retry.
No live retry or runtime patch occurred in this task. See
[`native-sdk-failure-001/diagnosis.json`](../../../artifacts/first-contact/084/provider-readiness/native-sdk-failure-001/diagnosis.json).

Installed-adapter offline controls also retain HTTP 400 and `model_not_found`
from `BadRequestError`, and the code from Hermes `_StreamErrorEvent`. A truncated
stream has only `RuntimeError`; terminal `response.failed` metadata is omitted
by the installed auxiliary adapter and can surface as empty content. These are
synthetic contract observations, not diagnoses of the historical live failure.
No private stream interception was added.

Root's next fresh run `f83abd139ec94d76acd8d9bdd6d79831` retained
`BadRequestError` with HTTP 400. One separately authorized model-only diagnostic
reconstructed that exact captured request and invoked the unchanged installed
worker against the same frozen model/profile. It failed in 1.597 seconds with:
“The 'gpt-5.5' model is not supported when using Codex with a ChatGPT account.”
The endpoint supplied no code or parameter. There was one SDK invocation, no MCP
call, no workflow replay, no credential manipulation and no model change. Raw
error content remains private at mode 0600; the sanitized receipt is retained in
[`native-sdk-http400-001/`](../../../artifacts/first-contact/084/provider-readiness/native-sdk-http400-001/).
Discovery success had established configuration/resolver availability, not endpoint
acceptance of that model. No alternative model is qualified by this result.

The user then explicitly selected GPT-6.1. A completed read-only account catalog
query through the installed Hermes discovery function returned HTTP 200 in
1.274 seconds and lists `gpt-6.1-sol` with visibility `list` and priority 1.
This identifies the available catalog entry; it does not claim successful
inference. No model change, refresh or inference occurred during discovery,
and the original auth store was unchanged. The interrupted earlier tool call
had no retained result and no remaining owned process before resumption. See
[`native-codex-catalog-001/`](../../../artifacts/first-contact/084/provider-readiness/native-codex-catalog-001/).

The minimal GPT-6.1 readiness probe exposed a separate configuration boundary:
installed Hermes `get_config_path()` ignores Wright's `HERMES_CONFIG_PATH` and
reads the original profile `config.yaml`. The first probe therefore failed its
local exact-model assertion before any SDK generation. Its resolver changed the
auth-store digest; no direct credential mutation occurred and that digest alone
does not establish a refresh outcome. A read-only lookup confirmed the old
`gpt-5.5` resolution.

The supported correction is the installed Hermes `HERMES_MANAGED_DIR` overlay,
containing only `model.default: gpt-6.1-sol` and `model.provider: openai-codex`.
Its private file SHA256 is
`178137b218e972e7b83c34131716b6165808b3db6e1c92602b68609a1b2f6b67`.
With that override, one minimal model-only generation succeeded in 3.225 seconds
with confirmed `openai-codex` / `codex_responses` / `gpt-6.1-sol` routing and the
same adapter-reported model. The response was nonempty and tool-free but not
byte-exact `READY`; its digest is retained. Usage was unavailable. No MCP calls,
images or workflow runs occurred. Auth and both configuration files remained
unchanged. This establishes model-call readiness, not engineering correctness
or a reported upstream model revision. Both attempts and the supported override
are retained in
[`native-gpt61-sdk-readiness-001/`](../../../artifacts/first-contact/084/provider-readiness/native-gpt61-sdk-readiness-001/).

Gate execution is held pending the final source freeze. An isolated
official Node 22.22.2 ARM64 archive was checksum-verified and unpacked privately;
its bundled npm is 10.9.7. All 280 root-lock Node engine declarations accept this
version. Host Node and shared dependencies are unchanged. The toolchain receipt
is retained at
[`gate-preparation/node-toolchain.json`](../../../artifacts/first-contact/084/provider-readiness/gate-preparation/node-toolchain.json).
No full gate has started.

### Managed workspace and provider mounts

The native runtime owns workspace registration under its managed directory.
Only the parent directory has been prepared; the ordinary API must create and
register `handle-workspace` at
`/tmp/wright-first-contact-084-native-777akcxz/wright-home/data/workspaces/handle-workspace`.
Every selected provider will mount that exact absolute path at the same path
inside its own isolated container. The
[`native-handle-mount-plan.json`](../../../artifacts/first-contact/084/provider-readiness/native-handle-mount-plan.json)
records the proposed commands, image digests and remaining qualification
requirements. It does not claim the workspace or provider services exist yet.

The later [SDK model-observation audit](sdk-model-observation.md) confirmed that
installed Hermes's Codex completion shim echoes its model argument in the result.
New SDK evidence now labels that value `adapter_returned_model` and leaves
`upstream_reported_model` unknown. The successful GPT-6.1 call and selected route
remain observed; no historical evidence is rewritten or promoted to an upstream
revision claim. This correction was verified with synthetic transports only.
