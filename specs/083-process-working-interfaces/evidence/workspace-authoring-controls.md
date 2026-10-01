# Workspace authoring controls and native host connection

**Date:** 2026-10-01. **Branch:** `codex/083-process-working-interfaces`.
**Parent:** `7074ca495f3503ee1e68d29e236289f6fd6e1f2f`.
**Scope:** T039 implementation; T037/T041 browser acceptance remains pending.

## Implemented

The existing workspace process document offers Create/Update, visible generation
progress, exact preview/save, saved revision selection, compatibility checks and
rollback controls. Preview and working interfaces open through the current
workspace document strip. The existing common view remains available on the same
process and run. No second editor, browser window, process executor or vendor
controller is introduced.

Local recovery stores only validated request/job locators, scoped by process,
session and view. A known job is observed without generation. An uncertain
request requires explicit reconciliation with the same identity. Unavailable
storage blocks submitting a request whose identity could otherwise be lost.
Saving requires the server's recorded loaded-preview observation and exact build
hashes. Saved interfaces remain selectable when authoring capability lookup fails.

The existing `LiveAppSurface` accepts a native-issued presentation without using
the generic application's different principal fallback. Closing revokes only the
presentation/runtime. Deferred cleanup handles StrictMode and late open replies;
it does not cancel or restart a process.

The fixed runtime and trusted workspace host exchange a bounded handshake with
exact origin, frame window, presentation, generation and nonce checks. Only
allowlisted theme tokens and validated navigation locators cross the frame.
Navigation is resolved again by the native scoped client. A trusted handshake
can promote the existing presenter's initially unconfirmed frame status to ready.

Before the presentation bridge delegates a start to the existing runtime, it
retains one immutable view/request/input association in the existing UI metadata
repository. This record is a locator, not execution status or permission. The
native receipt endpoint verifies the current owned view/grant/association and
reads the existing start receipt. A frame signal cannot supply a run identity.
A different request cannot replace an uncertain start within that view; preparing
another run requires another view. No receipt means explicit reconciliation,
not automatic submission. The host attaches a confirmed receipt using the
existing document/run callback, then opens a fresh run-bound presentation.

## Checked scope

- **127 backend checks passed**, zero skips, 68.06 seconds: existing authoring API,
  surface authority, fixed static assets, managed presentation owners, new start
  association, additive repository migrations and owning core/client contracts.
- **120 frontend checks passed**, ten files, 21.42 seconds: native client,
  recovery, exact frame connection, tab/query/store restoration, authoring panel,
  presentation lifetime, common fallback and existing presenter behavior.
- App TypeScript passed. Generator consistency, lint, runtime JavaScript syntax,
  whitespace and preservation results are retained in the checkpoint manifest.

The service tests use actual repositories and owners with controlled model,
compiler and runtime ports. One controlled source run confirms repeated receipt
reads do not replay its two tasks. Preview observation in API/service fixtures
remains synthetic. DOM/component tests do not establish actual frame networking,
managed worker launch or served workspace acceptance.

Earlier checks exposed the existing descriptor's dictionary/camel-case instance
projection, a doubly encoded native request, mutable recovery scope, blank theme
values and assertions using different HTTP error mappings. These were corrected
without weakening authority or changing the existing error mapping.

See [checked scope](../../../../artifacts/process-interfaces/083/20261001-workspace-authoring-controls/checked-scope.json)
for commands, source hashes, logs and preserved original/protected work.

## Required next work

T034/T037 need an actual managed browser launch and host interaction. T041/T042
need the served workspace authoring journey, actual configured-model generation,
preview/save/update/reuse, layout/theme/accessibility and recovery proof. The
initial fresh-shell model preflight did not enable the qualified Hermes model SDK
transport; ordinary Hermes chat is deliberately insufficient for this confined
role. Restore the qualified host configuration before the live authoring proof.

T021, packed compiler resources in T032, both live engineering chains, migration,
distribution and M5 acceptance remain pending. This checkpoint is not full goal
completion, engineering acceptance, physical dispatch or user acceptance.
