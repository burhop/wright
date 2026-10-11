# Local experimental chat candidate

The accepted chat-only pilot is implemented on `codex/codex-platform-integration`,
based on fetched dev `ba2fad68c181165b96b9c15c40b1a1f63c88acb3`. It adds the official
pinned SDK/runtime adapter, private worker, platform-bound sessions, streaming,
readiness/catalog, one scoped read-only gateway operation, history/continuation,
cancellation and durable explicit terminal/unknown outcomes. It freezes actual
instructions/config/tool identity and rejects drift or uncertain automatic replay.

Remaining Codex native tools are an accepted experimental chat exception. Zero-tools
remains FAILED. All Codex process-UI model authoring and workflow starts remain gated,
including legacy native aliases and cached Hermes substitution. Wright retains its
executor, gateway permissions, accepted definitions, reviews and recovery. Manual
editor and existing-platform behavior were preserved; no tool authority was extended.

Real pinned-runtime gateway/lifecycle fixtures, bounded authenticated ChatGPT chat
restart, actual served workspace chat/history/API restart and 15 current editor cases
passed. Scoped Python/frontend regressions and frontend build passed. Exact counts,
retained failures, source hashes and official sources are in [evidence](evidence.md)
and the [capability/version matrix](qualification.md). The candidate is reviewable;
full repository/host qualification is incomplete and no merge-readiness is claimed.

No push, merge, release, live configuration change, engineering campaign resumption
or physical action occurred. Original clean dev/install/auth and existing evidence
remain separate. Owned pilot processes were stopped and disposable auth copies removed.
No engineering run/review/model-authoring job was created in the isolated UI database.

## Integration strategy

Keep this worktree/branch independent of the MCP-server testing/catalog-fix branch.
This candidate changes adapter/host composition and adds a scoped callback; it does
not alter shared gateway implementation or catalog entries. Database, runtime home,
workspace, ports and test outputs are isolated. Local commit identities are recorded
by Git; no remote branch or PR has been created.

Before any future authorized push, fetch dev, compare the current candidate against
both new dev and the MCP branch, resolve shared API/session conflicts in this branch,
and rerun affected regressions plus the repository push/merge gates. Do not overwrite
original evidence. Build the immutable image once from the clean committed archive;
retain scanner/image/source identities. A missing/failed gate is not waived because
this is experimental. Push/merge require separate authorization.

## Remaining stages and decisions

1. Complete immutable candidate image/security/packaged checks and full repository gates;
   address the independent exact-byte baseline defect through provenance review.
2. Use [Windows handoff](windows-handoff.md) for native isolation/ACL/descendant cleanup
   and served behavior. Linux x64 and Docker require distinct runtime proof.
3. Wait for released public startup tool-ceiling support; then prove empty and
   gateway-only sets before adding confined authoring or workflow-task dispatch.
4. Reuse versioned role assets, builder/preview/revisions/common view for authoring,
   and Wright's frozen routing/bounded decision loop/validation/recovery for tasks.
   Qualify fresh unchanged manufacturing-preparation and Robot Diagnosis copies.
5. API-key billing/auth identity, broader models/MCP tools and dollar-cost UI need
   explicit scope choices and independent qualification. No fallback is enabled.

No further input is needed for the already accepted GB10 chat scope. The current
experimental/native-tool exception and role gates remain in force for review.
The [proposed PR description](proposed-pr.md) describes the delivered scope and limits.
