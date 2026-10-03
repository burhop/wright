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
NumericPlot, ScalarFieldPlot, ResultRepresentation and WorkingControls. Component/type signatures are supplied from
the installed version. Kit styles are imported by the kit; use its theme tokens.

Snapshot inputs are declared input definitions, not frozen values. Frozen values
come from InputSnapshot bindings. Preserve explicit false, zero and null values;
never invent a default. Resolve required inputs and readiness before starting.
Only declared PendingInteraction values create user forms. Reviews and actions
are distinct from input responses. Match actions to both checkpoint and subject
digest. Never choose an arbitrary first action as dispatch authority.

ResultCard displays exact outputs, representations and assessment currentness.
Provider success, a valid file and a preview are separate from compliance.
Each snapshot output is an `OutputRef`: use its `step_id` and `port_id` for
stage grouping, plus `result_id`, `role`, `title`, `representations`,
`assessments` and `supported_viewers` for presentation. It has no `block_id`
field. Do not cast outputs to unknown shapes to bypass the public types.
Use supported viewers only; show safe inspection/download fallback otherwise.
For a generated results view, prefer `ResultRepresentation` to hand-written read
controllers. It accepts `client`, the host's `snapshot`, an optional selected
`ArtifactRef` as `reference`, and `onClose`. Wire `ResultCard.onOpen` to a local
selection setter. The component verifies membership in the supplied current run
results, uses the scoped client for exact reads, aborts superseded reads, and
provides shared viewing/download/loading/error states. It never attaches, starts
or independently observes a process:

```tsx
const [selected, setSelected] = useState<ArtifactRef | null>(null);
// Keep every ResultCard's existing onNavigate callback.
<ResultCard output={output} onOpen={setSelected} onNavigate={navigate} />
<ResultRepresentation client={client} snapshot={snapshot}
  reference={selected} onClose={() => setSelected(null)} />
```

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
There are at most two arguments: put context, preview and signal together in the
second options object. Do not pass a third options argument:

```ts
const context = snapshot.context.run_id
  ? { runId: snapshot.context.run_id }
  : { inputSnapshotId: snapshot.context.input_snapshot_id };
const blob = await client.getRepresentation(reference, { ...context, signal });
const readToolpaths = (signal: AbortSignal) => client.getRepresentation(
  reference, { ...context, preview: "toolpaths", signal },
);
```

Never silently select or merge ambiguous plates. Pass the artifact SHA-256 as
`sourceSha256` and an abortable scoped `readToolpaths` callback to
`RepresentationViewer`. The reader retains source/package digests, version,
true layers, nominal arc approximation and unknown feature labels. Neither a
preview nor recognized model/support comments establish engineering acceptance.
Unsupported motion, unreadable or excessive data keeps the exact download.
An independently produced, recorded `wright.gcode.toolpaths.v1` JSON result can
also be opened by `RepresentationViewer`, with that result's exact
`sourceSha256`. It displays the recorded evidence without requesting another
package parse. Keep its reported package hash distinct from its evidence-file
identity and retain linked assessments. The shared viewer requires bounded,
finite paths and reader provenance, and discloses any declared nominal section
and excluded machine setup/shutdown. It does not verify package correspondence,
interpret vendor commands or approve engineering. JSON reads are bounded to
16 MiB; ordinary text preview remains at 1 MiB.
CSV views retain the actual table; numerical axes are explicit display choices,
without inferred units, interpolated geometry or compliance claims.

For preparation, use InputEditor with declared definitions and draft bindings,
uploadInput for an explicit file choice, setInputs to freeze the bindings, and
checkReadiness for that exact InputSnapshot. Only an explicit, writable start
control calls start with the frozen snapshot and one retained request identity.
An input edit invalidates the local readiness display. The native host handles
the accepted start receipt and rebinds the working presentation to its run.

Prefer the shared `WorkingControls({client, snapshot, readOnly, onNavigate?})`
composition for preparation and declared interaction controls. It delegates to
the scoped client, checks Start permission for the exact frozen inputs, retains
mutation request identities before sending, and holds uncertain outcomes without
replay. The host still supplies authoritative snapshots and owns run observation
and start rebinding. Use a visible navigation error callback. If the current
projection cannot reconcile a retained receipt, offer the common working view;
never implement an alternative executor or guess a successful outcome.

For an update, Wright supplies `previous_manifest` and seeds the assigned
manifest with the saved bindings, capabilities, navigation and viewers. Preserve
those declarations when retaining their controls. `WorkingControls` preparation
requires `process.inputs`; starting requires `process.start`; declared responses,
reviews, actions and cancellation require their corresponding capabilities.
Include only capabilities supplied in `available_process_capabilities`. A source
import or visible control does not grant permission. A deliberately read-only
interface must disclose unavailable operations and offer the common view.

For declared interactions, CheckpointCard's response, review and execution props
are public UI-kit callbacks, not additional AppProps. Match the currently enabled
Action to both checkpoint_id and subject_digest. Use respond, decide or
requestAction respectively, with one request identity recorded before mutation.
Do not choose a first arbitrary action or dispatch on mount. On an uncertain
response, disable new mutations and offer explicit read-only reconciliation;
never replace the uncertain identity or automatically retry. Get current state
from the client/host. The common working view remains available for canonical
recovery; UI-local loading, form drafts and errors are not process status.

For updates, preserve valid bindings and change the requested presentation.
Layout/title changes do not invalidate engineering evidence. Changed required
binding/schema needs compatibility checks and a common-view fallback. UI version,
source/build/role/model hashes are retained by Wright, not fabricated by the UI.
