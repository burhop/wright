# Playwright MCP usage guide

Last updated:16 October2026. Status: existing bundled provider; new desktop-workspace qualification pending. No engineering workflow or Windows desktop acceptance is claimed.

## Identity and sources

Independent provider: [Microsoft Playwright MCP](https://github.com/microsoft/playwright-mcp/tree/5f8fc00210b27b4407c375b59cda4838045d429c). The ARM64 engineering bundle pins @playwright/mcp0.0.78; separate historical [0.0.80 preflight](../evidence/curation-2026-09-09/playwright-mcp-0.0.80-preflight.json) does not qualify0.0.78. Read the [setup recipes](../mcp-server-setup-recipes.md) and docker/mcp-bundle.linux-arm64.yaml before use. Do not install the latest package silently.

## Installation and readiness

The selected existing ARM64 image wright-desktop-engineering:download-ca71bf92 has image ID sha256:d2251671c9b658b027342931c68b5114076684deecb298828bb0e420852176ab. Its bundle build/service smoke passed; browser operation requires separate evidence. Use an isolated disposable browser context, headless Chromium and the selected container executable. No personal browser profile, credentials, host filesystem mount or external network is needed for an about:blank tab-list proof.

## Verified workflows and successful calls

Initial standalone initialization and tools/list succeeded (server reports1.62.0-alpha-1783623505000). The first browser_tabs list call returned an explicit missing chrome-for-testing error: the caller omitted the bundle's PLAYWRIGHT_BROWSERS_PATH environment setting. The corrected prerequisite uses that exact recorded setting and the read-only browser_snapshot tool; it completed against an isolated about:blank page with isError=false. The initial and corrected containers both terminated after their bounded calls. This is a caller configuration failure, not a provider bug. Evidence: /tmp/wright-desktop-workspace-tools-proof-20261017/provider.json and provider-corrected.json. The verified standalone prerequisite is initialize, tools/list and browser_snapshot with an empty argument object. Its result reports Page URL: about:blank and an empty accessibility tree. browser_tabs combines read and destructive variants, so its annotations must not be rewritten as read-only just because one action is list. The selected browser_snapshot schema reports readOnlyHint=true and destructiveHint=false; the proof supplies no filename. Subsequent Wright qualification must use the normal gateway workspace binding and desktop reasoning callback, with exact tool schema/evidence and denied-membership controls. Standalone success alone does not qualify a workflow or the Windows panel.

## Pitfalls and recovery

Do not confuse Playwright MCP with browser controls in the desktop harness. Tool-list discovery does not prove browser startup. Preserve exact initialization/launch errors; do not replace the provider or weaken permissions. After an uncertain operation, inspect the existing operation/container before retrying.

## Validation, authority and limitations

The independent provider owns browser interaction. Wright owns tool authority, accepted workflow, durable run and recorded outputs. New proof is confined to a disposable local context. It proves browser-tool integration rather than CAD/engineering compliance or user acceptance. No shared live workspace or protected campaign may be used.

## Bugs and maintenance

No new provider defect or issue submission is claimed. Record exact package/browser versions, inputs, actual results and evidence before marking a capability verified. Retain version/platform-specific failures and update this guide after qualification.
