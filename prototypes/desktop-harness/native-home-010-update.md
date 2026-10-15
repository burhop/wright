# Named 0.10.0 candidate qualification and rollback

Installed and exact-package verified; Windows acceptance pending. The saved goal authorizes this named update after exact
qualification and private backup. No other plugin, setting or service changes.

Candidate runtime: /tmp/wright-desktop-template-entry, code ab3ba5f7.
Marketplace: prototypes/desktop-harness/native-home-010-candidate.
Fresh state: /tmp/wright-desktop-home-010-state-20261015-01; API 8163.
Enable desktop bridge, native editor, working view and local reviews only.
Image inputs, confined inspection and enrolled MCP tasks remain disabled.

Changes: New workflow and Use a template in Workflows, using shared source and
template owners; retains workspace Refresh and same-run review/Continue.
34 tools; the two added operations list templates and create a scoped copy.
No new executor, direct engineering tools or generated-UI authority.

Before installation: qualify the actual package command/resource and combined
profile, run browser creation/template/editor checks, and recheck local review
continuation. Record failures and exact hashes. Back up the current named
selection and every cached version privately; compare all other config before
and after. Preserve existing 0.9 service, state and old cache bytes.

Apply only after those checks:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-template-entry/prototypes/desktop-harness/native-home-010-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Scoped rollback to the preserved 0.9 runtime:

```sh
codex plugin marketplace remove wright-desktop-gb10-prototype --json
codex plugin marketplace add /tmp/wright-desktop-continuation-candidate/prototypes/desktop-harness/native-home-09-candidate --json
codex plugin add wright-desktop-gb10-prototype@wright-desktop-gb10-prototype --json
```

Do not restore an entire config over unrelated changes. Restore older named
cache files if the CLI evicts them; compare their hashes. Verify installed
manifest, package files, tools and resource against candidate receipts.
No desktop restart. Windows rendering/interaction remains a separate acceptance
check; local browser tests and installation cannot establish it.

Official package documentation rechecked 15 October 2026:
https://developers.openai.com/plugins/build/plugins
Repository gates on the parent do not qualify this candidate's later changes.

## Qualification checkpoint

Actual package MCP 2025-11-25: 34 tools, exact 2,225,204-byte resource.
Eleven actual MCP/browser checks passed with no browser errors, including Robot
and manufacturing template copies at narrow/wide widths. The combined profile
also completed a fresh private synthetic review/continue run across reconnects;
a stale subject was denied. See native-home-010-evidence.json.
Named update applied with private backup and all 18 old cache files preserved.
Installed protocol/resource/package hashes match the tested candidate. No unrelated
configuration changed. See installed-010-evidence.json. Repository qualification is separate.
