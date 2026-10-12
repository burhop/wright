# Desktop reasoning progress and the manual turn boundary

On 11 October 2026 (America/New_York), the user reported that clicking Run in
`dave` looked stuck and did not explain what was happening. Native
`wright_reasoning_pending` returned the actual queued response task. The existing
desktop conversation answered that task through `wright_reasoning_answer`, and
Wright completed the same run without restarting or substituting a model worker.

## User journey and remaining capability gap

Open the saved workflow through Workflows, click Run, and inspect its current
task and results. During a desktop AI handoff the editor now shows:

- **Waiting for desktop chat** above the diagram, in the Run control, and in
  the run summary.
- The queued time and the last successful status check.
- A specific instruction to continue the workflow in the same desktop chat.
- Navigation to the exact active task and expandable run/request identities.

The backend run remains active while the response is pending. This is not a
declared human-input or engineering-review checkpoint. The UI does not create
questions, approvals or dispatch authority. Pending status clears after Wright
accepts the response and continues the same run; reopening reconciles with that
durable identity. Failed status reads report unavailable status instead of
claiming that the model is generating a response.

The installed tool-only plugin has not demonstrated a supported event mechanism
that automatically starts a turn in the existing desktop conversation when Run
is clicked. Therefore a user must currently send, for example, **Continue the
workflow in dave** in this chat. This change fixes the misleading progress view
and completes the reported queued task. It does not qualify automatic wakeup,
unattended multi-step desktop operation or native plugin panel hosting. The next
integration experiment must use a supported same-conversation event mechanism;
a separate SDK/app-server model worker is not a substitute.

## Shared and external ownership

The existing Wright supervisor, source compiler, recorder, reasoning repository,
validator and gateway still own execution and evidence. No backend transport or
frozen binding was changed. The existing scoped `/api/desktop/reasoning` read
supplies the handoff identity; the normal run observer supplies the active run,
source digest and step. The browser adapter authenticates those reads normally.

`WorkflowRecoveryPage` selects a read-only desktop status adapter in the existing
hosted presentation mode. The editor accepts an optional status reader, so other
agent platforms keep their existing behavior. The reader validates workspace,
session, run, schema and adapter identities, rejects ambiguous requests, and
never derives policy from prompt wording. Visibility/unmount cancel only status
GETs. Responses from an old run or adapter scope cannot update the new view.

The editor keeps the accepted source, flowchart, inspector and working view.
Source mismatches prevent associating a handoff with another revision. Missing
status capability leaves existing execution observation and recorded results
usable, with an explicit unavailable status. No credentials, live authority,
saved instruction bodies or required output checks are transferred or changed.

## Exact observed runs

The user's reported run:

- Workspace: `a5c5778b-0546-449b-9136-1af345067703` (`dave`).
- Run: `cb5ee5af479c41ec959518ebfa034e76`.
- Request: `2839e806-5052-4f5e-acd5-574b9216c440`.
- Accepted reply: `dave-welcome-user-run-answer-01`.
- Native final read: `completed`; output `welcome-001.md`, SHA-256
  `d54792ed09067e46956083c41374863c9ac48ba5f53190ff26b71e14d470ccb8`.
- Original accepted source digest remains
  `183ddb9db74f6014ac2c6b0841c68c326512f6bed4cd0e29ad09c6bad3956ae8`.

Fresh isolated digital proof workspace:

- Workspace: `bda9d8b6-7637-4fb4-a78d-a762678fb6df`.
- Session: `desktop-7eb465b9-291f-48ed-9008-c33c78fa3cb4`.
- Source: `workflows/desktop-progress-proof.workflow.wflow`, digest
  `1e387b27375cefef6c754bbb17113ac626cdf681a3e8c4ffd24cc57bda9fb11e`.
- Native-started run: `1bb4d7367fc447cba373ae85cd0ab0ab`.
- Editor-Run-started run: `9e340a97da7947e28a41115c2a9dab01`.
- Both reached their actual desktop response wait, survived browser reload, and
  completed after this conversation submitted the exact native-tool reply.
- The second proof produced indexed `welcome-001.md`; SHA-256
  `266bc1048b9c90b61e30ae79ced035b3d9921e39e5e53e7f2abd8d3c2038e781`.
- Browser source mutations: none. Runs and earlier output bytes remain retained.

## Verification and evidence

100 focused checks passed across status validation, late/stale observations,
editor presentation/completion, ordinary workspace behavior and private LAN
hosting. Web TypeScript compilation passed. The existing browser capture harness
passed three read/reopen checks and four normal-Run/read/reopen/completion checks:

- `/tmp/wright-desktop-progress-ui-20261011-01` — native-started run.
- `/tmp/wright-desktop-progress-ui-20261011-02` — actual editor Run control.

The harness supplies no model answer, uses no credential override, omits private
browser traces, and does not replay a start. The actual conversation submits
replies only through the installed native Wright tool. Each proof links the
served frontend source, queued request, same run, accepted reply and output.
These are GB10 browser proofs; post-change Windows in-app rendering and user
acceptance remain separate. Model/app identity remains unreported to Wright and
not independently attested. No physical or protected-campaign operation occurred.

Suggested screenshot caption: **Wright now shows when a workflow is waiting for
this desktop conversation, including the exact task and continuation step.**
Use the waiting and completed screenshots in the second evidence root, labelled
as browser verification. No external publication is authorized.
