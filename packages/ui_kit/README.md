# Wright UI kit

`@wright/ui-kit` supplies the same public React presentation components to native
working views and saved process interfaces. It imports no private application
state, routes or services. Presentation patterns do not execute operations.
The optional `WorkingControls` composition delegates explicit user requests to
the existing scoped process client. The backend remains the owner of execution,
provider qualification, review records and engineering acceptance.

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
| ImageThumbnail | Bounded inline raster preview from scoped Blob bytes, including uploaded references; rejects active formats and stale reads without fetching external images. |
| FileDownloadProvider | Optional host delivery for exact scoped bytes; explicit requested, declined and unavailable outcomes. Standalone browser downloads retain their existing behavior. |
| ReadinessPanel, ReasonNotice | Backend readiness, later-input classifications, correction and technical detail disclosure. |
| ProgressPanel | Distinct run states and fresh observed progress; no extrapolated time/percentage or fabricated completion. |
| ActionButton, CheckpointCard | Explicit callbacks and exact permitted checkpoint/subject actions; no implicit approval. |
| WorkingControls | Shared preparation and declared-interaction controls over the supplied scoped client, with retained request identities. |
| ResultCard, EvidenceReference | Exact result/representation/assessment links, currentness and producer navigation. |
| FindingsPanel, NavigationButton | Owning-service findings/corrections and exact host navigation intents. |
| RepresentationViewer, DataTable | Bounded bitmap/STL/plaintext/Markdown/CSV views and paginated tables; unsupported-format fallback. |
| ResultRepresentation, RepresentationDownload | Exact scoped result reads, loading/errors, stale-read disposal, shared viewing and exact-file download. |
| ThreeDViewer, ToolpathViewer | Neutral 3D orbit/zoom, all supported layers and reported categories; no device protocol. |
| NumericPlot, ScalarFieldPlot | Supplied numeric profiles/samples, ranges and units; no analysis or acceptance verdict. |

Markdown representations (`text/markdown` or `text/x-markdown`, up to 64 KiB)
show headings, lists and tables with a **View source** disclosure. The original
Markdown text stays available and exact downloads retain the supplied bytes.
HTML is skipped, and links and
embedded images are passive text: they cannot fetch files, navigate or obtain
authority from document contents. Referenced evidence remains available through
the existing scoped evidence controls. Plain text is not inferred to be Markdown.

Schema editors show unsupported forms explicitly instead of dropping required
fields. Defaults are shown only when present in backend bindings; schema constants
require a deliberate choice. Clearing a number removes the value; false is
preserved. The backend owns full schema validation and readiness.

`WorkingControls` takes `{client, snapshot, readOnly, onNavigate?}`. Use it in
an interface receiving Wright's public `AppProps`; supply the host's current
snapshot rather than implementing another process monitor. It freezes explicit
input drafts, checks readiness and reads the permitted Start action for that
exact frozen input digest. Input edits invalidate preparation. An expired
assessment or missing/disabled Start permission keeps Start disabled.

Reviews, declared responses, actions and cancellation use only the current
backend actions and exact checkpoint/subject identity. Every mutation records
one request identity in session storage before sending; unavailable storage
prevents sending. Mounting and restoration never replay operations. An unknown
outcome holds new mutations. Explicit reconciliation only clears a retained
review/action when the exact receipt is present in the same process/run snapshot.
Start, response and cancellation recovery use the canonical common working view
when the public projection lacks a matching receipt; the component does not
invent one. The native host owns accepted-start rebinding and run observation.
Reads and uploads are aborted when the process/run scope unmounts; that does
not cancel an accepted run.

`CheckpointCard` accepts an optional `response` control for declared input steps:
`{value, onChange, onSubmit, busy?, readOnly?, blockedReason?}`. It uses the exact
interaction's `response_schema` and only its matching permitted action/subject.
No fields or responses are invented from AI prose. A missing value explains what
to provide; busy, read-only, stale and consumed controls stay disabled. The host
calls the scoped client's `respond` explicitly and follows the same run. The
component never submits on mount or decides engineering acceptance.

For declared reviews, `CheckpointCard.review` accepts
`{reason, onReasonChange, onSubmit, busy?, readOnly?, blockedReason?}`. It renders
only the supported choices actually listed in `interaction.decisions` for a
matching backend review action. Requested changes require a reason; approval is
separate from dispatch. The controller explicitly calls the scoped `decide`.

`CheckpointCard.execution` accepts `{onSubmit, busy?, readOnly?, blockedReason?}`
for a matching permitted action. The user confirms review of its exact evidence
before continuing. A changed subject clears that confirmation. The host explicitly
calls `requestAction`; saved decision and action receipts are evidence rather than
permission. Authorization, provider acceptance, observed completion and cancellation
outcome are displayed separately. No mutation runs on mounting a component.

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
Readiness expiry also updates while idle: an expired ready assessment is labelled
as needing refresh, while the host and backend separately guard starting a run.

Actions require both current backend permission and an explicit handler. Read-only
and missing-capability views remain disabled with reasons. Checkpoint cards only
show actions matching both checkpoint and subject digest. They do not invent a
question, action, review, default or subject. The native controller and generated
bridge independently recheck authority through the owning services.

## Theme and isolation

The kit bundles the existing Wright tokens and scoped component CSS.
Result image readers default to a maximum height of `70vh`. A tailored view may
set `--wright-result-image-max-height` on its reader container to fit a compact
review layout. Images keep `object-fit: contain`; this affects presentation only,
not the exact file, retrieval scope, evidence or review permissions.

Native `apps/web/src/tokens/design-tokens.css` imports the same public token resource,
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

`parseRecordedToolpaths(data, exactEvidenceSha256)` uses the same finite parser
for a separately recorded neutral toolpath JSON result. The scoped result reader
owns its exact file identity. Its reported package hash stays distinct from the
evidence-file hash; rendering this record does not revalidate package correspondence.
Supported reader provenance is required. Explicit nominal section markers, line
ranges, excluded prefix/suffix counts and selected-text hash are validated and
displayed. The view prominently discloses excluded, unverified machine setup and
shutdown. It neither interprets unknown commands nor changes engineering gates.

CSV views are bounded to 2 MiB, 10,000 data rows, 50 columns and 8 KiB fields;
quoted commas/newlines/quotes and CRLF/BOM are supported. Tables paginate rather
than silently pretending that initial rows are complete. Text previews are
limited to 64 KiB. JSON reads are bounded to 16 MiB so recorded neutral layer
data can use the same shared 3D viewer; ordinary JSON text remains bounded to
1 MiB and is displayed as inert text in a scrollable pane. HTML/SVG is never
embedded as executable document content.
Larger/unsupported representations retain exact open/download fallback.
PDFs use `readPdfPage(page, signal)` through the existing scoped result client.
The server verifies exact membership and source bytes before rendering one page
as passive PNG data (`wright.pdf.page.v1`). Limits are20MiB per PDF,200 pages,
1800px per side and8MiB per page response. The reader preserves the original PDF
download; the raster is a presentation, not a new engineering output. PDF forms,
links and scripts are not activated. Missing/failed rendering shows a download
fallback. The UI verifies source hash, page identity and PNG dimensions, discards
stale reads and resets page selection when the original blob changes.
**Enlarge drawing** displays the available page pixels inside a focusable,
scrollable region; **Fit drawing** restores the page overview. Enlargement is
local presentation state and resets for a different source blob. It does not
request another engineering operation or change the original PDF.
Numeric plots display supplied values with finite extents, at most 10,000
samples; scalar fields do not invent interpolated geometry.

Result identity, finding/profile scope, hashes, freshness, engineering acceptance,
canonical checksums and provider attestation remain backend/assessment authority.
An attractive rendering or empty findings list cannot approve a subject.

`ResultRepresentation({client, snapshot, reference?, onClose?})` composes the
shared result viewer and exact download with bounded scoped reads. Pass the
host-owned snapshot and the reference selected through a ResultCard. It rejects
references absent from that current run's outputs, aborts reads on replacement
or context change, and keeps loading/errors local to presentation. It does not
attach, observe, execute or cancel process work. This allows AI-authored layouts
to reuse the read lifecycle without reconstructing client signatures or recovery.

Recorded validator assessments use the same reader. `RepresentationViewer` accepts
`readValidationReport(signal)`, supplied by both the common view and
`ResultRepresentation`. Recognizing assessment JSON is only a presentation hint:
the scoped backend must match the exact bytes to its owning run's validation report.
The reader presents HOLD/PASS, currentness, original checks, observations, units,
methods and limitations from that report. It never evaluates or approves a result.
The original JSON remains the download; source previews are collapsed and bounded
to1MiB. A missing older-host capability leaves a visible download fallback. Late
reads are aborted/ignored on file replacement. Saved UI bundles keep their existing
reader until explicitly rebuilt; the common view supplies the current fallback.

Review layouts adapt to the width of their containing panel. `CheckpointCard`
stacks evidence and response controls when two readable columns will not fit;
`EvidenceReference` keeps file details below its filename and Open file control.
Verify generated layouts with an actual pending review inside a narrow panel,
even when the full browser is wide. Empty-state previews cannot prove review
readability. Layout changes do not alter the pending subject or review authority.
