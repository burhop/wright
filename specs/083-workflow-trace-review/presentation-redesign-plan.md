# Engineering Review Presentation Redesign

**Date:** 2026-09-17. **Status:** Proposed implementation direction from the user's design-reset request. No claim of user acceptance or implementation completion.

**Evidence:** [Package review](presentation-review-2026-09-17.md). **Producer handoff:** [Process execution improvements](process-execution-improvements.md). **Implementation prompt:** [Goal](presentation-redesign-goal.md).

This is an amendment to feature 083, not a new workflow editor or validation project. Earlier checks establish export functionality, not acceptance of the report's engineering usability. This plan supersedes the generic file/property-led detail view. Preserve the working offline export, input imagery, final-model viewer, per-row expansion, named actors, and provenance features.

**Incremental implementation, September 17:** The activity inspector now leads
with inline evidence and a grouped process account. Bundled offline PDF viewing,
readable retained Markdown, source-manifest attribution and in-place reference
selection remove the drawing/download detour. This is not completion or user
acceptance of the full domain presentation plan. See the implementation log.

## Product Direction

The report is a completed engineering work record. A reviewer should be able to answer:

1. What was requested, and what was supplied?
2. What was produced or concluded, and what is its recorded release/validation scope?
3. What work led to that result?
4. Why was a particular choice made, and which exact evidence supports it?

Use **Request -> Results -> Process**, with progressive disclosure within each. At activity level use **Inputs used -> Work performed -> Outputs and supporting checks**. These are two different levels of explanation, not competing page orders.

Do not require an engineer to interpret transport JSON, GUIDs, storage byte counts or task-name slugs. Do not replace these with unsupported narrative. A readable statement must remain traceable to a source location or recorded event.

## Page Composition

### 1. Request and Input Basis

- Use the case's actual human title, short completed-run identity and date. Present the original request as a compact excerpt, with the full supplied text one action away.
- Place the supplied sketch directly beside or below the request where it is legible. It is an input concept, never a final design preview. Fit the full drawing; do not crop dimension callouts.
- Present supporting documents with meaningful names and one short source-backed description of their role. Distinguish user-supplied material, externally retrieved references and review-time reconstructed context.
- For a small set, show all logical inputs. For a large set, group by engineering purpose and place a counted disclosure adjacent to the group. No detached total that disagrees with the visible list.
- Treat PNG/SVG, PDF/page image and source/thumbnail as representations of one logical item only when provenance proves that relationship. A preview is not a second input or independent corroboration.
- Critical supplied conditions may be shown here as a compact, cited basis: operating load, envelope, material, target or interface. Do not promote extracted request text into a formally approved requirement unless approval evidence exists.
- Bound the section so a typical desktop first viewport includes the start of Results. Long prompts/documents must not push the engineering result several screens away. On mobile, use concise text and a deliberately sized useful sketch with access to its full view.

### 2. Engineering Results

- Lead with the principal result, not counts of activities/files. CAD: inspectable part or assembly. Analysis: conclusion plus explanatory field/curve. Harness: wiring diagram. Failure: retained partial work and the recorded stopping point.
- Use a concise conclusion taken from the producer record. If no conclusion was recorded, say what artifacts were produced without inventing a recommendation or winner.
- Use up to a few engineering facts that explain the result. Every fact has a subject, value, unit, condition and source. More precision and the original value remain available in detail.
- Put actual delivery/release state alongside the conclusion. Keep execution completion, upstream check outcomes, release authorization and physical dispatch separate. A simulated transfer is not a manufactured part.
- Existing holds, failed checks and scope qualifications must remain visible at the appropriate result/check. Do not manufacture a new concerns score or hide a producer's hold to make a successful execution look approved.
- Organize CAD/simulation deliverables by purpose, not extension: Design, Analysis, Manufacturing, or equivalent groups only when present. Each opens the relevant evidence in context.
- For Pi, show the A/B enclosure geometry first and the A/B thermal/flow comparison below at a readable size. Do not cram two models and two 2200-pixel plots into four tiny equal cards. The same plots can appear as thumbnails in relevant expanded swimlanes.
- The main model is an unframed viewer within the results band, with restrained view/reset/fullscreen/download controls and a static fallback. Supporting repeated media may use small bordered tiles. No decorative dashboard cards around whole sections.

### 3. Process and Handoffs

Retain responsibility swimlanes. Do not flatten the process into one row or use a global expand-all mode.

| State | Contents | Behavior |
| --- | --- | --- |
| Compact activity | Short engineering verb/object title, tool identity, state icon and repeat count only when relevant | Approximately 156-184 px wide with stable tracks; title wraps within a bounded height. No repeated "Tool used", "Recorded workflow activity", timestamps, file lists or unknown-value grids. Full title accessible. |
| Expanded responsibility row | Same activities and horizontal order, one useful result sentence and one or two evidence thumbnails or compact outcome rows per activity | Clicking the responsibility header/chevron expands only that row. Show meaningful preview captions and subject-specific outputs, not free-floating links. Neighboring rows stay compact. |
| Selected activity | Focused engineering account described below | Opens a roomy inspector without expanding all rows or losing graph position. |
| Input row | Compact input blocks at the same visual scale as activity blocks | Row expansion reveals request/image/document purpose within those blocks. No oversized always-open prompt slab. |

Graph layout rules:

- Freeze readable responsibility labels; keep phase headings and a clear horizontal scroll region. Group headings by real engineering phase, not one verbose heading per internal task ID.
- Use recorded graph/dependencies when present; preserve branch and retry structure. Reuse existing graph/layout libraries where appropriate, rather than writing a new graph engine.
- Where only event chronology is retained, show a visibly distinct recorded-order connector, identified once in the legend and in connector detail. Do not label it as a document transfer or draw false causality between concurrent activities.
- Explicit data handoffs show the transferred subject, with versions and occurrences in detail. Repeated passages stay on one edge with a traversal list. Distinguish whole-run attempts, activity occurrences and internal tool retries.
- The supplied-input row must not float disconnected above the process. Draw confirmed input-consumer arrows where bindings exist. For unbound run-level inputs, draw a labeled workflow-entry connection to the first recorded activity, explicitly distinguished from proven activity consumption. Clicking either connection exposes its inputs and relationship scope. If no activity was recorded, do not invent an entry target.
- Compact is a semantic reduction, not tiny text. Thirty activities will not all be readable across a laptop width. Use horizontal navigation, a small overview navigator and jump-to-selected-result/phase; do not auto-shrink every label to fit the entire run.
- Keep all lane identities visible when navigating; do not replace them with a compressed single path. Expand the selected row only when requested. Keep selected activity in view after expansion, resize and zoom.
- Route edges outside media/text; avoid repeated "Next recorded activity" boxes on every edge. Recalculate routing after row disclosure without changing graph selection.
- Do not invent omitted future activities in a failed run. Show known unexecuted blocks only from the retained executed definition; otherwise stop at the last known activity with the recorded blocker.
- Provide equivalent keyboard navigation and a concise accessible process outline within the same process surface, not a second visible duplicate index.

### 4. Activity Inspector

Use a wide, responsive inspector, approximately 960-1160 px maximum on desktop, full-screen on narrow viewports. It is not a narrow scrolling file-list drawer. A consistent back path restores the selected activity, occurrence, row expansion and scroll.

Opening a block shows, in order:

1. **What happened:** engineering title and a one-sentence purpose/outcome. A compact secondary line identifies the actual tool, recorded version and elapsed time when available. Keep absent metadata in execution details, not a wall of "Not recorded" cells.
2. **Inputs used:** named, exact source versions with a brief role and an informative thumbnail/excerpt when useful. The complete user prompt belongs at the run input and is linked here, not repeated in every block. Mark run-scope references as such if consumption by this activity is unproven.
3. **Work performed:** ordered actions with the input involved, operation, observation/decision, and resulting item. Put relevant evidence alongside the action that used or created it. A retrieved image needs a caption explaining subject, source and relevance.
4. **Outputs and checks:** principal outputs, changes from input, producer-reported checks, approval or handoff. Attach measurements to the exact checked version; use subject/criterion/result/unit/outcome/source columns when appropriate.
5. **Further detail:** recorded assumptions and decision rationales; exact task instructions; tool calls/configuration; timing breakdown; logs and original records. Group files by role within the activity, not in a second global supporting-documents section.

The default work account should be concise, commonly three to six actions, with longer sequences disclosed. An ordered method described in a retained report must be labeled as that report's account. Only timestamped call records justify claiming exact executed tool-call order. Do not generate missing historical reasoning, search queries, prompts or actions with an LLM.

For a loop, the inspector has an occurrence selector with outcome and change summary if recorded. Switching occurrence switches its inputs, outputs, measurements, decisions and checks together. Never mix a final artifact with an earlier approval/check.

### Example: Pi Reference Research

Rename the vague display title "Source dimensions" to a supported engineering label such as "Established reference dimensions". Preserve the original task identity in execution details.

- Input context: the customer's Pi 5 enclosure request and styling concept at run scope; claim direct step consumption only when evidence establishes it.
- Action: retrieved manufacturer mechanical/product/cooler references. Show publisher, URL, retrieval time and original documents. The source manifest supports the retrieval operation; it does not supply a complete model/MCP call transcript.
- Observation: drawing page 1 supplies approximate board/mounting dimensions. Show the drawing and the recorded 85 x 56 mm outline / 58 x 49 mm mounting pattern with its reference-only warning.
- Action/observation: examined the ruthex dimensional table and installation reference. Show the RX-M2.5x5.7 row association and distinguish the dimensional evidence from the illustrative installation image.
- Output: `manufacturer-research.md` separates manufacturer facts, customer goals and absent measurements. Present the useful account as a document, not a bag of file sizes.
- Instructions: original user request is available; exact resolved research prompt is not in the inspected bundle. Record the recovery request in the producer backlog rather than substituting today's script text.

### 5. Evidence Viewer

An evidence item opens a large visual/document surface with a compact context area: what it is, why it matters, origin, activity/occurrence, and source location. On narrow screens, context stacks below the media. Keep navigation back to the originating statement.

| Content | Required presentation | Truthful fallback |
| --- | --- | --- |
| PNG/JPEG/WebP and existing SVG evidence | Full image fit, enlarge/pan when needed, legible caption/source; SVG as inert image | Original download if unsupported; no inline active SVG |
| PDF | Inline multipage viewing, page navigation/zoom, source-page anchors and original download | Retained page renders with clear page coverage plus PDF download; record if the direct PDF viewer is unsupported in a tested browser |
| Markdown/text | Readable document with headings/tables, source links remapped to packaged identities | Original file and explicit unresolved links; no arbitrary HTML execution |
| CSV/TSV | Labeled table with units, row count and paging; relevant charts only from known column semantics | Raw file for unknown schemas; do not guess units or axes |
| STL | Existing offline Three.js viewer with correct framing, units when known and original download | Faithful retained/derived image plus download when WebGL or budget prevents interaction |
| STEP/3MF/native CAD | A qualified existing viewer or provenance-linked display representation | Clear format/original access; no unsupported claim of native viewing or invented geometry |
| VTK/VTU analysis fields | Faithful display-only postprocessing with legend, units, region/plane/time and source field identity | Known field plots plus field download; interactive field viewer is optional, not a prerequisite for useful reports |
| Engineering JSON | Typed engineering summary, cited original record and complete meaningful detail | Safe readable original behind disclosure, never endless anonymous property tables as the primary view |
| Retrieved HTML/code/logs | Sanitized inert document or escaped text, with origin and scope | Original download; never execute included supplier HTML or generated CAD source to show a report |

Resolve local library/viewer capabilities before choosing dependencies. Use a proven PDF renderer if native embedding cannot meet file-origin requirements. Bundle necessary scripts, workers, fonts and licenses. A web-server-only PDF demo is not completion of a standalone ZIP feature.

## Engineering Content Rules

### Domain Presentations

Implement reusable evidence presenters, composed for the ten families; do not create 30 separately authored pages.

| Presenter | First useful information | Supporting visual/detail |
| --- | --- | --- |
| Reference research | Question, source, observation, relevance and limitations | Original PDF/image with exact page/region; extracted interpretation separate from source fact |
| CAD/geometry | Final design and role, key interfaces/dimensions, recorded changes | Part/assembly view, datum/hole pattern, supplied inspection tied to geometry version |
| Numerical analysis | Question, model/load case, result and producer scope | Fields/curves, setup, materials/BCs, mesh evidence and convergence/verification records when supplied |
| Printing | New design, orientation/preparation, slicing parameters, handoff state | Actual support geometry only when retained; no duplicate part image or current flattened toolpath page |
| Robotics | Measured deviation/event and diagnostic conclusion | Trajectory and synchronized timelines with frame/time/alignment/gap semantics |
| Harness/PCB | Design diagram and delivery state | Pin/net/BOM schedules, routing/board views, upstream electrical/native checks and warnings |
| Sizing studies | Recorded selected candidate and conditions | Candidate curves/table, limits, refinement/sensitivity evidence; not an inferred physical qualification |
| Failed process | Last useful result, exact stopping action, reason and impact | Supplied concept/partial artifacts identified as such; diagnostic details and recorded repair guidance |

Within-run alternatives, candidates and mesh levels are part of one engineering result. Cross-run comparison remains out of scope.

### Visual Evidence Rules

- Every promoted image answers an engineering question. Include subject, role and the operation/decision it supports; omit decorative/duplicate previews.
- Analysis graphics require meaningful bounds, legend, units, coordinate/region identity, case/time selection and camera/plane. Comparisons need shared scales or explicit scale differences. Retain source and render recipe.
- Display postprocessing may read retained geometry/fields/CSV. It must not solve again, change geometry, regenerate supports, call a validator or run model-authored source code to fill a report.
- Attach post-run visualizations as representations derived from exact artifact versions, not as newly discovered historical outputs. Attribute the renderer separately from the historical producer.
- A useful mesh view or section can be derived when retained data supports it. A genuine residual history, check result, support mesh or missing physical measurement cannot be fabricated from a static image.
- Report-only and full-data modes distinguish excluded source bytes from absent source bytes. An intentionally omitted large artifact is not a capture failure.

### Measurements and Validation

Distinguish file integrity/availability, digital geometry checks, numerical checks, requirements validation, human approval, release state and physical verification. They answer different questions.

Show a validation claim next to its subject with who/tool, what was checked, criterion, measured result and units, outcome, scope and supporting record. The producer owns the criterion and conclusion. The UI may format units/precision, but must preserve originals and conversion provenance. Do not infer a pass, selected candidate, convergence or approval from numbers alone.

Missing evidence appears where relevant and is logged in the process improvement list. Do not show a top-level list of newly invented unresolved concerns. Conversely, preserve actual producer-reported holds/warnings and limitations even when execution completed.

## Backend and Projection Plan

Extend the existing capture/evidence/export model and producer envelope, rather than creating a second data store or identity system. Keep report generation read-only with respect to the historical run.

The semantic presentation layer needs these linked concepts:

| Concept | Minimum information |
| --- | --- |
| Activity account | Purpose/outcome, exact occurrence, inputs, ordered supported actions, outputs, known tool/timing references |
| Source citation | Evidence ID/digest, document page/section/JSON pointer/event locator, origin and linkable target |
| Artifact and representation | Original version, purpose/role, origin class, representation-of/derived-from links, source digests, display recipe |
| Engineering observation/decision | Statement, subject, value/unit/conditions when relevant, source, actor and recorded rationale; approval separate |
| Check result | Producer, checked version, method/criterion, result/unit/outcome, scope and evidence references |
| Relationship | Explicit consumes/produces/transfers/approves/derives; separate from recorded chronological order and report grouping |
| Availability | Included, omitted by export mode, redacted, external reference, capture unavailable, unsupported display, or not applicable |

Each important displayed fact carries a source citation. If source mapping cannot be established, do not silently upgrade a heuristic into recorded truth. Human-friendly labels may use domain adapters; tool identity and artifact lineage need stronger evidence than a matching filename/task slug.

Use typed adapters for known producer schemas, then safe document renderers for unfamiliar formats. Preserve access to full arrays/records; replace the generic 12-table cutoff with semantic sections and paging. Unknown formats stay readable without pretending to understand them.

Keep large binaries out of initial HTML except deliberately bounded offline display assets. Reuse original packaged identities and document link resolution; handle ZIP members safely. Original hashes stay unchanged when a readable document view remaps links or converts units. Derived assets get their own manifest entries, hashes, renderer version and parameters.

## Implementation Sequence

1. **Reconcile Spec Kit:** read this plan, audit and backlog; amend `spec.md`, `plan.md`, `data-model.md`, contracts and `tasks.md`, then run the Spec Kit consistency analysis. Record the reopened presentation acceptance explicitly. Keep T068 and producer work separate unless explicitly assigned.
2. **Evidence model and inventory:** map selected records for all 30 cases, classify available/recoverable/absent information, fix provenance/counting and data omission before more visual polish. Establish contract tests for exact sources, versions, arrays, origins and unknowns.
3. **Coherent vertical slice:** implement request/results/process/activity/viewer together for real Pi case01, including its research PDF and both CFD variants. Prove the approach also with a numerical sizing case and a failed sheet-metal case before expanding family adapters. Use the existing report exporter; no one-off hand-written report HTML.
4. **All-family coverage:** complete presenters for all ten families and all 30 selected runs. Render useful retained evidence for Pi02/03 and heat spreaders where feasible; provide a truthful recorded fallback and producer request for unsupported render paths. Do not reuse another case's imagery.
5. **Scale and offline quality:** exercise the real 25-activity heater case, 17-activity PCB cases, and an explicitly labeled 30+ activity stress fixture. Validate media and transitions at real review viewports; complete packaging checks for every case.
6. **Deliver reviewable packages:** regenerate 30 ZIPs plus catalog; supply direct HTML and ZIP links, screenshot evidence and a concise list of remaining producer gaps. Report technical checks separately from user acceptance; never mark design accepted merely because tests pass.

The UI work must not depend on waiting for missing historical data. Recover what can be proved, expose bounded gaps locally, and continue. New producer capture is a separately assignable workstream.

## Acceptance Scenarios

- From Pi case01, identify the supplied sketch, final enclosure variants, analysis scope and source of an important dimension without opening JSON or reading internal IDs.
- Open the reference-research activity and understand input context, retrieved references, recorded observations and resulting basis. Open the mechanical PDF inline at page 1, return to the same action and see its provenance.
- Inspect both A/B field views, read their scales and plane, reach original fields and see derivation status. No missing variant due to table caps; no new validation or winner claim.
- View CAD-export integrity evidence without mistaking byte presence/digest matches for dimensional or engineering validation.
- Open a dimension or assumption and reach its exact source statement. Inspect a recorded approval and identify Wright AutoTest versus a named human, including the exact approved subject.
- Expand only the CFD responsibility row; useful visual evidence becomes visible in that row. Other rows remain compact; connectors do not pass through text or thumbnails. Selecting the final result brings its activity into view.
- Input-to-process arrows remain visible and correctly attached when the input row is compact or expanded, on desktop/mobile and after zoom/resize. Test both confirmed consumption and run-level entry without falsely labeling the latter as consumed by the first activity.
- Use a 30+ activity graph without shrinking text into illegibility or replacing lanes. Keyboard, zoom, horizontal pan and row disclosure preserve focus/selection. Repeated paths expose the correct output for each pass.
- In heat-spreader/heater reports, understand selected candidate, units, conditions and recorded numerical limitations from result views. In harness/PCB reports, see diagrams/check scope and actual release qualifications.
- In failed sheet-metal/bracket reports, identify the stopping point and retained work without a fake final part, manufactured outcome, or unexecuted FEA.
- Open extracted full-data ZIPs under `file://` with networking blocked and Wright stopped. Verify PDFs, images, readable documents, CSV views, advertised 3D viewers, internal links, back navigation and original downloads. Explicitly qualify browser support; do not claim untested native PDF/3MF behavior.
- At 1297x791, 909x791, 796x791 and a mobile viewport, inspect screenshots for useful framing, readable plots, no text/edge overlap and no page-wide overflow outside the graph. Verify WebGL pixels and interaction, not just canvas existence. Test missing/corrupt/oversized/unsupported evidence and disabled WebGL.
- All 30 selected reports retain correct run/attempt identities, original bytes/hashes and failure status. Presentation assets do not inflate historical output counts. Full-data archives retain available underlying evidence and safe relative links.

## Out of Scope

New engineering simulations/checks, physical tool/printer dispatch, fabrication or approval decisions, workflow-editor redesign, cross-run comparisons, annotations, retrospective invented prompts/tool calls, and feature 082 integration. Do not activate feature 081 deferred validation or reinterpret its G0 gate.
