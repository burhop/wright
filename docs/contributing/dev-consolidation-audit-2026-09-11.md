# Dev consolidation audit — 2026-09-11

This record prevents completed work in historical Wright worktrees from being
implemented again. The comparison baseline was `origin/dev` at
`70350874df083ca7b9fedce67e7c8c171860bce5`, after MCP curation PR 124 merged.

## Recovered into the consolidation branch

| Source | Disposition | Preserved result |
| --- | --- | --- |
| Primary checkout metrics work | Ported | `729b0cf3` retains the standalone development dashboard, structured events, history, health endpoint, and publication guidance without embedding the QA dashboard in Wright's product UI. |
| Dirty `codex/080-canonical-workflow-recovery` worktree | Committed and merged | `92a52655` preserves the previously uncommitted workflow implementation; merge `f01bdb6d` reconciles it with the current MCP catalog and native process implementation. |
| `codex/live-qa-20260821-112046` | Product changes retained | `ce56f39c` contributes Rivet run evidence, durable artifact records, confined workspace document production, digest-verified reads, and run-inspection improvements. Its branch-specific EPP program snapshot was excluded after reconciliation because it describes an older exact Git subject and cannot be published as current `dev` evidence. |
| `codex/080-hermes-mcp-isolation` | Partially retained | `4d9ff1da` keeps the Hermes dependency consistency check in future Docker smoke runs. The older all-tools virtual environment change is superseded by the per-tool `uv tool` isolation merged in PR 124. |

The recovered workflow merge keeps the reviewed workspace **Workflows** entry
and `WorkflowRecoveryPage` described in
`docs/contributing/workflow-ui-integration.md`. It also keeps the newer native
process route instead of replacing the reviewed editor with the narrower
native-only canvas.

## Historical branches that do not need replay

| Branch family | Disposition | Reason |
| --- | --- | --- |
| `codex/079-visual-workflow-composition` | Superseded | Its draft model, guarded API, composer, and UI work are ancestors of the fuller 080 recovery now merged. |
| `codex/079-native-*` and `codex/079-scoped-helper-smoke` | Already represented | Current `dev` contains the native process API, runtime persistence, MCP containment, security checks, UI, tests, and later dependency updates. The remaining commit differences are earlier review/probe/governance revisions or older forms of files now present. |
| `codex/081-native-workspace-replacement` | Selectively superseded | Its workspace change replaces the reviewed workflow editor with the narrower native process canvas, contrary to the current integration guidance. The useful Hermes smoke assertion was retained separately. |
| `codex/mcp-curation-lifecycle` | Superseded | PR 124 is the corrected final MCP catalog and status implementation and is already in `dev`. |
| `codex/epp-continued-development` | Historical state only | Contains program-state reconciliation and a revert sequence, with no missing product implementation. |
| `codex/078-process-definition-view-pr117-abandoned` | Historical state only | Contains abandoned program-control transitions and no missing product implementation. |
| Release-candidate and review worktrees | Generated evidence only | Remaining changes are build products, temporary test databases, caches, or historical evidence copies. They are not source inputs to `dev`. |

## Separate repositories

`D:\repos\SolidEdgeMCP` is a separate deliverable and must not be copied into
the Wright repository. Its `codex/bug-fixes` checkout currently contains a
large uncommitted development body (49 tracked files plus new source, tests,
benchmarks, and scripts). Preserve and finish that work in the SolidEdgeMCP
repository, then update Wright's pinned integration revision only after that
repository has a reviewed commit. The other one-level repositories under
`D:\repos` were clean when inspected.

## Focused verification

- Wright web production build passed after both recovery merges.
- MCP catalog, curation, migration, and capability-view checks passed: 25 tests.
- Workflow artifact persistence, workspace document gateway, migration, and
  run-inspection checks passed: 36 tests.
- MCP server setup and qualification suites were intentionally not rerun during
  consolidation so they would not block moving to real workflow work.

For a future audit, compare patch-equivalent commits as well as ancestry:

```powershell
git branch --no-merged origin/dev
git log --right-only --cherry-pick --no-merges origin/dev...<branch>
git diff --name-status origin/dev...<branch>
git worktree list --porcelain
```
