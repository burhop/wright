# Prototype caller retirement — 2 October 2026

**Scope:** source/API/component checkpoint. T048/T049 remain incomplete.

New work already uses the common or saved working interface on the accepted
process/durable run. Historical `printDemoRun` links continue through the neutral
read-only recorder adapter. This change retires the obsolete operational entry
points rather than wrapping their vendor implementation in another service.

## Current dispositions

| Location | Change and retained boundary |
| --- | --- |
| API startup | Removed the existing uncommitted Studio restoration hook. Generic catalog/installed-server reconciliation remains intact. Original edited bytes are preserved privately. |
| Workspace API | Removed preparation, capability/status polling, dispatch, dispatch observation, retry, cancellation and camera handlers. A hidden GET/POST compatibility handler returns HTTP 410 `PROTOTYPE_RETIRED`; it has no workspace/gateway/body dependencies and cannot contact a provider. |
| Workspace schemas | Removed three obsolete prototype request models. Shared process/run/action/validation schemas retain their own authority. |
| Native web client | Removed prototype operational methods and vendor status/slot types. Retained the existing canonical image-upload operation under the neutral `uploadWorkflowImage` name. |
| Unused prototype page/style | Removed `PrintPartDemoPage.tsx` and its stylesheet after verifying the shared/history entry has no import. The original edited page bytes are preserved privately. |

No workflow, run, validation profile, review, output or campaign counter was
changed. No provider invocation, print, cancellation or other external effect
was submitted. Compatibility replies do not claim a printer stopped or a previous
dispatch failed. Existing saved-result navigation remains an exact, read-only
identity check.

## Preservation

Before edits, copied and byte-verified 15 files under
`.local-run/process-interfaces-083/t048-retirement-preserved-001/files/`, with
their original relative paths, hashes and original uncommitted binary patch.
This includes every existing mixed prototype edit and untracked experiment.
The archive is private, ignored, inactive and excluded from distributions; it is
not an external vendor project or an installed integration. It permits restoring
the original user work without retaining vendor operations in the product path.

The current preservation check verifies every archived byte, protected campaign
hash, approved context pointer and nonretired prototype byte. The former
`t047-resumed-preservation.py` expects deliberately retired active locations and
is superseded for this migration by `t048-check-preservation-001.py`. Do not
interpret deliberate removal of these callers as permission to change unrelated
work or to discard the preserved original edits.

## Verification and remaining work

- Eight inert endpoint cases plus schema/authority checks and historical reader:
  14 passed in 2.02 seconds; two existing dependency warnings.
- Historical-result/workspace-tab components: 14 passed across two modules.
- Full web TypeScript check passed with an isolated incremental cache.
- Ruff checks pass on affected Python files; new test formatting passes.
- Initial test fixture incorrectly mounted the router at `/api` instead of its
  actual `/api/workspace` prefix. Its eight 404 failures are retained separately;
  the corrected fixture and final tests pass. No product route was changed to
  accommodate that fixture error.

This does not remove the remaining service modules, protocol/Studio scripts,
transitive slicing/campaign bindings or their tests. Those need separate caller
disposition and provider-boundary verification. The live installed hosts still
use the previous candidate; a fresh installed history/retirement walkthrough is
required before closing T048/T049. Both engineering second-run reviews remain
unanswered. Full Feature 083 completion, release and human acceptance are unproven.

## Device and Studio source retirement checkpoint

The subsequent dependency audit found no application or shared-owner caller of
the two prototype service modules. Their remaining dependencies were confined to
the prototype set and its vendor-specific test. Removed eleven source files:

- `workspace_service/print_part_demo.py` and `print_part_demo_printer.py`.
- `configure_print_demo_offline.py` and `configure_print_demo_studio.py`.
- `print_demo_p1s_mcp.py`, `print_demo_p1s_session.py`, and `print_demo_p1s_transfer.py`.
- `print_demo_studio.py` and both Windows Studio inspection/automation helpers.
- `tests/test_print_demo_dispatch.py`, which tested the removed vendor code.

This removes repository-specific template setup, vendor status interpretation,
device transfer/control/camera and Studio automation. Shared execution, action
authority, observations, validation and read-only history retain existing owners.
It does not create another vendor adapter.

All eleven files were verified against private exact-byte snapshots before
removal. Eight were already in snapshot 001; three additional session/transfer/
test sources are in `t048-retirement-preserved-002`. The current checker verifies
all 18 archived files and permits these deliberate active-source removals. Seven
removed files were tracked; four automation experiments were untracked and remain
available in the archive. The untracked Studio documentation remains unchanged.
No user workspace, provider configuration, review, campaign counter or artifact
was modified. The first removal was filesystem-denied before any source removal;
the authorized retry checked exact paths and hashes again before completion.

Previously configured commands referencing deleted scripts need independently
qualified bindings before reuse. No saved command was silently replaced or
re-executed. Existing historical data remains available read-only.

Initial regression results were 39 passes and 23 setup errors: pytest's default
temporary directory was outside the writable workspace. The report is retained
as `temp-fixture-failure-001.xml`. A fresh workspace-local fixture passed all 62
checks: inert retired endpoints, exact read-only history, shared action execution,
async observations, scoped action authority and three package-owner isolation
checks. Two existing dependency warnings remain. Ruff and preservation checks
pass. These tests do not validate removed vendor implementations.

Three installed-resource tests also pass in 53.72 seconds. Newly built aggregate,
private-service and source-archive-rebuilt wheels retain public client/kit/static
resources and exclude both retired service modules. This is package-resource
proof, separate from installed browser acceptance.

Dataset/jig slicing wrappers still have campaign/proof dependencies. Independent
provider qualification, their disposition, the complete engineering replacement
and fresh installed historical navigation remain pending. T048/T049 stay open.

## Installed history continuation

The subsequent [installed history proof](installed-history-retirement.md) uses a
new aggregate wheel with retired modules absent. Six native browser checks now
pass on copied retained canonical history, including editor return and exact
recorder file tabs; eight retired URLs return inert 410 replies. Source/run and
durable UI/continuation hashes are unchanged. Two earlier fixture failures are
preserved. Original user prototype data shapes, transitive slicing and complete
engineering replacement remain unverified; T048/T049 stay open.
