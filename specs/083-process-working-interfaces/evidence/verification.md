# Verification record — partial feature acceptance

## Generated-interface and existing surface boundaries, 2 October 2026

Code checkpoint before this run: `beb3339a` on
`codex/083-process-working-interfaces`. Existing unrelated mixed prototype
changes remain preserved; this is a development-workspace verification, not a
clean production release candidate. No API/model/engineering service was started
for this test group.

Command, from the repository root:

```powershell
.venv/Scripts/python.exe -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp=.local-run/process-interfaces-083/t040-resume-security-010 packages/workspace_service/tests/test_process_ui_authoring.py packages/workspace_service/tests/test_process_ui_build.py packages/workspace_service/tests/test_process_ui_presentations.py packages/workspace_service/tests/test_process_ui_start_association.py packages/workspace_service/tests/test_process_interface_service_boundaries.py packages/workspace_service/tests/surfaces/test_process_ui_static.py apps/api/tests/test_process_ui_surface_authority.py apps/api/tests/test_process_ui_authoring_api.py apps/api/tests/test_surface_scope_security.py apps/api/tests/test_surface_webmcp_security.py apps/api/tests/test_surface_preview_security.py --junitxml=.local-run/process-interfaces-083/t040-resume-security-010.xml
```

Observed terminal completion: **149 passed, zero skips, 117.98 seconds**.
Seven existing Starlette/httpx/AnyIO warnings concern deprecated client/cookie
interfaces; dependency upgrades were not introduced into this feature.

The group checks controlled owner/API boundaries: exact workspace/process/UI/run
and source identities; origin, expiry, revocation and replacement; read-only
preview mutation denial; no generic tool authority; malformed/oversized input;
corrupt immutable assets; fixed build/import/CSS restrictions; repair budgets and
role retention; durable duplicate-request handling; explicit authoring cancel
versus observer disconnect; saved reuse without model/compiler; and closing a
presentation without cancelling its process. Existing MCP App and WebMCP scope
checks remain separate from generated-interface grants.

The models/providers are controlled fixtures. Some builds use the actual fixed
local compiler, but this group does not make a fresh actual-model, live-MCP,
browser, installed-distribution or engineering-acceptance claim. It completes
T040's scoped regression requirement; T053 remains pending the full affected
regression/acceptance record.

## Separate served evidence

Historical result navigation has six passing served-workspace checks and
sixty-four previously recorded focused component checks; see
`workspace-acceptance.md` and
`artifacts/process-interfaces/083/20261002-historical-result-navigation/`.
Its two failed attempts remain retained. Those numbers are separate suites and
are not added into a purported unique total. The original failed engineering run
was neither replayed nor relabelled successful.

## Supplied-artifact approval regressions

The first file-list attempt named a nonexistent reference test module and ran no
tests; it is not counted as verification. An initial expanded suite reported one
failure in the existing rule preventing implicit supplied-file transfer. The fix
requires explicit accepted-definition opt-in and preserves that regression.

Latest command:

```powershell
.venv/Scripts/python.exe -m pytest -q -rs --tb=short -p no:cacheprovider --basetemp=.local-run/process-interfaces-083/t047-retained-handoff-binary-006 packages/workspace_service/tests/test_workflow_binary_file_consumers.py packages/workspace_service/tests/test_process_preparation_service.py packages/workspace_service/tests/test_workflow_approval_execution.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_approval_resume.py apps/api/tests/test_process_interface_actions.py apps/api/tests/test_process_interface_checkpoints.py --junitxml=.local-run/process-interfaces-083/t047-retained-handoff-binary-006.xml
```

Terminal completion: **94 passed, zero skips, 60.17 seconds**, with two existing
dependency warnings. The preceding qualified
group (`t047-retained-handoff-binary-005`) passed 94 tests in 39.31 seconds with
two existing dependency warnings. These are overlapping suites, not additive
counts. The tests exercise explicit boolean opt-in, denial of unrelated supplied
files, binary/text/MCP consumer distinctions, exact source/artifact approval,
file changes before and after decision, simulator receipts and same-run recovery.

The separate normal API follow-up and unchanged-profile independent assessment
are described in `printed-proof.md`; they are not a physical-effect test or
completion of the original failed run's skipped gate.

## Resumed runtime, continuation and validator regression group

Code checkpoint: `d44b9dcb`, after the operator documentation/example commit.
All 37 module paths were confirmed to exist before execution. The exact argument
array is retained in
[command.json](../../../artifacts/process-interfaces/083/20261002-runtime-regressions/command.json);
the suite uses the repository venv, `-q -rs --tb=short -p no:cacheprovider`,
a fresh private `--basetemp` and JUnit output. Terminal exit code is zero:
**659 passed, zero skips, 131.09 seconds**. Two existing Starlette/AnyIO
deprecation warnings remain; no dependency upgrade was introduced.

[Checked scope](../../../artifacts/process-interfaces/083/20261002-runtime-regressions/checked-scope.json),
raw terminal output and JUnit results are retained together. This suite exercises
the existing unattended/response-timeout contracts; neutral MCP actions and
gateway restrictions; failed-tool evidence; source design checks; run supervision;
declared input and approval continuation/restart; exact snapshot overlays/readiness;
observations/cancellation; source execution; 082 validation/rework/result identity
and correction feedback; migrations; native lifecycle and checkpoint APIs.

These are controlled runtime/service/API regressions, not fresh model/provider,
browser, installed or engineering acceptance. They overlap earlier suites and
must not be added into a purported unique total. The preservation check passes
after the run. No retained engineering process was resumed or review answered.
T053 remains unchecked for its remaining component/browser/security/package-boundary
and full affected acceptance scope. T056's new completion ledger remains open.

## Accepted-source MCP task allowlist editor regression

The actual fresh consumer source revealed a diagram parser rejection of the
runtime's documented `mcp_task_tools` array. The shared editor now retains the
bounded, distinct nonempty string list through its existing structured settings
envelope. It grants no tools and does not replace backend capability checks.
Tests include malformed lists, an inappropriate exact-tool block and a cold
round trip of the actual accepted source.

Current command, from `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/prototypes/workflow-recovery/mcp-settings.spec.ts src/prototypes/workflow-recovery/recovery-instruction-fields.spec.ts src/prototypes/workflow-recovery/recovery-authoring.spec.ts --maxWorkers=1
```

**74 tests pass across three files**, terminal zero, 14.55 seconds for the
recorded rerun. Raw output is retained in
`artifacts/process-interfaces/083/20261003-wheel-exact-source-ui/editor-tests.log`.
The earlier 5.47-second pass is the same scope, not an additional unique total.
Served workspace evidence now opens the exact accepted diagram and matches its
working-view results. This is narrower than complete editor or T053 acceptance.
The unchanged protected/archive/context byte check also passes.

## Current shared recorded-result and evidence proxy checkpoint

See artifacts/process-interfaces/083/20261003-wheel-shared-viewer-verified for
raw outputs: 109 kit/result/common tests; an overlapping 32 proxy/result tests;
42 API authority tests; successful app/node typechecks; and 3 installed public
resource tests. These counts overlap and must not be summed as unique coverage.
Fifteen actual served browser checks establish preview and working-context
reload, nineteen exact results/held assessment, real ninety-layer canvases and
rotation/layer/support controls. The final browser has no console/page/failed
responses. Structure validation passes for the successful report. The retained
sandbox launch stop has no page/screenshot and its image-interaction structural
check is explicitly unavailable. Exact inventories and actual credential scans
retain public evidence; traces remain private. Existing engineering and human
review limitations are unchanged. This does not close T053's broader audit.

### Exact common evidence-tab routing on two live digital processes

The shared host now chooses an exact common workspace tab for evidence focus,
never an arbitrary saved/preview interface. 106 affected locator, common-view and
workspace-tab checks pass (8.57 seconds), including seven new scope/selection
cases. Full app TypeScript exits 0. Actual saved-wheel navigation passes three
checks with full held assessment/result focus and exact selected producer. Latest
saved-Heat completed-output proof passes five checks: eighteen-result parity,
765 supplied samples, full held assessment, exact selected producer and genuine
working reload. Both final browsers have no console/page/failed-response errors.
Five copied report structures pass; exact public inventories and credential-value
scans are retained in 20261003-two-process-exact-navigation. Test counts overlap
prior suites. No generation/build, engineering start/review or physical operation
occurs. Earlier wheel routing failure, premature Heat loading assertion and
separate open-view capacity stop remain preserved. This strengthens T047/T053
within recorded scope; neither broad task is marked complete.

### Browser document departure and exact presentation cleanup

[Scoped evidence](../../../artifacts/process-interfaces/083/20261003-presentation-departure-verified/README.md)
retains the actual two-interface twelve-check walkthrough, independent backend
closed-view observations, unchanged retained artifacts/authoring records, exact
source hashes, commands and failure limits. The current affected frontend group
passes **63 tests / five files / 9.67 seconds**; backend static-host, presentation,
start-association and native API authority passes **73 tests / 38.64 seconds**
with two existing dependency warnings and zero skips. App typecheck exits 0.
The earlier 36-case subset overlaps; none of these counts are additive with prior
suites. Authenticated browser traces remain private. No model generation, build,
process start, review response or uncertain simulator replay occurs. T053 remains
open pending its full affected-suite and acceptance audit.

### Current common/editor regression continuation

The [18-file scoped inventory](../../../artifacts/process-interfaces/083/20261003-editor-native-regression-002/inventory.json)
retains 19-pass served mocked common/editor/composer/082 browser checks,
57-pass common/recovery components, 44-pass readiness/preparation/service-boundary/
API-lifetime backend checks, and the first 12/13 browser attempt. No skips; app
typecheck exits 0. The accepted-run counter now has a pre-rejection POST counter:
zero blocked requests and one positive request are checked explicitly. Four
obsolete simulation expectations are replaced without changing production gates.
See [common-view mapping](common-view.md) for T021 closure and
[reproduction/scope](../../../artifacts/process-interfaces/083/20261003-editor-native-regression-002/README.md).
Protected archive/campaign/context and unrelated prototype byte checks pass;
credential-value scans pass. Controlled regression evidence is not new live
model/provider or engineering acceptance. T053's broader audit remains open.

### Explicit run-path preparation and continuation

The [controlled runtime proof](../../../artifacts/process-interfaces/083/20261003-run-path-binding-verified/README.md)
records 237 passes and one existing Windows symlink-privilege skip across fifteen
affected suites, plus passing Ruff checks. Twenty-nine new parameterized cases
cover shared-source repeat runs, separate outputs, connected MCP schema checks
without readiness effects, raw/resolved template identity, owner reopen,
changed-template rejection, enrolled local-review continuation and duplicate
reconciliation. Both verification handles are terminal. The retained setup attempt
ran no tests because an incorrect filename was supplied. Protected archives,
campaign/context and unrelated prototype byte checks pass. No live model/provider,
browser or current installed-build behavior is established here. Example adoption,
UI compatibility and actual engineering repeat-run evidence remain open; neither
T047 nor T053 is closed by these controlled checks.
