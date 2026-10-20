# Windows pilot routing repair

## Subject and scope

The Windows agent requalified `c06944b1afae2857c3af4cfd3d5a3124b7d53de8`
and reported successful local authentication, normal workspace access and
source save/reopen. Its preserved handoff is
`.local-run/windows-pilot-requalification-c06944b-20261020/SHARED-DEFECTS.md`.
It also reproduced two shared defects: the SDK omitted configured `high`
reasoning, and the authoring session-lock endpoint rejected SDK workflow setups.
These are readiness repairs on PR #165, separate from desktop UI development.
All prior PR checks completed successfully before this correction began.

The user's journey remains: author/refine a workflow through the isolated local
Hermes chat, then execute its accepted process through Wright's existing bounded
runner, gateway, validation and durable review/resume services. Session model
selection and model reasoning never grant process-review or external-action
approval. Roadster remains held until actual Windows readiness passes.

## Changes and compatibility

- Read the selected profile through the installed Hermes configuration loader and
  reasoning resolver, including its per-model overrides. Validate configured
  values instead of allowing a silent SDK fallback. The existing model-only
  worker sends resolved effort on text, helper/repair and native-image requests.
- Include effort and the config-loader SDK identity in the frozen public route,
  its configuration digest and existing SDK invocation evidence. Changed effort
  fails parent/worker checks before inference and the durable continuation check
  before execution. Unsupported explicit settings report the bounded
  `SCOPED_MODEL_REASONING_UNSUPPORTED` code.
- Qualify explicit `low`, `medium`, `high`, `xhigh`, `max` only on
  `codex_responses`. Disabled/minimal/other transport settings are unavailable
  rather than silently changed. Absent legacy reasoning fields remain absent
  when reading history; never backfill historical provenance. Older runtime
  identities may require restoration or a deliberate new run, not rewritten
  history or replayed effects.
- Chat model discovery uses the chat HTTP service independently of workflow SDK
  selection. With an exact session ID, Wright requests only the session lock and
  verifies the exact object, session, provider, model and accepted-lock receipt.
  It does not update the profile default. Missing or denied lock confirmation
  remains a failure; there is no alternate model/transport fallback. Global
  selection remains unavailable while SDK execution is selected.
- The pilot probe now accepts `--expected-reasoning-effort high` and rejects a
  missing/different resolved effort before inference. The Windows guide includes
  this argument. Existing editor behavior, process UI compatibility/fallback,
  provider implementation and installed desktop plugin are unchanged.

## Evidence

Evidence directory: `/tmp/wright-windows-routing-repair-evidence-20261020/`.
The original Windows handoff and first failed reproduction remain unchanged.

- `sdk-reasoning-reproduction.json`: reproduced the original defect with the
  candidate's real worker and controlled SDK responses: no reasoning sent;
  high → low neither changed its frozen identity nor prevented another dispatch.
- `installed-sdk-boundary.json`: actual installed Hermes Codex adapter with
  network disabled and controlled responses. The worker's extra-body effort
  reaches the underlying Responses request as `high`; high → low changes the
  identity and prevents a second request. Exact worker/SDK hashes are retained.
  This is request-construction evidence, not live Astra inference.
  The portable receipt is retained beside this document as
  [windows-routing-repair-20261020.json](windows-routing-repair-20261020.json).
- `focused-chat.log`: 34 API checks passed, including both workflow transports,
  exact session-only selection, no profile-default update, denied/mismatched
  receipts, and distinct chat discovery failure.
- `focused-routing-final.log`: 82 SDK/image/route/continuation checks passed,
  including translation repair, preserved legacy absence, and reasoning drift.
  Existing Robot Tracking Diagnosis and sheet-metal supplier-handoff preparers
  retain their inputs, engineering requirements and reviews while testing
  frozen reasoning on isolated plans. No providers or campaigns were executed.
- `probe-final.log`: 41 worker/probe checks passed, including explicit expected
  `high` and rejection of a missing or different resolved effort.
- Final probe checks, image scan and pre-push gate results are recorded in the PR
  before delivery. The previous full gate and CI receipts belong to the previous
  commit; current-head CI and a current full merge gate remain merge requirements.

Windows still owns actual Astra/high authoring and execution evidence, personal
sign-in, durable restart/resume in its running pilot, and the real bounded
producer → measurement → correction → revalidation chain. Hermes-internal
requests that Wright cannot observe remain explicitly unverified. No model
inference, engineering pass, Windows acceptance, or live UI change is claimed
by these local regression checks.
