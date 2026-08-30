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

## Closure verification checkpoint — 2026-08-29 18:28–18:46 EDT

Exact source checkpoint `1a2cebb42e4ce7b24ed48dceda6281cd39c68e02` adds one closed runtime/browser relation: every `test_evidence` history observation must match exactly one canonical test checkpoint by commit and observation time, and its complete evidence-identity set must equal that checkpoint's selected suite-source evidence set. No readiness, benchmark, dependency, or external action changed.

| Area | Exact command | Result |
| --- | --- | --- |
| Runtime relationship and negatives | `$env:PYTHONPATH='packages/tool_registry/src'; D:\repos\wright\.venv\Scripts\python.exe -m pytest packages/tool_registry/tests/test_program_status.py -q -p no:cacheprovider --basetemp D:\repos\wright\test-results\epp-f01b-runtime-closure-20260829-1828` | `18 passed in 11.71s`; commit and timestamp corruption are rejected. |
| Browser relationship and negatives | `npm --prefix apps/web run test -- --run ProgramStatusRefresh` | `14 passed`; commit, timestamp, and selected-evidence mismatches are rejected. |
| Full program control | `D:\repos\wright\.venv\Scripts\python.exe -m pytest tests/program_control_plane -q -p no:cacheprovider --basetemp D:\repos\wright\test-results\epp-f01b-program-control-closure-20260829-1832` | `308 passed, 1 declared skip in 812.16s`. |
| Runtime/API/package/native/security slice | `$env:PYTHONPATH='packages/tool_registry/src;apps/api/src'; D:\repos\wright\.venv\Scripts\python.exe -m pytest packages/tool_registry/tests/test_program_status.py apps/api/tests/test_program_status_api.py tests/e2e/test_program_status.py tests/packaging/test_wheel_contents.py tests/native_runtime/test_program_status_lifecycle.py tests/test_security_scanner_setup.py -q -p no:cacheprovider --import-mode=importlib --basetemp D:\repos\wright\test-results\epp-f01b-focused-closure-escalated-20260829-1835` | `32 passed` with two deprecation warnings. The first sandboxed run produced five setup errors only because it could not stat the user's local Hermes executable; the identical permission-enabled rerun passed. |
| Full browser regression | `npm --prefix apps/web run test -- --run` | `99 files, 404 tests passed` in `105.75s`. |
| Browser type and production build | `npm --prefix apps/web run build` | TypeScript project build and Vite production build passed. The first sandboxed build could not replace generated `dist`; the identical permission-enabled rerun passed. |
| Python lint and format | `D:\repos\wright\.venv\Scripts\ruff.exe check --no-cache scripts/validate-engineering-process-program.py scripts/program_control tests/program_control_plane apps/api packages/core packages/agent_adapters packages/tool_registry packages/data_vault packages/workspace_service` and the same targets with `ruff format --check --no-cache` | Lint passed; all `570` files passed format after normalizing one working-tree-only mixed line ending in `apps/api/src/api/composition.py`. Git content remained unchanged. |
| Browser format | `npm exec prettier -- --check src/services/program-status.ts src/__tests__/ProgramStatusRefresh.test.ts` from `apps/web` | Passed. |
| Strict release type gate | `D:\repos\wright\.venv\Scripts\python.exe -m mypy scripts/release src/wright_engineering --ignore-missing-imports --cache-dir D:\repos\wright\test-results\epp-f01b-mypy-push-20260829-1839` | `Success: no issues found in 32 source files`. |
| Broader diagnostic MyPy | `D:\repos\wright\.venv\Scripts\python.exe -m mypy scripts/release scripts/program_control src/wright_engineering packages/tool_registry/src/tool_registry/program_status.py --ignore-missing-imports --cache-dir D:\repos\wright\test-results\epp-f01b-mypy-cache-20260829-1837` | `47` existing warning-mode errors across `tool_registry`; the two `program_status.py` locations blame to earlier commits `f075328c` and `dbb19e6e`, not this closure repair. This is recorded baseline debt, not converted to a pass. |

## Final local and Linux verification — candidate `d3119acc` — 2026-08-29

The approved append-only lease-checkpoint correction is committed at `7aa9816be4a7b0e5d9774cc3436fc71f7e7c964a`. The single authorized deterministic packaged-browser rebuild is committed at exact candidate `d3119accd82d0d16a33a87255856d75b02a5f15b` (tree `cc6a0e1adb90708461ee52f87f460507b4a67c45`, program tree `295324e6922ab0bab7db08f12dc0fa805d6d3389`). The committed validator passed with zero blockers; readiness, benchmark `0/100`, release eligibility, dependencies, and public contracts remain unchanged.

| Area | Exact command or evidence | Result |
| --- | --- | --- |
| Committed validator | `D:\repos\wright\.venv\Scripts\python.exe scripts\validate-engineering-process-program.py validate --source d3119accd82d0d16a33a87255856d75b02a5f15b --format text` | Passed; exact commit/tree/program tree, clean worktree, and zero validation blockers. |
| Full local program control | `D:\repos\wright\.venv\Scripts\python.exe -m pytest tests\program_control_plane -q -p no:cacheprovider --basetemp D:\repos\wright\test-results\epp-f01b-d3119acc-program-control` | `311 passed, 1 declared skip in 781.31s`. |
| Deterministic package rebuild | `D:\repos\wright\.venv\Scripts\python.exe scripts/build-native-runtime.py --skip-frontend-build --output D:\repos\wright\test-results\epp-f01b-closure-runtime-20260829T2320Z --evidence D:\repos\wright\test-results\epp-f01b-closure-runtime-20260829T2320Z.json` | Wheel `71d166ae…`, sdist `bbbb1bf4…`, UI manifest `81a1291c2c3c27f67ccb2a5105b00f9cbcd89176d426f76b42a1f0d3bb73e88b`, runtime lock `5ee9590e5d906448aa86d75a15fd145fa85dc3e6b9e40e8594e5117b8f6e4896`; only authorized packaged web assets changed. |
| Packaged browser and refresh | Focused packaged-browser and refresh suites against the rebuilt assets | `15 passed`. |
| Packaged runtime/API/native/security | `$env:PYTHONPATH='packages/tool_registry/src;apps/api/src'; D:\repos\wright\.venv\Scripts\python.exe -m pytest packages/tool_registry/tests/test_program_status.py apps/api/tests/test_program_status_api.py tests/e2e/test_program_status.py tests/packaging/test_wheel_contents.py tests/native_runtime/test_program_status_lifecycle.py tests/test_security_scanner_setup.py -q --import-mode=importlib` | `32 passed`; two deprecation warnings only. |
| GB10 exact Linux verification | Bundle `D:\repos\wright\test-results\epp-f01b-d3119acc.bundle`, SHA-256 `0194b5c8ec78999cd4d03bd2ad91e019128c9f797d4f00eb53c0aafb1cc6d85f`, verified in an isolated lease-compatible checkout | PASS: validator zero blockers; control-plane correction group `118 passed`; packaged runtime group `32 passed`; workspace-service surface baseline `19 passed`; API surface-auth baseline `12 passed`; POSIX listener baseline `7 passed`; expected packaged entries and corrected raw manifest digests matched. The initial digest verdict was reclassified after the coordinator corrected two transcribed expected suffixes; GB10's computed hashes had matched the build evidence exactly. |
| Engineering-usability review | Independent reviewer `usability-auditor`, exact `d3119acc` | PASS, no new P0/P1; browser comprehension, honest population separation, current action, release posture, accessibility/table fallbacks, and packaged/source parity accepted. Focused browser `32 passed` and source-free/runtime `18 passed`. |
| Architecture/test review | Independent reviewer `architecture-auditor`, exact `d3119acc` | PASS, no new P0/P1; checkpoint/evidence binding, append-only correction closure, frozen scope, and packaged/source parity accepted. Transition chain `65 passed`, runtime relationship `1 passed`, browser relationship `14 passed`. The pre-existing nullable-denominator P2 remains unchanged and non-blocking. |

Windows local and Linux GB10 evidence are green. macOS atomic replacement/native lifecycle remains CI-only and is not represented as locally executed. T046 and T047 are complete. T048 remains deliberately open: no dev push gate, push, PR, merge, benchmark, publication, release, or other external delivery action ran.

## T048 dev push-gate checkpoint — 2026-08-29

The authorized pytest collection-isolation correction keeps each selected suite's default import behavior and, when the broad `tests` target is also selected, excludes every nested `tests/...` target that the gate already runs separately. This prevents duplicate `test_cli.py` collection without breaking suite-local helper imports. The focused gate-policy regression passed `10/10`, Bash syntax passed, and `git diff --check` passed.

The corrected `scripts/check-dev-push.sh` then completed UV synchronization, Ruff, formatting (`586` files), strict release MyPy (`32` source files), API tests (`382 passed, 1 skipped`), and tool-registry tests (`361 passed`). The broad test invocation collected cleanly and completed with `546 passed, 47 skipped, 1 failed`; the sole failure was the pre-existing host-dependent Docker persistence test because the installed Docker CLI's daemon query did not return within its explicit 10-second deadline. No EPP-F01B, collection-isolation, package, API, or browser failure occurred.

T048 remains open because the authoritative gate is red. The Docker host limitation is outside the collection-only correction authority and was not changed, skipped, or documented as a pass. No push, PR, merge, benchmark, publication, release, or other external delivery action occurred.

### Authorized Docker host-readiness disposition — 2026-08-30

The persistence gate now treats an installed but nonresponsive Docker daemon exactly like a missing or explicitly unavailable daemon: unavailable local host evidence, not a product pass or failure. The change catches only the daemon readiness probe's bounded `TimeoutExpired`; a responsive daemon still executes the unchanged exact-image inspection, disposable-volume creation, container replacement, restored-byte assertion, and cleanup path. Focused verification passed `6 passed, 1 skipped`, with dedicated negative coverage for a timed-out daemon and positive coverage for the exact successful readiness command. T048 remains open until the full dev push gate completes.

The subsequent full gate passed every Python phase, including API `382 passed, 1 skipped`, tool registry `361 passed`, broad regression `542 passed, 47 skipped`, program control `311 passed, 1 skipped`, and Docker persistence `6 passed, 1 skipped`. Its first frontend TypeScript compile exposed one deterministic portability issue: `Headers.entries()` is not declared by the app's configured library surface. The bounded correction uses `Headers.forEach()` to produce the same normalized bridge-header record. The existing desktop-adapter transport regression passed `12/12`, TypeScript compilation passed, and Prettier passed. The full gate must still be rerun to a terminal result before T048 closes.

The corrected full gate then passed all backend, frontend, isolated Chromium (`4/4`), and strict documentation phases, but its successful Playwright cleanup removed two durable JSON fixtures stored directly under the default `test-results/` output root. The gate did not leave its candidate unchanged. The bounded gate-policy correction moves Playwright's transient artifacts to `test-results/playwright/`, preserving the existing durable `test-results/program-status/` evidence. Focused gate-policy verification passed `10/10`, and a browser artifact was observed in the isolated subdirectory without removing either tracked JSON fixture. T048 remains open until the authoritative gate passes and leaves a clean worktree.
