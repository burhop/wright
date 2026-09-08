# First curation pass: decisions, evidence, and limits

Reviewed 8 September 2026 on `codex/mcp-curation-lifecycle`, based on Wright commit
`1ada5de0aaa608baadafa41031e5877eb685bed3`. Live evidence identifies this candidate
as `1ada5de0-plus-curation`; it was tested from the working source before the
implementation commit, not from a published Wright release artifact.

## Inventory decisions

The original bundle contained 70 records. Four sourced candidates were added:
[GitHub](https://github.com/github/github-mcp-server),
[Atlassian Rovo v2](https://support.atlassian.com/atlassian-ai-gateway/docs/how-to-upgrade-from-atlassian-rovo-mcp-v1-to-atlassian-rovo-mcp-v2/),
[Grafana](https://github.com/grafana/mcp-grafana), and
[Partuno](https://github.com/JPMarhefka/partuno). They remain Follow up; publisher
documentation establishes availability, not Wright qualification or repeat use.
Partuno is a community integration, not a DigiKey/Mouser official implementation.

The [report](report.md) lists **2 curated, 63 follow-up, and 9 removed** records.
These counts are distinct from installations, custom records, managed tools, and
active signed catalog versions in a deployed Wright instance.

| Curated integration | Qualified scope | Boundaries |
|---|---|---|
| Autodesk Product Help | Product discovery through direct MCP and the Hermes-facing gateway; native Windows x64 and Linux x64 container | Read-only public service 3.2.0; applicable publisher terms remain an independent onboarding step; not CAD authoring |
| OpenSCAD | Three direct cube exports and gateway exports; dimensions and 480 mm³ volume verified | Linux x64 container; pinned Git source; no native Windows/macOS or complex geometry claim |

Nine records were removed from ordinary uninstalled discovery:
`mcp-ui-shopify`, `webmcp-standard`, `calculix-simulation`,
`freecad-booleans-lucygoodchild`, `trikos529-openscad`,
`nvidia-kit-cae-agent-skills`, `aps-mcp-server-petr`,
`aps-mcp-server-nodejs`, and `revit-mcp`.
The report contains each reason and proposed next action. No user installation,
credential, file, or workspace binding was deleted or disabled. BREP and Playwright
were corrected from the old `tested` tier where top-level validation was not tested.
Zoo's repository URL was updated to its current vendor repository identity.

## Source intake

[GitHub observations](research.json) cover 54 repository identities: 44 were
observed and 10 unavailable because of redirects, missing resources, or rate
limits. The file is explicitly marked incomplete. Unavailable is not archived.
The new CLI preserves this distinction and keeps last-good evidence on failed
future runs. Stars and activity were recorded as research signals, not adoption.

Four public Registry searches returned 37 name/version leads: five manufacturing,
five requirements, four sourcing, and 23 operations. The per-search JSON files
retain raw lead identity, pagination state, and related known catalog IDs.
Version duplicates and unrelated search matches mean this is not 37 new servers
recommended for installation. These leads were not executed or automatically
added to the user catalog. Publisher-source verification remains required.

## Verification

- 119 backend/API tests passed across catalog distribution, signed updates,
  preservation, install plans, compatibility, and the local child-MCP API journey.
- After the last validation changes and final qualification records, 49 targeted
  tests passed, including legacy signed metadata, invalid curation rejection,
  real evidence hashes, deployment/configuration binding, and API retirement.
- Seven Chromium library tests passed, including three-list navigation, lifecycle
  gaps, installed-state access, signed metadata activation/rollback, and a narrow
  layout accessibility check. These browser tests use mocked API responses.
- Ten frontend component and WebMCP adapter tests passed. The production web build,
  changed Python lint checks, and changed frontend lint checks passed.
- Live external qualification separately passed the actual MCP backend and
  production `api.gateway_stdio` gateway on the three environments above. The
  API/browser test fixtures are not used as evidence of vendor compatibility.

The isolated base image was
`sha256:70df876f46133fc44bf6f448ca37a16fade3bbb3f5293290065b0a3e1e559d29`.
OpenSCAD-specific dependencies were installed only in disposable containers.
No base image, shared Python environment, vendor account, or physical device was
modified. Existing Vite chunk-size/config-loader and Starlette deprecation warnings
remain; the checks passed.

## Remaining work and rollout

Follow the [qualification backlog](../../followups/curation-qualification-2026-09-08.md)
and [runbook](../../curation-runbook.md) for account/host-dependent qualification,
repeat adoption, cancellation/recovery, and three cross-tool lifecycle journeys.
Most lifecycle stages still have no current technical recommendation. Hardware
commissioning and native-browser WebMCP conformance remain separate work.

Anthropic's [MHS announcement](https://www.anthropic.com/news/model-hardware-standard-research-preview)
describes a research preview ahead of open sourcing. Wright now represents that
status and blocks ordinary hardware onboarding; this is not a conforming MHS
driver or verified physical-device support.

The software, catalog and CI workflow changes are local to the isolated branch.
They have not been pushed, released, or activated in the user's running database.
Existing active catalog snapshots are preserved, including older bundled
snapshots. Deployments already using those snapshots need the reviewed signed
catalog update through the existing activation workflow; replacing application
files alone does not silently replace the active snapshot. The weekly workflow
begins operating after normal integration into the default branch.
