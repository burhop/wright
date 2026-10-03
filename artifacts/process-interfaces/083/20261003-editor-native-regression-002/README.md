# Current common/editor regression continuation

Source checkpoint: `1ef45ee1`, with the three test-file changes identified in
`checked-scope.json`. Frontend: existing owned Vite server on loopback 5243;
installed Chrome, one worker, no browser/package download. All browser APIs are
intercepted by the existing fixtures. No real backend/model/MCP/physical action
is exercised by these browser tests.

## Results

- **19 browser tests pass**, no skips, failures or flaky results, 48.19 seconds:
  common working view (3), editor (13), composer (1), requirements validation (2).
- **57 component tests pass**, no skips, 6.17 seconds: common view (46), recovery
  journal (11).
- **44 backend tests pass**, no skips, 6.77 seconds: input readiness, preparation,
  scoped service boundaries, and API run lifetime; two existing dependency warnings.
- Whole-app TypeScript exits 0. Protected archives, campaign/context and unrelated
  prototype byte checks pass. These checks do not alter or decide those subjects.

Native Run is an explicit preflight affordance. Readiness still displays missing
inputs. Editing and reopening cannot themselves dispatch. Two setup-blocked
journeys click Run and assert both zero POST requests and zero configured runs;
the positive 082 journeys assert one request and one run. Missing input/schema/
source/capability readiness and lost-ack/detach/reopen behavior retain backend
authority. The fixture's new request counter increments before rejecting any
request, so rejected attempts are not hidden by the accepted-run counter.

The first continuation passed 12 of 13 editor tests and stopped one test on an
additional old disabled-button assertion after saved-input reopen. Its exact JSON
and error context are retained under `retained-first-attempt/`. The correction
checks native affordance, visible 2/3 input readiness and zero execution requests.
No product execution gate was relaxed. Other tests in that batch continued;
this was a regression batch, not a stop-at-first-error exploratory walkthrough.

## Reproduction

From the repository, configure `PLAYWRIGHT_BASE_URL` for an owned current frontend
and absolute `WRIGHT_PLAYWRIGHT_OUTPUT_DIR` / `PLAYWRIGHT_JSON_OUTPUT_NAME`. Run:

```text
node node_modules/@playwright/test/cli.js test tests/ui-integration/workflow-recovery.spec.ts tests/ui-integration/process-validation.spec.ts tests/ui-integration/process-common-view.spec.ts tests/ui-integration/workflow-composer.spec.ts --config .local-run/process-interfaces-083/playwright-system-chrome.config.ts --project chromium --workers 1 --reporter line,json --timeout 90000
```

The private config simply imports the root config and selects installed Chrome;
it is host-specific, not a distributed dependency. From `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/components/process-interfaces/CommonProcessView.spec.tsx src/services/process-view-recovery.spec.ts --maxWorkers=1
node ../../node_modules/typescript/bin/tsc --noEmit -p tsconfig.app.json
```

From the repository, use a fresh workspace-owned pytest temporary/cache root:

```text
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_process_interface_service_boundaries.py apps/api/tests/test_process_interface_run_lifecycle.py --basetemp <owned-root>/temp -o cache_dir=<owned-root>/cache --junitxml=<owned-output>/backend-results.xml -q
```

T021's common-view component/mocked/served/reconnect/navigation scope is complete.
T041/T052/T053 retain broader authoring, installed editor and regression obligations.
Engineering parity, repeat-run isolation, migration, provider qualification and
human/physical acceptance are not certified. Counts overlap historical suites.
Screenshots document the controlled UI, not live engineering outputs. The exact
assessment screenshot was visually inspected. Browser diagnostics beyond the
test assertions were not independently audited in this batch.
