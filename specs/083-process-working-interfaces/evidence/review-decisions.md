# Scoped review-decision evidence — 2026-10-01

## Checked implementation and remaining scope

This is a **partial T027 milestone**, based on `b141e296` on
`codex/083-process-working-interfaces`. T027 remains unchecked. The complete goal
remains active, including review/action forms, supervised action continuation,
source/inspector editing, T028 recovery journeys and all later live authoring,
engineering, migration and distribution proof.

The new `ProcessReviewDecisions` owner composes existing approval and artifact
review services. It validates authenticated process capability, current accepted
source, exact registered run receipt and that run's declared checkpoint. Run and
actor are server-derived. Review decisions retain their bounded reason and request
identity atomically with the existing decision. Different identities/choices
conflict; declared inputs cannot be decided as approvals. This introduces no
new executor, decision database or generic provider invocation API.

The native decision route accepts only source/session, subject digest, declared
decision, bounded reason and request ID. Actor/run/auto/destination/integration
fields are rejected. The public client validates the retained exact subject,
request and decision, marks lost or unverifiable acknowledgements uncertain, and
does not automatically retry. `PendingInteraction.decision` is optional recorded
evidence; the kit displays the decision and labels test attribution. It grants
no external dispatch permission. Actual reviewer instructions/controls are still
pending in the common view.

Terminal artifact decisions are projected through the existing run recorder as
completed or changes requested. Action approvals retain awaiting-approval state
until a separate authorized action. Exact retry restores an interrupted recorder
projection without a second decision/event/model/tool invocation. Older review
payloads without request metadata preserve their read shape and attribution;
v2/v3 approval and enrolled operation regressions remain covered.

## Current verification

- **710 backend/API tests pass**, no skips, two existing TestClient warnings,
  148.82 seconds. Includes 23 new scoped-service and 14 new native-review tests;
  existing approval, artifact review, input/supervisor/continuation, MCP-operation,
  gateway integration restriction, 082 validation/rework, owner/projection,
  shared contract and repository tests are in the recorded 42-module command.
- **139 frontend checks pass**: 70 public client, 31 public kit and 38 common-view
  component checks. The common-view forms themselves have not been expanded in
  this milestone. Their existing behavior is regression scope only.
- App TypeScript passes; generated client/schema fixture check passes; focused
  Ruff and ESLint pass. ESLint uses the existing explicit web config and excludes
  its two pre-existing intentional control-character regular expressions from
  `no-control-regex`; source/security behavior is unchanged.
- A fresh Vite 8.2.0 production build passes: 927 modules, 32.33 seconds. Existing
  chunk-size and plugin-timing notices remain. No browser server was started or
  claimed to serve this build.
- Original ten prototype hashes, three protected campaign hashes, two mixed API
  deltas and approved context are preserved. No physical/supplier effects,
  campaign continuation, global model changes, push, merge or release occurred.

[Checked scope, exact commands, logs and recorded unit subjects](../../../artifacts/process-interfaces/083/20261001-t027-reviews/checked-scope.json)
retains the actual run/checkpoint/subject/decision identities and artifact hashes.
Private logs and build output are under `.local-run/process-interfaces-083/`.
The pytest root is a fresh `t027-backend-current` directory under the authorized
visualizations test root. All owned verification processes finished.

Models, provider responses and reviewers in these checks are explicitly synthetic
unit/transport fixtures. The native tests exercise the production human-decision
path with the local control-plane principal; this is not human engineering
acceptance or one of the enrolled live digital demonstrations. No live model,
live MCP, engineering, served-browser or user acceptance is established here.

## Preliminary attempts and corrections

The initial artifact fixture used an unsupported template name and then an
incorrect review step type; these failures were corrected to the existing
`manual-review` work-step grammar. Initial repository readback exposed an extra
`request_id: null` on old reviews; the additive metadata is now omitted for
legacy decisions. An API assertion initially expected an unwrapped `detail`
error; it now verifies Wright's actual `error_code` envelope. All are covered by
the fresh passing run rather than treated as current proof.

The first broad command referenced a nonexistent inspection test and ran no
tests; the qualified command uses the existing `test_process_approval_inspection`
module. Initial build/lint launch paths did not resolve the installed root
dependencies/config; corrected commands use the actual root Vite executable and
explicit existing ESLint config. No dependencies, access controls or unrelated
services were changed to work around those launch errors.

## Next action

Wire explicit review choices/reasons and exact-request reconciliation into the
shared kit/common view. Add action transport to the existing run supervisor so
the backend owns operation/continuation lifetime. Preserve exact checkpoint,
subject, provider/artifact/destination/settings identities and distinguish accepted
submission from observed completion. Then finish inspector/source editing and the
required served workspace/recovery journeys. Do not treat this backend/client
milestone as completion of those UI or live proof obligations.
