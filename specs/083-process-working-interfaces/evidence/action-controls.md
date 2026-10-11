# Supervised action and working-view controls — 2026-10-01

## Implementation scope

This is a partial T027 milestone on `codex/083-process-working-interfaces`, based
on `c62f7ba1`. T027 remains pending for editor inspector declarations. T028's full
two-checkpoint UI/recovery proof, T021's remaining editor regressions, and all
M3–M5 authoring, live engineering, migration and distribution obligations remain
required. The complete implementation goal stays active.

The native action route delegates to the existing run supervisor and canonical
approval consume/execution/recorder authorities. It derives run and principal
from authorized process scope, validates the exact accepted source/checkpoint/
subject and retains a one-shot request identity before dispatch. Closing an HTTP
observer does not cancel its owned task. A 202 response can precede provider
acceptance; it acknowledges authorization, not completion. Duplicate live requests
attach to the same owned task; completed duplicates read the saved outcome.
Unknown submissions and unfinished claimed continuations cannot be replayed.
Confirmed delivery with no downstream claim can continue without redispatch.
Qualified provider cancellation uses the existing monitor/runtime capability.

The additive `PendingInteraction.action_receipt` distinguishes authorization,
acceptance/rejection/unknown submission, delivery, provider reference, observed
outcome, cancellation request and cancellation outcome. It is recorded evidence,
not permission. Public request bodies cannot choose actor/run/destination/settings
or integration-test authority. Existing history, aliases and v2/v3 checks remain.

Shutdown previously left interrupted continuation claims marked `executing`.
The existing recorder now seals any remaining executing claim as `outcome_unknown`
before its final evidence write. It does not restart the segment or infer effects.

The common view and public kit now render supported **declared** review choices,
bounded reasons and a separate exact-subject confirmation for continuing an action.
Requested changes require a reason. Changed/stale/missing permission and read-only
views cannot submit. After a decision/receipt, redundant controls disappear while
recorded evidence remains visible. Authorization is labelled separately from
provider acceptance and actual completion.

Input, review and action request intent is saved before mutation in a bounded,
closed browser locator cache scoped by session/workspace/source revision/run.
Reopening reads this intent without submitting it. Explicit reconciliation uses
the original request ID and immutable payload; backend authorities still validate
every request. Corrupt/mismatched caches and unavailable persistence fail before
new effects. Confirmed replies clear only their matching cache entry, including
when the observer closed during the call. No browser executor or lifecycle
authority was introduced.

## Verification

The [checked-scope manifest](../../../artifacts/process-interfaces/083/20261001-t027-actions/checked-scope.json)
records current code/log/artifact hashes, exact commands, preserved files and
actual synthetic unit/browser subjects. Qualified scope:

- **745 backend/API checks**, 44 modules, no skips; two existing TestClient
  deprecation warnings. Includes 19 supervised-action and 16 action-route checks,
  review/input/continuation/projection/storage regressions, 082 validation/rework,
  approved MCP dispatch/monitor/cancel, and unattended execution policy.
- **158 frontend checks**, public client, kit, common view and new recovery-store
  suite. Includes declared review/reason/confirmation, separate authorization/
  observations, lost response/review/action acknowledgement reopen, exact explicit
  reconciliation, read-only/storage rejection, closed scope and corrupt cache.
- **Six served normal-workspace browser journeys**: source edit/save/reopen,
  declared input response after tab reopen, lost response acknowledgement, review
  then action, and reload/reconciliation of lost review/action acknowledgements.
  Each keeps one start/run and makes no editor-run or cancellation request.
- App/client/kit TypeScript, generated schemas, focused Ruff/format/ESLint and a
  fresh 927-module Vite production build pass. Shared client/cache lint excludes
  intentional control-character regexes from the generic `no-control-regex` rule;
  their source and validation behavior are unchanged by that override.

The browser loaded current Vite source at `http://127.0.0.1:5241`, with process
definition/composer/recovery flags enabled, through the normal workspace Workflow
entry and existing document tabs. System Chrome and 1440×1000 action viewports
were used. Screenshots under
`artifacts/process-interfaces/083/20261001-t027-actions-browser-qualified/` were
visually inspected for review controls, authorization waiting and reopened observed
completion. This is bounded layout evidence; complete responsive/accessibility
and editor acceptance remain T052/T053 work.

All model/reviewer/provider data here are controlled synthetic unit or HTTP
fixtures. Service/API checks use real existing SQLite/file/source authorities;
browser checks use controlled HTTP contracts. No live configured-model authoring,
engineering MCP, engineering acceptance, hardware/supplier operation or user
acceptance is established. No protected campaign was resumed or changed.

## Preliminary attempts

The first focused action run passed 82 overlapping checks. An added cancellation
fixture initially pinned the original profile digest instead of its changed
cancel-capable profile; the corrected fixture uses its actual qualification.
Another focused run exposed the interrupted-claim bug described above; the
corrected 79-check run passes. A first frontend attempt placed unsupported-choice
copy in the wrong component; component checks caught it and the helper is now
scoped to checkpoint cards. The first browser attempt during that failure was
stopped; its result is not qualification. A focused lint check caught an unused
resolution variable; the authorization call remains and the assignment was removed.
Final backend verification was rerun after correction/formatting.

An initial relative browser output path resolved under the private config
directory. Final qualified browser output uses an absolute repository artifact
path. Visual inspection led to removal of redundant completed-review controls;
component/browser/build checks were rerun against the resulting source.

## Next work

Finish source/inspector controls for input schema and declared human interaction
while preserving the reviewed canvas and accepted-definition semantics. Complete
the two-checkpoint UI recovery proof and remaining editor regressions, then
implement the prepared coding-agent role and AI-created reusable interfaces
through Wright. This milestone is not completion of the full feature.
