# Playwright MCP usage guide

Last updated:16 October2026 (proofs dated17 October UTC). Status: actual standalone and normal Wright workspace gateway operation verified on GB10 ARM64. No engineering campaign or Windows desktop acceptance is claimed.

## Identity and sources

Independent provider: [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp/tree/5f8fc00210b27b4407c375b59cda4838045d429c). The ARM64 engineering bundle pins @playwright/mcp0.0.78; separate historical [0.0.80 preflight](../evidence/curation-2026-09-09/playwright-mcp-0.0.80-preflight.json) does not qualify0.0.78. Read the [setup recipes](../mcp-server-setup-recipes.md) and docker/mcp-bundle.linux-arm64.yaml before use. Do not install the latest package silently.

## Installation and readiness

The selected existing ARM64 image wright-desktop-engineering:download-ca71bf92 has image ID sha256:d2251671c9b658b027342931c68b5114076684deecb298828bb0e420852176ab. Its bundle build/service smoke passed; browser operation requires separate evidence. Use an isolated disposable browser context, headless Chromium and the selected container executable. No personal browser profile, credentials, host filesystem mount or external network is needed for an about:blank tab-list proof.

## Verified workflows and successful calls

Initial standalone initialization and tools/list succeeded (server reports1.62.0-alpha-1783623505000). The first browser_tabs list call returned an explicit missing chrome-for-testing error: the caller omitted the bundle's PLAYWRIGHT_BROWSERS_PATH environment setting. The corrected prerequisite uses that exact recorded setting and the read-only browser_snapshot tool; it completed against an isolated about:blank page with isError=false. The initial and corrected containers both terminated after their bounded calls. This is a caller configuration failure, not a provider bug. Evidence: /tmp/wright-desktop-workspace-tools-proof-20261017/provider.json and provider-corrected.json. The verified standalone prerequisite is initialize, tools/list and browser_snapshot with an empty argument object. Its result reports Page URL: about:blank and an empty accessibility tree. browser_tabs combines read and destructive variants, so its annotations must not be rewritten as read-only just because one action is list. The selected browser_snapshot schema reports readOnlyHint=true and destructiveHint=false; the proof supplies no filename. Subsequent Wright qualification must use the normal gateway workspace binding and desktop reasoning callback, with exact tool schema/evidence and denied-membership controls. Standalone success alone does not qualify a workflow or the Windows panel.

## Pitfalls and recovery

The fresh normal-workspace workflow completed through actual MCP stdio, the
desktop reasoning handoff and WorkflowMcpRuntime. This conversation supplied the
tool proposal and the final response after reading its real result; the relay
script never called another model. Wright executed exactly one browser_snapshot
with empty arguments and saved browser-observation.md with SHA-256
3fc151a8bd832c350852c7f88f3f07c31d7c9acc674e3c67fc82527f3096fd24.
The run is c88caf405f87457c93849790bfb8de4c in the private state
/tmp/wright-desktop-workspace-normal-state-20261017-01. It used ordinary workspace
membership and no integration-test enrollment. Local operator setup registered
the already installed immutable container and actual discovered schema; it did
not fabricate a provider validation result. This proves dispatch, not the native
Connections installation journey.

Negative controls revoked membership and changed the selected input schema
after a desktop request was pending. Both runs failed before any provider call;
the original registration was restored. The corrected panel transport also
preserves the owner's actionable preallocation capability rejection instead of
labeling it an uncertain effect. Bare 5xx responses and uncertain uploads still
require reconciliation. Evidence: normal-workflow.json,
denied-current-permission.json, negative-revoked.json and negative-schema.json
under /tmp/wright-desktop-workspace-tools-proof-20261017/. Initial invalid source
filename/duplicate-port fixture failures were retained and corrected before any
execution; they are not provider defects.

Do not confuse Playwright MCP with browser controls in the desktop harness. Tool-list discovery does not prove browser startup. Preserve exact initialization/launch errors; do not replace the provider or weaken permissions. After an uncertain operation, inspect the existing operation/container before retrying.

## Validation, authority and limitations

The independent provider owns browser interaction. Wright owns tool authority, accepted workflow, durable run and recorded outputs. New proof is confined to a disposable local context. It proves browser-tool integration rather than CAD/engineering compliance or user acceptance. No shared live workspace or protected campaign may be used.

## Desktop provider controls and restart proof

The native-panel prototype locally qualified shared Start/Stop and exact tool
switches through the existing lifecycle and registry owners. The user-owned
`desktop-playwright-lifecycle` registration uses the same immutable ARM64 image
and package above, a network-disabled disposable container and no host mounts.
Starting receives the selected workspace root; another workspace observes the
same shared process/tool flags. After disabling browser_snapshot, stopping and
restarting Wright, rediscovery preserved the deny. An explicit enable and a final
disable audit passed; the actual workflow gateway omitted the disabled tool.
No tools/call or engineering run was performed in this lifecycle proof.

A failed initial fixture used a catalog-owned row whose overridden launch command
was restored by catalog reconciliation on restart. Its Start failed before spawn.
Use a distinct user-owned registration for such an isolated container fixture;
this is not a catalog defect or authority to change the catalog. Copied historical
catalog validation metadata was removed before final restart/audit: the fixture's
local validation remains not_tested. Successful discovery/lifecycle does not
claim catalog installation or engineering validation. The corrected final provider
is stopped, workspace memberships retained, and callable contracts removed.

Evidence: /tmp/wright-desktop-provider-controls-proof-20261017/checkpoint.json,
browser-disable-1792210219940/, browser-restore-1792210303549/ and
browser-audit-1792210374078/. These use the actual resource/MCP/storage with a
simulated Chromium host, not the Windows desktop. Existing checked GB10 harness
configuration hashes were preserved; desktop activation skips legacy Hermes
profile synchronization. No provider bug was reported.

## Desktop uninstall qualification

A separate fresh user-owned `desktop-playwright-uninstall` fixture reused the
same immutable0.0.78 image. The actual native Connections panel started it with
network disabled, a read-only filesystem and one CPU/1GiB/256-process limits;
only initialize/tools-list ran. Stale state and foreign-session uninstall were
denied while the actual container stayed running. Explicit shared-impact confirm
then used Wright's existing uninstall owner: the process/container stopped and
the registry became inactive/not-installed. Saved configuration, a synthetic
credential-store reference, both workspace memberships and the image remained.

The outer host deliberately withheld the successful uninstall reply. The panel
blocked another write and refreshed saved state without repeating uninstall.
Another workspace saw the same result; current workflow-tool selection omitted
the provider. The fixture still has no local protocol-validation acceptance and
no provider tools/call or engineering run occurred. Uninstall retains downloaded
packages and setup; registration/credential deletion is a separate operation.
Recorded installed-version metadata is not a new upstream version attestation.

Evidence: /tmp/wright-desktop-uninstall-proof-20261017/checkpoint.json and
browser-1792218083496/report.json. This is GB10 ARM64 lifecycle verification in a
labeled simulated desktop frame, not Windows acceptance or catalog installation.

## Desktop custom-command setup qualification

A separate fresh proof used the normal native Add a custom MCP local-command
form and existing source preview → saved plan → approval → apply → protocol
validation → workspace Enable owners. Exact package metadata and its LICENSE
file were inspected in the existing immutable0.0.78 image before recording the
required independent technical source/license review. The unknown-source license
gate remains in place; this is not personal account/terms completion.

An unreviewed source stayed blocked. Stale/foreign approval, validation before
apply and Enable before protocol validation were denied. Withheld approval/apply
replies recovered through saved reads without replay. The actual independent
provider initialized/listed schemas in a bounded read-only/network-none container;
explicit enable applied only to one workspace. One onboarding run and one passed
local protocol validation were recorded; no tools/call or engineering run.
Global support remains uncertain and recorded installed-version metadata null.
The provider was stopped afterward, retaining setup, validation and membership.

Evidence: /tmp/wright-desktop-command-apply-proof-20261017/checkpoint.json,
source-review.json, readback.json and browser-1792219071705/report.json. This is
GB10 ARM64 simulated-host resource/owner qualification, not Windows acceptance,
clean catalog requalification, gateway execution or an engineering demonstration.

## Bugs and maintenance

No new provider defect or issue submission is claimed. Record exact package/browser versions, inputs, actual results and evidence before marking a capability verified. Retain version/platform-specific failures and update this guide after qualification.
