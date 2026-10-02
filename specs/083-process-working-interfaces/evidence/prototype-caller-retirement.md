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
