# Windows research readiness follow-up

Baseline: `daf1b12c2135902667cc761e42e15ffb95714359` (merged PR166).
Branch: `codex/windows-research-readiness`. The installed 0.19 desktop plugin
and the separate Windows engineering pilot remain unchanged by this worktree.

## Journey and scope

An engineer adds an independent research MCP to an existing workspace, uses
supplied references where sufficient, and researches only missing information
before later engineering work. Adding a provider must preserve the active
workspace/session, isolated model profile and unrelated settings. Missing optional
provenance must not crash dispatch or grant permission to replay an operation.

The current Windows handoffs are PR165 comments
[6304986530](https://github.com/burhop/wright/pull/165#issuecomment-6304986530)
and [6305062857](https://github.com/burhop/wright/pull/165#issuecomment-6305062857).
They distinguish two shared defects from optional-research and PDF capability
gaps. SteveCAD export succeeded for the retained revision; its new export build
and original successful build are separate evidence. Roadster remains held here.

## Tasks and decisions

- [x] Reproduce null provenance and catalog-induced binding loss on current dev.
- [x] Make missing/non-string source provenance conservatively non-repeatable;
      retain explicit read-only/idempotent annotations and existing scoped rules.
- [x] Preserve an existing explicit binding during static/catalog synchronization
      inside the existing atomic config writer. Explicit workspace selection still
      uses the binding owner; no restart, shared-profile change or new lifecycle.
- [x] Qualify source/native bindings, unrelated settings, first dispatch and
      rejected duplicate operations with controlled fixtures.
- [x] Resolve optional research through a typed accepted-source contract or
      existing declared control mechanism. Do not waive mandatory engineering
      tool evidence or force redundant searches. Preserve source/input identities,
      frozen routing, output validation, review and uncertain-outcome handling.
- [x] Run the full local merge gate, exact-image smoke and packaged-artifact checks.
- [ ] Complete the normal pre-push/browser gate and current-head PR CI; publish
      exact commits and scoped evidence to the Windows handoff. Windows owns
      live requalification.

Reuse: `wright_gateway_sync`, atomic YAML merge, accepted source compiler,
`WorkflowMcpRuntime`, run recorder, gateway, instruction assets and existing
validation/recovery. Independent providers own research/engineering protocols.
No new executor, auth framework or UI redesign is part of this correction.
Existing editor/common-view compatibility is preserved; any new accepted setting
must round-trip and unavailable capabilities must remain explicit.

## Evidence index

- Original handoff copies: `/tmp/wright-windows-rebind-evidence-20261020/windows-research-followup-6304986530.json`
  and `windows-research-followup-6305062857.json` in the same directory.
- Focused reproduction and qualification: `.local-run/windows-research-readiness/`
  in this worktree (isolated fixtures, no live engineering).
- Canonical integration status remains
  `/tmp/wright-desktop-resume-evidence-20261019/CURRENT-STATUS.json`.

Implementation, controlled verification, actual Windows use and user acceptance
will be recorded separately. Historical runs and evidence are never rewritten.

## Local implementation checkpoint

The two reported defects reproduced before changes (nine failing cases). The
repairs pass 121 related API/runtime checks. Optional research is implemented as
`mcp_completion_policy: supplied_inputs_or_tools`, requiring saved instruction
asset `context.mcp-input-completion` and explicitly read-only tools. Defaults 1.3.0
add the asset; accepted older instruction bodies are not silently rewritten.

53 focused checks cover supplied-input/tool evidence, denied completion after
failure, metadata drift, saved helper requirements, format repair, same-run
continuation with changed-source rejection and portable transfer. Controlled
Pi enclosure design-basis and Robot Tracking Diagnosis analysis-stage fixtures
preserve their original prompts and template bytes. They do not qualify live
engineering tools or the whole workflows. The existing editor parser/formatter
passes 29 source/diagram save/reopen checks, including the explicit setting.

Initial local failures and the sandbox API wait are retained in the evidence
index, not discarded. The host run completed normally.

**Remaining:** normal pre-push/browser gate, current-head PR CI, exact GitHub
commit delivery and Windows actual request/readiness checks. A research provider without `readOnlyHint=true`
is not automatically reclassified; the optional path remains unavailable for
such tools. A qualified PDF reader is separate provider work. Full engineering
readiness and actual Windows 0.19 panel acceptance remain with their owners.

Focused receipts: `.local-run/windows-research-readiness/focused-evidence.json`.

## Full local qualification

Product commit `3e7ef89b3e6f7ebcb3a2030520e667c7f3374b2f` passes the full
merge gate, exact-image cold API/Hermes smoke and installed-code probe. The wheel
and source archive contain the exact helper, manifest, runtime and binding-owner
bytes. [Portable qualification evidence](evidence/windows-research-20261020/qualification.json)
records source/image/artifact identities, checks and log hashes. Generated native
outputs were archived before restoring this isolated worktree.

The local WebKit library limitation is verified and retained; the normal Chromium
push checks and full GitHub browser/Windows CI remain required. Actual Windows
requests and desktop usability acceptance are separate. No claim of complete
engineering readiness or new live-provider qualification is made.
