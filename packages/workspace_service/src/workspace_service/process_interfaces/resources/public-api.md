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

For updates, preserve valid bindings and change the requested presentation.
Layout/title changes do not invalidate engineering evidence. Changed required
binding/schema needs compatibility checks and a common-view fallback. UI version,
source/build/role/model hashes are retained by Wright, not fabricated by the UI.
