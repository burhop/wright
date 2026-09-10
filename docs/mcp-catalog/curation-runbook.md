# Maintaining Wright's integration shortlist

Updated 9 September 2026. This is the operating procedure for the implemented
catalog review fields, API, library filters, and curation commands. The separate
[research plan](curation-research-plan-2026-09-08.md) records the original proposal
and its source research. The [dated report](evidence/curation-2026-09-08/report.md)
contains the first inventory decisions. Its counts are evidence dated to that run,
not a claim that every integration has been exercised.

## What users see

The library opens on **Curated**, evaluated for the current machine's platform,
deployment, launch configuration, and review date. **Follow up** contains useful
candidates needing evidence, credentials, a host application, fixes, or an owner.
**Removed from discovery** retains the reason and any replacement identities but
does not offer catalog installation. **Show installed integrations** includes
retired records. Reviews never uninstall, disable, replace, or delete user work,
credentials, workspace bindings, or custom integrations.

The nine engineering stages are requirements, concept/architecture, detailed
design, analysis/simulation, BOM/sourcing, manufacturing/assembly, test/quality,
release/change management, and operations/service. A stage count is potential
coverage by individual integrations. It does not prove handoffs between systems.
Source verification, transport, installation readiness, and curation remain
separate dimensions. An old `tested` label cannot promote an entry.

## The repeatable cycle

1. **Inventory.** Review the bundled catalog, active signed snapshot, managed
   servers, custom records, and installed state separately. The September bundle
   began with 70 records, not 75 distinct qualified implementations. The API
   preserves deployed and custom records; this first desk review covers the
   bundle, not the user's production database.
2. **Discover.** Search publisher release notes and developer documentation,
   the official MCP Registry, and primary GitHub repositories. Search gaps first:
   requirements/traceability, component sourcing, manufacturing data, inspection,
   and service. User requests and documented repeat use are additional inputs.
   Directories and stars are leads, never proof of use or quality.
3. **Resolve identity.** Identify publisher, exact implementation, release,
   endpoint/package, license, and supported host. Multiple servers can share a
   repository. Aliases, API candidates, protocol references, and agent skills are
   not interchangeable with installable MCP servers. Never revive a retired
   identity automatically because a registry lists a new version.
4. **Desk review.** Assign intended lifecycle stages, reason, owner, next action,
   review date and due date. Review maintenance, source changes, release and issue
   history, security advisories, authentication, account cost, data access, and
   setup burden. A failed fetch, redirect, rate limit, or quiet repository does
   not itself justify removal. Stable software need not commit every month.
5. **Qualify.** Follow the required [clean-container process](mcp-server-testing-process.md).
   Pin the implementation, install only its prerequisites in a disposable Intel
   Linux Wright container, initialize the MCP session, list tools, perform a safe
   real backend task, verify the artifact or expected result, then repeat through
   the Hermes-facing `wrightgateway` MCP. Run three fresh direct sessions; add
   separate native/platform qualification for every additional recommendation.
   Authentication expiry, timeout, cancellation, failure recovery, and uninstall
   behavior belong in each integration's complete acceptance recipe.
6. **Decide.** Publish Curated only for a useful, currently qualified workflow.
   Use Follow up for an unresolved gap with a concrete next action. Remove from
   discovery for a verified obsolete/non-server entry, an archived unsupported
   implementation with no current qualification, or a documented serious defect
   without an acceptable supported path. Preserve history and replacement limits.
7. **Publish and monitor.** Review the catalog diff and evidence together, run
   schema and application checks, then distribute through Wright's existing
   signed catalog update mechanism. Activation changes metadata. Installation
   and workspace enablement retain their existing explicit workflow.

Plan for 15–20 integration families, normally one preferred choice per capability
and at most one justified alternative. This is a selection ceiling, not a quota.
The September implementation establishes the review system and initial technical
qualification; it does not claim a finished, broadly adopted portfolio across
all nine stages. Do not fill gaps with weak recommendations.

## Evidence and renewal

`curation` records the reviewed disposition and its rationale. A qualification
records platform, `native` or `docker`, workflow, source and Wright revision,
verification and expiry dates, configuration digest, and evidence file/digest.
All four results—protocol, backend, gateway, and outcome—must be passed. Evidence
expires after at most 60 days; the initial review cycle is 30 days. Changing a
launch command, endpoint, dependency, host requirement, credentials, or safety
gates makes the existing qualification inapplicable. Runtime evaluation demotes
stale recommendations to Follow up while retaining the original decision.

The publication tests verify the committed evidence hashes, configuration
binding, passing cleanup, platform, and Hermes-facing gateway result. Runtime
clients trust the signed metadata; they do not fetch arbitrary evidence paths.
Mutable remote services must be retested on reported version/schema changes and
within the renewal window. This implementation does not continuously fingerprint
each running remote service or attest local host versions on every call.

`adoption: unknown` is honest and visible. Technical qualification can establish
a narrow recommendation while repeat adoption is still unknown. Prefer those
with measured adoption when selecting between similarly qualified integrations.
Record publisher reports separately from independent reports and Wright repeat
use. A later opt-in usage study should count successful sessions and repeat
workspaces without collecting prompts, designs, tokens, or credentials. No new
user telemetry is collected by this change.

## Commands and cadence

Run from the repository with its normal Python environment:

```bash
uv run python -m tool_registry.catalog_curation report --as-of 2026-09-08 --output-dir artifacts/mcp-curation
uv run python -m tool_registry.catalog_curation report --output-dir artifacts/mcp-curation-next --previous artifacts/mcp-curation/report.json
uv run python -m tool_registry.catalog_curation research --output-dir artifacts/mcp-curation
uv run python -m tool_registry.catalog_curation discover --search sourcing --output-dir artifacts/mcp-curation/discovery-sourcing
```

`report` is deterministic for the same catalog, policy, date, and optional
platform. It emits JSON and Markdown with all three lists, reasons, next actions,
due dates, gaps, and an optional delta. `research` observes public GitHub metadata
without credentials. `discover` reads one bounded Registry page; pass its
`next_cursor` with `--cursor` to explicitly review another page. It strips package
commands and does not install, register, or execute discovered content.

Only the two fixed public HTTPS origins are permitted for intake. Redirects are
not followed, reads are bounded, and GitHub concurrency is limited to three.
Unavailable sources are recorded as unavailable. Partial/failed network runs
write `research.attempt.json` or `discover.attempt.json`, return exit code 2, and
preserve the last good result. Reports do not change catalog decisions.

The existing MCP catalog workflow now saves a report on relevant PR/push runs.
Its Monday schedule and manual dispatch additionally observe repositories and
search five lifecycle terms. Artifacts are retained for 90 days. Partial source
checks emit a CI warning with the attempted observations. There is no automatic
promotion, retirement, PR publication, package installation, or hardware action.
The schedule takes effect when this workflow reaches the default branch.

Assign one maintainer to weekly source triage, integration owners to monthly
qualification renewal, and a quarterly portfolio review to remove duplication
and reassess lifecycle gaps. Urgent verified breakage can retire a recommendation
immediately through the reviewed signed-update process. A fetch failure alone
cannot do so. Reinstatement requires fresh evidence and an explicit review.

## Initial qualification runner

`scripts/qualify-catalog-scenarios.py` is an opt-in operator runner with ten
fixed recipes: public Autodesk help product discovery; OpenSCAD, BREP, FreeCAD,
and Blender geometry workflows; an OASiS scikit-fem solve; ROS 2 bag retrieval;
headless AutoCAD DXF authoring; standalone Rhino solid 3DM authoring; and KiCad
PCB authoring, audit, and fabrication export. It uses
actual protocol clients and Wright's production gateway composition; it refuses
Wright's mock-runner environment. It records three direct sessions, the gateway
service result, and the actual gateway MCP result. The artifact oracles inspect
STL dimensions and volume, BREP STEP exchange-file boundaries, the OASiS VTU
mesh, field finiteness, boundary values, and expected solution range, or the
ROSBag SQLite schema, CDR payloads, types, and nanosecond timestamps.

Run the script inside a newly created Intel Linux Wright container, with candidate
source mounted read-only at `/candidate`, evidence output mounted at `/evidence`,
and `PYTHONPATH` including `apps/api/src`, every `packages/*/src`, and `src` from
that candidate. Use the image's Python with Wright runtime dependencies. Record
the resolved image digest and candidate revision in the arguments:

```bash
python /candidate/scripts/qualify-catalog-scenarios.py --execute \
  --server autodesk-product-help-mcp --platform linux_x64 \
  --environment clean-wright-container --wright-revision REVIEWED_REVISION \
  --container-image REVIEWED_IMAGE_DIGEST --output /evidence/autodesk-help-linux.json
```

For OpenSCAD, first install `git openscad xvfb xauth` using the container's package
manager, then select `--server openscad-mcp`. The catalog pins Git commit
`d438b84fff8af9d646c2bcb76fe58fa4ad387de0` and launches it using `uv tool run`.
Neither `uvx` nor Git is assumed present in the base image. Record prerequisite
versions. Discard the container after each server. Never modify the base Docker
image to satisfy a catalog test. See the setup recipes and problem log for the
observed results and any outstanding blockers.

For BREP, install only `brepjs-cad@0.103.0` and copy the reviewed
`docker/mcp/brep-mcp-launcher.cjs` to `brep-mcp-wrapped` on `PATH`. The launcher
works around the published package's data-URL entry defect without modifying the
third-party package. The runner also checks invalid-program cleanup and the
server's bounded sandbox timeout.

For `freecad-mcp-nekanat`, install the FreeCAD 1.1.1 AppImage, its documented
Xvfb/OpenGL libraries, and addon commit
`63acb305573194a011641ab13ccfb391fe95769f`. Start the localhost-only addon bridge,
then run the catalog command. The command pins `mcp[cli]==1.28.1`; a fresh
unconstrained install resolves MCP SDK 2.x and fails before initialization because
the server still imports the 1.x `FastMCP` API.

For `oasis-open-fem-agent`, install Git only. The catalog uses uv-managed Python
3.12 and pins OASiS commit `7c184d5b7ca5cda6086f3912d1c7923c58307780`,
`mcp[cli]==1.28.1`, and `scikit-fem==12.0.2`. Keep its child `PYTHONPATH` empty:
OASiS publishes generic top-level `core`, `tools`, and `server` modules which can
otherwise collide with Wright's packages. The runner also starts a deliberately
slow solve with a one-second Wright deadline and verifies that no solver process
remains after the stdio transport is retired.

For `rosbag-mcp-pypi`, install no system prerequisite. The catalog pins the
`rosbag-mcp==0.2.0` wheel, MCP SDK 1.28.1, `rosbags==0.11.5`, NumPy 2.5.3,
Matplotlib 3.11.1, and Pillow 12.3.0 under uv-managed Python 3.12. Keep the
child `PYTHONPATH` empty. The runner creates a deterministic two-message ROS 2
SQLite bag, queries the first message through three direct sessions and both
gateway layers, and checks the database and CDR bytes independently. The
package's repository link is unavailable and repeat adoption is unknown, so the
qualification expires after 30 days and remains limited to Linux known-message
retrieval.

For `blender-mcp`, install Blender 4.3.2, `python3-requests`, Xvfb, xauth, and
procps only in the disposable container. The catalog pins source commit
`5f8ddaf6e987c4aa0c3467fcc548838b28f64477`, disables telemetry, and enables
the server's safe mode. The runner mounts that revision's add-on read-only,
exposes Debian's system Python packages to Blender's embedded interpreter, and
starts the UI process under Xvfb. It verifies 28 tools, three direct sessions,
both gateway layers, STL dimensions and volume, object topology and bounds, a
controlled backend error, add-on disconnect/reconnect, and process-group/port
cleanup. The 113 upstream tests also pass. Optional network asset and generation
features remain outside this qualification.

For `autocad-mcp-u-c4n`, the catalog pins source commit
`abc2a82e7128358b9e228a7d9442b37019aa3fe5` and its 47-tool lean profile. Save
`ALLOWED_PATHS` through Wright's per-installation configuration path. The
qualified Linux scope uses the ezdxf backend to create, reopen, and independently
inspect a mechanical DXF and to reject an out-of-workspace save. Live AutoCAD COM
mode requires a separate Windows qualification.

For `rhino-mcp-easehee`, the catalog pins source commit
`3e10efb9963be36ee1209f8f9ebd2cc6efcfcc46`. The qualified scope is standalone
rhino3dm authoring of a millimetre solid Brep, native 3DM save/reopen, and
independent topology and bounds inspection. Live Rhino/Grasshopper bridge mode
and standalone mesh/STL output remain outside the recommendation.

For `kicad-mcp-blwfish`, install KiCad 9, its symbol and footprint libraries,
and Git only in the disposable container. The catalog pins release commit
`bcc6f11de92e5f47cb7dde1d24565f7779b2fbed`. The qualified scope searches an
installed footprint, authors and reopens a native PCB, audits it, exports Gerber
and drill data, and validates the board and archive independently. DRC is excluded
because release 0.13.0 writes a history message to stdout and corrupts the MCP
JSON stream. FreeRouter is also excluded.

## Product-design process-chain runner

After ten integrations have current scoped evidence, run
`scripts/qualify-catalog-process-chains.py`. It refuses mock mode and refuses any
input whose Linux Docker qualification is no longer current or no longer matches
its catalog configuration hash. It discovers the exact tool schemas, enables
only BREP, OASiS, AutoCAD, KiCad, and ROSBag in one disposable Wright workspace,
and makes every engineering call through `GatewayService`.

The fixed chains are:

1. a two-hole mechanical bracket from STEP/STL authoring through a scoped
   scikit-fem structural screening solve to an independently inspected review DXF;
2. a native KiCad controller board and fabrication package through a board-driven
   enclosure envelope and thermal solve to a provenance-bound ROS 2 validation
   trace; and
3. a field deflection record bound to drawing revision A, retrieved through
   ROSBag MCP, which triggers and preserves a controlled revision B DXF.

Each handoff verifies design/revision identity, units, artifact bytes and hashes,
declared Wright approvals, a fail-closed corrupted-manifest probe, and cleanup.
The FEA is a screening model: the structural solve uses an equivalent solid
section and excludes the mounting holes, while the electronics solve uses a 2D
conductive board with ambient edges. The ROS 2 records are deterministic
qualification fixtures, not physical test results.

Prepare a fresh container with the selected KiCad packages and the same reviewed
BREP launcher described above, then run:

```bash
python /candidate/scripts/qualify-catalog-process-chains.py --execute \
  --platform linux_x64 --environment clean-wright-container \
  --wright-revision REVIEWED_REVISION --container-image REVIEWED_IMAGE_DIGEST \
  --installed-item kicad-cli=REVIEWED_VERSION \
  --installed-item kicad-symbols=REVIEWED_VERSION \
  --installed-item kicad-footprints=REVIEWED_VERSION \
  --installed-item brepjs-cad=0.103.0 \
  --prerequisite reviewed-brep-compatibility-launcher \
  --prerequisite system-python-pcbnew-oracle \
  --output /evidence/process-chains-linux.json
```

## Generating the independent Engineering MCP curation dashboard

The internal curation dashboard is a standalone static report generated from
the catalog, its qualification evidence, the latest process-chain evidence, and
the preceding dated report. It is not shipped in Wright's application, API, or
package, and it must not be added to the user-facing Tool Registry. Do not edit
its generated `status.json` or embedded evidence by hand.

After every qualification or catalog decision:

1. Preserve the raw JSON evidence in a dated directory. For an existing curated
   scope, update only the matching catalog qualification with its new Wright
   revision, dates, evidence path, and SHA-256. A changed launch configuration
   needs a new qualification rather than renewal of the old one.
2. Run the three Tier 1 chains when any of their five inputs changed. Keep their
   result labeled as a synthetic integration fixture; it is not production or
   physical test evidence.
3. Generate the dated report and its independent dashboard directory:

```bash
uv run python -m tool_registry.catalog_curation report \
  --as-of 2026-09-09 \
  --output-dir docs/mcp-catalog/evidence/curation-2026-09-09 \
  --previous docs/mcp-catalog/evidence/curation-2026-09-08/report.json

uv run python scripts/generate-engineering-mcp-status.py \
  --process-chains docs/mcp-catalog/evidence/curation-2026-09-09/process-chains-linux.json \
  --previous-report docs/mcp-catalog/evidence/curation-2026-09-08/report.json \
  --history docs/mcp-status/history.json \
  --qa-output artifacts/mcp-status-qa \
  --public-output artifacts/mcp-status-public
```

The generator refuses missing or altered current qualification evidence. Invalid
or unavailable process-chain evidence becomes a secondary diagnostic and cannot
blank the integration list. It validates reviewed assessments and both output
schemas, reconciles canonical membership and counts, and builds a detailed QA
projection plus a public allowlist projection.

The dashboard assigns one of six portfolio categories to every MCP, WebMCP, and
hardware record. These categories describe the next curation action and do not
replace the exact technical result:

- **Works:** current scoped protocol, backend, gateway, outcome, and cleanup evidence.
- **Preview:** useful checks passed; complete Wright qualification remains.
- **Requires login:** a current server reached an authentication challenge.
  This proves the access boundary, not post-login tools, backend behavior, or
  Wright gateway operation. Keep it out of ordinary product discovery until an
  authenticated read and gateway call pass.
- **In progress:** planned work, repair, evidence review, renewal, host software,
  licensing, hardware, or a lab environment remains.
- **Abandoned:** a reviewed decision closed evaluation. Retain the reason and any
  replacement to prevent repeated review.
- **Blocked by vendor:** an attributable vendor restriction explicitly asks that
  this integration use not proceed. Authentication, licenses, paywalls, or HTTP
  errors do not establish this category.

Works, Preview, and Requires login form the green technical-assessment total.
Green is not customer adoption or production acceptance.

Review the generated directory, run the catalog checks, and verify the dashboard
through a local static HTTP server:

```bash
python -m http.server 18765 --bind 127.0.0.1 \
  --directory artifacts/mcp-status-qa
```

Capture the served verification and screenshots with:

```bash
node scripts/verify-engineering-mcp-dashboard.mjs \
  --base-url http://127.0.0.1:18765 \
  --output-dir artifacts/mcp-status-verification
```

The verifier derives expected counts and exact member totals from `status.json`,
opens all six categories including the zero vendor state, checks reloadable URL
filters, search, history, and the narrow layout, rejects browser or HTTP errors,
and writes five screenshots plus `served-dashboard-verification.json`.

After human review, repeat generation with `--record-snapshot --public-output
docs/mcp-status`. Ordinary preview builds do not mutate history. See
`docs/mcp-catalog/status/README.md` for correction and rollback rules.

## Protocol boundaries

- **MCP:** Existing stdio and remote HTTP runtime support remains in place.
  Streamable HTTP and legacy SSE are distinct catalog values; Autodesk help's
  metadata now names its actual Streamable HTTP protocol.
- **WebMCP:** The browser adapter follows the current draft registration shape:
  `document.modelContext.registerTool(tool, {signal})` returns a promise, and abort
  removes the native registration. Disposal and per-call cancellation propagate.
  Native registration remains opt-in and permission/feature checked. Wright's
  workspace-bound surface bridge remains separately identified; its tests do
  not claim browser-wide conformance or support for arbitrary third-party pages.
  Source: [WebMCP draft](https://webmachinelearning.github.io/webmcp/).
- **MHS:** Anthropic calls this the Model Hardware Standard. Its August 27
  announcement describes a research preview with MCP, CLI, and API access and
  future open sourcing. There is no verified public driver contract in this
  research from which to implement a conforming Wright driver. The catalog can
  represent `mhs_preview` separately from generic `hardware_mcp` and prevents
  either from becoming an ordinary curated/installable integration. No fake
  MHS transport or physical-device support is claimed. A later integration needs
  the published/partner specification, device inventory, exclusive control,
  deterministic limits and interlocks, calibration, approved read/simulation
  modes, cancellation, emergency-stop semantics, and device-specific qualification.
  Source: [Anthropic announcement](https://www.anthropic.com/news/model-hardware-standard-research-preview).
