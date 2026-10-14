# Wright inside the OpenAI desktop harness

**Forward plan, updated 14 October 2026:** see
[Desktop engineering-demo readiness](demo-readiness-plan.md) and its
[proposed implementation goal](demo-readiness-goal.md).

The remainder of this file records the initial prototype plan and checkpoints.
Its installation, branch and authorization statements are historical; they are
not the current baseline. The approved 0.4.0 desktop plugin is installed, and
PR 153 contains the later integration candidate. Preserve this record and the
separate Codex-inside-Wright chat pilot.

## Baseline and authority

- GB10 Linux ARM64, Python 3.13.12; branch
  `codex/openai-desktop-harness-prototype`, freshly fetched dev
  `ba2fad68c181165b96b9c15c40b1a1f63c88acb3`.
- Original checkout remains dev `a4a31c97`; prior pilot and its dirty planning
  documents are preserved at `/tmp/wright-codex-platform-integration`.
- Locked dependencies installed only in this worktree's `.venv`, using
  `UV_CACHE_DIR=/tmp/wright-desktop-prototype-uv-cache uv sync --frozen
  --all-packages --all-groups --extra runtime`.
- Installed CLI reports 0.159.2; this does **not** establish the GUI build.
- Local implementation, tests, isolated digital runs and commits authorized.
  No push, merge, live configuration change, physical action or protected run.

## Journey and tasks

1. Implement and test a durable scoped reasoning request/response handoff at the
   existing source executor callback. Prove a live answer from this desktop
   conversation before investing in UI integration.
2. Freeze the qualified desktop connection and instruction identity; distinguish
   reported models from verified routing. Reject drift and duplicate/stale replies.
3. Connect through a small authenticated MCP plugin using existing workspace,
   accepted-source, process and gateway services. Prepare exact connection changes
   and rollback before requesting permission to modify live desktop settings.
4. Host the existing workspace UI beside the desktop conversation. Remove chat
   and unnecessary agent activation only in opt-in hosted mode. Verify Workflows
   entry, editing, saving, working views and existing standalone behavior.
5. Complete a small real digital reasoning + gateway + declared-input/review run.
   Reconcile the same durable run after interruption; never replay uncertain work.
6. Exercise fresh manufacturing-preparation and Robot Tracking Diagnosis copies.
   Regress changed shared boundaries and existing platforms.
7. Supply reproducible startup/connection instructions, limitations, evidence and
   social-ready screenshots/captions. Completion requires the full desktop journey.

## Decisions and boundaries

The prepared Windows baseline is preserved at its original worktree/startup
paths, clean and detached at local checkpoint `a17acb851b8ab978fdb619d318c9a6b67458af3e`.
Development continues on `codex/openai-desktop-harness-prototype` in
`/tmp/wright-openai-desktop-harness-prototype-next` with its own locked environment.
No source bytes, private state or live settings in the Windows target were
replaced. No merge, push or release occurred. The qualified four-line admission
patch is applied only in the new development checkout; its adapter/probe/test
formatting is corrected there. Fresh leased response/action proofs qualify the recorded local boundaries,
including response-task API-restart retention and late-answer denial. Installed
Windows loading and any connected-target promotion require separate explicit setup.

- Wright owns graph execution, state, validation, reviews, gateway permissions and
  recovery. The plugin transports bounded tasks and results; it is not an executor.
- Desktop conversation supplies reasoning. No Hermes, SDK/app-server worker or
  alternate authentication/model fallback can satisfy this demonstration.
- Request handoff receipts belong in the existing Data Vault SQLite store. They
  do not become another run-status authority. Exact instructions reuse saved
  assets; no behavioral policy in adapter literals.
- Earlier zero-tools failures and chat-only exception remain valid evidence.
  This boundary needs separate qualification; prompts do not enforce permissions.
- Browser-hosted Wright is acceptable for the prototype but is not a native
  plugin panel. GUI build, direct connection, remote-host accessibility, model
  attestation, usage visibility and global native-tool enforcement remain unverified.

## Evidence and progress gallery

See [evidence.md](evidence.md). Add real screenshots at workspace/editor, live run
and continuation milestones, with short captions and precise demonstrated scope.
Never present concept art as implementation or publish externally.

## Current checkpoint

- Durable handoff and per-run callback dispatch implemented; actual desktop
  replies completed a canonical run through the pinned MCP protocol client.
- Hosted UI preserves the existing editor and common view without mounting
  Wright chat or requesting agent/inference APIs in the recorded browser journey.
- Synthetic declared-input run completed under the same ID after MCP disconnect
  and controlled API restart; invalid input and boundary denials are recorded.
- Local plugin package and minimal configuration/rollback candidate prepared.
  The user confirmed a Windows desktop and requested a handoff. GB10 plugin
  registration is not the selected route; no live installation is authorized.
  Prepare the Windows stdio/SSH and browser-forward candidate for exact review.
  The credential-free handoff archive, relay prompt, actual screenshots and
  canonical source example are prepared. Executable/authorized SSH alias and
  installed desktop/rendering proof require Windows observations.
- Exact read-only gateway/action-task qualification now passes locally over
  MCP, including reconnect without inspection replay. Fresh original
  manufacturing and Robot Tracking copies, full editor acceptance, abrupt liveness/recovery, installed
  desktop-plugin behavior and desktop right-panel rendering remain outstanding.
- Native workflow MCP discovery intentionally excludes management tools. The next
  read-only gateway experiment should reuse the existing
  `wright-workspace-files__inspect_file` capability and its exact enrolled
  source/input/schema authority; do not weaken that management-tool exclusion.
  Its test enrollment is not an engineering review or external-action grant.
- The preceding prompt-writing turn made no implementation progress. The current
  turn adds real confined gateway/MCP action, denied authority, same-run reconnect,
  served screenshot and 114-test regression evidence. See qualified-gateway-evidence.json.
