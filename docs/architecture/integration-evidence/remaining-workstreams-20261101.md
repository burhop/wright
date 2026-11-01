# Consolidated outstanding workstreams — 1 November 2026

Status: local integration candidate; qualification and GitHub checks pending.
This records implementation and observed checks, not native Windows acceptance.

## Scope and ownership

The user explicitly included the first-contact/golden-hour work, workflow trace
and reporting, and the earlier opt-in Codex chat adapter. The desktop integration
and Windows reverse-engineering fixes are already in dev through PRs #174 and
#178. This candidate starts from their combined dev tip,
`c072794c61b745183a4d3a16f5cd98ab0521414c`.

The first-contact changes are taken from code-only snapshot
`b001bf6a93da855ccf5bebe92cc7d6d3627a5cf6`. The original campaign history is
preserved locally and is not part of this public integration. Workflow trace
source comes from `c0712255`, applied as a code-only commit without campaign ZIPs
or screenshots. The opt-in chat adapter comes from `25f807f2`. Original worktrees,
uncommitted changes, private evidence and historical runs remain untouched.

## Shared engineering experience

Users choose a workspace, describe the engineering job, inspect and refine its
accepted workflow, supply declared inputs and respond to declared reviews, then
inspect recorded results and their producing steps. The workflow diagram,
source and inspectors remain available alongside optional working process UIs.
Trace and reporting read the same durable run and exact subjects; they do not
execute a second process or grant approval. Missing or changed capabilities stay
explicit. A changed design requires fresh affected checks and approvals.

The integration retains Wright's existing workflow runtime, gateway authority,
validator/repair contracts, process client, UI kit, revision storage and common
view. Interrupted dispatched operations require reconciliation and are never
silently replayed. Native tab selection and Windows delivery remain host-specific
acceptance questions, independent of simulated-host and component checks.

## Reconciliation decisions

- Keep dev's security pins, exact-image checks, Windows junction/confinement
  coverage, both validator readers and the replacement-handle fixtures.
- Refresh gateway tool exposure through the shared workspace owner. Preserve
  explicit configuration isolation and existing manual gateway-refresh support.
- Capture workflow trace through canonical process execution and durable-record
  owners, retaining run-log and cancellation fields.
- Retain both browser callback and device sign-in presentation, with explicitly
  injected device presenters taking precedence. No accounts or credentials change.
- Keep accepted instruction bodies intact. Combined defaults are version 1.4.0
  for newly authored workflows; saved workflows are not silently upgraded.
- Keep the replacement-handle catalog at the incoming explicit 1.0.3 revision.
  Older saved sources and their original provenance remain inspectable; absent
  historical catalog revisions do not acquire current readiness by substitution.
- Keep one MCP selector in the shared editor. An unavailable saved binding stays
  visible with a clear warning rather than being cleared or replaced.
- Preserve accepted connection-point ownership when source edits reuse an
  existing global port identity; cold source reconstruction remains supported.

## Experimental Codex chat scope

The optional adapter uses the pinned `openai-codex==0.162.1` dependency. It is
separate from using the desktop conversation as Wright's LLM harness. Existing
sessions retain their bound platform when defaults change. The previously
accepted experimental chat exception permits remaining native runtime tools;
this does not satisfy Wright's zero-tools contract. Process-UI authoring and
workflow execution through this adapter remain gated. No silent Hermes, model
or authentication fallback is introduced.

## Qualification and limitations

Four bounded CC0 fictional-handle proof files are included so the shipped
recorded preview can verify its receipt, assessment and exact package hash. No
broader campaign history is included. Public docs label private evidence paths
as retained local records rather than offering broken download links.

Raw logs are retained in the local integration evidence directory. Full API:
846 passed. Core: 378 passed. Agent/registry: 1,147 passed, 21 skipped, with the
single expected-version correction passing its 26-test owner suite. Focused API
reconciliation: 80 passed. Focused frontend reconciliation: 173 passed; additional
chat link/status checks: 14 passed. Native panel rebuilt with no external assets.
Remaining focused workspace regressions: 99 passed. These results are preliminary; full merge/pre-push gates and all current-head CI
remain required before merge. No engineering process, protected campaign,
physical operation, personal sign-in or production deployment was started.

Actual Windows panel rendering, viewer preference persistence, file delivery and
chat-switch restoration must not be inferred from local or simulated tests.
Existing UI capabilities and usable common-view fallback remain required.
