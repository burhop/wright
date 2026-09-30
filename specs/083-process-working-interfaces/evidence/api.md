# Native process API — T010

Date: 2026-09-30. Branch: `codex/083-process-working-interfaces`.
This is authenticated transport/service regression evidence, not a served-browser
or live model/MCP demonstration.

## Implemented boundary

The existing `/api/workspace` mount now includes:

| Method and suffix | Owning operation |
|---|---|
| GET `/process-interfaces/interaction` | Preparation or exact recorded-run projection |
| POST `/process-interfaces/inputs` | Immutable input preparation |
| POST `/process-interfaces/readiness` | Existing source-run qualification |

Source requests supply `session_id`, confined `path` and
`expected_storage_digest`. Readiness also supplies `input_snapshot_id`. Input
requests supply bounded typed `bindings`. The server derives workspace from
the persisted session binding and derives principal/capabilities from native
authority. Caller-supplied workspace, actor and capabilities are forbidden.

The routes use the existing workspace dependency, persisted source scope and
engineer/admin validation read gate. Auth token/browser session and origin policy
remain the existing control-plane middleware. Projection does not bypass 082
assessment authorization. Current native capabilities expose only implemented
read/input/result/navigation operations; lifecycle commands are subsequent work.

Success and structured errors are no-store. Request materialization is bounded
to 64 MiB, both for declared lengths and chunked bodies, reusing the existing
source-body collector. Validation diagnostics are bounded and avoid submitted
values, discriminator tags, arbitrary field names and validator context. Existing
source endpoint error handling retains its previous behavior.

A recorded run retains its checkpoint/subject and original inputs. Supplying a
replacement preparation with a run attachment is rejected. Reading, subscribing
or inspecting does not release a checkpoint or replay execution.

## Tests and corrections

The initial new tests failed against absent endpoints. GET initially reached the
SPA fallback; the JSON contract assertion exposed that rather than treating its
HTTP 200 as success. The first implementation corrected the contract type's
owning import (`Locator` belongs to process interactions).

An additional failing test showed that Pydantic's discriminator message/context
could echo a submitted tag even after the raw input field was removed. New-prefix
errors now expose safe declared fields/type only. This does not weaken input
validation. Tests cover real service preparation/readiness, no execution, exact
recorded-run attachment, denied replacement inputs, foreign session, changed
source, caller identity injection, authentication/origin, viewer role and both
request-body limit modes.

Focused endpoint checks: **11 passed**, including an actual fixture checkpoint
through the existing recorder/approval service. Decisions are controlled fixture
data, not engineering acceptance or live proof enrollment.

Combined command, repository root / Python 3.13.5:

```powershell
.venv/Scripts/python.exe -m pytest apps/api/tests/test_process_interfaces_api.py apps/api/tests/test_workflow_sources_api.py apps/api/tests/test_workflow_run_inspection_api.py apps/api/tests/test_workflow_execution_snapshot_api.py apps/api/tests/test_workflow_artifact_reviews_api.py apps/api/tests/test_workflow_approval_resume_api.py apps/api/tests/test_workflow_integration_run_api.py apps/api/tests/test_process_validation_routes.py apps/api/tests/test_security.py apps/api/tests/test_main_security.py -q -p no:cacheprovider --tb=short --basetemp=C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/process-api-regressions-1
```

Result: **73 passed, one existing skip, 13.19 seconds**. Two existing
Starlette/httpx/AnyIO deprecation warnings remain; dependencies were not changed.
The same process handle was polled to terminal completion.

Ruff passes for the new router/schemas/tests and changed main module. New files
use the existing formatter. `main.py` contains prior prototype edits; only the
feature's added import/mount/body-limit/error hunks are staged. The owned patch
was regenerated with LF endings after its first staging check rejected Windows
line endings. No reset, overwrite or wholesale staging was used.

## Next

Backend-owned task/start/event/cancel work (T013–T016) remains pending. The old
source streaming endpoint still owns execution within its request until T015;
these read/preparation routes do not pretend to fix disconnect behavior. Client,
common/tailored UI, model generation, live engineering chains, migration and
installed distribution verification remain required by the full active goal.
