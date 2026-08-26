# Implementation Plan: Engineering Workflow Prototype

**Branch**: `076-engineering-workflow-prototype` | **Date**: 2026-08-24 | **Spec**: `specs/076-engineering-workflow-prototype/spec.md`

**Input**: Feature specification and postmortem evidence for an engineer-readable, disposable workflow prototype.

## Summary

Build a checkpointed prototype that tests whether Wright can present engineering work as understandable phase lanes, reviewable artifacts, gates, feedback loops, approvals, and notifications while retaining provider-neutral LLM and generic MCP integration.

The prototype will not reimplement or fork Rivet and will not introduce CAD-, FEA-, manufacturing-, supplier-, or other domain-specific runtime services. A versioned Wright workflow specification is canonical. Candidate graph libraries are replaceable view/interaction adapters. LLMs propose validated atomic changes with a preview/accept boundary. MCP actions bind exact workspace catalog tools and invoke them only through the existing governed gateway.

Progress is intentionally incremental: establish a baseline, make the target UI concrete with a reusable read-only visual slice, run a shallow three-candidate graph bakeoff around that visual contract, wire the selected canvas adapter, add typed manual editing, add generic MCP binding, add LLM authoring, integrate the reference story, and then write an evidence-backed architecture decision. Each major checkpoint is independently reviewable and can result in continue, change, stop, or defer.

## Discovery Operating Mode

This branch exists to reduce ambiguity before Wright commits to a production
architecture. It is an experimental notebook with executable examples, not a
production implementation in progress. Code quality must be sufficient to make
results credible, but a working prototype behavior is not automatically a
recommended product design.

Every increment and every future agent working on this branch must:

1. name the ambiguity or question being tested;
2. state a falsifiable hypothesis and the smallest useful experiment;
3. identify what is deliberately excluded from the experiment;
4. record the observed result, including confusing or failed behavior;
5. distinguish evidence from inference and provisional choices from decisions;
6. update `evidence/prototype-lessons-learned.md` and, for material
   experiments, add a focused evidence note; and
7. leave an explicit remaining-question list and a keep, revise, or discard
   recommendation.

Do not broaden an experiment merely to make the prototype appear complete.
Shared API changes, schemas, fixtures, executor behavior, and UI conventions
on this branch are spike evidence until a later production specification and
architecture review accepts them. A later implementation may replace all
prototype code while retaining the lessons, contracts, tests, and examples.

## Technical Context

**Language/Version**: TypeScript 6 and React 19.2 in `apps/web`; existing Python/FastAPI services remain unchanged unless CP4 proves a narrowly scoped generic API gap.
**Primary Dependencies**: Existing React Router, Zod, Vitest, Testing Library, Playwright, Wright design tokens, workspace service client, MCP catalog/gateway, approvals, artifacts, and evidence APIs. Candidate-only dependencies evaluated at CP1B: `@xyflow/react`, Rete.js packages, and LiteGraph.js.
**Storage**: Versioned deterministic TypeScript/JSON fixtures and optional browser-local ephemeral drafts. No SQLite, vault, or production schema migration in the prototype.
**Testing**: Vitest model/component tests, deterministic fake LLM/MCP contract tests, at most three focused Chromium journeys, existing pre-push gate only at accepted push checkpoints.
**Target Platform**: Wright web application in supported desktop browsers; Chromium is the automated prototype browser.
**Project Type**: Existing monorepo web application with established API and package boundaries.
**Performance Goals**: T0 model feedback <=5 seconds; T1 prototype component feedback <=30 seconds; T2 contract suite <=2 minutes; usable pan/select/open behavior for the 100-block bakeoff fixture.
**Constraints**: Feature-flagged direct route; no production navigation; no Rivet project migration; no candidate-native persistence; no domain-specific executor/service taxonomy; generic MCP gateway only; no model/tool execution without established approval/evidence boundaries; checkpoints remain discardable.
**Scale/Scope**: One fully expressed reference scenario, one early visual contract, three candidate harnesses at CP1B, one selected implementation thereafter, 25- and 100-block evaluation fixtures, three structurally different MCP contract fixtures, at least 20 LLM proposal fixtures, and no more than three browser journeys.

## Constitution Check

_GATE: Must pass before implementation research is accepted and be rechecked after CP1B selection and CP4 integration._

| Principle                             | Plan response                                                                                                                                                                                       | Status |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| Modular monorepo and clean boundaries | Prototype lives under one isolated web feature. Domain, canvas, services, fixtures, and evaluation code have directed dependencies. Shared production modules are reused through public boundaries. | Pass   |
| Provider-neutral agents               | The LLM adapter accepts/returns a provider-neutral authoring contract. Deterministic fixtures are primary; a configured provider is optional.                                                       | Pass   |
| Offline-first behavior                | All required acceptance work runs with local fixtures. Live LLM/MCP demonstrations are optional additions.                                                                                          | Pass   |
| MCP-first tool integration            | The prototype binds existing generic catalog tools and invokes through the governed gateway. It adds no engineering-tool wrappers.                                                                  | Pass   |
| Data and artifact governance          | Real calls preserve existing workspace scope, approval, artifact, and evidence behavior. Local drafts contain no secrets or production data.                                                        | Pass   |
| Testing pyramid                       | Most behavior is covered by model/component/contract tests; browser tests are capped at three cross-boundary journeys.                                                                              | Pass   |
| UI design discipline                  | Custom blocks/panels use Wright tokens, Atomic Design-compatible components, keyboard/focus behavior, and accessible labels.                                                                        | Pass   |
| Manual lifecycle review               | CP1, CP2, CP4, CP5, CP6, and CP7 require recorded human review.                                                                                                                                     | Pass   |
| Plan approval before implementation   | This plan produces no product code or dependency installation until the user approves implementation/next checkpoint.                                                                               | Pass   |
| Phase isolation                       | Each checkpoint has a bounded hypothesis, evidence artifact, exit criteria, and stop option.                                                                                                        | Pass   |

No constitution violation is currently planned. If CP4 requires a new API, work pauses for a plan amendment proving it is a generic platform gap rather than a domain-specific endpoint.

## Project Structure

### Documentation for this feature

```text
specs/076-engineering-workflow-prototype/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── authoring-command.md
│   ├── canvas-adapter.md
│   ├── capability-template.md
│   ├── checkpoint-evidence.md
│   ├── generic-mcp-binding.md
│   └── workflow-spec.md
├── checklists/
│   └── requirements.md
└── evidence/                         # Created checkpoint by checkpoint
    ├── prototype-lessons-learned.md  # Living cross-checkpoint findings
    ├── cp0-baseline.md
    ├── cp1-canvas-bakeoff.md
    ├── cp2-static-usability.md
    ├── cp3-editing.md
    ├── cp3e-workflow-code-roundtrip.md
    ├── cp3f-run-observability.md
    ├── cp3g-headless-four-block.md
    ├── cp3h-ui-execution-projection.md
    ├── cp3i-output-delivery.md
    ├── cp3j-artifact-rail-concept.md
    ├── cp3j-artifact-rail-concept.png
    ├── cp3o-block-interface-and-composition-research.md
    ├── cp4-generic-mcp.md
    ├── cp5-llm-authoring.md
    ├── cp6-integrated-scenario.md
    └── cp7-architecture-decision.md
```

`evidence/prototype-lessons-learned.md` is the durable, living record for
cross-checkpoint usability, execution, diagnostic, architecture, and testing
findings. Each accepted checkpoint updates or explicitly confirms it. CP7 must
disposition every candidate rule and P0/P1 debt item as accepted, revised,
superseded, rejected, or deferred; passing tests alone cannot close a finding.

### Proposed source code

```text
apps/web/src/prototypes/engineering-workflow/
├── domain/
│   ├── workflow-schema.ts
│   ├── workflow-validation.ts
│   ├── workflow-commands.ts
│   ├── workflow-reducer.ts
│   ├── workflow-diff.ts
│   ├── workflow-layout.ts
│   └── *.spec.ts
├── fixtures/
│   ├── drill-bit-holder-workflow.ts
│   ├── scale-workflows.ts
│   ├── generic-mcp-catalog.ts
│   └── llm-authoring-proposals.ts
├── canvas/
│   ├── canvas-adapter.ts
│   ├── react-flow/
│   │   └── ReactFlowBakeoffHarness.tsx
│   ├── rete/
│   │   └── ReteBakeoffHarness.tsx
│   └── litegraph/
│       └── LiteGraphBakeoffHarness.tsx
├── components/
│   ├── EngineeringWorkflowPrototypePage.tsx
│   ├── EngineeringWorkflowCanvas.tsx
│   ├── PhaseLane.tsx
│   ├── EngineeringBlock.tsx
│   ├── BlockDetailsPanel.tsx
│   ├── McpBindingPanel.tsx
│   ├── AuthoringProposalPanel.tsx
│   ├── SemanticDiff.tsx
│   └── RunEvidencePanel.tsx
├── services/
│   ├── authoring-adapter.ts
│   ├── deterministic-authoring-adapter.ts
│   ├── mcp-catalog-adapter.ts
│   ├── mcp-invocation-adapter.ts
│   └── prototype-draft-store.ts
├── evaluation/
│   ├── candidate-rubric.ts
│   ├── candidate-metrics.ts
│   └── usability-script.md
├── feature-flag.ts
└── index.ts

apps/web/src/components/pages/
└── EngineeringWorkflowPrototypeRoute.tsx  # Lazy route boundary only

tests/ui-integration/
└── engineering-workflow-prototype.spec.ts # Maximum three journeys
```

**Structure Decision**: Keep the prototype visibly isolated under `apps/web/src/prototypes` so it can be removed without touching production workflow code. Only the lazy route and feature-flag check live outside that directory. Shared production code may be imported through existing public clients; prototype modules are not imported by production surfaces. Candidate graph packages are referenced exclusively within their individual harness directories at CP1. After selection, rejected harnesses and dependencies are deleted before CP2 unless evidence requires a minimal retained comparison fixture.

## Architecture and dependency rules

```text
React route/components
       │
       ├── CanvasAdapter ── candidate graph library
       │
       ├── Workflow commands/reducer/validation ── canonical Workflow
       │
       ├── AuthoringAdapter ── deterministic fixture or configured LLM
       │                         (proposals only)
       │
       └── GenericMcpAdapter ── existing workspace catalog/governed gateway
                                  (approvals, artifacts, evidence)
```

Dependency rules:

1. Domain modules import no React, graph library, LLM provider, MCP client, or storage implementation.
2. Product components import the common canvas contract, never a candidate package.
3. Canvas adapters receive readonly canonical models and emit Wright intents only.
4. Manual and LLM edits use the same reducer and whole-model validator.
5. LLM adapters never invoke MCP; MCP adapters never interpret authoring prose.
6. MCP adapters contain no tool-name, vendor, domain, or file-format dispatch branches.
7. Real calls use existing catalog, approval, governed invocation, evidence, and artifact boundaries.
8. No prototype module is a prerequisite for an existing Wright route.

## UI concept to prove

The canvas uses horizontal process flow within configurable vertical phase lanes. Each block has a consistent anatomy:

- role icon and plain-language title;
- short purpose/status summary;
- labeled input/output ports with artifact or data cues;
- optional exact MCP binding indicator;
- human/LLM/MCP provenance cue;
- approval, evidence, warning, or stale-binding state;
- accessible selection and keyboard affordances.

The small role vocabulary controls shape/accent, while phase controls lane/background. Status uses an independent indicator so color is not overloaded. Connections distinguish data/control/feedback by line treatment and label, not color alone. Selecting a block opens a structured side panel for details, mappings, documents, evidence, and review rather than expanding every block into a form.

Define/Verify/Manufacture are reference-template phases, not hard-coded product categories. Other templates can use Discover/Design/Validate/Release, Plan/Make/Inspect/Ship, or user-defined phases without new code.
Engineering capability selection uses two levels. The narrow palette shows pinned, recent, and workflow-relevant templates. A searchable library handles the larger engineering landscape, including CAD, FEA, CAM, CFD, PLM/PDM, kinematics, thermal analysis, metrology, quality, and future organization-defined capabilities. Categories, keywords, expected inputs/outputs, and friendly names are discovery metadata only. Adding any executable capability still creates the same generic `mcp-action` block and requires an exact catalog tool binding before it can run.

The early visual slice is a visual contract rather than a throwaway screenshot:

- reusable React components own the application shell, palette, capability library, phase headers, block cards, review gates, inspector, legend, and status language;
- a typed reference fixture supplies the content;
- a small static projection owns only fixed positioning and connector routing;
- CP1B candidates must render around or reuse this visual system without becoming the canonical model;
- editing, execution, persistence, LLM calls, and MCP calls remain disabled and visibly labeled until their checkpoints.

## Incremental delivery checkpoints

### CP0 — Baseline and postmortem (documentation only)

**Hypothesis**: Wright can define measurable learning goals and avoid repeating the current feedback-loop failures before installing another graph library.

Deliverables:

- freeze the drill-bit-holder reference fixture as canonical JSON/TypeScript data;
- capture current Rivet screenshots and the equivalent user tasks;
- record current edit-to-feedback and user-task timings;
- document retained platform seams and current coupling/test failures;
- finalize graph rubric, test timing harness, and checkpoint evidence template.

Exit criteria:

- reference scenario and task script are unambiguous;
- baseline timings and screenshots are reproducible;
- no product or dependency code has changed;
- human approves CP1A or stops.

### CP1A — Engineer-readable visual contract

**Hypothesis**: A faithful read-only UI based on the generated target image can make the intended product concrete without prejudging the canvas library or creating throwaway product logic.

Scope:

- implement the feature-flagged direct route outside normal navigation and backend bootstrap requirements;
- render the reference workflow with reusable Wright-token React components and a typed fixture;
- include the top workflow toolbar, compact palette, searchable engineering capability library, configurable phase lanes, role-based block cards, review diamonds, data/control/feedback connections, inspector, legend, zoom controls, and minimap;
- make blocks selectable and capability discovery searchable/filterable while leaving edit/run/save actions disabled;
- capture the workflow and capability-library views at the reference dimensions;
- add focused component and flag tests; install no graph dependency.

Exit criteria:

- visual review confirms the slice is materially faithful to the reference image;
- CAD, FEA, CAM, CFD, PLM/PDM, kinematics, and additional capabilities are discoverable without a long flat palette;
- capability categories do not select runtime code and all executable templates still map to generic MCP actions;
- reusable presentation components are separated from static positioning/connector code;
- focused component feedback remains <=30 seconds and the production web build passes;
- human approves the visual contract before candidate wiring.

### CP1B — Shallow graph-library bakeoff

**Hypothesis**: At least one MIT candidate can express the engineer-readable visual grammar while keeping the Wright model canonical and tests fast.

Scope:

- perform a current license/maintenance/security review before installation;
- add isolated, branch-only harnesses for React Flow, Rete.js, and LiteGraph.js;
- render the same frozen reference fixture read-only;
- demonstrate phase lanes, custom blocks, ports, gates, feedback, selection, fit/focus, and 25/100-block fixtures;
- run the same accessibility, component-test, bundle, interaction, and deletion-cost measurements.

Explicit exclusions: editing, persistence, LLM, live MCP, execution, candidate-native serialization, production styling polish.

Exit criteria:

- scored rubric with evidence for all candidates;
- selected candidate has no score below 3 for accessibility, canonical separation, or component testability;
- one candidate is recommended and rejected candidates can be deleted without domain changes;
- if none passes, stop or authorize a fourth candidate; do not start a custom renderer by default;
- human selects continue/change/stop.

### CP2 — Selected canvas integration and usability validation

**Hypothesis**: Mechanical engineers can understand the reference workflow materially faster than the current Rivet presentation.

Scope:

- retain only the selected canvas adapter;
- replace the CP1A static projection/connector layer while retaining the approved visual components and typed fixture;
- prove pan, zoom, selection, focus, and layout behavior through the common adapter;
- implement details/evidence panels using deterministic data;
- add keyboard focus, readable labels, non-color cues, empty/loading/error examples;
- run a five-person or equivalently documented formative task review where practical.

Exit criteria:

- at least 80% of participants correctly identify phases, inputs, tool actions, review gates, feedback path, and produced artifacts without coaching;
- median task-comprehension time is at least 30% better than recorded current-Rivet baseline;
- T1 component tests remain <=30 seconds;
- human approves visual grammar before editing work.

### CP3 — Typed manual editing and local drafts

**Hypothesis**: A small command/reducer model supports understandable editing and undo without adopting a canvas vendor's state model.

Scope:

- implement strict schema, full validation, commands, reducer, semantic diff, selection/view state, undo/redo;
- support add/edit/move/connect/delete for phases, blocks, ports, and connections;
- add optional browser-local draft persistence keyed by schema version and workflow ID;
- reject invalid loads atomically and provide fixture reset/export for debugging.

Exit criteria:

- domain tests complete <=5 seconds;
- every manual mutation is a typed command with inverse or history behavior;
- saved drafts contain only Wright schema/view state and no vendor objects;
- candidate library can be removed/replaced without changing saved fixture or reducer tests;
- human completes the reference edit script.

### CP4 — Generic MCP binding and governed invocation

**Hypothesis**: Existing Wright MCP boundaries can power arbitrary action blocks without domain-specific services.

Scope:

- map the exact existing workspace catalog/API fields to the generic binding contract;
- build schema-driven tool selection and argument mapping UI;
- detect missing/stale server/tool/schema identities;
- invoke three structurally different deterministic tools through one adapter;
- optionally demonstrate one configured live tool only after deterministic conformance passes;
- display normalized approval, result, artifact, error, and evidence state.

Exit criteria:

- the same adapter handles scalar/text, nested/artifact, and approval/error fixtures;
- static checks/review find zero CAD, FEA, manufacturing, supplier, tool-name, or file-format dispatch branches;
- real invocation, if used, goes only through the governed gateway;
- no parallel catalog, approval, evidence, or artifact service is created;
- any necessary API gap is documented and separately approved as generic;
- human verifies binding identity and evidence in the UI.

### CP5 — LLM-assisted workflow authoring

**Hypothesis**: Natural language can efficiently create and change workflows when the LLM is constrained to reviewed atomic commands.

Scope:

- implement provider-neutral authoring adapter and deterministic proposal fixtures;
- validate response, base revision, command limits, MCP identities, and complete resulting model;
- show assumptions, warnings, and semantic diff;
- support accept/reject with no mutation before acceptance;
- optionally demonstrate a configured Wright LLM provider behind the same contract.

Exit criteria:

- at least 20 fixture cases; >=90% of valid deterministic cases accepted on first response and 100% invalid cases rejected without mutation;
- stale proposals cannot overwrite a newer revision;
- LLM output contains no candidate-native graph state and cannot invoke MCP;
- user can create or modify the reference flow faster than the CP3 manual baseline while understanding the proposed changes;
- human reviews prompt-to-proposal behavior and failure UX.

### CP6 — Integrated reference scenario and comparative evaluation

**Hypothesis**: The selected architecture supports the complete product-design story with understandable status, feedback, artifacts, approvals, and traceability.

Scope:

- integrate manual/LLM editing, generic MCP bindings, simulated or governed execution results, artifacts, gates, feedback, approval, and notifications;
- execute at most three focused Chromium journeys: edit, bind/invoke, propose/review;
- repeat comprehension tasks against the prototype and current Rivet baseline;
- record bundle, performance, test timings, defect causes, and architectural escape cost.

Exit criteria:

- reference story is demonstrable end-to-end without domain-specific runtime code;
- success criteria from the specification are measured, not inferred;
- ordinary prototype feedback targets remain satisfied;
- browser tests are limited, repeatable, and high-value;
- human accepts evidence for final decision work.

### CP7 — Architecture decision and formal-change proposal

**Hypothesis**: Prototype evidence is sufficient to choose a long-term direction without carrying prototype code directly into production.

Deliverables:

- ADR comparing retain Rivet, hybrid, replace with selected adapter, and stop/defer;
- recommendation separated into reusable concepts, production-quality rewrites, rejected experiments, and unknowns;
- proposed production milestones, migration/compatibility approach, test strategy, and risk controls;
- plan for deleting the prototype branch/code after evidence is preserved;
- concrete implementation examples derived from the reference fixture and contracts.

Exit criteria:

- recommendation cites CP0-CP6 evidence and explicitly accounts for current-code postmortem costs;
- no big-bang production rearchitecture is authorized by implication;
- first production increment is independently shippable and reversible;
- human chooses retain/hybrid/replace/stop and separately authorizes formal planning.

## Test strategy and feedback economics

### T0: domain/model tests

Pure tests cover schema compatibility, referential integrity, commands, reducer history, semantic diff, LLM proposal application, MCP mapping resolution, and scale-fixture generation. These must not mount a graph library or browser.

### T1: component and adapter tests

Component tests cover block anatomy, phase labels, ports, side panels, keyboard/focus behavior, adapter event translation, and loading/error/review states. Candidate packages are mounted only in their isolated harness tests.

### T2: deterministic boundary contracts

Fake catalog/invocation and authoring adapters exercise realistic request/response shapes, approval/error/artifact results, stale schema identity, invalid LLM output, and provider failure. They use no network, external model, or engineering application.

### T3: browser journeys

One Chromium file contains at most:

1. open fixture, inspect phases, and make a manual edit;
2. bind an exact fixture tool, invoke through fake gateway, and inspect evidence/artifact;
3. request an LLM change, inspect diff, reject once, then accept a valid proposal.

Playwright selectors use accessible roles/names and stable test IDs only where semantics are insufficient. Screenshots are checkpoint evidence, not blanket snapshot tests.

### Check ordering

1. formatting/lint for touched files;
2. T0 focused tests;
3. targeted type check/component test;
4. prototype T0/T1 suite;
5. T2 contracts;
6. relevant single browser journey;
7. broader repository/full push gate only for an accepted checkpoint push.

Every recorded run includes duration and failure class. Environment failures such as the observed Windows PTY invalid-handle cascade are preserved and fixed or routed around explicitly; they are not counted as product regressions.

## Evaluation measurements

| Measure                     | Collection method                                              | Decision use                                              |
| --------------------------- | -------------------------------------------------------------- | --------------------------------------------------------- |
| Comprehension accuracy/time | Same task script against current Rivet baseline and CP2/CP6 UI | Validates engineer-readable visual grammar.               |
| Graph candidate score       | Common 0-5 rubric plus screenshots/tests/bundle notes          | Selects or rejects library at CP1.                        |
| Canonical separation        | Dependency review and candidate-deletion exercise              | Prevents new vendor lock-in.                              |
| Generic MCP conformance     | Three different schema/result fixtures through one adapter     | Detects domain categorization or tool-specific branching. |
| LLM proposal validity       | >=20 deterministic fixtures and optional provider sample       | Validates bounded authoring approach.                     |
| Feedback latency            | Measured T0/T1/T2 commands                                     | Prevents return to browser/full-gate inner loop.          |
| Browser value/flakiness     | Journey duration, retries, and defect yield                    | Keeps only high-value end-to-end coverage.                |
| Change size                 | Files/lines per checkpoint and review notes                    | Supports causal, incremental review.                      |

## Risks and mitigations

| Risk                                                  | Mitigation / stop condition                                                                                                     |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Prototype quietly becomes production architecture     | Feature flag/direct route, local-only drafts, no migrations, explicit CP7 decision before formal implementation.                |
| New library repeats Rivet coupling                    | Canonical model and adapter contract precede candidate code; reject any candidate that requires native persistence.             |
| Three-candidate bakeoff becomes a long implementation | Read-only common fixture, strict CP1 exclusions, time box, delete rejected harnesses immediately.                               |
| Domain-specific services proliferate                  | One generic MCP adapter, exact catalog bindings, three conformance tools, explicit zero-domain-branch acceptance.               |
| LLM produces unsafe or opaque changes                 | Typed atomic commands, strict limits, transactional validation, semantic diff, explicit acceptance, no direct execution.        |
| Existing MCP API shape is insufficient                | First map existing public clients/routes; pause for generic contract amendment rather than creating a parallel/domain endpoint. |
| Playwright remains slow/flaky                         | Maximum three journeys; model/component/contract tests own behavior; full gate only at push checkpoints.                        |
| UI color/complexity overwhelms engineers              | Consistent block anatomy, small role vocabulary, phase/status separation, non-color cues, CP2 comprehension gate.               |
| Phase names become hard-coded                         | Phases are ordered user/template data; Define/Verify/Manufacture is only the reference fixture.                                 |
| Large checkpoint hides cause/effect                   | One hypothesis per checkpoint, bounded commits/evidence, human gate before expanding scope.                                     |

## Complexity Tracking

No constitution exception is requested. Candidate dependencies are temporary prototype costs and must be reduced to one or zero after CP1. Any proposed backend addition, custom renderer, production persistence, Rivet migration, or domain executor requires a plan amendment and separate approval.

## Planning gate

Phase 0 and Phase 1 design artifacts are complete when this plan, research, data model, quickstart, and contracts pass consistency review. Product implementation and dependency installation remain paused until the user approves CP0/implementation planning. Task generation should be checkpoint-oriented and must not collapse CP0-CP7 into one implementation batch.
