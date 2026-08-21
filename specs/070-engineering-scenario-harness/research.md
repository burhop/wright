# Research: Rivet Engineering Scenario Harness

## Scope and method

Research focused on primary format/standards sources and the existing Wright/Rivet implementation. The objective was not to reproduce full CAD/CAE parsers; it was to select compact, deterministic invariants that demonstrate multi-MCP engineering validity while remaining offline, redistribution-safe, and hardware-safe.

## Decision 1: Versioned manifest and artifact vocabulary

**Decision**: Use one Wright-owned scenario manifest schema and one normalized artifact envelope. Each artifact retains its source media/schema/version, units, coordinate system, producer call, input hashes, content hash, and bounded payload or authorized vault reference.

**Rationale**: CAD, ECAD, CAE, parametric, additive, and CAM files differ substantially. A normalized envelope supplies common provenance without pretending that one geometry schema can replace native formats. Explicit versions let unknown/breaking contracts fail closed.

**Alternatives rejected**:

- Store arbitrary child JSON: lacks shared provenance, unit, bounds, and schema guarantees.
- Convert every format to one mesh: loses ECAD topology, CAE convergence, parametric tree topology, materials, and manufacturing semantics.
- Embed full artifacts in reports: breaks size, licensing, and sensitive-data boundaries.

## Decision 2: Unit policy

**Decision**: Retain original units, require their declaration for dimensional values, normalize comparable values to SI, and reject unknown or dimensionally incompatible conversions.

**Evidence**: The BIPM SI Brochure defines the International System of Units, coherent derived units, and canonical symbols ([BIPM SI Brochure, 9th edition](https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf/2d2b50bf-f2b4-9661-f402-5f9d66e4b507)).

**Rationale**: A deterministic harness must detect the classic metre/millimetre and Celsius/Kelvin boundary errors. Silent inference can turn a syntactically valid workflow into a physically meaningless result.

**Alternatives rejected**:

- Compare raw numeric values: fails whenever tools use different but compatible units.
- Assume common engineering defaults: unsafe and nondeterministic across applications and locales.
- Pull in a large general unit library immediately: unnecessary for the bounded initial dimensions and increases packaged dependencies; the public contract leaves room for replacement later.

## Decision 3: ECAD invariants

**Decision**: The deterministic ECAD artifact represents a bounded KiCad PCB-derived summary and validates recognized header/version, millimetre coordinates, board thickness/dimensions, layers, nets, component envelopes, and clearance relationships.

**Evidence**: KiCad documents UTF-8 S-expression formats and common syntax ([KiCad S-expression introduction](https://dev-docs.kicad.org/en/file-formats/sexpr-intro/index.html)); the PCB format specifies the `kicad_pcb` root, version/generator fields, general thickness, layers, nets, and coordinates in millimetres ([KiCad PCB format](https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/)).

**Rationale**: These properties are sufficient to prove ECAD-to-CAD enclosure handoff and detect unit/frame/clearance regressions without packaging a full KiCad parser or third-party board.

## Decision 4: FEA and CFD validity differs from tool completion

**Decision**: Solver artifacts include input mesh/content hashes, convergence state/history, finite result fields, and selected engineering quantities. Assertions independently evaluate convergence, completeness, bounds, conservation/residuals, and upstream correlation.

**Evidence**: CalculiX documents FRD as the results format used to access prior-calculation results including displacements and stresses ([CalculiX GraphiX manual](https://dhondt.de/cgx_2.19.pdf)). SU2 documents history, surface, restart, mesh, and visualization outputs plus convergence/history fields ([SU2 custom output](https://su2code.github.io/docs_v7/Custom-Output/)).

**Rationale**: A solver can exit normally while a computation is unconverged or correlated to the wrong input. Engineering validity must therefore be a separate assertion phase.

**Alternatives rejected**:

- Treat process exit zero as pass: misses non-convergence and incomplete results.
- Compare full vendor result files byte-for-byte: brittle, large, platform-dependent, and poorly diagnostic.

## Decision 5: Grasshopper-style parametric topology

**Decision**: Represent parametric inputs/outputs as typed data-tree branches with integer paths and ordered items; assert branch topology as well as values.

**Evidence**: Rhino documents that Grasshopper data is stored in tree structures and branch paths are ordered integer indices in braces ([Grasshopper advanced data structures](https://developer.rhino3d.com/guides/grasshopper/gh-algorithms-and-data-structures/advanced-data-structures/), [The why and how of data trees](https://developer.rhino3d.com/en/guides/grasshopper/the-why-and-how-of-data-trees/)).

**Rationale**: Flattening can preserve values while changing which component/branch they belong to, which materially changes downstream geometry.

## Decision 6: 3MF and slicing invariants

**Decision**: Use a small Wright-generated 3MF fixture and validate OPC/package structure, declared units, meshes, build items, references, finite coordinates, non-empty/valid triangles, and a bounded slicer summary. Never execute or transfer printer instructions.

**Evidence**: The 3MF Consortium publishes royalty-free core and extension specifications for units, meshes, materials, components, build items, and slices ([3MF specifications](https://3mf.io/spec/), [3MF Core Specification 1.3](https://3mf.io/spec/core-v1-3-0/)).

**Rationale**: 3MF provides an open, structured additive artifact with explicit units and packaging relationships. Static validation demonstrates design-to-print preparation without a printer, vendor slicer, or uncontrolled profile.

**Alternatives rejected**:

- STL only: no standard unit declaration and insufficient packaging/material semantics.
- Run a full slicer in normal tests: adds large platform-specific binaries and unstable profile/output dependencies.

## Decision 7: CAM is static lint only

**Decision**: The initial CAM artifact is a bounded RS274-style text summary with an explicit dialect and unit mode. Assertions reject physical actuation intent, machine-control/spindle/coolant/tool-change codes, ambiguous modal state, unsupported constructs, and non-finite/out-of-bounds coordinates. It is never sent to equipment.

**Evidence**: NIST publishes the RS274/NGC interpreter specification and reference implementation as a canonical G-code dialect ([NIST RS274NGC Interpreter Version 3](https://www.nist.gov/publications/nist-rs274ngc-interpreter-version-3)).

**Rationale**: Static syntax/modal checks add manufacturing coverage while preserving the constitution's manual hardware gate and program Gate E.

## Decision 8: Deterministic fake MCP architecture

**Decision**: Tests start multiple independent stdio MCP fixture processes that implement normal initialization/discovery/call/cancellation. Scenario graphs bind static namespace-qualified tools and execute through the Loop 069 injected Wright provider and gateway.

**Rationale**: In-process mocks could prove assertions but not Rivet/gateway behavior. Distinct child processes prove namespace collisions, binding, authority, ordering, progress, cancellation, result limits, audit, and cleanup with no external dependency.

**Alternatives rejected**:

- One fake server with many domains: does not prove multi-MCP coordination or namespace isolation.
- Live vendor tools in normal tests: nondeterministic and blocked by platforms, licenses, credentials, hardware, and cost.
- Rivet direct child launch: duplicates MCP ownership and bypasses Wright policy/lifecycle boundaries.

## Decision 9: Test tier and environment guards

**Decision**: Tier 1 is deterministic/offline/bounded. Tier 2 is an explicitly selected disposable clean-container public MCP probe. Tier 3 is credentialed, proprietary, GPU, hardware, or manual evidence. Guard classification happens before install/start and records `ready`, `blocked`, or `skipped`.

**Rationale**: This matches the repository MCP validation process, prevents hidden host mutation, and preserves the catalog distinction between confirmed MCPs, API-wrapper candidates, and watchlist entries.

**Initial Tier 2 candidates**: NVIDIA Elements and official Ansys PyFluent have current clean-container initialization/tool-list evidence. They remain partial until Wright/Hermes gateway proxy validation; Omniverse remains credential-blocked. Community Ansys/COMSOL entries with current SDK incompatibilities are failure/compatibility evidence, not Tier 1 dependencies.

## Decision 10: UI placement

**Decision**: Add scenario discovery/preflight/report sections to the existing Rivet workflows panel and service client.

**Rationale**: Engineering users should not learn a second runner. The existing panel already owns review, run, progress, cancellation, history, and evidence, so scenario UI can provide curated entry and engineering interpretation while reusing those controls.

**Alternatives rejected**:

- Separate test application: duplicates workflows, navigation, and state.
- Hide scenarios as ordinary workflow templates only: cannot communicate tier, domains, resource/safety guards, artifact contracts, and engineering assertion results.
