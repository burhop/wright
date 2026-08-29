# Quickstart: Browser Program Status Acceptance

This is the planned human-repeatable acceptance path. Commands become executable only after the exact EPP-F01B approval subject and lease are approved.

## Preconditions

- Checkout is clean and on the approved implementation branch.
- The implementation commit matches the active lease.
- No benchmark, product operation, push, publication, or release is implied.

## 1. Publish one committed status bundle

```powershell
uv run python scripts/publish-engineering-program-status.py --repository . --source HEAD --data-root .local-run/program-status-demo/program-status
```

Expected: the exact source catalog validates and its digest is reported; repository validation passes; one `current.json` is atomically installed; and output reports commit, tree, program tree, publisher-attested raw Git-blob digest/evidence, independently recomputed canonical dashboard digest, bundle ID, and path. Re-running unchanged `HEAD` produces identical canonical `source + dashboard + supplement` identity bytes and bundle ID.

## 2. Run focused verification

```powershell
$env:PYTHONPATH = "packages/tool_registry/src"
uv run pytest packages/tool_registry/tests/test_program_status.py
$env:PYTHONPATH = "apps/api/src;packages/tool_registry/src"
uv run pytest apps/api/tests/test_program_status_api.py
Remove-Item Env:PYTHONPATH
uv run pytest tests/program_control_plane/test_program_status_publisher.py
npm --prefix apps/web run test -- --run ProgramStatus
$env:WRIGHT_PLAYWRIGHT_PORT = "5187"
$env:CI = "1"
npx playwright test tests/ui-integration/program-status.spec.ts --project=chromium
```

Expected: valid, corrupt, stale, empty, source-catalog mutation, raw-attestation evidence mismatch, canonical-identity mismatch, current/historical-action conflict, zero-benchmark missing context, correction/finding/verification mislink, non-canonical path, malformed parsed GitHub URL, auth, refresh, accessibility, and deterministic-regeneration cases pass.

## 3. Open the page

Set `$env:WRIGHT_DATA_ROOT = ".local-run/program-status-demo"`, start Wright using the normal local runtime command, then open `http://127.0.0.1:<wright-port>/program-status`. The publisher writes the required `program-status/current.json` child beneath that data root.

Confirm:

1. The first viewport answers how much registered work exists, what exact work is active, why it matters, how much customer capability is implemented, how tests are trending, and what changes next.
2. Program-wide registered task totals are separate from active-feature totals; undecomposed roadmap work is disclosed; active-agent rows either cite exact assignment/lease evidence or say unavailable.
3. The all-use-case funnel is recomputable from typed per-use-case evidence whose exact subjects resolve through the stage's catalog-allowed source and named parser. It distinguishes in-progress, user-accepted implementation, and acceptance-bound independent verification with a verifier different from the evidence author. The 100-process subset uses unique `EPP-PROC-001..100` IDs and separately distinguishes defined, implemented, tested, independently verified, and dashboard-reconciled benchmark-qualified; remaining means total minus implemented.
4. `100 proposed customer stories` remains separate from both governed use-case funnels and qualified benchmark results.
5. Test history uses exact times, commits, suites, selected run IDs/keys, terminal/aggregate roles, collected case identities/digests, and canonical counts; `total` equals both the identity count and outcome sum; Python/TypeScript golden fixtures agree on NFC/UTF-8 framed identity/run-key bytes and canonical-JSON runs bytes; append-only continuity and latest selection are publisher-attested, while projected digests/disjointness/arithmetic/pass rate are independently recomputable; unsupported categories say unavailable.
6. Four independent readiness areas and non-compensating release state are clear. Benchmark is honestly `0/100` with typed phase, hold reason, dependencies, authority, and non-governing next qualifying action.
7. Task burn-up, use-case funnels, test outcomes, roadmap/customer capability, readiness, and benchmark charts explain meaning, latest change, limitation, and next evidence-backed action and all have semantic tables.
8. The dashboard's old action is visibly historical, exactly one current program action comes from current program state, and metric/lane guidance cannot supersede it.
9. Integration/CI and continued-development lanes have distinct branches and purpose-labeled actions.
10. Evidence details use canonical relative paths and parsed-safe URLs, expose freshness/recovery without sensitive content, and show reciprocal correction/finding/verification links plus verdict/blocking outcome.

## 4. Demonstrate failure containment

Alter an isolated copy of the demo projection without changing its envelope digest. Do not edit committed evidence.

Expected: the fixture is rejected; the last valid page remains visible and is labeled failed/stale with recovery. Repeat with a duplicated/out-of-range process ID; wrong stage source, nonexistent subject, resolved-verdict mismatch, or equal evidence author/verifier; acceptance-unbound independent verification; duplicate/conflicting test run key; rewritten prior ledger prefix; cross-language digest mismatch; `total != len(test_case_ids)`; overlapping component test identity; and missing packaged dashboard schema. Starting without a valid bundle shows unavailable values only.

## 5. Demonstrate committed refresh

Start the standard contributor publisher in a third terminal, then commit an isolated approved fixture change while the page remains open:

```powershell
uv run python scripts/publish-engineering-program-status.py --repository . --source HEAD --watch-committed --data-root .local-run/program-status-demo/program-status
```

Expected: the watcher uses its declared two-second default; within 10 seconds it observes the new committed identity, atomically installs it, the ETag changes, and every panel swaps together. Unchanged identity returns 304 and adds no history point. The separate publisher endpoint and refresh state show activity or bounded failure without changing bundle identity.

## 6. Delivery gates

After implementation authority exists, run normal repository checks, packaged-runtime smoke without `.git` or network, and then the dev push/merge runbooks. Direct push to `dev` is never permitted.

## Executed acceptance checkpoint — 2026-08-29

The human-repeatable path above was executed locally against exact commit `25dad93f01cb942f271f815bf7b85ad3f9aaae2a` (tree `6dd5795228146cead31a6c86a419c4deb1f50313`, program tree `b13ebef292935ac0676022c5dc15ca664c82eab2`). No benchmark, dependency, network, push, PR, merge, publication, release, or customer/product operation ran.

- Corrected the publish example after the first literal run failed closed because `--repository` was absent. The corrected command installed bundle `b0fc25a943e35bea8681649f2cb1479d4aa35924373b679bf07fbf0919f41b07`; its second run reported `changed=false`, and `current.json` remained byte-identical with SHA-256 `8393b826d597a6d64ff05f932961fe648cd6d4475b2e39c7b9d3aa95b686516b`.
- The installed bundle passed source-free `ProgramStatusReader` validation. The focused reader suite passed 18/18 and the authenticated API suite passed 5/5.
- The full publisher suite passed 30/30 in 388.79 seconds, including closed-source mutation, action and benchmark authority, work/use-case/test arithmetic, wrong/missing evidence, reciprocal correction relationships, deterministic history, exact paths/URLs, replacement containment, and deterministic regeneration.
- The focused browser suite passed 28/28 after synchronizing one legacy empty-use-case fixture with the required `items: []` and `benchmark_summary` fields.
- The isolated-port Chromium walkthrough passed 4/4: six-question comprehension, accessible graph/table fallbacks, exact committed atomic refresh plus heartbeat, and last-valid/unavailable failure containment. The initial default-port run was invalid because Playwright reused an unrelated stale Wright server; the documented isolated-port command prevents recurrence.
- Current truthful limitations: the governed use-case registry and canonical test-run ledger contain no delivery observations; active assignment evidence is absent; benchmark execution is unauthorized and remains `0/100`; readiness and release eligibility are unchanged.
