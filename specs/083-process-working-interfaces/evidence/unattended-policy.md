# T025 — Unattended execution and recorded diagnostics

Date: 2026-10-01. Parent milestone: `7d4c4a11`. Branch:
`codex/083-process-working-interfaces`. T025 is complete; the full M0–M5 goal
remains active. T026 neutral approved action dispatch is next.

## Implemented boundary

The actual configured `generate_workflow_response` adapter asks for a closed
`wright.unattended-step/1` completion disposition independently of the requested
text/Markdown/HTML/JSON document. Status and failure reason are validated in core.
The existing response string carries observer usage/disposition metadata; source
execution checks disposition before document formatting, result publication or
file saving. Bare prose, unknown/extra envelope fields, invented forms and
contradictory dispositions fail as MODEL_OUTCOME_INVALID. No model repair/retry
was added to this adapter. Trusted legacy injected callbacks retain their string
interface; qualifying another real model adapter must include this policy.

Existing MCP task decisions include the same unattended instructions. Explicit
input_required dispositions fail as INTERACTION_NOT_DECLARED. Mixed blocked/tool
decisions cannot dispatch accompanying calls. After an earlier successful call,
the diagnostic preserves its receipt and does not repeat it. The existing single
tool-free response-format repair includes the policy and cannot introduce an input
request. Legitimate document question marks and JSON status fields are data; no
prose classification is used. A model's completed claim remains subject to the
existing evidence checks and 082 engineering validation.

This does not create a checkpoint, questionnaire, default requirement, agent
platform, executor or rework mechanism. A declared 082 revision budget authorizes
only its existing correction scope. Tests verify that a question before the
producer or during its eligible revision stops the process without another
revision, altered target or downstream release.

Run logs retain bounded code/correction and step-diagnostic events. Read composition
projects optional diagnostics[] Reasons with source-backed step navigation and
canonical log references. Shared client types/schemas are regenerated from core.
The common working view displays these corrections in Progress. Closing/reopening
and inspecting do not dispatch work. Required-input preflight and actual declared
checkpoint authority remain their existing owners.

## Checked commands and scope

- `.local-run/process-interfaces-083/t025-backend-final.log`: **444 passing**
  tests across 26 backend/API/adapter/core/storage modules, no skips; 102.70 s.
  Includes source, MCP evidence/failure, response-format correction, v2/v3
  continuation, approvals, supervision, input overlays, projection and actual
  authenticated response-route regressions. Two existing TestClient deprecation
  warnings remain. The two subsequently added explicit 082 policy tests are in
  the additional run below; implementation code was unchanged.
- `.local-run/process-interfaces-083/t025-validator-final.log`: **73 passing**
  tests, no skips; 8.91 s. Modules: test_workflow_unattended_policy,
  test_workflow_process_validation, test_workflow_process_validation_rework,
  test_validation_result_identity and test_process_validation_feedback.
  Policy cases overlap the first command; counts are not added together here.
- Python commands use `.venv/Scripts/python.exe -m pytest -q -rs
  -p no:cacheprovider` and fresh writable basetemps under
  `C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/`.
- Vitest: services/process-client.spec.ts,
  components/process-interfaces/CommonProcessView.spec.tsx,
  components/common/ProcessUIKit.spec.tsx; **136 passing**, no failures, from
  apps/web. Report: `.local-run/process-interfaces-083/t025-components-checked.json`.
- TypeScript application check and production `npm run build --workspace apps/web
  -- --outDir D:/repos/wright/.local-run/process-interfaces-083/t025-production-final`
  pass; **927 modules**. Existing large-chunk notice remains. Contract generator
  `--check`, focused Ruff and ESLint, and whitespace check pass.
- Playwright: process-common-view.spec.ts and process-declared-interactions.spec.ts;
  **six passing**, no skips/failures/flakes; 31.3 s. Installed Chrome, one worker,
  private system-Chrome config, Vite at 127.0.0.1:5240 with
  VITE_WRIGHT_PROCESS_DEFINITION_VIEW/WORKFLOW_COMPOSER/WORKFLOW_RECOVERY all `1`.
  Journeys use the normal workspace Workflow entry, preserve authoring/source,
  and exercise negative diagnostic/navigation/reattach, start recovery, declared
  source save/reopen and same-run input response/lost acknowledgement. Report:
  `.local-run/process-interfaces-083/t025-browser-final.json`.

Final screenshots and checked scope are under
`artifacts/process-interfaces/083/20261001-t025-browser-final/` and
`artifacts/process-interfaces/083/20261001-t025-policy/checked-scope.json`.
The diagnostic screenshot was visually inspected for visible correction, owning
step navigation, no invented form and no misleading running/percentage claim.
Browser HTTP is controlled; service models and default-model transport responses
are synthetic. No live-model/provider or engineering-acceptance claim is made.
The shared editor host emitted its existing ResizeObserver and React Flow notices,
and an unmocked background surface-events proxy encountered absent local API port
8000. These observations are retained in the scope report; this lane does not
qualify a live backend or claim a warning-free production session.

API tests actually use the configured model adapter through controlled HTTP after
a real persisted declared barrier. Earlier artifacts remain; duplicate submission
after a failed claimed segment is rejected with OUTCOME_UNKNOWN (503) and does
not call the model again. This retains the existing conservative effect guard,
rather than treating a failed claimed segment as replayable.

Initial fixture failures (wrong executor return shape, fixture step name, common
view prop/capability and expected unknown-claim transport status) are retained in
private preliminary logs/reports. Final checks above pass. A preliminary browser
pass exposed a stale running observation in its negative fixture; that fixture
was corrected and the final six-journey suite rerun. Preliminary artifacts are
not presented as final evidence.

Preservation check: ten original prototype hashes, three protected campaign hashes,
two mixed API deltas and two approved context files match their correct baselines.
No protected campaign, hardware, supplier, credentials, vendor behavior, service
configuration, push, merge or publication was changed by this milestone.
