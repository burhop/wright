# Feature Specification: Rivet Engineering Scenario Harness

**Feature Branch**: `codex/rivet-engineering-program` (feature identity: `070-engineering-scenario-harness`)

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Build a growing suite of meaningful Rivet engineering tests that use multiple workspace MCPs across CAD, ECAD, FEA, CFD, Python, CAM, Grasshopper, and additive manufacturing, with engineering-valid results and high usability."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run curated multi-domain engineering scenarios (Priority: P1)

An engineer opens a scenario library in Wright, chooses a curated engineering example, reviews the participating MCP capabilities and expected artifacts, and runs the scenario through Rivet. The result explains whether the engineering checks passed, not merely whether every software call returned successfully.

**Why this priority**: The harness is valuable only when it proves that Rivet can coordinate multiple engineering domains and produce trustworthy, inspectable outcomes.

**Independent Test**: Run each of the three Tier 1 scenarios against deterministic fake MCP servers through the workspace gateway and verify the expected artifacts, engineering invariants, provenance, and cleanup without credentials, network access, paid software, GPUs, or physical equipment.

**Acceptance Scenarios**:

1. **Given** the structural bracket scenario, **When** it runs, **Then** CAD geometry, Python-derived mass properties, and FEA results traverse at least two independent MCP servers and pass unit-aware geometry, mass, displacement, and stress checks.
2. **Given** the electronics enclosure scenario, **When** it runs, **Then** ECAD board-envelope data, CAD enclosure geometry, CFD thermal results, and a Python margin calculation traverse multiple MCPs and pass clearance, temperature, convergence, and margin checks.
3. **Given** the parametric manufacturing scenario, **When** it runs, **Then** Grasshopper-style parameter-tree data produces manufacturing geometry, a 3MF/slicer result, and statically linted CAM output without authorizing or commanding physical motion, heat, extrusion, a spindle, or a machine controller.
4. **Given** a scenario is selected, **When** the engineer reviews it before execution, **Then** Wright shows its domains, tier, expected capabilities, estimated local resource class, required optional dependencies, safety boundary, and output assertions.
5. **Given** a Tier 1 scenario and a clean local Wright installation, **When** it runs repeatedly, **Then** it produces the same normalized pass/fail result and stable artifact digests except for explicitly excluded time and trace fields.

---

### User Story 2 - Diagnose an engineering failure precisely (Priority: P1)

When a scenario fails, an engineer sees the exact workflow node, namespaced MCP capability, artifact, engineering invariant, expected range or relationship, observed value, units, and recovery guidance. Transport, policy, tool, artifact, and engineering-validation failures are distinguished.

**Why this priority**: A generic "workflow failed" message is not useful for engineering validation and makes multi-tool failures expensive to investigate.

**Independent Test**: Inject deterministic faults for a missing capability, unit mismatch, invalid artifact, non-converged analysis, failed numerical bound, policy denial, and residue; verify each report names the correct node/capability and violated invariant without leaking secrets or raw local paths.

**Acceptance Scenarios**:

1. **Given** a child MCP returns millimetres where metres are declared, **When** an assertion evaluates the artifact, **Then** the run fails with a unit incompatibility attributed to that artifact and node rather than silently converting an undeclared value.
2. **Given** an FEA or CFD output is syntactically valid but not converged, **When** the scenario completes, **Then** the analysis invariant fails even though the tool call succeeded.
3. **Given** an assertion value is outside tolerance, **When** the report is opened, **Then** it shows the normalized observed value, expected rule, tolerance, source artifact, and correlated call provenance.
4. **Given** a capability is missing or denied, **When** execution is attempted, **Then** no downstream child call is made and the report identifies the unmet capability and a safe recovery action.
5. **Given** a report contains child-supplied text, **When** it is stored or displayed, **Then** it is bounded and redacted and cannot inject executable UI content.

---

### User Story 3 - Inspect reproducible evidence and compare runs (Priority: P2)

An engineer or maintainer can inspect a scenario run from the scenario level down to workflow nodes, MCP calls, normalized artifacts, assertions, and cleanup. The record contains enough exact provenance to reproduce the result or explain why a later run differs.

**Why this priority**: Engineering examples become useful regression tests only when their inputs, implementations, units, tolerances, and evidence are versioned and comparable.

**Independent Test**: Complete a passing run and a deliberately failing run, reload Wright, inspect both reports, and compare their exact scenario, workflow, capability, fixture, artifact, assertion, and environment identities.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** its evidence is inspected after restart, **Then** it retains scenario and workflow revisions, exact capability bindings, child call identities, fixture revisions, normalized artifact digests, assertion definitions and outcomes, timestamps, and cleanup status.
2. **Given** two runs of the same scenario, **When** a material input, implementation, schema, fixture, tolerance, or environment classification differs, **Then** the comparison names the changed identity and does not claim strict reproducibility.
3. **Given** a scenario emits multiple artifact types, **When** the report is viewed, **Then** each artifact is labeled by engineering domain, media/schema type, coordinate and unit system, producer node, validation status, and safe vault reference.
4. **Given** a report is exported, **When** another maintainer reviews it, **Then** it contains bounded portable metadata and hashes but no credentials, bearer authority, unrestricted filesystem path, or embedded proprietary payload.

---

### User Story 4 - Extend the harness with deterministic scenarios and assertions (Priority: P2)

A Wright maintainer can add a scenario manifest, reusable fixture behavior, and artifact assertion without building a bespoke test runner. Validation rejects incomplete, unsafe, nondeterministic, or incompatible definitions before they enter the library.

**Why this priority**: The requested test suite must grow across engineering domains without every new example becoming a one-off integration.

**Independent Test**: Add a small test-only scenario using the public manifest and assertion contracts, validate it, run it against deterministic fake MCPs, and confirm an invalid or unsafe variant is rejected with field-level guidance.

**Acceptance Scenarios**:

1. **Given** a new manifest, **When** it is validated, **Then** required domains, capabilities, tiers, resources, safety constraints, workflow identity, artifact contracts, assertions, timeouts, and cleanup rules are checked before publication.
2. **Given** a reusable fake MCP fixture, **When** it is configured for success, delay, malformed output, unit mismatch, or deterministic failure, **Then** it exposes the same namespaced discovery and gateway execution boundary as ordinary workspace MCPs.
3. **Given** an assertion plugin receives an unknown schema version or incompatible unit dimension, **When** it evaluates an artifact, **Then** it fails closed with a stable reason code.
4. **Given** third-party sample data or fixtures are added, **When** the catalog is validated, **Then** source, license, redistribution status, and modification notice are recorded; generated Wright-owned fixtures require an explicit provenance declaration.
5. **Given** a scenario requests network, credentials, proprietary applications, GPU, excessive resources, or hardware, **When** it is classified, **Then** it cannot be placed in Tier 1 and cannot run without an explicit higher-tier opt-in.

---

### User Story 5 - Run selected clean-container integrations safely (Priority: P3)

A maintainer can select eligible Tier 2 scenarios that exercise real public MCP packages in disposable clean containers. The harness records whether the integration is runnable, partially runnable, blocked, or failed, while preserving the same scenario and evidence model used by Tier 1.

**Why this priority**: Deterministic doubles prove Wright's control plane, while bounded real-package probes provide evidence that selected ecosystem integrations actually initialize and behave as expected.

**Independent Test**: Run one explicitly selected, credential-free public MCP probe in a disposable clean container, retain bounded gateway evidence and cleanup status, and verify that unavailable credentials or applications produce a classified skip/block rather than a normal-test failure.

**Acceptance Scenarios**:

1. **Given** a catalog entry is confirmed and platform-compatible, **When** a Tier 2 scenario is selected, **Then** it uses the documented clean-container process and records catalog revision, package identity, platform, installation command digest, discovered capability digest, and cleanup.
2. **Given** the required application or credential is absent, **When** preflight runs, **Then** the scenario is classified as blocked or skipped with an actionable reason and does not prompt, download large assets unexpectedly, or mutate the host.
3. **Given** a candidate is only a hosted/API-wrapper candidate or watchlist entry, **When** it is selected, **Then** Wright refuses to present it as a confirmed runnable MCP.
4. **Given** a disposable integration run ends, **When** cleanup completes or times out, **Then** the report states whether processes, containers, files, or other bounded residue remain.

### Edge Cases

- A scenario manifest is valid structurally but references an unavailable, ambiguous, disabled, or schema-changed workspace capability.
- Two artifact producers use different length, temperature, angle, force, pressure, or mass units, or omit a coordinate system or unit declaration.
- Floating-point values differ only within a declared absolute/relative tolerance, contain NaN/infinity, or cross a dimensional boundary.
- CAD meshes are empty, non-finite, degenerate, non-manifold, or have an unexpected bounding box, volume, or mass relationship.
- ECAD files have invalid headers, missing layers/nets, implausible board thickness, or board/enclosure coordinate-frame disagreement.
- FEA/CFD results are present but incomplete, non-converged, physically implausible, or reference an input mesh digest different from the upstream artifact.
- Grasshopper-style data trees preserve values but change branch paths or topology.
- 3MF/slicer artifacts have missing units, invalid package relationships, empty build items, unsafe printer instructions, or inconsistent volume estimates.
- CAM text contains an unsupported dialect, ambiguous units, an uncontrolled coordinate change, machine-control codes, or physical-actuation intent.
- A child returns an oversized, secret-like, HTML/script-bearing, unsupported, or path-traversal artifact reference.
- A run is cancelled during an assertion, a child call returns late, Wright restarts, or cleanup leaves bounded residue.
- Tier 2 installation would require credentials, a license acceptance, a large download, host software, a GPU, or a platform not declared compatible.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST provide a catalog of versioned engineering scenario manifests that can be listed, inspected, validated, and run from the Rivet experience.
- **FR-002**: Every scenario manifest MUST declare a stable identifier and revision, title, purpose, engineering domains, test tier, resource class, expected duration, workflow identity, capability requirements, inputs, artifacts, assertions, safety constraints, environment guards, timeouts, cleanup rules, and provenance/license metadata.
- **FR-003**: The initial Tier 1 catalog MUST include at least three independently runnable multi-MCP scenarios: structural bracket, electronics enclosure cooling, and parametric manufacturing.
- **FR-004**: The initial Tier 1 scenarios collectively MUST exercise CAD, ECAD, FEA, CFD, personal Python computation, CAM, Grasshopper-style parametric data, 3D-printing packaging, and slicing concepts.
- **FR-005**: Every Tier 1 scenario MUST call at least two independently registered deterministic MCP servers through the Wright workspace gateway and existing Rivet binding, review, authority, policy, approval, progress, cancellation, audit, and evidence boundaries.
- **FR-006**: The harness MUST NOT create a direct Rivet-to-child-MCP connection or embed child commands, URLs, credentials, environment variables, or lifecycle configuration in scenario manifests.
- **FR-007**: Scenario preflight MUST resolve exact current capability bindings and MUST block missing, ambiguous, disabled, incompatible, unreviewed, cross-workspace, or stale bindings before child invocation.
- **FR-008**: Deterministic fake engineering MCPs MUST support namespace-qualified discovery and configurable success, delay, malformed artifact, unit mismatch, domain failure, cancellation, and cleanup outcomes through the same gateway boundary.
- **FR-009**: Fake MCP outputs MUST be deterministic for a scenario revision and seed, and any intentionally variable fields MUST be declared and excluded from strict digest comparison.
- **FR-010**: The harness MUST define versioned normalized artifact envelopes carrying domain, artifact type/schema and version, declared units and coordinate system where applicable, producer node/call, source-input digests, content or vault reference, content digest, and validation status.
- **FR-011**: Raw child filesystem paths, unrestricted resource URIs, bearer authority, credentials, and unvalidated artifact claims MUST NOT be accepted as scenario artifacts.
- **FR-012**: The harness MUST provide versioned assertion plugins for structured numeric values, dimensional units, tabular data, meshes/geometry, ECAD board data, FEA results, CFD results, Grasshopper-style data trees, 3MF/additive packages, slicer summaries, and static CAM/G-code lint.
- **FR-013**: Assertions MUST support exact, set-membership, range, monotonic, relational, absolute tolerance, and relative tolerance rules as applicable, while rejecting undeclared unit conversion and NaN/infinite values unless explicitly allowed by a domain contract.
- **FR-014**: Geometry checks MUST support finite/non-empty geometry, coordinate and unit declaration, bounds, vertex/face counts, degeneracy, manifoldness where required, volume, surface area, mass-property relationships, and upstream digest correlation.
- **FR-015**: ECAD checks MUST support a recognized board schema/header, declared dimensions and units, board thickness, layer/net presence, component envelope and keep-out/clearance relationships, and upstream digest correlation.
- **FR-016**: FEA and CFD checks MUST distinguish solver/tool completion from engineering validity and support convergence, result completeness, finite values, expected sign/range, tolerance, conservation or residual limits, and mesh/input digest correlation.
- **FR-017**: Grasshopper-style data-tree checks MUST retain branch paths, branch ordering where material, item counts, value types, and topology rather than comparing only flattened values.
- **FR-018**: Additive checks MUST validate a recognized 3MF package/core structure, units, mesh/build objects, referenced components/materials where used, and bounded slicer summary values without requiring a printer profile or executing printer commands.
- **FR-019**: CAM/G-code checks MUST be static only, MUST require a declared dialect and units, and MUST reject physical-actuation intent, machine-control codes, unsafe or ambiguous modal state, and any attempt to send output to machinery.
- **FR-020**: Every assertion failure MUST identify the scenario, workflow node, namespaced capability, artifact, invariant identifier, expected rule/tolerance, observed normalized value, units, and stable failure category/reason code.
- **FR-021**: Reports MUST distinguish preflight, policy/approval, transport, MCP/tool, artifact-contract, engineering-assertion, timeout/cancellation, and cleanup/residue failures.
- **FR-022**: Scenario runs MUST preserve exact scenario, workflow, graph, capability binding, schema, catalog, fixture, artifact, assertion, environment, policy/approval, child-call, timing, terminal-state, cancellation, and cleanup identities in durable bounded evidence.
- **FR-023**: Scenario reports MUST be inspectable after restart and exportable as bounded portable metadata and hashes without secrets, reusable authority, raw host paths, or proprietary artifact payloads.
- **FR-024**: Run comparison MUST identify material changes in scenario, workflow, bindings, schemas, fixtures, inputs, assertions/tolerances, artifacts, and environment before claiming strict reproducibility.
- **FR-025**: Scenario listing, preflight, progress, cancellation, report, and recovery states MUST be available through thin provider-neutral Wright APIs and usable from the existing Rivet workflow UI.
- **FR-026**: The UI MUST explain domains, participating capabilities, tier, optional dependencies, resource/expected-duration class, safety boundary, artifacts, assertion status, and actionable recovery in engineering-oriented plain language.
- **FR-027**: A scenario definition MUST fail validation when required metadata, contracts, safety constraints, cleanup, or provenance/license information is missing or incompatible.
- **FR-028**: Reusable fixture/sample data MUST declare whether it is Wright-generated or third-party; third-party content MUST record source, license, redistribution status, and modification notice.
- **FR-029**: Tier 1 normal tests MUST run offline with bounded local CPU, memory, disk, and time and MUST NOT require network access, credentials, paid/proprietary applications, GPUs, hardware, large downloads, or interactive prompts.
- **FR-030**: Any scenario requiring network, credentials, proprietary applications, GPU, large assets, or external services MUST be Tier 2 or Tier 3, explicitly selected, guarded by preflight, and excluded from normal gates.
- **FR-031**: Tier 2 public MCP validation MUST follow the repository clean-container process and record catalog entry/revision, platform, package/container identity, installation evidence, discovery digest, gateway evidence, result classification, and cleanup/residue.
- **FR-032**: Catalog states for confirmed MCPs, hosted/API-wrapper candidates, and watchlist/no-public-MCP entries MUST remain distinct; only eligible confirmed entries may be represented as directly runnable public MCP integrations.
- **FR-033**: Environment guards MUST fail closed before installation or execution and MUST never silently add MCP-specific host software, accept a license, prompt for secrets, download large model/application assets, or mutate a developer's global environment.
- **FR-034**: Cancellation MUST propagate through the existing Rivet/Wright gateway path, prevent later nodes and late results from publishing success, and record cleanup or bounded residue truthfully.
- **FR-035**: Existing non-scenario Rivet workflows and clients MUST retain their current behavior and must not gain broader MCP authority from the harness.
- **FR-036**: No scenario, assertion, fixture, optional integration, or test may start or command physical machinery, motion, heat, a spindle, extrusion, a printer, a robot, or a PLC.
- **FR-037**: Scenario validation and execution MUST reject child-supplied executable markup, traversal paths, unbounded payloads, secret-like values, and unsupported schema versions with stable reason codes.

### Non-Functional Requirements

- **NFR-001**: On a reference local development machine, listing 100 cached scenario summaries MUST complete in under 300 milliseconds, manifest validation in under 500 milliseconds, and report loading for 1,000 bounded events/assertions in under one second at the 95th percentile, excluding child MCP execution.
- **NFR-002**: Every evidence field and artifact preview MUST have an authoritative size/count ceiling; a single event remains at or below the existing 64 KiB ceiling and terminal run output remains at or below the existing 1 MiB ceiling unless a separately reviewed limit replaces them.
- **NFR-003**: Given the same scenario revision, deterministic fixture revisions, seed, normalized inputs, and implementation identities, Tier 1 runs MUST yield identical assertion outcomes and artifact content digests across supported local platforms, excluding declared nondeterministic metadata.
- **NFR-004**: Scenario library, preflight, progress, failure, assertion, evidence, and cancellation UI MUST be keyboard operable, usable at 320 CSS pixels and 200% zoom, convey status with text in addition to color, manage focus, and produce no serious or critical automated accessibility findings in deterministic journey tests.
- **NFR-005**: Cancellation MUST reach the active local gateway child call within one second in deterministic tests, and normal Tier 1 cleanup MUST finish within five seconds or report explicit residue.
- **NFR-006**: Manifest, artifact, assertion, and report contracts MUST use explicit schema versions and reject unsupported breaking versions rather than guessing or partially evaluating them.

### Key Entities

- **Scenario Manifest**: The immutable, versioned definition of an engineering example, including its workflow, domains, tier, capability needs, inputs, outputs, assertions, resources, safety, environment, cleanup, and provenance.
- **Scenario Catalog Entry**: A bounded summary used to browse and select a published scenario and identify its manifest revision and availability state.
- **Scenario Run**: One exact execution of a scenario bound to a workspace, workflow revision, capability set, environment classification, and run manifest.
- **Normalized Artifact Envelope**: A typed, hashed, unit- and coordinate-aware record that connects a child result or vault artifact to its producer and upstream inputs.
- **Engineering Assertion Definition**: A versioned invariant, expected relationship, tolerance, applicability, and failure guidance applied to one or more normalized artifacts.
- **Engineering Assertion Result**: The pass, fail, skip, or error evidence containing normalized observations, units, expected rule, source identities, and reason code.
- **Fixture Profile**: A deterministic fake MCP behavior revision and seed, including supported capabilities and configured success or fault outcomes.
- **Environment Guard**: A preflight rule that classifies resource, platform, application, credential, network, and hardware requirements before execution.
- **Scenario Report**: The durable bounded hierarchy connecting a scenario to workflow nodes, gateway calls, artifacts, assertions, timing, cancellation, cleanup, and recovery.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can select, preflight, run, and understand a passing Tier 1 engineering scenario in under five minutes without configuring child MCP connections inside Rivet.
- **SC-002**: At least three Tier 1 scenarios each invoke two or more independent deterministic MCP servers through Wright, and together cover all nine requested engineering areas: CAD, ECAD, FEA, CFD, Python, CAM, Grasshopper, 3D printing, and slicing.
- **SC-003**: In deterministic negative tests, 100% of injected missing-capability, unit, schema, convergence, numeric-bound, policy, cancellation, and cleanup failures are attributed to the correct node/capability and violated invariant category.
- **SC-004**: Repeated Tier 1 runs with identical material identities produce identical normalized artifact digests and assertion outcomes on supported platforms, excluding explicitly declared time and trace fields.
- **SC-005**: 100% of normal harness tests complete without credentials, network access, proprietary/paid applications, GPUs, physical hardware, large downloads, global-environment mutation, or interactive prompts.
- **SC-006**: Every completed, failed, cancelled, or blocked run retains exact workflow/capability provenance, bounded artifact/assertion evidence, and truthful cleanup/residue status after application restart.
- **SC-007**: A maintainer can add and validate a deterministic test scenario using documented manifest, fixture, and assertion contracts without modifying the core runner, and invalid/unsafe definitions fail with field-specific guidance.
- **SC-008**: Selected Tier 2 probes use clean containers, preserve confirmed/candidate/watchlist catalog distinctions, and leave no unreported host or container residue.
- **SC-009**: Automated accessibility checks report no serious or critical findings for the scenario library, preflight, progress, and report journeys.

## Assumptions

- Loop 069's workspace MCP gateway, reviewed capability bindings, run authority, progress, cancellation, and evidence model are the required execution boundary and are not replaced by this harness.
- Tier 1 domain outputs are compact, Wright-generated deterministic fixtures shaped from public engineering file-format conventions; they are test evidence, not certified solver or manufacturing results.
- Unit normalization uses SI as the canonical comparison basis while retaining original declared units; undeclared or dimensionally incompatible conversion fails closed.
- The initial scenario UI extends Wright's existing Rivet workflow panel rather than embedding a second test application.
- Artifact payloads remain in Wright-authorized storage; reports carry bounded previews, metadata, and hashes.
- Optional real MCP probes are validation evidence, not prerequisites for completing normal product tests or for claiming that a proprietary engineering application is installed.
- CAM and additive outputs are analyzed statically only; execution, transfer to equipment, and machine control are out of scope.
- Scenario authors are trusted repository contributors, but manifests and child outputs are still treated as untrusted data at runtime.

## Out of Scope

- Certifying numerical accuracy of a commercial CAD/CAE/CAM solver or qualifying results for production engineering release.
- Running proprietary applications, paid hosted APIs, credentialed services, large local models, GPUs, or physical equipment in normal tests.
- Controlling CNC machines, printers, robots, PLCs, spindles, heaters, motion systems, or other physical devices.
- Replacing the Engineering MCP Catalog or adding unconfirmed hosted/API-wrapper candidates as if they were public MCP servers.
- General-purpose visual workflow authoring changes unrelated to engineering scenario selection, execution, or evidence.
- Local model discovery, installation, or runtime management, which is covered by later program loops.
