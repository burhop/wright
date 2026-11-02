# Feature Specification: Workflow Trace and Product Review

**Feature Branch**: `codex/083-workflow-trace-review`

**Created**: 2026-09-16

**Status**: Implemented; real-corpus acceptance recorded

**Input**: The user wants a simple, results-first Trace page for reviewing a completed engineering workflow, with progressively disclosed process, decision, input, requirement, validation, and artifact evidence. Include failed runs, repeated paths, imagery, Wright viewers, and portable reports. Engineering checks remain external to Trace; feature 083 presents their recorded evidence. Start with the 24 existing processes with outputs.

## User Scenarios & Testing _(mandatory)_

### User Story 1 - See the results (Priority: P1)

An engineer opens Trace from a saved workflow run and immediately sees the principal deliverables, meaningful previews, and recorded execution outcome. They can open a result without first interpreting a graph or a diagnostic dashboard.

**Why this priority**: Understanding and accessing the result is the primary job.

**Independent Test**: Open a completed CAD-and-document run from the workspace, inspect its results, and open its files without expanding process details.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** Trace opens, **Then** the initial view shows its name, concise purpose, recorded outcome, and primary deliverables; prompts, logs, technical metadata, and evidence lists are collapsed.
2. **Given** an image or CAD result with a recorded preview, **When** the result is displayed, **Then** the actual image or model preview is shown and the original artifact is accessible.
3. **Given** a STEP result, **When** the reviewer opens it in Wright, **Then** the existing compatible Wright viewer is used, or the interface explicitly offers a linked display representation and the original STEP when that installation cannot view the original directly.
4. **Given** a successful run with recorded assumptions, **When** the reviewer expands assumptions, **Then** the assumptions and their sources appear without an invented unresolved-concerns summary.

### User Story 2 - Explain an output or decision (Priority: P1)

A reviewer investigates a deliverable, requirement, assumption, or decision and follows the recorded links to the exact supporting inputs and evidence.

**Why this priority**: The report must support engineering review without making its own correctness judgments.

**Independent Test**: Follow a design decision to its source document and requirement revision, then open the corresponding validation report and the exact artifact that report describes.

**Acceptance Scenarios**:

1. **Given** recorded requirement and user-approval evidence, **When** the reviewer investigates a result, **Then** they can navigate to the requirement revision, original input, approval, and evidence supporting the result.
2. **Given** validation produced by another component, **When** the reviewer opens validation details, **Then** its recorded conclusion, producer, subject revision, and supporting files are available without Trace performing or reinterpreting that validation.
3. **Given** a recorded decision, **When** its justification is opened, **Then** the recorded rationale and cited evidence appear, rather than a newly generated explanation presented as historical fact.
4. **Given** a step's recorded prompt and context, **When** prompt details are expanded, **Then** the executed prompt, available configuration, and referenced documents can be inspected. Content never captured is identified locally as unavailable.

### User Story 3 - Follow the process and its iterations (Priority: P1)

A reviewer opens the process graph, recognizes the workflow that ran, and selects blocks, connections, or semantic groups to inspect their role and actual execution.

**Why this priority**: The visual process connects results to the work that produced them.

**Independent Test**: Inspect a run that revisited a path, select its connection, and open the distinct outputs from each traversal.

**Acceptance Scenarios**:

1. **Given** a saved run, **When** its graph opens, **Then** the blocks and connections describe the definition used for that run, including branches not taken; later editor changes do not rewrite the report.
2. **Given** a selected block or connection, **When** its details open, **Then** the reviewer sees its purpose and the recorded inputs, transfers, outputs, and executions associated with it.
3. **Given** three traversals of one path, **When** it is selected, **Then** three ordered occurrences and their associated attempts and outputs are available while the overview retains one recognizable path.
4. **Given** an earlier output was superseded, **When** that attempt is selected, **Then** its retained version opens and is distinguishable from the final deliverable.

### User Story 4 - Review a failed or blocked run (Priority: P1)

An engineer reviews all retained work through the failure and opens the recorded error or blocker to debug it.

**Why this priority**: Useful results and evidence must survive unsuccessful execution.

**Independent Test**: Open a run that failed after producing files; inspect those files and its failure evidence without rerunning anything.

**Acceptance Scenarios**:

1. **Given** a failed or blocked run, **When** Trace opens, **Then** available partial results appear with their actual status and the reported error or blocker is visible.
2. **Given** a cancelled or interrupted run, **When** its record is opened, **Then** the last durable state and available evidence are shown without asserting success or inventing an end time.
3. **Given** a past failure was resolved by a later attempt in the same run, **When** the final report opens, **Then** it shows the final recorded outcome and preserves the failure in that attempt's history.

### User Story 5 - Send a portable review package (Priority: P2)

An engineer exports the report alone or the report with related data. A recipient extracts the ZIP and opens the report without a Wright installation or account.

**Why this priority**: Reviews need to travel with the evidence supporting them.

**Independent Test**: Move the extracted package to another directory, disable network access, open its report, and follow links into included inputs, outputs, iterations, and validation reports.

**Acceptance Scenarios**:

1. **Given** a full-data export, **When** it is extracted, **Then** the report links to available input data, artifacts, validation documents, and execution evidence through portable package-relative references.
2. **Given** a report-only export, **When** the recipient opens it, **Then** the report and packaged previews work, and omitted original files are explicitly identified rather than represented by broken local links.
3. **Given** a model with a supported portable viewer, **When** opened offline, **Then** it is interactive using bundled resources. Otherwise its recorded preview, original file, and concise viewer-unavailable placeholder are accessible.
4. **Given** an unavailable external or session-only resource, **When** exported, **Then** its reference and availability are retained without claiming its bytes are included.

### Edge Cases

- An old run lacks the executed definition, expanded prompt, requirement links, or some iteration events. Show only attributable facts; do not substitute the current workflow or manufacture history.
- Several attempts overwrite the same filename. Earlier retained bytes must remain associated with earlier attempts; unavailable historical bytes must not resolve to the latest file.
- A validation report refers to a different artifact revision, or two external records disagree. Preserve subjects and source records; Trace does not choose a new engineering verdict.
- No final artifact exists, or a run produces hundreds of files, large simulation fields, or a directory-based project. Preserve the result hierarchy without opening every file or overwhelming the initial view.
- Branches, nested groups, parallel tasks, retries, and design revisions require distinct occurrence identities. Display order alone is not proof of a data transfer.
- CAD previews and analysis images can describe different geometry, variants, units, or coordinate systems. Display their recorded relationships and labels without measuring or validating them.
- Missing files, deleted resources, unsupported formats, interrupted capture, and unavailable previews must leave the report navigable.
- Offline exports must handle repeated filenames, cross-platform filenames, moved directories, large files, and links within included documents.

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: Trace MUST be reachable from a saved run through the normal workspace Workflow/Workflows experience and support a stable link to that run.
- **FR-002**: The initial view MUST prioritize final deliverables, available previews, concise purpose, and recorded outcome. Detailed process, prompts, assumptions, logs, and validation evidence MUST use progressive disclosure.
- **FR-003**: Actual errors or blockers MUST be visible for affected runs. Trace MUST NOT introduce an unresolved-concerns dashboard, engineering score, or independent acceptance verdict.
- **FR-004**: The graph MUST represent the definition executed and preserve its recognizable blocks, connections, and semantic groups. Each meaningful graph element MUST be selectable; exact editor positioning is not required.
- **FR-005**: Selecting a step MUST distinguish its configured purpose from its recorded behavior and provide access to inputs, outputs, prompts, documents, tool activity, decisions, and validation evidence where captured.
- **FR-006**: Selecting a connection MUST expose its meaning and recorded transfers. Repeated traversals MUST be listed separately with links to corresponding attempts and artifacts.
- **FR-007**: Attempts and iterations MUST retain distinct identities and available artifact versions, including superseded outputs, without duplicating the entire graph by default.
- **FR-008**: Recorded input, requirement, user-approval, decision, assumption, artifact, and validation relationships MUST be navigable in both directions where those relationships exist.
- **FR-009**: Trace MUST display validation supplied by other components with its producer and exact subject. It MUST NOT perform engineering checks, extract new requirements, approve requirements, or infer correctness from workflow completion or file presence.
- **FR-010**: A documented interface MUST describe the identities, provenance, subjects, evidence references, and optional engineering context required from validation and workflow producers.
- **FR-011**: Prompts MUST be concise or collapsed initially, with recorded executed text and linked context accessible on demand under existing access and credential-handling rules.
- **FR-012**: Result presentation MUST support documents, images, structured data, CAD/mesh models, engineering analyses, and multi-file deliverables through existing viewers, linked representations, or a clear original-file fallback.
- **FR-013**: Geometry, mesh, simulation, electronics, manufacturing, and numerical evidence MUST remain understandable through recorded labels, units, settings, source documents, and linked reports, without adding domain validation.
- **FR-014**: Trace MUST include failed, blocked, cancelled, and interrupted runs and their retained partial results, errors, and last known execution state.
- **FR-015**: Capture MUST persist incrementally during execution so inspection and other consumers do not depend on successful terminal report generation or an attached browser.
- **FR-016**: New runs MUST retain the executed definition and available presentation layout, bound input revisions, recorded prompts, occurrence relationships, and artifact versions needed for later inspection. Capture gaps MUST remain explicit.
- **FR-017**: Historical runs MUST be readable without rerunning them or changing their original evidence. Missing historical content MUST be disclosed only where relevant.
- **FR-018**: Users MUST be able to export either the report with its display assets or a ZIP containing the report and all available related data, organized by purpose and run occurrence.
- **FR-019**: The exported report MUST open locally after extraction without Wright or a network connection. Included report links MUST resolve after moving the extracted directory.
- **FR-020**: Exports MUST identify included, omitted, unavailable, and externally referenced resources; preserve artifact identities; and distinguish display representations from originals. Portable interactive viewers MAY fall back to previews and file access when unavailable.
- **FR-021**: Report access, artifact access, and export MUST preserve existing workspace authorization and file confinement. Generated content MUST be displayed using the existing safe rendering conventions.
- **FR-022**: Report browsing MUST NOT mutate workflows, execute tools, rerun steps, change approvals, or invoke engineering validators.
- **FR-023**: The initial acceptance corpus MUST cover the user's 24 existing processes with outputs, with a recorded case/run manifest. Synthetic examples MAY cover exceptional states but MUST NOT be counted as real corpus coverage.
- **FR-024**: Record identities and report links MUST be suitable for future anchored reviewer comments. Comment editing, review assignments, automated feedback, comparison between runs, and live monitoring are deferred.
- **FR-025**: The standalone swimlanes MUST describe completed or stopped engineering work from supplied inputs to produced outputs. Supplied text, input previews and linked documents MUST be accessible outside their consuming blocks. A consumer relationship MUST come from retained evidence.
- **FR-026**: The activity detail MUST lead with what the activity did, recorded software/version, brief input references, and available execution history. It MUST NOT repeat the full user request as its primary content. Recorded design assumptions and decisions MUST retain source navigation.
- **FR-027**: Supplied models, generated models and repaired versions MUST have unambiguous labels and provenance. Produced-file access and activity/handoff navigation MUST be integrated with the swimlanes, including keyboard and narrow-screen use, without a duplicate standalone index.
- **FR-028**: Activity passes, internal tool/CAD iterations and whole-run AI requests MUST remain distinct. Missing software versions, per-call traces or revision counts MUST NOT be inferred from current installations, filename conventions or aggregate usage.
- **FR-029**: Result labels MUST distinguish a newly designed replacement part from digital mesh cleanup and from a physically manufactured or repaired part. Slicer whole-model thumbnails, support geometry and toolpath/layer views MUST be labeled according to the actual retained representation; an absent support-geometry preview MUST NOT be invented.
- **FR-030**: Recorded printing parameters and support-generation results MUST be grouped under a clear 3D printing context with links to their source records. Alternate input image formats MUST be identifiable by format without conflating their file identities.
- **FR-031**: Each activity block MUST identify the recorded tool at diagram level, with explicit tool/version information and source evidence in its detail view. Unrecorded identities or versions MUST be labeled unavailable.
- **FR-032**: The process diagram MUST preserve every responsibility swimlane and supplied-input lane, with compact activity blocks by default. Each responsibility cell MUST provide an intuitive, keyboard-operable disclosure control that expands or collapses only its own row's secondary information and produced files. There MUST NOT be a global Compact/Detailed switch. Other rows, shared column alignment and independent expansion states MUST remain unchanged. Tool identities, pass counts, block/connection selection and full detail access MUST remain available while compact. At least 30 activities MUST remain usable through small blocks, scrolling, pinned responsibility labels and explicit zoom/fit controls, with connectors following independently expanded rows.
  Supplied inputs MUST use comparably compact, individually selectable blocks, not an oversized summary strip. Expanding the input responsibility row MUST group each input's text, preview and source links within its own block. Large input sets MUST remain bounded with access to all remaining inputs. The supplied set's connection to its recorded consumer MUST remain visible in both states.
- **FR-033**: Verified alternate representations of one supplied image MUST appear as a single reviewer-facing input, with alternate formats available through progressive disclosure. Both original file identities and bytes MUST remain preserved in full-data exports.
- **FR-034**: Review-time reconstructions and documentary tool attribution MUST be packaged with their source identities and clearly distinguished from original execution evidence. Reassembled context MUST link to its verified constituent inputs, and documentary attribution MUST match the exact case and attempt; neither establishes an uncaptured software version or raw tool-call trace.
  Input-overview counts MUST exclude review-time reconstructions and alternate representations. Reassembled context MUST have a separate disclosure. All supplied inputs in a small set MUST be directly visible; larger sets MUST use a counted overflow disclosure adjacent to the list it expands, not a detached aggregate-input action.
- **FR-035**: New process executions MUST durably capture UTC start and terminal timestamps and monotonic elapsed milliseconds for every activity attempt, including authorization, retries, loops, failures and cancellations. Each attempt MUST retain its own timing identity. Start events MUST persist before tool dispatch and terminal timing with the outcome. Interrupted attempts MUST retain the last durable timing evidence and an explicit incomplete state; no fabricated completion time or zero-duration substitute is allowed. Reports and exports MUST display the selected attempt's timing, not whole-run time. Historical gaps MUST remain explicit. This new producer requirement requires runtime implementation and restart/failure tests before acceptance.
- **FR-036**: Overview imagery MUST add distinct engineering information, such as design geometry, actual support geometry, orientation changes, or layer/toolpath evidence. A recolored whole-model thumbnail MUST NOT be promoted as an additional result or as evidence of supports or slicing. Manufacturing presentation MUST prioritize recorded support outcomes, model preparation operations and slicing parameters with source links. Missing support imagery MUST remain explicit; retained redundant images remain accessible among the producing activity's files, not duplicated in the overview.
  The current flattened toolpath projection MUST NOT expose a review page or navigation entry, including activity file lists. Its original evidence MUST remain preserved in full-data exports. Toolpath review is deferred until useful toolpath data and a suitable presentation are available.
- **FR-037**: A campaign inventory MUST pin one exact retained run, attempt, dataset revision, and template revision for each of the 30 campaign examples. Completed cases MUST retain the reviewed successful selection; incomplete cases MUST pin the latest retained attempt and preserve its partial artifacts and recorded stopping reason. Inventory construction MUST NOT rerun a workflow or reinterpret a failure as success.
- **FR-038**: One batch command MUST export all cases or an explicit subset in report-only or full-data mode through the same standalone renderer used by the reviewed single-run report. Output MUST contain one ZIP per selected example, an extracted offline report for each ZIP, and a package-relative HTML catalog grouped by workflow family.
- **FR-039**: Campaign report presentation MUST be reusable across geometry/CAD, thermal/CFD, robotics, wiring harness, PCB, Modelica, sheet-metal, and manufacturing workflows. The overview MUST promote only meaningful recorded images and principal engineering deliverables; all additional retained files remain accessible through the producing activity.
- **FR-040**: Every campaign package MUST verify its archive integrity, manifest membership, extracted bytes, and resource SHA-256 values. Every extracted report MUST render under `file://` with networking blocked, expose at least one recorded activity, and open activity detail without browser errors.
- **FR-041**: Historical software identity MUST use exact producer evidence or the retained workflow/task identity. Compact blocks MUST NOT show an unexplained `Not recorded` tool; unavailable historical versions MUST remain explicitly unavailable rather than being guessed.
- **FR-042**: Standalone engineering reviews MUST present retained visual inputs directly when they improve understanding, rather than reducing them to text links. For CAD-oriented completed runs, reviewer-facing final STL geometry MUST be available in a self-contained offline 3D viewer when a bounded retained STL representation exists. The renderer MUST select principal product geometry deliberately and MUST NOT promote fluid domains, board surrogates, analysis meshes, redundant color variants, or unrelated retained models as the final design. STEP and other unsupported originals MUST remain clearly labeled downloads.
- **FR-043**: Generic engineering records MUST be projected into test- and decision-oriented summaries. Raw byte counts, transport identities, and one-row observation tables MUST NOT dominate activity detail. Campaign swimlanes MUST organize activities into useful engineering responsibilities, expose recorded visual evidence when a row is expanded, and show recorded execution-order connectors when authored artifact handoffs were not retained. Such connectors MUST be labeled as execution order and MUST NOT imply unrecorded artifact lineage.
- **FR-044**: Data-derived engineering visualizations MUST be promoted when they materially improve review of retained analysis results. Each visualization MUST identify its source artifacts, derivation status, field or metric, comparison basis, and validation limitations; it MUST NOT be presented as an original solver screenshot or a newly executed analysis. Relevant visualizations MUST appear both with the principal results and on the producing or collecting activity when its responsibility row is expanded. Full-data exports MUST retain the visualization, its source result records, and the underlying available field archive.

### Key Entities _(include if feature involves data)_

- **Run record**: Execution identity, definition revision, lifecycle, source evidence, and retained data used by the report.
- **Execution occurrence**: A particular step attempt or path traversal, including its parent scope and associated inputs and outputs.
- **Artifact version**: A specific produced or consumed file/resource and its representations, provenance, role, and availability.
- **Evidence link**: A recorded relationship connecting an input, requirement, approval, assumption, decision, artifact, or externally supplied validation result.
- **Report revision**: A reproducible presentation of a particular recorded run and evidence selection, including export membership.
- **Corpus selection**: The exact 30 campaign cases and pinned run records selected for report generation: 24 reviewed completed attempts and six retained incomplete attempts.

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: For every selected completed corpus run, primary outputs are visible without expanding a technical panel, and opening a principal deliverable requires at most one selection after the report loads.
- **SC-002**: In documented review walkthroughs, the executed prompt, a linked input, a decision justification, and associated validation evidence can each be reached within three selections from the relevant result or graph element when recorded.
- **SC-003**: Every recorded attempt and traversal in the selected iteration scenarios is inspectable, with zero links that substitute a later artifact version for an earlier one.
- **SC-004**: Failed, blocked, cancelled, and interrupted examples preserve all retained partial output links and accurately present the recorded stopping state; no incomplete run is labeled successful by Trace.
- **SC-005**: All packaged report links resolve after extraction and relocation with networking disabled. Resources not included have explicit availability states, and any advertised interactive viewer passes offline viewing checks.
- **SC-006**: Existing records from all 24 selected processes receive a report acceptance result. Coverage records distinguish real data, missing local data, and synthetic scenarios; unavailable cases do not count as passed.
- **SC-007**: An interruption/restart scenario retains all acknowledged occurrence records and captured artifact versions up to the last durable write, independently of report rendering.
- **SC-008**: For a representative local report of up to 100 graph elements and 1,000 evidence references, initial results appear within two seconds after cached assets load, with large file bodies loaded only on demand.
- **SC-009**: The campaign inventory contains exactly 30 unique cases across all 10 workflow families, reports 24 completed and six failed runs, and identifies zero missing produced artifacts for the transferred bundle.
- **SC-010**: A full-data batch produces 30 independently usable ZIPs and 30 extracted reports; automated integrity verification reports 30 passed and zero failures.
- **SC-011**: With HTTP and HTTPS blocked, browser automation opens all 30 extracted reports, finds activity blocks, opens activity detail, and records zero remote requests, page errors, or ambiguous tool labels. Desktop and mobile captures exist for every workflow family.
- **SC-012**: For each campaign run with selected principal STL geometry, the extracted report renders a nonblank interactive canvas without a network request. The Raspberry Pi enclosure review visibly presents its supplied sketch and both final enclosure concepts, excludes CFD-domain meshes from the result gallery, shows all recorded activity-order connections, and presents CAD export verification without raw byte-count tables.
- **SC-013**: The Raspberry Pi enclosure review presents the retained Variant A/B air-speed and temperature comparisons at overview level and as thumbnails on the CFD results activity. Both images render at their retained 2200 x 990 resolution offline, link to the exact field archive and comparison record, and disclose that convergence and engineering validation were not claimed.

## Assumptions

- Completed-run inspection is the primary experience; failed or stopped run records remain reviewable. A live monitoring interface is outside this feature.
- Authorized workflow and validation producers may supply evidence and domain-check results through the documented envelope. This feature does not activate deferred feature-081 content validation.
- The campaign contains 24 completed-output attempts and six incomplete attempts. Reports cover all 30 without rerunning them; incomplete reports preserve the latest retained attempt, partial outputs, and exact stopping reason.
- Recorded upstream approvals are displayed; Trace does not create a new approval workflow.
- The exported report opens by double-clicking its entry HTML after extracting the ZIP. Complex viewer availability can vary; the report and original-file links must still work.
- Lightweight comments remain a follow-on once stable evidence anchors exist. No annotation UI is required for initial delivery.
