# Experimental Codex chat pilot

Approved implementation scope: 11 October 2026. Branch `codex/codex-platform-integration`
on fetched dev `ba2fad68c181165b96b9c15c40b1a1f63c88acb3`. The original clean dev
checkout at `a4a31c97` and installed Wright remain separate and unchanged.

The user accepted **Chat pilot exception; gate authoring/workflows** after the pinned
runtime failed zero-tool qualification. Deliver an opt-in workspace-chat integration
with documented native-tool exceptions. Use the official runtime; maintain no fork.
[Exceptions](exceptions.md) retain the failed contract and explicit limits.

## Implemented ownership and boundaries

The official Python SDK controls the documented app-server over stdio. Pin both
`openai-codex` and `openai-codex-cli-bin` to 0.162.1; the existing desktop 0.159.2
is unchanged. A bounded worker supplies clean environment/private home/cwd, explicit
denial, an RPC allowlist, bounded notifications and owned POSIX process cleanup.
The SDK approval default and inherited environment are never used unmodified.

The adapter depends on core contracts and an injected storage port. DataVault owns
SQLite chat/session/turn receipts. WorkspaceService supplies host composition; API
composition supplies the adapter and scopes its gateway callback. Package dependency
rules are unchanged. Existing session associations retain their platform; changing
the default affects new sessions. Unsupported saved providers never fall back.

Wright retains workflow definitions, durable runs, accepted validation, declared
input/review checkpoints, external-action authority and recovery. Codex chat cannot
start a workflow or enter the confined process-UI authoring role. Cached Hermes
role owners cannot substitute for a Codex session. Existing job status/cancellation,
saved interfaces, common views and manual editor capabilities retain their owners.

Each chat records exact instructions, a redacted resolved configuration snapshot,
tool controls/descriptor, model/effort, authentication identity digest and client/runtime
versions. Digests are checked against snapshots and resolved configuration on continuation.
A durable dispatching receipt precedes handoff; ACK, terminal state and uncertain
outcome are distinct. Reconcile only a known exact native turn. Never replay lost ACKs,
unknown effects, duplicate attempts, reroutes or drift automatically.

One fixed read-only `wright__workspace_status` operation travels through an experimental
public dynamic-tool callback into the existing Wright GatewayService. Freeze its
session/workspace/principal binding. Empty arguments, active native thread/turn and
permitted name are mandatory. Gateway permissions and audit retain authority; agent
approval denial grants no process review or external-action permission. This is not
native Codex MCP stdio compatibility proof. Remaining native tools are the accepted
chat exception, not a qualified gateway-only set.

Evidence scopes remain separate: SDK call/notification, native ACK/terminal, gateway
receipt, local fixture provider request and observable result. No opaque provider
prompt, tool effect or billing cost is inferred from an app-server payload.

## Milestones and next stages

1. Baseline, isolation, negative authority control and durable foundations: implemented.
2. Smallest useful milestone: authenticated text chat, streaming, scoped gateway read,
   saved history/continuation, cancellation and immutable routing: implemented and tested.
3. Reviewable local pilot: source/UI regression, evidence matrix, local gates, commit and
   Windows handoff. Qualification records below distinguish passes from limitations.
4. Deferred authoring: require a released public enforced empty tool set; then reuse
   process-ui-author/1, existing instructions, client/kit, isolated builder, preview,
   saved revisions and common-view fallback. Prove corrections stay in the frozen role.
5. Deferred workflow tasks: require the same tool ceiling; then generalize existing
   frozen model dispatch while preserving Wright's bounded decision/gateway loop,
   durable runs, validation, checkpoints and no-replay recovery. Use fresh original
   manufacturing-preparation and Robot Tracking Diagnosis copies as contrasting proofs.
6. Separate Linux x64, native Windows and Docker lanes and full repository gates before
   any broader support claim. Packaging declarations are not host qualification.

## Validation and integration

Tests cover success, denial, drift, unknown dispatch/transport loss, duplicate attempts,
restart reconciliation, rerouting, cancellation terminal state, default switching and
cached-role substitution. A real credential-free runtime fixture proves gateway
success/denial/audit and restart/cancellation. Bounded authenticated ChatGPT turns
prove gpt-6.1-sol/high access and continuation; the original credential file is unchanged.
The served workspace opens Workflows and the latest reviewed editor acceptance cases
exercise actual controls, not a detached route or mocked editor.

No MCP catalog fixes or shared gateway implementation changes belong to this branch.
Fresh local state and ports isolate this workstream. Before future authorized integration,
fetch current dev, inspect overlap, rebase without original evidence changes, and run
repository gates. No push, merge, release, live configuration change, protected campaign
resumption, physical work or human engineering acceptance is authorized or claimed.
