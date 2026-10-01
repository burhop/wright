# Wright UI kit

`@wright/ui-kit` supplies the same public React presentation components to native
working views and saved process interfaces. It imports no private application
state, routes or services. It never starts a process, qualifies a provider,
records a review or decides whether engineering output is acceptable.

## Compose a working view

```tsx
import { useState } from 'react';
import { ProcessUI, Section, InputEditor, ProgressPanel, ResultCard } from '@wright/ui-kit';
import type { InputBinding, InteractionSnapshot } from '@wright/process-client';

export function WorkingView({ snapshot }: { snapshot: InteractionSnapshot }) {
  const [drafts, setDrafts] = useState<Record<string, InputBinding | null>>({});
  return <ProcessUI>
    <Section title="Your request">
      {(snapshot.inputs ?? []).map(input => <InputEditor
        key={input.input_id} definition={input}
        binding={drafts[input.input_id]}
        onChange={binding => setDrafts(previous => ({ ...previous, [input.input_id]: binding }))}
      />)}
    </Section>
    <Section title="Progress">
      <ProgressPanel state={snapshot.state} observations={snapshot.observations ?? []} />
    </Section>
    <Section title="Results">
      {(snapshot.outputs ?? []).map(output => <ResultCard key={output.result_id} output={output} />)}
    </Section>
  </ProcessUI>;
}
```

This example is a presentation fragment: it does not execute on mount. A host
controller prepares/saves the drafts through the scoped client, checks readiness,
and connects explicit controls to the backend-permitted actions. Render guards
and disabled buttons cannot replace backend checks. Mount controllers under an
accepted-revision key; stale async replies must never enter another process/run.

## Public components

| Component | Purpose |
| --- | --- |
| ProcessUI, Section | Consistent theme and composable sections; no required domain stages. |
| InputEditor, SchemaField | Declared values, objects/arrays/local definitions, units/frames and actual configured options. |
| ImageThumbnail | Bounded bitmap Blob preview, including uploaded references; releases local URLs. |
| ReadinessPanel, ReasonNotice | Backend readiness, later-input classifications, correction and technical detail disclosure. |
| ProgressPanel | Distinct run states and fresh observed progress; no extrapolated time/percentage or fabricated completion. |
| ActionButton, CheckpointCard | Explicit callbacks and exact permitted checkpoint/subject actions; no implicit approval. |
| ResultCard, EvidenceReference | Exact result/representation/assessment links, currentness and producer navigation. |
| FindingsPanel, NavigationButton | Owning-service findings/corrections and exact host navigation intents. |
| RepresentationViewer, DataTable | Bounded bitmap/STL/plaintext/CSV views and paginated tables; unsupported-format fallback. |
| ThreeDViewer, ToolpathViewer | Neutral 3D orbit/zoom, all supported layers and reported categories; no device protocol. |
| NumericPlot, ScalarFieldPlot | Supplied numeric profiles/samples, ranges and units; no analysis or acceptance verdict. |

Schema editors show unsupported forms explicitly instead of dropping required
fields. Defaults are shown only when present in backend bindings; schema constants
require a deliberate choice. Clearing a number removes the value; false is
preserved. The backend owns full schema validation and readiness.

File upload is a host callback returning an exact ArtifactRef. The browser
does not embed files in input JSON. Selecting a replacement clears the old
binding before upload. Upload failure does not reuse the previous file. The
thumbnail is tied to its Blob identity; cleanup revokes its URL and prevents
showing the old file under a new title. File MIME/data verification and digest
authorization remain with the owning host service.

Progress freshness expires while a view is idle. The timestamp is never renewed
by reading/rendering. Confirmed terminal history remains historical; a terminal
operation does not advertise remaining time. The optional `now` prop permits
a host clock source. No completion percentage is derived from the stage count.

Actions require both current backend permission and an explicit handler. Read-only
and missing-capability views remain disabled with reasons. Checkpoint cards only
show actions matching both checkpoint and subject digest. They do not invent a
question, action, review, default or subject. The native controller and generated
bridge independently recheck authority through the owning services.

## Theme and isolation

The kit bundles the existing Wright tokens and scoped component CSS. Native
`apps/web/src/tokens/design-tokens.css` imports the same public token resource,
so there is one owning palette/spacing/font fallback definition. `ProcessUI`
accepts `theme="dark"` or `theme="light"`; an isolated host supplies theme through
its reviewed handshake. Font stacks fall back locally without network requests.
3D backgrounds/materials react to ancestor theme changes. No parent CSS/private
React import is required. Keyboard focus, native labels/fieldset grouping,
status/error announcements, button reasons and reduced-motion CSS are provided.
Actual served browser/responsive/accessibility verification remains required.

## Viewer limits and evidence

STL display is bounded to 32 MiB/three million finite vertices and displays Z-up
coordinates. This only rotates the view, never the exact stored file or its
manufacturing orientation. Missing WebGL/invalid data has an actionable fallback.
Scene controls, observers, frames, geometry and materials are disposed on close.

`parseToolpaths(data, exactPackageSha256)` reads the neutral
`wright.gcode.toolpaths.v1` view document and checks its package identity,
finite coordinates, strictly ordered layer indices, at most 10,000 layers and
one million segments. The loader does not execute G-code or control a device.
Only explicit `classification_source: "gcode_feature_comments"` enables reported
model/support categories. Older documents lack this evidence and display all
paths as unclassified. This field describes a reader method; it does not certify
support adequacy, machine compatibility or engineering compliance.

CSV views are bounded to 2 MiB, 10,000 data rows, 50 columns and 8 KiB fields;
quoted commas/newlines/quotes and CRLF/BOM are supported. Tables paginate rather
than silently pretending that initial rows are complete. Text/JSON previews are
limited to 64 KiB. HTML/SVG is never embedded as executable document content.
Larger/unsupported representations retain exact open/download fallback.
Numeric plots display supplied values with finite extents, at most 10,000
samples; scalar fields do not invent interpolated geometry.

Result identity, finding/profile scope, hashes, freshness, engineering acceptance,
canonical checksums and provider attestation remain backend/assessment authority.
An attractive rendering or empty findings list cannot approve a subject.
