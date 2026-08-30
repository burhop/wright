# Customer Process User-Story Catalog

**Status:** planning draft; not benchmark authority, implementation approval, or qualification evidence

**Created:** 2026-08-28

## Purpose and boundary

This catalog organizes Wright's future demonstrations and benchmark candidates around customers and their independently meaningful engineering outcomes. It is intentionally not a list of isolated tools, technical specialties, MCP servers, or individual workflow steps.

The first stories are small, concrete, and suitable for immediate `T0` contract validation and deterministic `T1` execution with local fixtures or mocks. Later stories become progressively broader and less specified because their details should be learned from implementing and observing the earlier stories.

Nothing in this file:

- counts toward the governed `0/100` benchmark total;
- authorizes benchmark generation or execution;
- authorizes MCP invocation, external email, purchasing, application mutation, machine control, or physical actuation;
- makes an MCP server part of a customer story's stable identity; or
- changes the approved roadmap, readiness state, WIP lease, or release eligibility.

A story becomes a benchmark case only after `EPP-B01` supplies an approved manifest, provenance, oracle, failure/recovery contract, partition, attempt policy, evidence, and independent qualification. Cosmetic or provider-only variants do not become distinct counted cases.

## Ordering model

| Wave | Story IDs | Roadmap anchor | Intended learning |
|---|---:|---|---|
| 1 | 001–010 | `EPP-F02` / Phase P1 | Express customer outcomes as stable, readable process definitions; validate simple document and review flows without MCPs. |
| 2 | 011–025 | `EPP-F03` / Phase P1 | Execute deterministic multi-step workflows with mock capabilities, immutable evidence, feedback, failure, and recovery. |
| 3 | 026–045 | `EPP-F04` / Phase P2 | Bind abstract capabilities to exact MCP servers/tools and produce schema-aware preflight without live invocation. |
| 4 | 046–070 | `EPP-F05` / Phase P2 | Run approved workflows through governed live boundaries and deliver inspectable artifacts. |
| 5 | 071–085 | `EPP-F06` / Phase P3 | Let users and bounded AI compose, adapt, compare, and approve reusable process definitions. |
| 6 | 086–100 | `EPP-B01`, `EPP-B02`, `EPP-C01` / Phase P4 | Discover and qualify complex, cross-organization, proprietary, remote, and physical customer journeys. |

## Progressive automation contract

The customer outcome remains stable while its validation level advances:

```text
draft
-> accepted_story
-> process_defined
-> t0_contract_validated
-> t1_deterministic_validated
-> t2_integration_validated
-> t3_live_validated
-> benchmark_candidate
-> independently_qualified
```

`T4` physical actuation is outside the current required benchmark and needs separate planning, safety authority, human approval, and evidence. A process may remain valuable and demonstrable at any lower tier.

For every accepted story, automation should eventually verify:

1. stable story identity, customer archetype, outcome, inputs, deliverables, and success definition;
2. major phases, feedback loops, human decisions, failure/recovery behavior, and artifact lineage;
3. abstract capability requirements independent of tool or provider names;
4. optional exact MCP/application bindings and honest missing-capability diagnostics;
5. the highest supported validation tier without promoting mock evidence into a live claim; and
6. immutable run and review evidence before any qualification status changes.

## Wave 1 — Simple process definitions and no-MCP validation

The first five stories form a small product-definition chain. Each is independently useful, but they can also be composed later into sheet-metal, additive, machined-part, electronics-enclosure, and other design processes.

### EPP-US-001 — Turn text and images into a product concept brief

**Customer:** Product designer or small manufacturer

**User story:** As a product designer, I want Wright to organize my text, reference images, intended use, quantity, and constraints into a reviewable concept brief so that I can confirm what I am trying to create before detailed engineering begins.

**Inputs:** User text; one or more reference images; intended use; target quantity; known constraints.

**Customer-visible result:** A versioned concept brief containing the objective, users, operating context, explicit requirements, source references, assumptions, unknowns, risks, and expected deliverables.

**Immediate acceptance:** Every explicit user constraint is traceable to the brief; observations and assumptions are distinct; missing material information is listed; the user can accept, reject, or request a revision.

**Initial automation:** `T0` schema/traceability checks and `T1` deterministic fixtures using supplied text and images. No research, CAD creation, MCP call, or external action is required.

### EPP-US-002 — Research missing product-definition details

**Customer:** Product designer

**User story:** As a product designer, I want Wright to research or inspect approved references for missing dimensions, materials, gauges, standards, and comparable products so that I can decide which proposed details belong in the design basis.

**Inputs:** An approved concept brief; user-supplied documents or an explicitly permitted research source set; a list of unknowns.

**Customer-visible result:** A research packet that separates sourced facts, calculations, comparable examples, assumptions, conflicts, and unresolved questions, with provenance for every proposed detail.

**Immediate acceptance:** No proposed detail silently becomes a requirement; unsupported claims remain unknown; conflicts and uncertainty are visible; the user can accept or reject each proposal.

**Initial automation:** `T0` provenance and decision checks plus `T1` execution against frozen local research fixtures. Live web research is optional later and never required for the first runnable example.

### EPP-US-003 — Produce a concrete design document

**Customer:** Product designer

**User story:** As a product designer, I want Wright to combine my accepted concept and research decisions into a concrete design document so that downstream engineering work starts from one clear, versioned basis.

**Inputs:** Accepted concept brief; accepted research decisions; declared assumptions and exclusions.

**Customer-visible result:** A design document with functional and physical requirements, interfaces, material and manufacturing constraints, acceptance criteria, required artifacts, open issues, and revision identity.

**Immediate acceptance:** Every requirement has an identity and source; values include units where applicable; conflicts are rejected; open issues cannot be represented as settled requirements; the output revision is immutable once submitted for review.

**Initial automation:** `T0` contract, unit, reference, and completeness validation followed by deterministic document generation at `T1`. No CAD or MCP is required.

### EPP-US-004 — Check a design document against its requirements

**Customer:** Design reviewer

**User story:** As a design reviewer, I want Wright to check a proposed design document against its source requirements and report passes, failures, missing evidence, and contradictions so that revision effort is focused and auditable.

**Inputs:** Exact design-document revision; exact requirement set; declared review policy.

**Customer-visible result:** A requirement-by-requirement review with evidence references, pass/fail/needs-input status, severity, rationale, and bounded revision guidance.

**Immediate acceptance:** Every requirement receives exactly one honest result; missing evidence never passes; summary counts equal the detailed population; feedback points to the exact document revision and requirement.

**Initial automation:** Deterministic positive, negative, missing-input, contradiction, and stale-revision fixtures at `T1`.

### EPP-US-005 — Approve or return a design document

**Customer:** Product owner or engineering approver

**User story:** As the accountable approver, I want to review the exact design-document revision and its requirement check, then approve it or return it with comments so that downstream work cannot use an ambiguous or unapproved basis.

**Inputs:** Exact design-document revision; exact review result; approver comments.

**Customer-visible result:** An immutable approve, reject, or revise decision bound to the reviewed revision, with actor, time, comments, and the permitted next action.

**Immediate acceptance:** A decision cannot attach to a different or changed revision; rejection and revise outcomes do not grant downstream authority; approval exposes only the next action allowed by policy.

**Initial automation:** `T0` decision and transition validation plus `T1` accept/reject/revise/stale-subject fixtures. No MCP or external action is required.

### Remaining Wave 1 stories

| ID | Customer archetype | High-level user story | First useful proof | Definition maturity |
|---|---|---|---|---|
| EPP-US-006 | Engineer receiving an existing project | Inventory a supplied package of documents, images, CAD/mesh files, tables, and notes so the engineer can see what exists, what is missing, and which artifacts are authoritative. | `T0/T1` local artifact inventory, safe preview metadata, duplicate/missing-reference checks | Ready to specify |
| EPP-US-007 | Manufacturing reviewer | Review a drawing, bill of materials, and manufacturing notes for completeness and internal consistency before the package is released. | `T0/T1` frozen document fixtures with positive and negative controls | Ready to specify |
| EPP-US-008 | Additive manufacturing designer | Review an existing STL or mesh for size, units, orientation assumptions, closedness, thin regions, and other declared printability risks without modifying or printing it. | `T0/T1` deterministic mesh fixtures and an inspectable report | Ready to specify |
| EPP-US-009 | Buyer or product owner | Compare supplier quotations against an approved request, quantity, delivery date, technical exceptions, and commercial terms without sending or accepting anything. | `T0/T1` local RFQ/quote fixtures with normalization and exception checks | Ready to specify |
| EPP-US-010 | Maintenance coordinator | Turn technician notes, equipment history, photos, and approved manuals into a prioritized diagnosis and inspection plan without commanding equipment or ordering parts. | `T0/T1` frozen incident fixtures with uncertainty and escalation checks | Ready to specify |

## Wave 2 — Deterministic multi-step workflows with evidence and recovery

| ID | Customer archetype | High-level user story | Initial target | Definition maturity |
|---|---|---|---|---|
| EPP-US-011 | Sheet-metal product designer | Run the accepted concept, bounded research, design-document generation, requirement review, revision loop, and approval as one inspectable process. | `T1`; mock research and artifact producers | Shaped |
| EPP-US-012 | Additive manufacturing designer | Turn text and reference images into an approved 3D-modeling and print-preparation plan with declared geometry, material, quality, and review expectations. | `T1`; planned artifacts only | Shaped |
| EPP-US-013 | Drawing reviewer | Review a drawing package, return markups, receive a revised package, and prove every issue was resolved or explicitly dispositioned. | `T1`; deterministic review/rework loop | Shaped |
| EPP-US-014 | Buyer | Build an RFQ package from an approved design package and route the exact draft for human approval without sending it. | `T1`; local package and approval evidence | Shaped |
| EPP-US-015 | Product owner | Evaluate one or more quotes, record technical and commercial exceptions, and approve, reject, or request clarification without contacting a vendor. | `T1`; deterministic decision workflow | Shaped |
| EPP-US-016 | Mechanical designer | Turn bracket requirements into a proposed parametric-model definition, mock geometry artifact, requirement check, and revision loop. | `T1`; provider-neutral fake model producer | Shaped |
| EPP-US-017 | Electronics product designer | Develop an enclosure concept, board/connector constraints, thermal-study plan, and mock evidence package for review. | `T1`; deterministic ECAD/CAD/thermal fixtures | Shaped |
| EPP-US-018 | Manufacturing engineer | Develop a fixture or jig concept from part, operation, datum, load, access, and safety requirements and route it through design review. | `T1`; mock artifacts and checks | Shaped |
| EPP-US-019 | Verification engineer | Turn a design basis into a traceable verification plan that assigns inspection, analysis, demonstration, or test evidence to every requirement. | `T1`; coverage and gap assertions | Shaped |
| EPP-US-020 | Simulation engineer | Define a study with exact model revision, loads, boundary conditions, assumptions, outputs, acceptance criteria, and review gates before solver execution. | `T1`; plan and evidence-record lifecycle | Shaped |
| EPP-US-021 | Quality engineer | Triage a nonconformance, contain affected artifacts, propose cause and corrective-action work, and route the disposition for approval. | `T1`; failure and recovery evidence | Shaped |
| EPP-US-022 | Change-control engineer | Compare an engineering change against the released baseline and identify affected designs, drawings, BOMs, analyses, suppliers, tests, and approvals. | `T1`; immutable before/after identities | Shaped |
| EPP-US-023 | Maintenance planner | Progress an incident from intake through evidence collection, diagnosis, inspection plan, blocked-prerequisite handling, and approved work order. | `T1`; interruption and resume behavior | Shaped |
| EPP-US-024 | Procurement engineer | Assemble a technically complete supplier handoff package, validate its contents, and route it for internal approval without external delivery. | `T1`; artifact completeness and approval | Shaped |
| EPP-US-025 | Release engineer | Verify that a product release package contains the approved design, drawings, BOM, analyses, deviations, instructions, and signoffs before release. | `T1`; deterministic completeness gate | Shaped |

## Wave 3 — Exact capability binding and no-call preflight

These stories preserve the customer outcome while introducing replaceable bindings. A server or application name belongs to binding metadata, not to the stable story identity.

| ID | Customer archetype | High-level user story | Initial target | Definition maturity |
|---|---|---|---|---|
| EPP-US-026 | Sheet-metal designer | Select an installed capability for creating a sheet-metal model and see exact server, tool, schema, approval, and missing-input diagnostics before any call. | `T0/T2` preflight only | Candidate |
| EPP-US-027 | Sheet-metal designer | Preflight native-model save and neutral STEP export destinations, formats, versions, overwrite behavior, and workspace retention. | `T0/T2` preflight only | Candidate |
| EPP-US-028 | Sheet-metal designer | Preflight flat-pattern creation and DXF export, including gauge, bend, orientation, and output-contract readiness. | `T0/T2` preflight only | Candidate |
| EPP-US-029 | Drawing author | Preflight drawing-sheet, view, dimension, title-block, manufacturing-markup, and export capabilities for an approved design. | `T0/T2` preflight only | Candidate |
| EPP-US-030 | Additive designer | Select and validate an image/description-to-geometry capability and its required inputs without generating geometry. | `T0/T2` preflight only | Candidate |
| EPP-US-031 | Additive manufacturing engineer | Preflight mesh inspection, repair, orientation, and support-generation capabilities against one exact STL revision. | `T0/T2` preflight only | Candidate |
| EPP-US-032 | Additive manufacturing engineer | Preflight slicer profile, material, printer envelope, quality, support, and G-code output contracts without slicing. | `T0/T2` preflight only | Candidate |
| EPP-US-033 | Printer owner | Preflight an installed printer-application connection, exact device identity, readiness, and authorization without uploading or starting a job. | `T0/T3` read-only preflight | Candidate |
| EPP-US-034 | Structural analyst | Bind model preparation, meshing, solve, and result-extraction capabilities while validating units and data mappings before execution. | `T0/T2` preflight only | Candidate |
| EPP-US-035 | Thermal analyst | Bind geometry, material, boundary-condition, solve, convergence, and report capabilities for a thermal study without execution. | `T0/T2` preflight only | Candidate |
| EPP-US-036 | CNC process planner | Bind stock, setup, tool, operation, simulation, postprocessing, and static lint capabilities without commanding a machine. | `T0/T2` preflight only | Candidate |
| EPP-US-037 | Quality engineer | Bind inspection-plan, measurement-import, tolerance-evaluation, and report capabilities for an exact released definition. | `T0/T2` preflight only | Candidate |
| EPP-US-038 | Electronics product designer | Bind board-envelope, connector, keep-out, enclosure, and thermal capabilities while preserving exact source identities. | `T0/T2` preflight only | Candidate |
| EPP-US-039 | Materials engineer | Bind approved materials-property sources and calculation capabilities while exposing provenance, applicability, and uncertainty. | `T0/T2` preflight only | Candidate |
| EPP-US-040 | Buyer | Preflight an approved RFQ email package, recipient, attachments, classification, and send authority without transmitting it. | `T0/T3` external-write preflight | Candidate |
| EPP-US-041 | Buyer | Preflight access to a mailbox or quote repository and map received quotation fields without sending, accepting, or deleting messages. | `T0/T3` read-only preflight | Candidate |
| EPP-US-042 | Technical writer | Bind document, drawing, and PDF generation capabilities and validate templates, metadata, destinations, and output contracts. | `T0/T2` preflight only | Candidate |
| EPP-US-043 | Release engineer | Bind version-control or lifecycle-management capabilities and validate exact item, revision, transition, and approval requirements without release. | `T0/T3` preflight only | Candidate |
| EPP-US-044 | Any engineer | Preflight workspace storage, artifact naming, versioning, retention, download, and open-in-application actions for a multi-artifact result. | `T0/T2` preflight only | Candidate |
| EPP-US-045 | Workflow owner | Substitute a materially different provider/tool binding for an abstract capability and prove the process requires no customer-story or case-specific runtime branch. | `T0/T2` generic conformance | Candidate |

## Wave 4 — Governed execution and actionable artifacts

| ID | Customer archetype | High-level user story | Initial target | Definition maturity |
|---|---|---|---|---|
| EPP-US-046 | Sheet-metal designer | Create a sheet-metal model from an approved design document, validate it, and save exact native and STEP artifacts in the Wright workspace. | `T2/T3`; governed CAD execution | Candidate |
| EPP-US-047 | Sheet-metal manufacturing engineer | Create and validate a flat pattern from the approved model and save an exact DXF artifact with lineage to the source revision. | `T2/T3`; governed CAD execution | Candidate |
| EPP-US-048 | Drawing author | Create a manufacturing drawing with flat view, dimensions, title block, bend information, and markup, then validate and save it. | `T2/T3`; review/rework loop | Candidate |
| EPP-US-049 | Sheet-metal product team | Execute the approved design-to-model-to-flat-to-drawing chain and stop with a complete, validated internal manufacturing package. | `T2/T3`; multi-artifact chain | Candidate |
| EPP-US-050 | Buyer | Send an approved sheet-metal RFQ package to approved recipients and retain exact delivery evidence and attachments. | `T3`; explicit human approval | Candidate |
| EPP-US-051 | Product owner | Approve or reject a received quote and, after explicit approval, send the corresponding award, decline, or clarification message. | `T3`; external mutation with approval | Candidate |
| EPP-US-052 | Additive designer | Generate a reviewable mesh and STL from approved text/image requirements, validate geometry lineage, and save the artifacts. | `T2/T3`; geometry generation | Candidate |
| EPP-US-053 | Additive manufacturing engineer | Inspect and repair a mesh, propose orientation and supports, obtain review, and save a validated printable STL revision. | `T2/T3`; review/rework loop | Candidate |
| EPP-US-054 | Additive manufacturing engineer | Slice an approved STL with an exact printer/material/profile identity and save validated project and G-code artifacts. | `T2/T3`; slicer execution | Candidate |
| EPP-US-055 | Printer owner | Deliver an approved sliced job to the exact printer application/device queue without starting physical motion and verify receipt. | `T3`; approved external delivery | Candidate |
| EPP-US-056 | CNC process planner | Produce and statically validate a machining setup, tool list, operation plan, simulation record, and postprocessed program without machine actuation. | `T2/T3`; static outputs only | Candidate |
| EPP-US-057 | CNC job-shop estimator | Turn a released part package into a reviewed manufacturing approach, risk list, cycle-time basis, and quotation package. | `T2/T3`; governed analysis and documents | Candidate |
| EPP-US-058 | Structural analyst | Execute a structural study, validate mesh/loads/units/convergence/results, and iterate design feedback until acceptance or bounded stop. | `T2/T3`; solve and feedback | Candidate |
| EPP-US-059 | Thermal analyst | Execute an enclosure thermal study, validate convergence and margins, and return actionable design feedback with exact evidence. | `T2/T3`; solve and feedback | Candidate |
| EPP-US-060 | Manufacturing engineer | Create and validate a fixture or jig model and drawing package from approved operation and datum requirements. | `T2/T3`; design and artifact checks | Candidate |
| EPP-US-061 | Fabrication designer | Create a weldment design, cut list, drawings, weld notes, and inspection requirements and route the package through review. | `T2/T3`; fabrication package | Candidate |
| EPP-US-062 | Process equipment designer | Create a reviewed equipment layout with interfaces, access, maintainability, safety clearances, and manufacturing handoff artifacts. | `T2/T3`; scope to be refined | Candidate |
| EPP-US-063 | Electronics product designer | Integrate exact board geometry and connectors into an enclosure, check clearance and thermal requirements, and release prototype artifacts. | `T2/T3`; cross-domain artifacts | Candidate |
| EPP-US-064 | Quality engineer | Import measurement results, evaluate them against exact tolerances, and issue an inspectable acceptance or nonconformance record. | `T2/T3`; metrology evidence | Candidate |
| EPP-US-065 | Quality and design team | Feed a nonconformance into a bounded design/manufacturing correction loop and prove the released revision resolves every accepted issue. | `T2/T3`; cross-record recovery | Candidate |
| EPP-US-066 | Procurement engineer | Build and compare a BOM sourcing plan using approved part identities, quantities, alternates, lead times, and supplier evidence. | `T2/T3`; approved external sources | Candidate |
| EPP-US-067 | Change-control engineer | Apply an approved change consistently across design, drawing, BOM, analyses, instructions, and release records, then prove no stale dependent remains. | `T2/T3`; coordinated mutation | Candidate |
| EPP-US-068 | Reliability engineer | Analyze approved sensor/history data, produce a diagnosis and maintenance recommendation, and update the work package after review. | `T2/T3`; data analysis and approval | Candidate |
| EPP-US-069 | Release engineer | Release an approved multi-artifact technical package through the governed lifecycle and retain exact deployment, rollback, and prior-version evidence. | `T2/T3`; release boundary | Candidate |
| EPP-US-070 | Automation user | Run the same approved process through browser and headless entry points and receive equivalent decisions, artifacts, evidence, cancellation, and recovery behavior. | `T2/T3`; UI/headless equivalence | Candidate |

## Wave 5 — Reviewed process authoring and composition

| ID | Customer archetype | High-level user story | Initial target | Definition maturity |
|---|---|---|---|---|
| EPP-US-071 | Sheet-metal process owner | Describe a sheet-metal process in plain language, inspect Wright's proposed canonical process and assumptions, and accept or reject the proposal without execution authority. | Phase P3 authoring evidence | Discovery shaped |
| EPP-US-072 | Sheet-metal process owner | Adapt an approved process for a different gauge, material, product family, or manufacturing partner while reviewing a semantic change set. | Versioned proposal and review | Discovery shaped |
| EPP-US-073 | Process architect | Create a reusable product-definition component from Stories 001–005 with explicit ports, gates, artifacts, and version compatibility. | Reusable component contract | Discovery shaped |
| EPP-US-074 | Design lead | Compose reusable definition, design, review, and correction components into a governed product-development process. | Composition and equivalence | Discovery shaped |
| EPP-US-075 | Additive process owner | Create an image-to-print-preparation process from a reviewed template and declare its material, printer, quality, and safety assumptions. | Reviewed authoring | Discovery shaped |
| EPP-US-076 | Additive process owner | Adapt a qualified preparation process to a new printer, material, or slicer profile and see which evidence becomes stale. | Change impact and requalification | Discovery shaped |
| EPP-US-077 | Analysis lead | Author a simulation process with model checks, solver-independent inputs, convergence, acceptance, feedback, and approval gates. | Reviewed authoring | Discovery shaped |
| EPP-US-078 | Quality manager | Generate an inspection process from customer requirements and internal standards, then review every proposed characteristic and disposition rule. | Reviewed authoring | Discovery shaped |
| EPP-US-079 | Procurement manager | Generate an RFQ/quote/award process from company policy while preserving human authority over recipients, commitments, and approvals. | Reviewed authoring | Discovery shaped |
| EPP-US-080 | Maintenance manager | Generate a diagnosis and maintenance process from approved manuals, history, safety rules, and escalation policy. | Reviewed authoring | Discovery shaped |
| EPP-US-081 | Cross-functional program lead | Define a multi-person review and approval process with roles, deadlines, escalation, rejection, delegation, and immutable decision evidence. | Authority-preserving composition | Discovery shaped |
| EPP-US-082 | Process owner | Compare two process revisions in human-readable and diagram forms and understand changed outcomes, gates, artifacts, bindings, and evidence requirements. | Semantic diff usability | Discovery shaped |
| EPP-US-083 | Process owner | Accept or reject individual bounded AI-proposed changes without accepting unrelated edits or granting execution authority. | Atomic proposal review | Discovery shaped |
| EPP-US-084 | Process administrator | Migrate saved process definitions across compatible versions while keeping historical runs readable and unsupported definitions explicit. | Compatibility and rollback | Discovery shaped |
| EPP-US-085 | Platform integrator | Reuse one approved process with multiple materially different MCP providers and applications without domain, vendor, or benchmark-case branches in the runtime. | Generic conformance | Discovery shaped |

## Wave 6 — Complex customer journeys and qualification discovery

These are deliberately high-level. Their boundaries, safety model, supported environments, oracles, and commercial claims should be refined only after evidence from earlier waves exists.

| ID | Customer archetype | High-level user story | Principal discovery areas | Definition maturity |
|---|---|---|---|---|
| EPP-US-086 | Sheet-metal product company | Progress from text/images and bounded research through an approved design basis, native model, STEP, flat pattern, DXF, manufacturing drawing, RFQ, quote decision, and approved vendor response. | Cross-organization authority, CAD fidelity, drawing/oracle policy, email and procurement evidence | Discovery |
| EPP-US-087 | Additive product studio | Progress from concept images and requirements through reviewed geometry, printable STL, support strategy, slicing, and an approved printer-ready package. | Geometry generation, printability oracle, materials/profiles, artifact lineage | Discovery |
| EPP-US-088 | Additive manufacturing operator | Deliver an approved job to a known printer, authorize physical printing, monitor progress, handle interruption, and retain truthful completion and cleanup evidence. | Physical safety, device identity, human presence, cancellation, failure recovery | Discovery; separate T4 authority required |
| EPP-US-089 | CNC job shop | Progress from customer geometry and requirements through DFM review, setup, tooling, simulation, approved program, quotation, and optional machine handoff. | Postprocessor identity, machine safety, proprietary applications, physical boundary | Discovery |
| EPP-US-090 | Fabrication shop | Progress from a weldment concept through design, cut list, drawings, welding/inspection plan, supplier RFQ, and approved fabrication package. | Welding standards, supplier capabilities, quality records, commercial boundary | Discovery |
| EPP-US-091 | Plastics product company | Progress from product requirements through moldability review, part/tooling concept, analysis, prototype plan, tooling RFQ, and approval. | DFM/oracles, tooling lifecycle, supplier/proprietary systems, cost evidence | Discovery |
| EPP-US-092 | Composites manufacturer | Develop a part definition, material/ply strategy, tooling, layup and cure plan, inspection package, and controlled manufacturing handoff. | Material provenance, process sensitivity, safety, inspection/oracle design | Discovery |
| EPP-US-093 | Electronics product startup | Progress from board and product requirements through enclosure, thermal/EMI considerations, prototype artifacts, sourcing, assembly, and validation planning. | ECAD/MCAD identity, cross-domain checks, supplier data, compliance | Discovery |
| EPP-US-094 | Automation integrator | Develop a robotic or automated workcell concept, layout, fixtures, sequence, safety review, simulation, customer proposal, and deployment plan. | Safety authority, simulation fidelity, controls interfaces, physical deployment | Discovery |
| EPP-US-095 | Controls engineering team | Progress from control requirements and existing-system evidence through logic changes, simulation, review, test, rollback, and an approved release package. | Runtime/PLC identity, safety state, test environment, deployment authority | Discovery |
| EPP-US-096 | Factory maintenance organization | Progress from an equipment incident through diagnosis, approved inspection, parts/tool planning, repair work order, execution evidence, and return-to-service review. | Safety isolation, technician authority, inventory/vendor systems, physical confirmation | Discovery |
| EPP-US-097 | Field quality organization | Progress from field inspection through evidence capture, nonconformance, containment, root-cause work, corrective action, verification, and customer disposition. | Mobile/offline evidence, identity, regulatory retention, customer communication | Discovery |
| EPP-US-098 | Regulated product organization | Progress an engineering change through impact analysis, verification, documentation, required approvals, compliance submission, release, and audit package. | Jurisdiction-specific policy, signatures, retention, claims and audit evidence | Discovery |
| EPP-US-099 | New-product introduction team | Coordinate design maturity, manufacturing readiness, quality planning, sourcing, supplier approvals, pilot evidence, issue closure, and production-release review. | Multi-party WIP, supplier boundaries, evidence scale, schedule and commercial claims | Discovery |
| EPP-US-100 | Configure-to-order manufacturer | Turn sales-approved requirements into a valid product configuration, engineering artifacts, quotation, customer approval, manufacturing package, and governed order handoff. | Configuration rules, pricing/commitment authority, ERP/PLM boundaries, variant qualification | Discovery |

## First implementation-learning tranche

The first automated learning loop should use `EPP-US-001` through `EPP-US-005` as one composable chain while preserving each story's independent acceptance:

1. validate each story and artifact contract at `T0`;
2. run frozen positive, missing-input, contradiction, rejected, revise, and stale-subject fixtures at `T1`;
3. render the process and exact results read-only;
4. record immutable step, artifact, review, and recovery evidence;
5. measure completion, comprehension, error detection, revision success, and accessibility;
6. revise the canonical process model only from observed evidence; and
7. promote no live/MCP claim until a later exact binding and execution gate passes.

After that chain is stable, `EPP-US-006` through `EPP-US-010` broaden the inputs and customer archetypes without requiring live engineering applications. Their evidence should determine which Wave 2 stories are specified next rather than committing now to a fixed implementation order for all remaining stories.
