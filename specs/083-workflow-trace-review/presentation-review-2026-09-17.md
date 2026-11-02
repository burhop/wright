# Engineering Report Review: 2026-09-17

**Purpose:** Evidence for the presentation redesign, not an engineering qualification of the generated designs.

**Scope:** Inspected all 30 exported report models and their selected run manifests; read representative engineering documents from all ten families, with deeper inspection of Raspberry Pi case01. Reviewed the user's screenshots and the retained desktop process screenshot. This was a local evidence/design review, not a new browser acceptance run or a rerun of engineering software.

## Evidence Snapshot

- Feature worktree: `/tmp/wright-083-workflow-trace-review`, branch `codex/083-workflow-trace-review`.
- `BUNDLE`: `/home/burhop/repos/wright/.local-run/feature-083-imports/campaign-081`.
- `REPORTS`: `/home/burhop/repos/wright/.local-run/feature-083-reports/campaign-081`.
- `REPORTS/catalog.json` SHA-256: `e72bbf46def293816f18a5c5833c4f85d1cbc6e9fd35c306c99fde0ace96dcc9`.
- `REPORTS/inventory.json` SHA-256: `b8fe66ea1f03ea0444aa2a3ef1f06fea61656f93fa9e1f9813a239a5a17a2874`.
- Campaign selection: 30 reports, 24 completed runs, six failed runs, ten families. Completion is not correctness qualification.
- Raw `produced_files` lists contain 846 entries across the selected runs. These include retrieved references and intermediate records, not 846 final engineering deliverables.

Counts below were obtained by parsing the JSON in each export's `wright-trace-data` script, not by visually guessing from screenshots. Source record selection comes from `catalog.json`.

| Observation | Measured scope | Interpretation |
| --- | --- | --- |
| Activity input relationships are mostly empty | 253 of 256 projected activities have no mapped input records or input documents in any displayed occurrence | The UI cannot explain transformations. This does not prove the inputs were absent during execution; examine source manifests and exact document references before declaring a capture gap. |
| Timing is often available already | 220 of 256 activities have at least one projected occurrence duration | Display retained timing; request new capture only for missing/incomplete timing. Do not say timing is universally unavailable. |
| Generic JSON tables reach a fixed cap | 127 document projections contain exactly the renderer's 12-table limit | Hitting the limit alone does not prove every document was truncated. In Pi case01, it demonstrably omits variant B from the comparison view. |
| Runtime evidence references do not resolve | All 30 selected run manifests reference a runtime-evidence path; none exists at that referenced path under the transferred bundle | A publication/recovery issue to investigate, not proof the original runtime never recorded it. The Pi case01 referenced basename was also not located in the inspected bundle. |
| Visual support varies greatly | Heat-spreader and PCB cases have zero result previews/models; Pi case02/03 have final models but no analysis previews | Some visuals can be rendered from retained data; others require producer exports. One renderer cannot treat every result as a CAD part. |

## Root Cause

The exporter largely organizes files and generic JSON properties. Engineers need a linked argument: what was requested, what was made or concluded, what work produced it, and which evidence supports each conclusion.

Adding thumbnails to a file inventory does not establish this argument. Equally, hiding provenance fields to simplify a table can leave a number with no subject, units, method, or meaning. The report needs semantic evidence relationships and domain-specific presentations, not more filename exceptions.

## Concrete Presentation Defects

1. **Meaningful data disappears.** `review_model.py::_readable_tables` recursively walks mappings, with depth, list-length, and 12-table limits. Pi case01 `cfd-comparison.json` is displayed through variant A and several boundaries; variant B is absent from that view. Pagination/disclosure must preserve semantic groups, rather than silently omitting them.
2. **Run outputs and review assets are conflated.** Pi case01's original manifest lists 40 produced files. The HTML says it produced 42 after two post-run CFD visualizations are attached. Derived presentation assets need separate origin, attribution, and counts.
3. **Visualization provenance is under-enforced.** The preparer selects global Pi case01 PNGs by case name. It records source artifact IDs but does not enforce the originating attempt/archive digest from the visualization recipe. The recipe and README are not bundled with those images. Binding to a case name is insufficient when attempts change.
4. **File publication is described as engineering creation.** Downloaded manufacturer PDFs, supplier images, and page observations are grouped as activity outputs without distinguishing retrieval, extraction, interpretation, and design authorship.
5. **The activity view foregrounds metadata.** Tool/version/pass/time cells precede a useful process account; generic properties and repeated unavailability messages dominate. Metadata matters, but it should support the action narrative.
6. **Media cannot always be inspected in context.** The standalone document renderer has no complete PDF viewing path. Its current CSP blocks object embedding. A native iframe alone is not evidence of cross-browser offline support.
7. **Order is not lineage.** Current generic graph connectors use recorded execution order. This restores navigation, but does not establish what artifact passed between activities or whether independent branches depended on each other.
8. **The graph is too sparse and repetitive.** The retained process screenshot has narrow tall blocks, repeated labels and large empty row areas; expanded CFD content is outside the visible horizontal region. Counting thumbnails in a test does not demonstrate that the relevant evidence was visibly reviewed.

Code entry points: `packages/workspace_service/src/workspace_service/workflow_trace/review_model.py`, `portable/review.js`, `portable/review.css`, `export.py`, and `scripts/prepare-workflow-trace-review-workspace.py`.

## Raspberry Pi: Evidence Already Available

Selected source: `BUNDLE/output/raspberry-pi-enclosure-01/attempt-032/`, run `ef9ed5964df742d69029db3e6cc7e581`. Paths below are under its `artifacts/` directory unless noted.

| Evidence | What an engineer should see | Availability |
| --- | --- | --- |
| `manufacturer-research.md` | Why the Pi mechanical drawing, product brief and insert references were consulted; observed dimensions; distinction between customer goals and reference-only manufacturer dimensions | Retained narrative, currently poorly surfaced |
| `research/manufacturer-evidence.json` | Original/final URLs, retrieval times, file digests, extracted pages, retrieval operation and extraction version | Retained structured provenance |
| `research/supplier-evidence.json` | Candidate insert identity, source URLs/times/digests and bounds of supplier claims | Retained structured provenance |
| `research/manufacturer-drawing.pdf` and its page observation | Board outline and mounting pattern with the manufacturer's reference-only warning; open the PDF at page 1 | Original PDF and rendered observation both retained |
| `research/insert-dimensions.jpg` and observation | RX-M2.5x5.7 row: receiving bore 4.0 mm, insert length 5.7 mm, surrounding wall 1.6 mm, minimum blind depth L + 1 mm, according to the recorded research | Retained; do not treat an observation as a second independent source |
| `research/insert-installation.jpg` | Installation reference only; no additional dimensional evidence | Retained; useful beside installation context, not as an unexplained hero image |
| Enclosure A/B models and CFD contracts | Distinguish product shell, analysis domain, board surrogate and heat-source patch | Retained STEP/STL and role information in contracts |
| `cfd-comparison.json`, preparation/solver reports | Actual mesh/region/field data, solver, setup and stated limitations; compare both variants | Retained; no need to invent analysis results |
| `cfd-fields.zip` | Source fields for meaningful analysis visualization | Retained for all three Pi cases, each with a different source identity |

The research activity has a start and completion timestamp: `13:18:24.208145Z` to `13:20:37.792644Z` on September 13, approximately 133.6 seconds. This is activity elapsed time, not necessarily active tool or model time.

The source manifest names retrieval operation `retrieve_pi_manufacturer_references` and extraction library `pypdf` 6.9.1. These are supported identities for those operations, not proof of every MCP/model version. The current preparation script names intended MCP calls and a research prompt, but is not the pinned executed definition. Do not present it as the exact historical prompt/call sequence.

The two existing CFD comparison PNGs live in `BUNDLE/visuals/ai-cfd-essay/`. Their README binds them to case01 attempt032 and field-archive SHA-256 `6500135c6cc3d8ca8e91332a76738017d5b0792514ca2a75e78fa1f311a5532d`. They show a horizontal z = 22 mm slice with shared temperature and velocity scales. They are post-run renderings, not solver screenshots. They must never be reused as case02/03 results.

The CFD producer explicitly records `engineering_validation_complete: false` and `steady_state_convergence_claimed: false`. Beautiful field plots must not imply otherwise. The report may display numerical findings and recorded scope, but cannot declare a thermally qualified winner.

## Cross-Family Findings

Each path starts at `BUNDLE/output/<case>/<attempt>/artifacts/`. These are representative findings, not a technical audit of every engineering conclusion.

| Family / sampled selection | Useful retained evidence | Presentation priority and caution |
| --- | --- | --- |
| Printed replacement part / case01 attempt003 | Design record, generated and cleaned meshes, image, mesh measurements, slicing settings and transfer receipt | New replacement design, digital cleanup, print preparation, simulated handoff. No duplicate recolored whole-part preview or unusable flattened toolpath page. |
| Pi enclosure / case01 attempt032 | Research PDFs/images, design basis, enclosure A/B, CFD contracts/fields/reports | Inspect final geometry, then meaningful A/B fields and setup. Preserve reference-only and exploratory-analysis scope. |
| Drill jig / case01 attempt012 | `jig.step`, `jig.stl`, `hole-layout.dxf`, `dimension-report.json` | Show jig and hole pattern; link dimensions to datum and inspection. The report explicitly retains ambiguous bushing stackup and does not claim physical fit or manufacturing qualification. |
| Heat spreader / case01 attempt008 | `sizing-decision.json`, `mesh-comparison.json`, `heat-balance.json`, STEP, VTU/CSV fields | Reported 40 mm baseline about 50 C versus 60 mm revision about 41.67 C at a declared 45 C limit; selected revision is a synthetic conduction candidate. Show field and mesh study, not file counts. Existing data permits display postprocessing. |
| Robot tracking / case01 attempt003 | `diagnosis.md`, trajectory SVG, timeline CSV, tracking metrics, bag inspection | Planned versus measured path, 45 mm peak lateral error at 15 s and event timing, units/frames/sampling. The diagnosis says temporal correlation, not proof of cause; no physical control changes occurred. |
| Harness / case01 attempt003 | Harness drawing, BOM/pin/cut schedules, manufacturer mating views, `verified/verification.json` | Diagram plus electrical/assembly result groups. Native verification reports a release hold and unknown contact resistance; copper-only voltage drop is not total voltage drop. |
| PCB / case01 attempt007 | Final/intermediate KiCad files, ERC/DRC, Gerbers, `verification-evidence.md` | Schematic/board views, exact checks and fabrication contents. Recorded 0 ERC errors/6 warnings and 0 DRC errors/3 warnings are not unconditional production approval. No report preview was retained; test a faithful render-only path or request producer previews. |
| Water heater / case01 attempt005 | Temperature curve, CSV studies, `heater-selection.md`, sealed model and refined-run evidence | 700 W demonstrated about 174.56 s to 90 C under the recorded case and 180 s target. Show candidate curves, loss case and numerical-study scope; not hardware qualification. |
| Lightweight bracket / case01 attempt006 | `mechanical-basis.md`, campaign diagnostic | CAD authoring blocked by underdefined pocket-blend geometry. Show supplied concept, retained basis and exact blocker; do not invent a final part or FEA. Case03 instead records an MCP failure and needs a different account. |
| Sheet metal / case01 attempt006 | Supplier references, `supplier-research-report.json`, `manufacturing-intent.md` | CAD blocked on forming/tool-access evidence and bend-development discrepancy. Display supplier/intent context and unfinished handoff. Case02 has a native CAD error, not the same engineering blocker. |

The 25-activity water-heater case03 and 17-activity PCB cases are useful real scale tests. A separate explicit test fixture may exercise 30+ activities, loops and parallel paths; it must not be represented as another real campaign result.

## Work Ownership

- **Presentation repair now:** semantic summaries, complete A/B data, sourced process narratives, media viewers, meaningful previews, truthful labels, graph readability, exact provenance and asset counting.
- **Recover from existing evidence where possible:** input bindings explicitly identified by records, page views, field/CSV plots, existing duration/tool facts, missing runtime files from their original storage.
- **Execution-agent improvements:** incremental bound input/tool/decision/iteration capture, exact prompts/definition snapshots, portable runtime publication, richer domain exports and explicit producer check/approval contracts. See [the separate backlog](process-execution-improvements.md).

Neither attractive output nor archive integrity establishes engineering correctness. The report must expose the evidence produced by other components without adding its own engineering acceptance decisions.
