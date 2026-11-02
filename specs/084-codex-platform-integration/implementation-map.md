# Reused boundaries and remaining integration

| Wright owner | Pilot changes / preserved responsibility |
| --- | --- |
| Core | Frozen chat configuration, instruction/tool snapshots and receipts; storage port without filesystem/database dependencies |
| DataVault | Additive chat metadata, immutable gateway binding and CAS turns; existing workspace platform association retained |
| Agent adapters | CodexAdapter implements existing BaseAgentEngine chat contract; isolated pinned SDK worker/transport; no DataVault import |
| WorkspaceService | Injected host composition, platform-aware context/lifecycle sync; no synthetic local session when Codex fails |
| API composition | Per-platform engine cache and session-bound routing; default only affects new sessions; owned shutdown |
| Wright gateway | Existing GatewayService permissions, scope, timeout and audit; fixed read-only dynamic-tool callback, no shared gateway implementation change |
| Evidence | Existing ChatInvocationRecorder gains separate app-server SDK call scope; existing Hermes provider evidence unchanged |
| Workspace UI | Default picker, per-session model catalog, truthful terminal notices, preserved Codex default and StrictMode history restoration |
| Process UI authoring | Existing role, assets, builder, preview, revisions/common view retained; Codex model entries explicitly unavailable, cached Hermes cannot substitute |
| Workflow tasks/runtime | Existing dispatch, bounded decisions, gateway authority, durable runs, reviews and recovery retained; Codex start routes gated |
| Editor | Current Feature 083 four-group editor, blank workflow, typed authoring, source/drafts/layout/conflicts retained; normal Workflows entry tested |

The registry describes Codex as experimental. Bare adapter-registry construction needs
application storage composition; API construction supplies it. No dependency-policy
exception, gateway catalog fix or second workflow executor is introduced.

## Deferred stages

1. Released public startup ceiling: prove empty and Wright-gateway-only tool sets,
   including nested/direct/delegation tools, configuration drift and restart.
2. Confined process-UI authoring: reuse process-ui-author/1 and existing versioned
   assets/client/UI kit/builder/preview/revisions/common view. Freeze correction turns;
   prove no tools and actual served generation/save/update/reuse.
3. Workflow-task model dispatch: generalize existing workflow_model_routing,
   workflow_sdk/report-generation contracts, preserving input/review checkpoints,
   external-action authority and uncertain-outcome holds. A Hermes provider named
   codex_responses is distinct from an embedded Codex agent platform.
4. Run fresh unchanged manufacturing preparation and Robot Tracking Diagnosis copies
   through shared mechanisms. Resolve the independent exact-byte baseline defect first;
   do not assign new campaign work or weaken requirements.
5. Qualify native Windows ACL/descendant cleanup, Linux x64 and authenticated/packaged
   Docker separately; scoped ARM64 Docker lifecycle and image-security proof already passed.
   Extend tools/auth/model/usage only after evidence supports those capabilities.

Developing Wright using Codex, embedding this optional platform in Wright, and
running development jobs in Codex Cloud remain separate uses. Cloud is not Wright's
workflow executor and is not qualified by these local tests.
