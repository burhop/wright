# Ordinary installed handle setup — actual UI evidence

Date: 2026-10-23. Scope: T007's installed setup and ordinary readiness path,
without engineering execution. Candidate 5 ran at `http://wright.localhost:18084/`
with runtime `563bc1210439605fd0ab9c30`. Its wheel SHA-256 was
`84b34cf1510ab4529503d8115d89ffda0ad527c314b66b46fcea3fdd20c93435`;
its served UI manifest SHA-256 was
`352fdfede88e1a0b1f83bf74fe9901316ee65220b07bdc532fbcf1a64eef3cad`.
This candidate predates the review-evidence ordering change and the subsequent
geometry proposal. Source acceptance below does not establish engineering
acceptance of its geometry assets.

## Observed installed journey

The actual workspace Workflow entry opened **Explore an example**, then created
**Drawer handle setup check** from the supplied Printed02 starter. Exploration
made no API writes. The **Set up this job** form discovered the three already
registered geometry, slicing and inspection tools and listed existing workspace
JSON files. No mock API, injected authentication, private preparation helper,
model call or provider execution was used for this setup.

The selection used the four exact profile copies identified by the prior
`handle-binding-004/preparation.json`: machine, original process, Orca process
and filament. `qualified-selection.json` records their actual paths, hashes and
byte counts, the selected server/schema identities, and the original-to-Orca
process difference (`tree_support_wall_count` string `-1` to string `0`). The
read-only managed mount matched the original workspace. These existing files
and configured providers are prerequisites, not products of the setup form.

**Prepare setup proposal** returned a real installed recipe proposal. The saved
and proposed source textarea contents matched their API SHA-256 values exactly;
all 50 dependency files matched the displayed manifest's hashes and byte sizes.
The selected profile snapshots matched their original file hashes. The proposed
source uses the manually reviewed `local_simulate_handoff` binding and contains
no `test://` handoff. The proposal explicitly reports `engineering_acceptance:
false` and `physical_dispatch: false`.

After inspecting source, dependencies and limitations, the separate acknowledgement
and **Accept prepared revision** saved revision 2 in the same editor. The raw
workflow identity and original template/version/source/layout provenance were
retained. The ordinary working view's **Prepare and check inputs** returned
`ready`, displayed **Ready to start**, and offered **Start process**. That button
was not pressed. No outputs existed. Closing the working view and source tab,
then reopening the source through the normal workspace route, retained the
accepted digest/revision and editor controls with no dirty source.

Exact subject:

- Workspace: `7e720c97-6048-4a50-944f-2376186db36b`.
- Session: `wright-local-3751adae-a1b3-4927-a3fd-b33f56510f20`.
- Source: `workflows/drawer-handle-setup-check.workflow.wflow`.
- Raw workflow ID: `t24c33b1d6391afe1e6d7aa65`.
- Accepted storage/definition revision: `2` / `2`.
- Accepted source SHA-256:
  `d7fc5c9d046b40c2e054ad3304d767439581a192c478680cdff7ca1db261fb97`.
- Proposal: `c5521077e0d84775be25b6c9f7ad3de8`, digest
  `b5e8683380cdc10593c2148472e6b6c2912f605fbeb7ff51730d0a477b12ff3f`.
- Recipe: `printed-handle-orca` version `1`, digest
  `761d98e20ef52bae1e41c3916dde18cb3e47241234f9ee96a8c6e201fbfa84cd`.
- Working-view readiness: `readiness-041a1365f52046118ce1930c02c09a4f`.

Template lineage becomes `revised`; its qualification/configuration/verified-run
fields remain null. Setup visibly states that discovery does not establish native
installation, shared-mount qualification or engineering success. The ordinary
readiness result establishes the existing preflight's current result only; this
proof does not establish a started run, completed review or native tool success.
No integration enrollment, synthetic review grant or engineering decision was
created by this proof.

## Retained controls and limitations

The original `replacement-drawer-handle` source revision 5 and pending run
`3735dcf5678847219bc88ca2c80cedc8` remained byte-identical. Their SHA-256 values
were respectively `9cd2acc8b36df3abea002a9e62b3171a8df0fc1b5c327eb35bdd20e047caeaef`
and `6c20eb33c933c8fb090c350b1955dada9e3bc6d1b494e87dcb8def94ecd0c9f0`.
Captured writes consisted of workspace activation, starter creation, setup
options/proposals/acceptance and ordinary input/readiness preparation. These are
metadata/source operations, not engineering execution. There were no run-start,
resume, decision, enrollment or provider-execution requests.

The first two capture attempts stopped before acceptance because the harness's
exact-label selector did not locate the nested source textarea. Both attempts and
their unaccepted proposals remain retained. The third capture used the two actual
textareas, asserted their visible label text and read-only state, then compared
full exact hashes. No source discrepancy or runtime change was needed.

A separate fresh workspace, `ddbbe95d-f8a7-490f-8ee2-0d5a6aef3f41`, initially
still discovered the globally registered tools under legacy `enabled_tools:
null`. No globally uninstalled-MCP condition is claimed. The fresh workspace
lacked all four qualified profile paths and kept proposal/acceptance disabled.
Its source `workflows/drawer-handle-missing-tools.workflow.wflow`, raw ID
`t4221fdff6b014c3999e64e53`, stayed at revision 1 and digest
`6884f8f17394750e7c8147d8e1c467c72b7c69d9e47f595977cc5e8428dc5dc1`.
Two actual `/api/agent/sessions` HTTP 502 responses occurred during creation,
while the workspace and editor still opened; they remain recorded.

With explicit coordination, the existing per-workspace tool-toggle API was then
used only on this isolated workspace to establish `enabled_tools: []`. The final
actual setup options contained empty arrays for all three roles, each selector
had only its empty placeholder, and Prepare/Accept remained disabled. Visible
recovery guidance said: “No matching tool is available. Enable a compatible
server in MCP Tools, then refresh choices.” This proves **no MCP enabled for this
workspace**, while all providers remain installed and the original workspace's
four server-ID memberships, including FreeCAD, remain unchanged. There was no
proposal, run or decision in this workspace.

Two follow-up findings are retained for triage rather than hidden by the passing
setup control. First, a workspace with null membership materializes installed
server *names* when the first UUID-based disable is submitted. The route reports
that UUID disabled while its name remains enabled. Removing the actual stored
names through the same API established the empty list; no membership-default
policy or product source was changed. Second, opening the unchanged starter's
working view refuses during source compilation with “Confirm visual intent needs
a supported execution type” and “Use an AI prompt or an MCP tool block for this
run.” It exposes no Start action, but gives an authoring correction rather than
directing the newcomer to task setup. No ordinary input/readiness request is
made in that refused view, so this is not a readiness-assessment result. An
intermediate harness assertion incorrectly expected the empty select widgets
themselves to be disabled; the final control instead checks their exact empty
choices and disabled proposal/acceptance actions.

The original workspace was restored active after each bounded observation. The
three protected files (original source, pending run and newly accepted setup
source) remained unchanged. No global provider toggle, native update, engineering
action or product-code change occurred.

## Evidence

All captures are local under
`artifacts/first-contact/084/native-handle-ordinary-setup-012/`:

- `report.json`: actual entry, offline exploration and creation; retained failed
  label-selector attempt. `report-002.json`: retained second selector attempt.
- `report-003.json` and `capture-003.mjs`: passing exact setup, acceptance,
  readiness and reopen; `proposal-003.json`: full source/dependency proposal.
- `qualified-selection.json`: exact existing profile/provider selections.
- `fresh-workspace-observation.json`: initial global-tool discovery and missing
  profiles. `missing-tools-report.json` retains the failed initial assumption.
- `isolated-no-enabled-mcp-report-003.json` and its capture script: passing
  explicit-empty membership, exact empty choices, blocked setup actions,
  unchanged source and restored original workspace. Earlier reports retain the
  UUID/name behavior and select-widget assertion; the final working-view
  screenshot retains the actual compiler refusal.
- `media.json`: screenshot/video paths, hashes, dimensions and durations.
  The successful setup video is 17.24 seconds, SHA-256
  `75af95be8482db05ed13468e160213e5e7e24473f7f78c47d5cad3930f129946`.

The exploration, source comparison, dependency manifest, accepted editor,
ordinary readiness, fresh-workspace setup and refused working-view screenshots
were visually inspected.
This is actual installed setup proof; the complete engineering journey and later
correction proof remain separate.
