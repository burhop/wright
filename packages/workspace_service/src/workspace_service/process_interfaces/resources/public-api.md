# Public interface composition contract — version 1

Allowed imports: `react`, `@wright/process-client`, `@wright/ui-kit`, local
`./style.css` and validated raster asset references under `./assets/`.
React's fixed JSX runtime is provided by Wright. The fixed host supplies:

```ts
import type { InteractionSnapshot, ProcessClient } from '@wright/process-client';
export interface AppProps {
  client: ProcessClient;
  snapshot: InteractionSnapshot;
  readOnly: boolean;
}
```

The host-bound client exposes getSnapshot, attach, follow, setInputs,
uploadInput, checkReadiness, start, respond, decide, requestAction, cancel,
getRepresentation and navigate. It has no arbitrary tool invocation. Exact
process/run/input/checkpoint identities are checked by the owning backend;
generated code does not grant itself another workspace or run. Do not construct
a native client or supply authentication yourself. Opening a saved UI requires
no model call or build. A preview's client rejects mutations independently of
disabled controls.

Use `@wright/ui-kit` public components: ProcessUI, Section, InputEditor,
SchemaField, ImageThumbnail, ReadinessPanel, ReasonNotice, ProgressPanel,
ActionButton, CheckpointCard, ResultCard, EvidenceReference, FindingsPanel,
NavigationButton, RepresentationViewer, DataTable, ThreeDViewer, ToolpathViewer,
NumericPlot and ScalarFieldPlot. Component/type signatures are supplied from
the installed version. Kit styles are imported by the kit; use its theme tokens.

Snapshot inputs are declared input definitions, not frozen values. Frozen values
come from InputSnapshot bindings. Preserve explicit false, zero and null values;
never invent a default. Resolve required inputs and readiness before starting.
Only declared PendingInteraction values create user forms. Reviews and actions
are distinct from input responses. Match actions to both checkpoint and subject
digest. Never choose an arbitrary first action as dispatch authority.

ResultCard displays exact outputs, representations and assessment currentness.
Provider success, a valid file and a preview are separate from compliance.
Use supported viewers only; show safe inspection/download fallback otherwise.
ProgressPanel displays actual state/observations and reported freshness. Closing
the app disposes observers, not the run. Abort pending reads when context changes
so a stale reply cannot enter a different process/run.

Wire result controls explicitly: `ResultCard` needs `onNavigate` and `onOpen`
callbacks. Use `client.navigate(target)` for its block/assessment targets and
`client.navigate({kind: "evidence", artifact_ref: reference.artifact_ref,
result_id: reference.result_id})` for exact evidence. In a managed presentation,
the backend supplies its already-authorized run when a navigation target omits
`run_id`. An explicit different run is rejected; a preparation presentation has
no run to supply. Native clients outside a managed presentation must specify the
recorded run for output navigation. Handle rejected navigation visibly rather
than interpreting a rendered or clickable card as verified evidence.

For a recorded 3MF or G-code artifact, `getRepresentation(reference, context)`
returns the unchanged bytes. An additive `preview: "toolpaths"` option requests
a bounded passive view through the same result/preparation scope; optional
`archiveEntry` selects one explicit G-code entry in a multi-plate archive.
Never silently select or merge ambiguous plates. Pass the artifact SHA-256 as
`sourceSha256` and an abortable scoped `readToolpaths` callback to
`RepresentationViewer`. The reader retains source/package digests, version,
true layers, nominal arc approximation and unknown feature labels. Neither a
preview nor recognized model/support comments establish engineering acceptance.
Unsupported motion, unreadable or excessive data keeps the exact download.
CSV views retain the actual table; numerical axes are explicit display choices,
without inferred units, interpolated geometry or compliance claims.

For updates, preserve valid bindings and change the requested presentation.
Layout/title changes do not invalidate engineering evidence. Changed required
binding/schema needs compatibility checks and a common-view fallback. UI version,
source/build/role/model hashes are retained by Wright, not fabricated by the UI.
