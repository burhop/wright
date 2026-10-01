# Declared interaction implementation evidence

## 2026-10-01 — Accepted-source declaration and editor preservation

**Scope:** T022 completed; T023 is in progress. T024–T028 are pending.
This milestone implements and checks the declaration/compiler boundary. It does
not yet implement durable human-response storage or same-run resumption.

The existing JSON-valued task grammar now accepts `authoring_template=human-input`
with an explicit version-1 `human_interaction`. The compiler requires an Engineer
work step, connected upstream evidence, bounded object response schema and exactly
one single `structured_result` response port. The compiled step is a distinct
barrier descriptor, without an AI prompt, tool call or approval action. Required
evidence ports must have producers. Unsupported conditional connections, implicit
declarations, extra execution bindings and automatic correction segments crossing
the barrier are rejected. This does not expand the supported graph/rework scope.

Readiness distinguishes a consumer's `declared_human_response` dependency, pinned
to the interaction step and response port, from `upstream_produced`. A future
answer is not required as an initial run value. Source input metadata continues
to use the existing bounded conversion/default/schema owner.

The refined editor preserves both `interaction_input` and `human_interaction`
nested objects using its existing managed configuration retention mechanism.
Cold parse/format/reparse and served Source editing/save/reopen retain the schema,
required fields, additional-properties policy, port and Engineer performer.
Source storage remains opaque; the existing source store is reused unchanged.

**Current execution limit:** `prepare_prompt_workflow` rejects a workflow with
human input as `WORKFLOW_HUMAN_INPUT_UNAVAILABLE` before tool qualification or
execution. Direct executor entry also rejects such a step rather than invoking
an LLM for it. These explicit temporary capability guards must be replaced by
T024's durable v3 checkpoint implementation. They are not the completed process
experience and do not satisfy waiting/resume acceptance. No actual runtime AI
clarification policy is claimed here; that is T025.

### Shared fixture and verification

[declared-human-input.workflow.wflow](../fixtures/declared-human-input.workflow.wflow)
is an explicitly synthetic compiler/editor fixture, not an engineering proof.
Its SHA-256 is
`bc9138c226242b6a89df3e3ea0d1ea18f35acac568de123ee988628c48baeea4`.
A backend check requires the committed cross-language fixture to match the
source factory. Original campaign workflows, assignments and checkpoints are
unchanged. No human or integration-test engineering decision was submitted.

Backend command from repository root:

```powershell
.venv/Scripts/python.exe -m pytest -q -rs -p no:cacheprovider --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t022-milestone packages/workspace_service/tests/test_process_human_input_source.py packages/workspace_service/tests/test_process_input_readiness.py packages/workspace_service/tests/test_workflow_source_execution.py packages/workspace_service/tests/test_workflow_execution_continuation.py packages/workspace_service/tests/test_workflow_design_check.py packages/workspace_service/tests/test_workflow_sources.py
```

**185 passed, two skipped** in 13.32 s. The existing source/lock symlink checks at
`test_workflow_sources.py:468` and `:576` cannot create symlinks on this Windows
host (WinError 1314). This is not cross-platform symlink verification; retain that
obligation for the required installed/Docker checks. Private output:
`.local-run/process-interfaces-083/t022-milestone-pytest.log`.

Frontend command from `apps/web`:

```powershell
node ../../node_modules/vitest/vitest.mjs run src/prototypes/workflow-recovery/recovery-authoring.spec.ts src/prototypes/workflow-recovery/WorkflowRecoveryConcept.spec.tsx src/components/pages/WorkflowRecoveryPage.spec.tsx src/components/process-interfaces/CommonProcessView.spec.tsx --reporter=json --outputFile=D:/repos/wright/.local-run/process-interfaces-083/t022-ui-final-vitest.json
```

**126 passed** across four files. App/browser-test type checks, focused Ruff and
ESLint pass; one existing `presentedRun` hook warning remains. A fresh production
build at `.local-run/process-interfaces-083/t022-source-ui-build` passes with 927
modules in 1.81 s. Browser checks used separately served development Vite 8.2.0,
not those production assets.

### Served normal-workspace check

Used the already-qualified private system-Chrome configuration and a separately
owned Vite process on 5238, with workflow recovery/definition/composer flags set.
Entered through the normal workspace Workflows control. Installed Chrome
154.0.8037.58, 1280×720. **Four distinct browser checks pass** in 22.1 s:

- Declared metadata/schema Source edit, apply, save and cold reopen; zero starts.
- Exact 082 requirements-review subject, requirement IDs/text and source locators.
- Invalid draft containment and subsequent canvas/source/AI authoring controls.
- Typed handles and layout-only save with unchanged accepted source/revision.

```powershell
$env:PLAYWRIGHT_BASE_URL = 'http://127.0.0.1:5238'
$env:WRIGHT_PLAYWRIGHT_OUTPUT_DIR = 'D:/repos/wright/artifacts/process-interfaces/083/20261001-t022-milestone'
$env:PLAYWRIGHT_JSON_OUTPUT_NAME = 'D:/repos/wright/.local-run/process-interfaces-083/t022-milestone-playwright.json'
node node_modules/@playwright/test/cli.js test tests/ui-integration/process-declared-interactions.spec.ts tests/ui-integration/process-validation.spec.ts tests/ui-integration/workflow-recovery.spec.ts --grep 'preserves declared input schemas|exact human requirements review|keeps one accepted definition|uses real typed handles' --config .local-run/process-interfaces-083/playwright-system-chrome.config.ts --project=chromium --workers=1 --reporter=line,json --global-timeout=120000
```

Use fresh output/temp directories when reproducing. The declared-interaction
browser file currently checks source authoring only; its checkpoint-consumption
journey remains to be added in T028. HTTP contracts are controlled fixtures.
No live API, default model, MCP, engineering acceptance or hardware is claimed.
The existing React Flow attribution warnings and one unrelated surfaces-event
proxy refusal to the unstarted API on 8000 were observed; this is not a clean
live-backend integration claim.

Retained scope and screenshots:
`artifacts/process-interfaces/083/20261001-t022-milestone/`.
The scope record includes exact original/saved source hashes, saved revision,
workspace/path and zero controlled starts. No credentials are recorded.
The source screenshot depicts the reopened accepted editor; assertions, not that
viewport image alone, establish nested schema preservation. The requirements
review was repeated after expanding the existing details drawer (**one pass** in
3.4 s); that screenshot shows the actual requirements and engineering-judgment
qualification. Its private report is `t022-review-expanded-playwright.json`.

Initial failures were test assumptions: the parser base must match `workflow test`,
the formatter emits bare performer enums, and the ready editor has no
`data-surface-state=ready` attribute. Corrected those assertions while retaining
identity/schema/save/reopen checks. An initial `import.meta` fixture read was
incompatible with this repository's Playwright module configuration; use its
established root-relative file loader. One negative backend assertion incorrectly
matched correction text against exception-message text; it now checks the
separate correction field. Preliminary failed reports remain private evidence.

The owned Vite process was stopped after verification. The ten original prototype
hashes, three protected campaign hashes, two mixed API deltas and approved 083
context match their intended baselines; private report `t022-preservation.json`.
No push, merge, release or external effect occurred. The complete goal remains active.
