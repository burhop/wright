# Process Execution Improvements for Engineering Reviews

**Started:** 2026-09-17. **Status:** Shareable producer backlog; not an instruction to rerun the campaign or implement validators. No item below is claimed implemented by this review.

**Companion documents:** [Evidence audit](presentation-review-2026-09-17.md), [presentation plan](presentation-redesign-plan.md), [existing producer contract](contracts/evidence-integration.md).

## Ownership and Use

This list concerns evidence that the execution software should preserve or publish so a reviewer can understand what actually happened. The results UI owns presentation, navigation and faithful display conversions. Domain producers and the separate validation owner retain authority over engineering checks, thresholds and conclusions.

Existing feature-083 capture hooks and evidence IDs may already cover parts of these requests for new runs. Audit them first; do not add parallel instrumentation, identity schemes or repositories. Historical absence from this bundle is not proof of absence from the original host.

Status vocabulary: **Audit/recover**, **Requested**, **In progress**, **Verified**, **Deferred**. Change an item to Verified only with a linked retained-run or contract-test example, producer revision and acceptance evidence. Keep IDs stable when handing this file to another agent.

Priority: **P0** prevents a trustworthy reconstruction or loses evidence; **P1** enables the normal engineering-review experience; **P2** extends an already useful account. Priority is about reporting evidence, not a new verdict on engineering risk.

## Do Not Send These Back as Capture Failures

Today's package review found substantial evidence that already exists:

- Pi manufacturer/supplier URLs, retrieval times, page observations, dimension interpretations and source restrictions are retained. The UI must expose them.
- Activity duration is present for 220 of 256 projected activities. Display it before adding missing-timing instrumentation.
- All three Pi cases retain field archives; heat-spreader cases retain VTU/CSV data; heater/robot cases retain time-series results. Rendering trustworthy plots from them is presentation work, not a new simulation.
- Existing producer checks, warnings, holds and assumptions in markdown/JSON must be projected completely. The UI's 12-table cutoff and wrong output counts are presentation bugs.
- The sketch's PNG/SVG and a document's page observation are not extra engineering inputs. Grouping representations is presentation work when the relationship can be proved.

## Backlog Summary

| ID | Priority | Status | Request | Primary owner |
| --- | --- | --- | --- | --- |
| PEX-001 | P0 | Audit/recover | Publish the exact executed definition, bound instructions and referenced runtime record | Runtime and campaign publisher |
| PEX-002 | P0 | Audit/recover | Preserve consumed input versions and explicit handoffs | Runtime / artifact publisher |
| PEX-003 | P1 | Requested | Complete occurrence, retry and timing capture | Runtime; existing FR-035/T068 |
| PEX-004 | P1 | Audit/recover | Identify actual tools, applications, models and versions per operation | Tool gateway / engineering adapters |
| PEX-005 | P1 | Requested | Record concise decisions and assumptions with supporting evidence | Workflow task/result producers |
| PEX-006 | P1 | Requested | Link requirement revisions and authorizations to exact subjects | Requirements / approval components |
| PEX-007 | P1 | Requested | Publish semantic artifact roles and representation lineage | Artifact and engineering producers |
| PEX-008 | P1 | Requested | Provide source/observation/usage links for research | Research adapters |
| PEX-009 | P1 | Requested | Make existing validation/check evidence consumable | Validation and domain-check owners |
| PEX-010 | P1 | Requested | Publish analysis setup, fields and visualization semantics | CFD / FEA / Modelica / diagnostics producers |
| PEX-011 | P2 | Requested | Retain useful CAD/manufacturing/electrical display outputs | CAD / slicer / PCB / harness adapters |
| PEX-012 | P0 | Audit/recover | Preserve complete failure/partial-work evidence and explicit side effects | Runtime / tool gateway / campaign publisher |
| PEX-013 | P0 | Requested | Make evidence publication incremental, portable and auditable | Evidence storage / campaign publisher |

## PEX-001: Exact Executed Record

**Observed:** All 30 selected run manifests refer to a runtime-evidence path that does not resolve under the transferred bundle. Pi case01's run has definition/template digests, but its exact resolved task prompt/call transcript is not in the inspected evidence. Today's preparation script is not proof of the historical instructions.

**Request:** Recover existing runtime records from their original storage if possible, verify the recorded digest, then publish them with referenced blobs. For new runs retain the instantiated executed workflow, compatible layout, bound task instructions, user/context references, template/code revision, tool configuration and final runtime evidence. Record provenance separately for user text, task template and actual resolved request. Redact credentials with explicit redaction metadata.

**Acceptance:** An exported run can show the exact instructions and definition that ran without the source checkout, current template or original host. Recoveries retain original timestamps/digests and are not labeled as contemporaneous new capture. Missing originals are explicitly classified, never reconstructed as fact.

## PEX-002: Inputs and Handoffs

**Observed:** 253/256 report activities have no mapped input/document binding. Existing records sometimes contain exact source paths/digests, so this is partly importer/presentation recovery work. Chronological neighbors do not establish consumption.

**Request:** At occurrence start, retain resolved input port/value/document bindings with artifact version/digest, prior producer occurrence, source locator and role. At transfer, preserve producer, consumer, ports and transferred versions. Capture same-path overwrites as new versions. Record rejected/superseded inputs when relevant to a retry.

**Acceptance:** Two occurrences using different bytes under the same filename have distinct input histories. A connector opens the exact transferred evidence. Parallel execution order never creates a false data dependency. Importers can link explicit retained references but must label unproven run-level context honestly.

## PEX-003: Occurrences, Retries and Timing

**Observed:** 220/256 activities already have projected duration; some historical automated authorizations lack it. Activity passes and run-level AI request counts do not reveal internal CAD revisions or tool retries. Existing requirement FR-035/T068 is the starting point.

**Request:** Persist run attempt, activity occurrence, parent operation, loop/iteration and tool-call attempt identities separately. Capture start/end timestamps and monotonic elapsed duration with units. Distinguish execution, queued/waiting, approval wait and retry backoff where available. Record retry reason, recovery action, prior/next artifact versions and terminal outcome. Interrupted durations must be marked incomplete, not estimated as finished.

**Acceptance:** A five-pass design loop displays five actual passes and their outputs; a transport retry is not counted as a design iteration. Failure, cancellation and restart have durable timing without a connected browser. Wright AutoTest authorization time is captured by the producer, not invented from an adjacent event.

## PEX-004: Actual Execution Identity

**Observed:** The Pi records identify a retrieval operation and `pypdf` 6.9.1; downstream records identify OpenFOAM/Gmsh. The UI still uses generic "Wright workflow automation" or node-name inference in places. Identity is uneven, not universally absent.

**Request:** Capture each actual tool/MCP operation and server/version, native application/version, solver/kernel/library versions, executable/container build identity and relevant configuration. Distinguish orchestrator, LLM, MCP adapter and native engineering software. For model use, record the resolved model identity/version when available, rather than only a routing alias. Never substitute today's installed version.

**Acceptance:** An engineer can identify what created a mesh versus what solved it, and what retrieved versus extracted a document. Each identity has a recorded source and scope. Unavailable historical versions stay unavailable while known tool names remain visible on compact blocks.

## PEX-005: Decisions and Assumptions

**Observed:** Design/research/diagnostic reports already contain useful interpreted dimensions, choices and limitations, but these are not consistently linked to inputs, operations and output versions.

**Request:** Publish concise task-level decision records: decision/assumption statement, actor or tool, scope, selected option, considered alternatives when actually recorded, cited evidence, affected output version and timestamp. Record why a change was made between design iterations and which assumption it depends on. Keep a quoted user requirement distinct from an LLM interpretation or designer-selected value.

**Acceptance:** Clicking a modeled feature or stated assumption reaches the relevant recorded rationale and source location. There is no request for private chain-of-thought or retrospective model-generated reasoning. If rationale was not recorded, the producer does not invent it later.

## PEX-006: Requirements and Authorization

**Observed:** Customer targets, manufacturer facts and designer assumptions coexist in Pi research. Automated approvals have subject digests; a completed task alone is not proof that a human approved requirements or release.

**Request:** Existing requirement/approval components should emit requirement ID/revision, statement, acceptance criterion, original input citation, scope and approval state; actor display name plus human/automation role; decision, timestamp and exact approved subject revision/digest. Use display name **Wright AutoTest** for this campaign's automated test authorizations while retaining raw identity. Record release/dispatch separately from approving a design basis.

**Acceptance:** A reviewer can trace a checked requirement back to the user-supplied source and correct approval, or see that no approval was recorded. Approval of version A cannot authorize version B. An automated test action is never shown as a named person's sign-off or physical dispatch.

## PEX-007: Artifact Roles and Representations

**Observed:** The runtime's `produced_files` collection mixes authored outputs, downloaded references and observations. Analysis meshes can resemble product geometry. Additional report renderings currently risk inflating historical output counts.

**Request:** Publish human-facing title, engineering purpose, origin class (supplied, retrieved, authored, transformed, observed, display-derived), principal/intermediate/supporting role, variant/assembly/region, producing occurrence and exact source versions. Represent preview-of, rendered-page-of, transformed-from and format-export-of relationships explicitly, with renderer/converter version and parameters.

**Acceptance:** The consumer selects a product shell rather than a fluid domain as the final part; groups sketch SVG/PNG and PDF/page images without losing originals; distinguishes a generated model from a supplied model and a mesh cleanup from physical repair. Post-run images remain review assets, not historical run outputs.

**CAD follow-up (2026-09-17):** Pi case01's `cad-authoring.json` explicitly states that source was authored but not executed by that step. The retained script would write `geometry-lineage.json`, but that file is absent from the transferred artifacts. Recover it from the original host if it exists; otherwise capture source digest, execution occurrence, export digest and variant together in future runs. The UI now labels later geometry as context rather than claiming the authoring step produced it. An export-inspection SHA-256 can identify an inspected mesh, but does not by itself prove which source revision created it.

## PEX-008: Research Provenance and Use

**Observed:** Pi source manifests already retain URL/time/digest and the research report gives page/row interpretations. What is missing from the bundle is a reliably joined exact retrieval/observation call trace and use relationship.

**Request:** Preserve original/final URL, publisher/title/revision, retrieval timestamp, response/content digest, operation/prompt or search query when one actually occurred, and observation page/crop/text range. Link the source to the observation/interpretation and the decision/input that used it. Record download versus web search truthfully; fetching a known URL is not proof that a search occurred.

**Acceptance:** The inspector explains what a supplier installation image shows and why it was consulted. An illustration is not mistaken for dimensional evidence. Source images and derived observations are not double-counted as independent proof. Sources remain inspectable offline when redistribution/access policy allows, with explicit exclusions otherwise.

## PEX-009: Existing Check Results

**Observed:** Thermal, jig, harness and PCB outputs contain substantive checks; they differ in subject identification, scope and structure. Some contain actual holds/warnings despite run completion. File-presence/digest inspection is not CAD correctness.

**Request:** Existing check producers emit a versioned check identity, exact subject, criterion/threshold with units, measured value, outcome, method/tool/version/configuration, relevant load case and supporting plots/documents. Preserve warnings, exclusions, indeterminate outcomes and declared applicability. Include a readable summary. Use the existing evidence envelope; retain producer authority and original vocabulary.

**Acceptance:** The report can show a dimensional check, mesh study, ERC warning or copper-only drop with correct context and provenance. It does not calculate a new engineering pass or silently apply an old result to a new design. This request does not commission new validators or activate deferred 081 content validation.

## PEX-010: Analysis and Plot Semantics

**Observed:** Pi field ZIPs, heat-spreader VTU/CSV, heater time series and robot trajectories are retained. Rich graphics are possible now, but setup-to-result relationships and preview manifests are inconsistent. Pi case01's producer does not claim convergence.

**Request:** Publish geometry/mesh/region identity, coordinate system and units, materials, loads/BCs/contact assumptions, solver setup/version, case/variant and time/iteration selection. Retain mesh statistics/quality and residual/refinement histories when generated. For plots publish field/component, unit, range, plane/camera, normalization, source digests and render recipe/version. For time series retain column/unit/frame/time/alignment/gap semantics. Record actual convergence statements, not a success-shaped proxy.

**Acceptance:** Temperature and velocity images can be reproduced from the correct case without rerunning analysis; a shared-scale comparison identifies its selection. A reviewer can trace a maximum or curve to source samples and load conditions. Missing convergence history is not reconstructed from final values. Postprocessing annotations and unit conversions are labeled and reproducible.

## PEX-011: Useful Engineering Visual Exports

**Observed:** Printing has a useful final model but not a useful support/layer view; its flattened toolpath projection was rejected. PCB packages contain native designs/Gerbers but no promoted schematic/board previews. CAD-native formats are not universally browser-viewable.

**CAD follow-up (2026-09-17):** All three heat-spreader `Create plate geometry` activities retain STEP outputs but no image or STL alongside them (eight STEP variants total). Pi case01's CAD execution record explicitly disables previews and does not retain a display mesh for every STEP-only component. Available enclosure/fluid-domain STL files can now be inspected directly in their producing activities; missing representations remain an export/capture requirement, not permission to execute historical CAD scripts.

**Request:** Where the producer already owns the application, retain a bounded faithful display representation and an original-to-preview link: CAD overview/critical section with units and component roles; actual pre-slice orientation and support geometry; schematic/board layers with orientation; connector mating face with pin/view convention. Layer/toolpath inspection is a separate future capability with actual layer metadata, not a renamed whole-model thumbnail.

For every geometry-producing occurrence and variant, publish a browser-viewable mesh or useful image linked to the native original's digest, with units, coordinate system, component identity, tessellation settings and renderer/converter version. Capture intermediate iterations as well as the selected final result. Source-authoring-only operations must remain distinct from geometry evaluation and export. When a bounded preview cannot be produced, publish its explicit reason without changing the engineering outcome.

**Acceptance:** Images answer a real inspection question. A zero-support result is stated with source evidence, not illustrated by invented supports. A CAD/Solid Edge original has a useful display fallback when feasible without implying browser-native support. Creating previews must not mutate the engineering artifact or dispatch a device.

## PEX-012: Failure and Partial Work

**Observed:** Bracket/sheet-metal run manifests stop at a started activity; their useful terminal reason comes from campaign diagnostics. Bracket case01 has an engineering-definition blocker, sheet-metal case02 a native CAD exception. Bracket case03 records many completed steps but only one published artifact, warranting an evidence-recovery audit rather than invented outputs.

**Live authoring follow-up (2026-09-18):** The Lightweight Equipment Bracket start request returned `WORKFLOW_TEMPLATE_SETUP_REQUIRED` before tool discovery, input preparation or run-record creation. Its diagnostic requires bracket geometry and CalculiX D034 clean-environment qualification. The UI had discarded the structured error code and shown "Workflow failed" and "Prompt sent" despite no execution. The frontend now preserves the code, correction and trace ID and identifies this as a maintainer-owned start blocker; this presentation fix neither qualifies the template nor establishes that its inputs or MCP configuration are valid.

**Preflight capture request:** Expose readiness before Run and persist rejected start attempts separately from executed runs. Reuse the existing diagnostic/trace identity and retain the blocker category, responsible owner, affected task/integration IDs, source revision, qualification scope, and actionable remediation. Record each check as passed, blocked, failed or not assessed; distinguish input requirements, missing MCP bindings, unavailable host software and Wright integration qualification. State whether a user can resolve the blocker or a maintainer must act. An installed MCP server or a prior campaign output is not sufficient evidence of live-template qualification. Acceptance includes reloading a rejected attempt without losing its cause, and never claiming a prompt/tool was dispatched when the gate prevented execution.

**Request:** Persist failure stage, exact failed operation, structured category, engineering-readable explanation, raw diagnostics, last successful checkpoint, affected artifact versions, unfinished/published status and tool side effects. Retain successful outputs incrementally even when a later tool fails. Distinguish "not attempted", "failed", "partially created" and "outcome unknown". Capture actual cleanup/device dispatch state and producer-authored recovery guidance where available.

**Acceptance:** A failed export contains the work actually retained up to failure, does not synthesize final deliverables, and explains whether a native file/device action may have occurred. Replay cannot create duplicate external effects merely to recover report evidence.

## PEX-013: Incremental Portable Publication

**Observed:** The campaign needed an explicit portable bundle transfer. The selected runtime references still do not resolve, although all transferred files passed checksum verification. A valid ZIP of an incomplete evidence set is still incomplete.

**Request:** Publish events/blobs incrementally, independent of a report/browser session, with idempotent identities, immutable content versions and a consistent database snapshot. Before portable publication, walk referenced evidence dependencies, classify missing/excluded/redacted items and publish a manifest. Include original/runtime records, source bytes when permitted, derived-asset recipes and logs needed for the account. Preserve the run outcome if evidence capture itself fails, but record that capture failure and its scope.

**Acceptance:** Crash/restart, path overwrite, active SQLite WAL and duplicate event delivery do not erase or misassociate evidence. An offline bundle opens without the original host and reports unresolved references before distribution. No credentials are exported. Missing runtime files are not excused by a checksum check covering only files that happened to be copied.

## First Handoff Sequence

1. Audit/recover PEX-001 and PEX-012 on the original campaign host without rerunning engineering tasks. Record whether missing items are recoverable, intentionally excluded or never captured.
2. Reconcile PEX-002/003/004/013 against existing 083 capture hooks and FR-035/T068; agree one additive versioned producer contract and ownership boundary.
3. Qualify that contract with one normal run and one retry/failure capture in an authorized test environment. Keep any test evidence clearly distinct from historical campaign outcomes.
4. Add semantic/domain exports PEX-005 through PEX-011 incrementally. The report work proceeds using retained facts and does not wait for all producer upgrades.

## Change Log

| Date | Update | Evidence |
| --- | --- | --- |
| 2026-09-17 | Started PEX-001 through PEX-013; separated existing-but-hidden data, recoverable publication gaps and future producer capture | [Today's package review](presentation-review-2026-09-17.md) |
| 2026-09-17 | Inline PDF/Markdown and digest-linked retrieval attribution now expose existing research evidence. This is a presentation repair, not newly captured process evidence. Exact task instructions and consumption bindings remain PEX-001/002 recovery requests. No producer item is marked Verified by the UI change. | [Implementation log](implementation-log.md#2026-09-17-evidence-first-activity-review-and-offline-pdfs) |
| 2026-09-17 | Added occurrence-level geometry preview requirements to PEX-011 and missing source/export linkage evidence to PEX-007. Existing STL models are now shown directly in CAD activities; this does not complete the producer requests. | Pi case01 `cad-authoring.json`, `cad-execution.json`, retained `enclosure-source.py`; heat-spreader case01-03 geometry output inventories |
| 2026-09-18 | Added preflight readiness, ownership and durable rejected-start evidence to PEX-012. Frontend diagnostics now distinguish a qualification rejection from a runtime tool failure; producer work and template qualification remain open. | `workflow_run_preparation.py` qualification gate; live bracket rejection trace `e1366032e22b839356180e42ada79599`; `workflow-recovery-bindings.spec.ts` blocked-start coverage |
