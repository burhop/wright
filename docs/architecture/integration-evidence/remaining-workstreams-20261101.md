# Consolidated outstanding workstreams — 1 November 2026

Status: local integration checkpoint; final gate and current-head CI receipts belong on the integration PR.
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
Full workspace suite: 3,146 passed, 13 skipped. Remaining focused workspace regressions: 99 passed. Model registry: 185 passed (performance slice excluded by the normal gate). Image/source-binding and packaging contracts: 145 passed. Synthetic timing/UI fixture reconciliation: 117 passed; synthetic dashboard integrity: 26 passed. These results are preliminary; full merge/pre-push gates and all current-head CI
remain required before merge. No engineering process, protected campaign,
physical operation, personal sign-in or production deployment was started.

Actual Windows panel rendering, viewer preference persistence, file delivery and
chat-switch restoration must not be inferred from local or simulated tests.
Existing UI capabilities and usable common-view fallback remain required.

## Qualification checkpoint

The approved storage and scanner corrections are implemented, with original
negative-test literals preserved. The root preflight passed 2,088 tests (66
skipped); release/native preflight passed 395 (7 skipped), with 86.48% coverage
against the 85% floor. Blocking release types pass. Current lint, formatting,
TypeScript and frontend build pass; workspace creation preserves its original
error cause, with four focused workspace regressions passing.

The product checkpoint is `50d35b493fc15d5202b2abe5adcd13f948a4ca19`.
Its rebuilt ARM64 image is
`sha256:03a1a62a98189d61d77e27306160eaa412ca4cb50ae55b6cd48f5fb70ce83dc7`.
The complete merge gate runs on that frozen source. A separate clean qualification
worktree runs the normal pre-push gate against `origin/dev`, using its own
dependencies, database and ports. Browser fixture corrections follow the visible
workspace picker/New workflow interaction and keep the editor/process mocks on
one exact saved filename; all exact source, result and no-dispatch checks remain.
These test-only corrections do not change the product image.

Chromium and Firefox launch using isolated lockfile-matched browser downloads.
GB10 WebKit cannot launch because `libgstreamer-plugins-bad1.0-0` and `libavif16`
are absent. The local full-gate browser limitation is documented; normal pre-push
Chromium coverage and required CI remain mandatory. No system libraries or live
services were changed for qualification.

This checkpoint does not claim complete gates or CI before their receipts exist.
Merge still requires successful full merge/pre-push qualification and every
required current-head CI result. Actual Windows/native acceptance remains
separate from all local and simulated-host results. No engineering run,
Roadster/protected campaign, physical operation, personal sign-in or production
release is authorized by these qualification records.

## Final consolidation audit

Current dev through PR #179 is reconciled, preserving real Windows junction and
record-read retry assertions. The subsequent changes are gate/test/docs only.
The full merge gate passed on product source `50d35b49`; the normal pre-push
run on `5f1336b1` exited 5 because the selector passed the browser fixture
generator to pytest. That failed run is retained and is not a passing receipt.
The selector now distinguishes pytest test names from helper source, with eight
executed shell-routing regressions; helper changes still select the broad suite.

The old desktop worktrees were compared before integration:

- Reasoning-status readers, cancellation/stale-response tests, private-LAN
  configuration and missing-Web-Crypto handling already have newer maintained
  equivalents in the candidate's same source locations. The original experiments
  remain preserved, rather than replacing newer implementation.
- The native viewer-selection probe and real-registration comparison are already
  present in `prototypes/desktop-harness`; actual native viewer selection remains
  distinct from registration and file-open acknowledgements.
- The old browser correction's common-view/declared-input/recovery targets and
  visible terminal-summary assertions are already in the current gate and tests.
- Hermes SDK usage counters are represented by commit `382acd03` and the current
  `public_usage` owner; Rivet integration was carried forward by `2ce04779` and
  subsequent editor changes. Old branch IDs alone are not evidence of missing code.
- Original Codex adapter planning notes and the untracked
  `desktop-harness-prototype.md` are retained as historical discussion; current
  adapter scope and accepted native-tools exception are recorded above.
- Old trace-worktree apparent deletions, old gate-generated frontend assets,
  screenshots, private campaign/website ZIPs and capture outputs remain local
  evidence or build products. They are not intentional source deletions or new
  feature changes. The detailed path/hash inventory is retained locally as
  `LOCAL-SOURCE-AUDIT.json` in the integration evidence directory.

No local experiment is represented as Windows acceptance. Fresh current-head
pre-push and GitHub CI results still govern publication and merge.

### Onboarding selector correction and retained checks

The cumulative normal pre-push at `c1936631` passed security/history scans,
dependency and exact-image audits, every selected Python suite, 2,308 frontend
unit tests, the production build and all 57 selected Chromium journeys. It then
**failed** four onboarding browser cases using obsolete `Review install plan`
and `Continue to installation` selectors; the live read-only case passed. That
run is retained as failed, not promoted to a green receipt.

The correction changes only the onboarding test's accessible control names and
its existing remote/local distinction. All exact apply-count, credential-boundary,
no-effect, source-normalization and changed-plan conflict assertions remain.
The five-case owner suite passes against an isolated API (32 seconds).
Under the runbook's test-only correction rule, the completed unchanged checks
are retained while the normal fast gate runs against frozen candidate `c1936631`
as its explicit change base. It retains the normal browser baseline, corrected
onboarding suite, read-only live case, frontend checks and strict docs. Full
current-head GitHub CI remains mandatory. This is transparent retained
qualification plus correction checks, not a claim that the failed cumulative
run succeeded.
