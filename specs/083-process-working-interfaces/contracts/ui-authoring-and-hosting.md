# Contract: coding role, saved interface and workspace hosting v1

## Coding role

Profile `process-ui-author/1` comprises role name/version, instruction resource
version/hash, model policy (`inherit_default` initially), adapter capability
requirements, allowed artifact scope, permitted tools and repair budget.
Store resolved adapter/model/config identity without credentials on each job.

Extend BaseAgentEngine with backward-compatible optional invocation context and
capability reporting. Hermes must apply effective role/system instructions on
every turn, honor the confined/no-tool first role and inherit the actual default
model. If the underlying platform cannot enforce these constraints, mark authoring
unavailable; do not fall back to broad `/agent/chat` workspace-tool activation.
Do not change a global profile/model for one generation. Future model overrides
and platforms remain capability-checked extensions, not claimed initial support.

Workspace-service authoring job reads the accepted interaction description,
public client/kit docs, template and optional previous UI source. It creates an
isolated session and requests structured source+bindings. Allowed first-role
output is presentation source only; it has no shell, arbitrary filesystem,
engineering MCP or process execution authority. If needed, narrowly scoped
authoring tools go through existing gateway enforcement, not prompt-only permission.

Generation shows resolving/generating/validating/building/preview-ready states and
actionable errors. At most two repair attempts receive exact bounded binding/build
diagnostics; persist budget, inputs and provenance. Cancel/reload reconstructs job
state. A failed job leaves the common working view usable.

## Source/binding envelope

`wright.process-ui/1` accepts fixed App.tsx, optional style.css, local assets and
binding.json. No package.json, scripts, compiler plugins, backend files, external
URLs, launch argv or environment overrides. Paths must remain under the assigned
revision draft. Initial bounds: 32 source/assets files, 1 MiB total text, 10 MiB
assets, 30 MiB built bundle, 120-second compiler timeout; expose configurable
administrative bounds without allowing model overrides.

Binding manifest fields:

- schema_version, ui_id/revision/parent, title.
- accepted ProcessRef plus interaction-contract major, client/kit supported versions.
- bindings: stable ID; selector kind (input, output role, assessment, interaction,
  observation, action); block/port/role identity; expected schema/version; required
  or optional; optional fallback description.
- requested capabilities: closed process operation scopes from the client contract.
- navigation targets and declared result-viewer types.

No credentials, hard-coded run IDs or raw campaign-path naming as authority.
The server compares selectors/types against the accepted process and actual
provider contracts. It grants only configured permitted scopes. Changing a required
binding/schema invalidates compatibility; unresolved optional bindings disclose
fallback. Titles/layout changes do not invalidate engineering output/review.

## Fixed build and installed resources

Public packages: `packages/process_client` (`@wright/process-client`) and
`packages/ui_kit` (`@wright/ui-kit`), local/pinned npm distributions initially.
Kit bundles tokens/styles and accessible primitives/patterns plus supported
format viewers. No apps/web private imports. The same kit powers the native
common view. Existing project lockfile/tool versions are the initial toolchain;
no new framework/package manager or automatic public package publication.

Wright owns the fixed builder/template/dependency allowlist and invokes pinned
compiler arguments, without executing generated package scripts. Node/build
availability is checked as an authoring capability; installed resources include
the template/toolchain declaration and packed client/kit. Air-gapped authoring
uses prequalified local tools/assets. Missing compiler/model returns unavailable;
opening saved apps works offline without generation/build/package download.

Persist source, binding, compiled static assets, build report and all hashes at
`.wright/process-uis/<ui-id>/revisions/<revision>/` through vault services.
Revision metadata references role/model/instruction/adapter/generation/build
provenance. Structured source/import checks are quality gates. Isolation, CSP and
server authority remain enforcement boundaries even for syntactically valid code.

## Preview/save/update API

Routes relative to the existing workspace mount:

| Route suffix | Behavior |
|---|---|
| GET /process-interfaces/authoring-capabilities | Actual role/adapter/model/build readiness and unsupported options |
| POST /process-interfaces/authoring-jobs | Request generation or update for accepted ProcessRef/base revision |
| GET /process-interfaces/authoring-jobs/{job_id} | Durable state, diagnostics and validated preview reference |
| GET /process-interfaces/authoring-jobs/{job_id}/events | Bounded progress/diagnostic event stream |
| POST /process-interfaces/authoring-jobs/{job_id}/cancel | Explicit authoring cancellation |
| POST /process-interfaces/uis/{ui_id}/revisions/{revision_id}/save | Save the built previewed revision using expected hashes |
| POST /process-interfaces/uis/{ui_id}/activate | Select compatible saved revision/rollback |
| GET /process-interfaces/uis/{ui_id}/compatibility | Accepted process/current binding comparison |
| POST /process-interfaces/uis/{ui_id}/present | Resolve saved artifact/grants and create workspace-tab presentation |
| GET /process-interfaces/uis/{ui_id}/runtime-diagnostics | Read exact revision/surface runtime state and bounded existing logs under native process scope |

Runtime diagnostics require `session_id`, `path`, `expected_storage_digest`,
`revision_id` and `surface_id`. The native owner verifies the process/UI and
immutable build provenance, then verifies the existing surface's principal,
workspace, session, Wright ownership and exact revision manifest. Log requests
accept `after_sequence >= 0` and `1 <= limit <= 100`; responses are `no-store`.
This endpoint delegates to the existing runtime/log owners and performs no start,
health probe, generation or process action. It does not change legacy generic
surface principal fallbacks. If the captured buffer is unavailable, persisted
runtime state remains readable with `logs: null` and
`logs_unavailable: "SURFACE_LOGS_UNAVAILABLE"`; this is not evidence that the
original process produced no logs.
After restart, the manager may have no live instance because startup
reconciliation revoked its authority. An exact scoped descriptor remains
readable as `state_source: "surface-reconciliation"`, with `generation` and
`last_health` null and `logs_unavailable: "SURFACE_INSTANCE_NOT_FOUND"`.
Its diagnostic summary describes reconciliation, not the original failure or
a new health observation. Live instances use `state_source: "runtime-owner"`.

Preview is read-only against actual references or an explicitly labelled isolated
fixture context. It cannot start work on mount. Saving activates presentation
metadata, not engineering source/evidence. Testing a real process is a separate
explicit operation on the authorized run context.

## Managed asset hosting and scoped bridge

Generate an internal managed-app manifest starting an installed generic Wright
static-asset runtime for the immutable bundle. Do not accept model-selected
command/URL. Reuse existing surface origins, cookie bootstrap, lifecycle, bounded
process ownership, sandboxing, health and revocation. Extend the manifest's closed
capability allowlist with reviewed process scopes. Resources remain local with
restrictive CSP; device/network access is not an implicit UI capability.

Reserve `/__wright/process` on the preview origin. SurfaceRouteAuthority and
CapabilityGrantService derive principal/workspace/presentation/runtime generation/
UI/process/attached-run identity server-side. All operations pass through the same
owning process services as native UI. Revoked/expired/stale presentation, wrong
workspace/run/UI, unsupported capability or changed subject rejects mutations.
Server-mediated representation access may expose a provider's supported stream;
it must not invent camera support or embed printer credentials.

MCP Apps keep same-server provider visibility/grants and separate contracts.
WebMCP page-local registration remains the reverse page-tool direction. Do not
widen either into arbitrary engineering tool access for a generated process UI.

## Tabs, navigation and fallback

Add typed process-common, process-working and process-preview descriptors to the
existing WorkspacePanel/EditorTabs/store/viewer host, preserving workspace files
and workflow editor. Reuse LiveAppSurface as the isolated presenter inside that
tab. Explicitly request panel presentation for these views; do not globally
change unrelated managed-app preferences or add another competing tab strip.

Persist view intent with process/UI/run references. Restore by backend lookup and
compatibility checks; local tab data is not permission. Close disposes/revokes
presentation only. Reopen attaches to the same run; it neither restarts nor cancels.
Validated exact-origin host messages carry theme/context and navigation intents,
never bearer credentials or broad tool authority. Deep links open the retained
accepted editor at exact block/result/assessment/evidence context.

Incompatible/missing UI offers the common view and focused Update interface.
Common/tailored surfaces show identical backend action reasons and assessment
currentness. Keyboard/theme/image preview/loading/error/reconnect states are
required. Unsupported result formats retain safe inspection/download alternatives.
