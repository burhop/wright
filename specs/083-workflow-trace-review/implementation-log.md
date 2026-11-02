# Workflow Trace Implementation Log

## Integration inventory

Recorded 2026-09-16 from `dev` commit `6c0602a4` in the isolated
`codex/083-workflow-trace-review` worktree.

- The feature-083 evidence contract is additive and producer-neutral. Validation
  work in other features is independent and is not a completion dependency.
- Shared integration files are
  `apps/api/src/api/routers/workspace.py`, API transport schemas,
  `packages/workspace_service/src/workspace_service/service.py`, and the web
  workspace service. New feature-specific modules should carry most behavior.
- Engineering validation remains external. Trace only retains and presents a
  producer's recorded conclusion, exact subject identity, and evidence links.
  Deferred feature-081 content validation remains disabled.

## Existing run and UI ownership

- Source workflow run JSON is recorded by
  `packages/workspace_service/src/workspace_service/workflow_run_record.py` and
  exposed through the workspace workflow-source run history API.
- Rivet run state and append-only events are stored by
  `packages/data_vault/src/data_vault/workflow_runs.py`; canonical execution
  records are defined in `packages/core/src/core/canonical_workflow_runs.py` and
  stored by `packages/data_vault/src/data_vault/workflow_execution_repository.py`.
- `packages/workspace_service/src/workspace_service/workflow_inspection.py`
  creates the current bounded, redacted inspection projection. It already keeps
  run inputs, inventoried graph nodes, lifecycle events, final outputs,
  artifacts, and failure diagnostics, but currently merges repeated node visits.
- `packages/workspace_service/src/workspace_service/rivet_evidence.py` builds a
  bounded evidence manifest with bindings, child calls, approvals, artifacts,
  and a timeline. The existing export is JSON, not an offline review package.
- Authorized run inspection and artifact routes live in
  `apps/api/src/api/routers/workspace.py`. The browser client methods are in
  `apps/web/src/services/workspace-service.ts`.
- The existing run UI is `apps/web/src/components/workflows/RivetRunInspector.tsx`
  and is embedded by both `DirectRivetSurface.tsx` and `RivetWorkflowRun.tsx`.
  Saved source-run history is owned by
  `apps/web/src/prototypes/workflow-recovery/WorkflowRunHistory.tsx`.
- The workspace viewer registry has an interactive Three.js STL provider only.
  STEP can be opened as text through the generic provider in tests, but there is
  no direct STEP geometry loader. No 3MF loader is registered.

## Ignore-policy check

The existing `.gitignore`, `.dockerignore`, and `.prettierignore` already cover
Python caches, Node dependencies, build/test output, local runtime state, and
generated archives. Feature evidence committed below is small source evidence;
generated report ZIPs and extracted packages remain under ignored local runtime
or test-output directories. No repository-wide ignore policy change is needed.

## Implementation

- Added strict trace identities, immutable SQLite WAL storage, idempotent event
  capture, external producer evidence ingestion, bounded projection, and stable
  future-comment anchors.
- Rivet records the executed graph snapshot and keeps repeated node visits as
  distinct attempts. Canonical workspace runs retain a compact graph, prompts,
  connection topology, and input identities before execution.
- Saved canonical runs and Rivet runs share a results-first Trace page with
  Process, Evidence, and Run history disclosure. Canonical history is reached
  from the ordinary workspace Workflows control.
- Report-only and full-data exports use deterministic relative paths, explicit
  availability states, integrity checks, and self-contained HTML. No offline
  interactive geometry viewer is advertised.
- The final standalone HTML is a styled results-first review. Full-data packages
  render retained raster outputs inline; report-only packages bundle those same
  presentation images under `assets/previews/` while omitting nonvisual originals.
- Trace stores and displays exact producer statements and subjects without
  running checks or creating a verdict.

## Verification

Recorded 2026-09-16:

- The final focused backend command passed 31 Trace domain, repository,
  workspace-service, campaign-import, and API tests.
- `bun run --cwd apps/web test -- ...`: 21 focused component tests passed,
  including results-first imagery and explicit repeated connection traversals.
- `bun run --cwd apps/web lint`: no errors; nine pre-existing hook warnings in
  unrelated files.
- `bun run --cwd apps/web build`: TypeScript and the production Vite build
  passed; existing large-chunk/config-loader warnings remain.
- Playwright: the unmocked live campaign check passed against the production
  build. It verified all 24 indexed run identities through the real API, normal
  Workflows entry, results-first Trace, retained imagery, graph selection, the
  real STL viewer with nonblank canvas pixels, both live exports, relocation,
  and offline `file://` use with HTTP/HTTPS blocked. Existing fixture checks cover
  desktop/mobile/200% text and editor create/save regression.
- Post-import campaign adapter/API/export slice: 38 focused Python tests passed;
  Ruff, `git diff --check`, and the corpus-manifest JSON check passed.
- The transferred bundle's complete `SHA256SUMS.txt` verification returned exit
  0. The repeatable corpus validator returned 24 selected / 24 Trace-accepted,
  with 786 artifact digests and sizes checked and zero content validations.
- The production build is running at `http://127.0.0.1:8094`; `/api/health`
  reports connected and `/` serves the built HTML. Startup uses documented local
  `WRIGHT_AUTH_MODE=compat` on loopback.

The prior served-browser record used mocked Trace API responses and was not
sufficient evidence of the transferred campaign. It has been superseded by
`tests/ui-integration/workflow-trace-live-campaign.spec.ts`, which uses no API
mocks and runs against the managed review workspace at
`/home/burhop/wright/workflow-trace-24-run-review-final`. The preparer script
stores normal workflow sources and run history while preserving every original
campaign `run.json` byte and recording source SHA-256 provenance.

The portable feature-081 campaign bundle was received under ignored local runtime
storage at `.local-run/feature-083-imports/campaign-081`. Independent verification
confirmed 10,530 files, 3,170,643,606 bytes, manifest digest
`db179dfa39f9262f37a6c9456ec337a7299e8a87030e6ff95e5f297db99f41bd`,
SQLite `integrity_check=ok`, and DELETE journal mode after online backup.

The campaign adapter projected every selected immutable `run.json`, preserving
observed step occurrences and per-step artifacts without inventing connections,
prompts, or validation. `scripts/validate-workflow-trace-corpus.py` selected the
latest completed attempt for each of 24 cases, rehashed 786 artifacts totaling
148,252,227 bytes, projected 220 step occurrences, built each report-only ZIP,
and returned 24/24 Trace acceptance with content validation unchanged at 0.

## Human-readable standalone review iteration

The user rejected the earlier standalone presentation as a technical-data
catalog. The new review direction is implemented first for the retained
`printed-replacement-part-01 / attempt-003` run, pending user UI acceptance
before extending engineering-specific projections across the remaining corpus.
This supersedes the earlier presentation-completion claim, not the retained
campaign's execution evidence.

- Results show the actual retained model/slicer images and downloadable models.
- Responsive swimlanes show four activities and three clickable handoffs.
  The original workflow layout was not retained. Handoffs are explicitly
  supported by the repair source reference, slicer input fingerprint, and
  transfer receipt's package fingerprint, not invented execution events.
- Detail panels show design dimensions, assumptions, before/after mesh
  measurements, repair tolerances, producer-reported checks, manufacturing
  settings, and readable source documents. Raw records are in the technical
  archive, not the primary presentation.
- Authorization identifies Engineering campaign automation as an automated
  integration-test actor, with time, scope, and simulated destination. There
  was no human sign-off or physical printer dispatch. The original source
  prompts and input bytes were not retained in the transferred output set;
  the report does not substitute current template content.
- Report-only export reads bounded engineering JSON for presentation, verifies
  its digest, and omits original nonvisual files. Full export includes all
  15 retained artifacts. Interactive offline 3D remains an explicit placeholder
  with recorded previews and original model downloads.

Verification on 2026-09-16:

- 17 focused exporter, canonical adapter, campaign workspace, and API tests passed.
- Two Chromium checks passed: relocated offline export regression and the new
  unmocked standalone engineering report check. The latter calls the real API,
  exports both modes, relocates them, blocks HTTP/HTTPS, checks every included
  artifact fingerprint, exercises steps/handoffs/source records/authorization,
  and checks 1440px desktop and 390px mobile layouts.
- Screenshots were visually inspected under `evidence/live-campaign/`:
  `engineering-review-desktop.png`, `engineering-review-mobile.png`,
  `engineering-review-mesh-details.png`, `engineering-review-authorization.png`.
- Ruff, JavaScript syntax checking, and `git diff --check` passed.
- No campaign rerun, new engineering validation, branch-082 integration,
  push, or merge was performed in this UI iteration.

### Browser review refinements

- Activity details now begin with the expandable prompt/instructions section.
- The standalone report now follows Inputs, Outputs, then Process & handoffs.
  The outcome introduction and completion badge belong to Outputs.
- Short recorded prompts appear inline. Long prompts have a bounded excerpt
  and full-text disclosure. The initial input list shows at most three items;
  the full list groups prompts, images, documents, models, and parameters, with
  search for larger sets and preserved search state on return from a detail.
- The selected real run exposes its three producer-recorded input references.
  Original prompt/image/context contents are absent from the transferred output
  set and remain explicitly unavailable. References never cause arbitrary file
  reads, network fetches, or same-filename substitution from an output.
- Focused exporter/API verification passed 17 tests. Browser coverage includes
  one-line prompts, large input sets, missing inputs, both ZIP modes, and the
  real campaign report at desktop, annotated 944px, and mobile widths.
- Removed the standalone Supporting documents catalog and Technical archive
  disclosure. Each swimlane activity now has a compact file control with its
  documents, outputs, and recorded image thumbnails. Unattributed files remain
  accessible within the process section without inventing a producing activity.
  Manifest and provenance JSON stay in the ZIP, without review-page links.
- Six offline Chromium checks passed after this change. The real-run check
  opens all 15 files through their producing activities in both ZIP modes and
  verifies that archive records remain packaged. Iteration-specific file and
  activity navigation is also covered. Desktop/mobile screenshots were inspected.
# 2026-09-17 Campaign-Wide Standalone Reports

- Added an authoritative 30-case inventory that retains the reviewed successful
  attempts and pins the latest retained attempt for six incomplete cases.
- Added one reusable all/selected batch command for report-only or full-data
  exports. It uses the existing canonical projection and standalone renderer,
  emits one ZIP and extracted report per case, and builds an offline catalog.
- Generalized results presentation across all 10 engineering workflow families,
  using meaningful recorded previews and principal deliverables. Compact activity
  blocks use explicit producer labels; unavailable versions remain explicit.
- Focused Python verification: 38 campaign workspace/export tests passed.
- Generated 30 full-data ZIPs and 30 extracted reports in ignored local storage.
- Integrity verification: 30 passed, zero failures.
- Offline Chromium verification: 30 reports, zero remote requests, zero browser
  errors, and successful activity-detail interaction in every report.
- Saved desktop/mobile screenshots for all 10 workflow families under the ignored
  generated campaign report directory.
- FR-035/T068 timing capture was not implemented or claimed by this work.

# 2026-09-17 Visual CAD Evidence and Process Semantics

- Added direct overview presentation for retained visual inputs and a bundled,
  file-origin Three.js STL viewer. Family-aware selection promotes the two final
  Raspberry Pi enclosure concepts, the drill jig, and the replacement-part mesh;
  CFD domains and surrogate solids remain supporting files.
- Replaced the Raspberry Pi CAD export byte tables with a test-oriented integrity
  summary and a collapsed file identity list. Expanded process rows now show
  retained image evidence where it helps.
- Split generic campaign execution into engineering responsibility lanes and drew
  explicit recorded-order connections from the durable activity events. The UI
  states that these lines establish execution order, not unrecorded artifact
  lineage.
- Regenerated all 30 full-data packages. Resource verification passed 30/30.
  Offline Chromium opened activity detail in every report with zero remote
  requests and zero page errors. Direct WebGL pixel checks passed for both
  enclosure concepts at desktop and mobile layouts.
- Focused verification passed: 59 Python tests, seven existing offline Playwright
  tests, and two visual/all-campaign Playwright tests.

# 2026-09-17 CFD Review Visualizations

- Added a first-class `review_visualization` resource role. The campaign
  preparer copies presentation imagery into the derived review workspace while
  preserving its source artifact identities and keeping the transferred run
  evidence unchanged.
- Promoted two actual-field comparisons for Raspberry Pi enclosure attempt 032:
  a Variant A/B air-speed slice and a Variant A/B temperature slice. Both were
  previously rendered from the retained OpenFOAM 10 VTK fields at z = 22 mm and
  use one shared scale per field.
- The output gallery now groups interactive final geometry separately from
  engineering visualizations. The recorded CFD collection activity exposes both
  figures as compact thumbnails when its `Verification & results` row is
  expanded.
- Detail views identify each figure as a review-time derivation, link its exact
  `cfd-comparison.json` and `cfd-fields.zip` source evidence, list the field,
  slice plane, comparison basis and renderer, and preserve the recorded warning
  that convergence and engineering validation were not claimed.
- Regenerated all 30 full-data reports without rerunning engineering work. The
  catalog remains at 30 cases; the enclosure ZIP contains both 2200 x 990 PNGs,
  the 21 MB field archive, and the source comparison record.
- Focused verification passed: 44 Python tests, Ruff, Ruff formatting, Prettier,
  `git diff --check`, one offline visual Playwright test, and the all-30 offline
  browser pass. Screenshots of desktop outputs, the expanded process, and mobile
  layout were visually inspected.

# 2026-09-17 Input-to-Process Connector Regression

- Restored visible input-row arrows when historical records retain run inputs
  but not per-activity consumption. These are explicitly labeled `Run inputs`
  and connect to the first recorded activity as workflow entry, not as a claim
  of verified consumption. Their detail view explains that distinction.
- Preserved `Inputs used` connectors for recorded activity bindings. Inputs
  without a binding remain accessible even when other inputs have bindings;
  no target is invented when the run has no recorded activities.
- Added clickable connector details and regression checks for Pi case01 and
  printed-part case01 under file-origin, networking-blocked Chromium at 1297,
  796 and 430 px widths, compact/expanded input rows, and 75 percent zoom.
  Endpoint assertions verify that arrows remain attached to the entry block.
- Added input-connector requirements to the presentation redesign plan.
  This fixes a narrow regression; the broader redesign remains pending.
- Regenerated all 30 full-data reports and ZIPs without rerunning workflows.
  Verification: 40 focused Python tests, three Playwright tests including the
  all-30 offline walkthrough, all-30 archive integrity checks and Prettier.
  Connector screenshots are under `/tmp/wright-083-input-connectors-final/`;
  inspected compact desktop and compact/expanded mobile arrows in view.

# 2026-09-17 Evidence-First Activity Review and Offline PDFs

- Replaced the narrow metadata/file-list-first activity drawer with a wider
  inspector. Its default evidence is a retained model, PDF, useful image or
  readable record. Inputs, work performed and outputs are grouped alongside it;
  a retained Markdown research account is rendered directly below. Execution
  metadata and the complete inventory are secondary disclosures. Related
  research references can switch the evidence in place. Duplicate engineering
  tables are not rendered twice.
- Bundled pinned PDF.js with a classic worker, character maps, standard fonts
  and licenses. The actual manufacturer drawing is visible after one click on
  Source dimensions. Multi-page PDFs have page, zoom and fit controls. No CDN,
  application backend or web server is needed when opening the extracted ZIP.
  Oversize/unsupported PDFs retain original-file access; rendering failure
  exposes a direct download instead of a blank preview.
- Joined retrieved-reference attribution to source manifests by retained SHA-256
  identity. The viewer exposes publisher URL and retrieval time without calling
  retrieved drawings AI-generated designs. Manifest operations are identified
  as a retained research account, not a complete tool-call transcript.
- Markdown uses the existing micromark ecosystem with unsafe HTML/protocols
  disabled; image URLs are made inert before insertion. License assets are
  hashed separately from engineering artifacts. Rebuild instructions and limits
  are in the portable viewer's VIEWERS.md.
- Rebuilt all 30 full-data reports/ZIPs from unchanged campaign evidence.
  All 30 archive/extracted-file checks passed. Focused Python coverage passed
  46 tests; Ruff, Prettier and diff whitespace checks passed. Offline Chromium
  checks cover actual drawing pixels, page/zoom/back/close navigation, 1297/796/
  430-pixel layouts, unreadable-PDF recovery, printing accounts, restored input
  arrows, CAD/CFD visuals and every report's first activity. Browser screenshots
  are under `/tmp/wright-083-pdf-review-final/`.
- This addresses the drawing/download detour and first activity-view redesign.
  It does not complete the full presentation-redesign plan, add engineering
  checks, reconstruct missing prompts or rerun historical workflows.

# 2026-09-17 Geometry-First CAD Activity Review

- Activity inspectors now open directly on their retained STL geometry, not
  only the principal final models promoted in the report overview. Variant
  selection stays within the inspector. Separate activity occurrences retain
  their own models; inspection records can expose a mesh only through a unique
  retained SHA-256 match.
- Pi's Author CAD source step authored Python and did not execute it. Its
  inspector shows the subsequent CAD result with explicit later-run attribution,
  a link to the producing activity and a missing-source-version-link notice.
  The mesh is not added to the authoring step's output inventory. Multi-pass
  authoring does not receive this contextual association.
- Improved Three.js framing for container aspect ratio and CAD Z-up, added
  fit-to-view, and release WebGL contexts when a viewer closes. Added a repeatable
  viewer bundle build and included its license in the portable manifest.
  Inline meshes are bounded to 8 MiB each and 32 MiB per report, prioritizing
  final models. STEP/3MF decoding is not introduced by this change.
- Rebuilt all 30 full-data reports and ZIPs from retained evidence without
  rerunning engineering tasks. They embed 21 models across 17 activity
  occurrences; all mapped activity models have inline payloads. All 30 archive
  integrity checks passed.
- Verification: 62 workspace-service trace tests, seven offline Chromium tests,
  Ruff lint/format, Prettier and whitespace checks passed. Pixel checks confirm
  nonblank geometry at 1297/796/430 px widths, variant switching, actual rendered
  movement during rotation, and fit-to-view. Inspected screenshots are under
  `/tmp/wright-083-geometry-final/`. The local report returned HTTP 200.
- Extended PEX-007 and PEX-011 with the observed missing geometry-lineage record,
  the eight STEP-only heat-spreader variants without retained previews, and
  per-occurrence/component preview capture requirements. These are open producer
  requirements, not new validation claims or a claim that every native CAD
  format is now viewable.

# 2026-09-17 PDF Canvas Flicker

- Confirmed that visible desktop scrollbars triggered additional PDF renders;
  the old renderer cleared its visible canvas by resetting width/height before
  drawing. A regression at the reported 796 x 791 viewport and 1.6 pixel ratio
  failed against the old report with 18 visible-canvas resets during zoom/resize.
- Made the PDF viewport size-contained with a stable scrollbar gutter. Observe
  its border box, fit against stable frame dimensions, coalesce resize events
  and skip identical page/zoom/size requests. Page dimensions no longer change
  the observed frame during rendering.
- Render replacement pages on a detached canvas, keeping the last completed
  drawing visible until the current request finishes. Superseded renders cannot
  publish a partial page. Closing cancels pending resize work; failed documents
  do not restart from resize notifications.
- Rebuilt all 30 standalone reports and ZIPs. All archive checks, 62 Python
  tests, eight offline Chromium tests, Prettier and whitespace checks passed.
  The new test runs with Chromium's hidden-scrollbar default disabled and checks
  zero visible-canvas resets, zero blank drawing frames, invariant frame size
  during zoom, and no further paints after settling. Existing tests cover PDF
  page navigation, error recovery, CAD/CFD views and all campaign reports.
- Visually inspected `/tmp/wright-pdf-stability-final/` screenshots. The served
  report returned HTTP 200. This is a presentation fix, not a producer capture
  requirement or a change to retained engineering evidence.
