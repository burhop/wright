# Phase 0 Research: Engineering Workflow Prototype

## Purpose

This research supports a disposable prototype. Its job is to reduce uncertainty before Wright commits to a production rearchitecture. It does not select a permanent canvas library, replace Rivet, or introduce engineering-domain services.

## Current Wright baseline and lessons

The current Rivet-based work proved several valuable platform capabilities:

- Wright can discover tools through a provider-neutral MCP catalog and invoke them through a governed gateway.
- Workspace scoping, approvals, audit evidence, artifacts, and run inspection are reusable product capabilities.
- A visual workflow can retain enough evidence for a user to understand what executed and what was produced.
- Spec-first contracts and compatibility tests are important because saved workflows and historical run results outlive individual UI releases.

The same work also exposed costs that the prototype must address:

- Product concepts are coupled too closely to an upstream editor's graph and serialization model. Engineer-facing concepts such as phases, gates, reviewable documents, feedback, and physical artifacts are difficult to express without editor-specific patches.
- The development loop is too slow. On the most recent full gate, the API and root suites each took roughly seven minutes; the complete gate repeated those costs before reaching frontend formatting, build, and browser checks.
- A PTY-specific Windows invalid-handle failure produced 42 cascading API failures even though the same tests passed outside a PTY. Test infrastructure failures are not sufficiently separated from product failures.
- Formatting failures appeared only after long backend suites. Fast, likely-to-fail checks are ordered too late for ordinary development.
- Focused browser tests found two real compatibility crashes in historical run data, but only late in the process. The lesson is to preserve a very small number of high-value browser journeys while moving schema normalization and compatibility cases into fast tests.
- The final change was large (101 files) and included generated or broad artifacts, making review and causal diagnosis harder than checkpoint-sized changes.

### Retain, change, avoid

| Decision | What                                                                                                             | Reason                                                                                                         |
| -------- | ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Retain   | Generic MCP catalog, governed invocation, approvals, audit/evidence, artifact handling, and workspace boundaries | These are durable platform capabilities and are not specific to Rivet or an engineering discipline.            |
| Retain   | Run inspection and compatibility normalization                                                                   | Engineers need traceable results, and historical data must remain readable.                                    |
| Change   | Introduce a Wright-owned, versioned workflow specification                                                       | Product meaning should not depend on a canvas vendor's node model.                                             |
| Change   | Treat the canvas as a projection and interaction adapter                                                         | This lets Wright evaluate or replace libraries without migrating business data.                                |
| Change   | Use atomic LLM edit proposals with preview and validation                                                        | An LLM should edit the Wright model, not generate opaque canvas state or invoke tools directly.                |
| Change   | Use fast model/component/contract tests for daily feedback                                                       | Browser automation should prove only the few cross-boundary journeys that cannot be proved more cheaply.       |
| Avoid    | Forking or reimplementing Rivet in the prototype                                                                 | That would repeat the coupling problem and make the prototype too expensive to discard.                        |
| Avoid    | CAD, FEA, procurement, or supplier-specific executors/services                                                   | They create an unbounded taxonomy. Domain language belongs in workflow content; execution remains generic MCP. |
| Avoid    | Full-gate execution after every edit                                                                             | Full gates protect checkpoints and pushes, not the inner development loop.                                     |

## Graph library bakeoff

All candidates must render the same immutable Wright workflow fixture, emit the same Wright interaction events, and persist no vendor-native graph state. The prototype will make a decision only after a shallow, time-boxed bakeoff.

### Candidate A: React Flow / xyflow

Official source: [xyflow/xyflow](https://github.com/xyflow/xyflow)

The project is MIT-licensed and provides React and Svelte libraries for node-based editors. Its React-first model fits Wright's React application and supports custom nodes, handles, connections, grouping, and viewport interaction.

Strengths:

- Lowest likely React integration cost.
- Custom React nodes can use Wright's design tokens, accessibility semantics, and component tests.
- Suitable as a view/controller while Wright retains the canonical model and execution semantics.
- DOM-oriented customization is likely to make focused component testing easier than a Canvas2D renderer.

Risks:

- It is deliberately UI-focused; Wright must own layout conventions, validation, execution, undo semantics, and persistence.
- It is easy to accidentally persist React Flow node/edge objects. The adapter contract must prohibit this.

Working hypothesis: leading integration candidate, subject to the common rubric.

### Candidate B: Rete.js

Official source: [retejs/rete](https://github.com/retejs/rete)

Rete.js is MIT-licensed and describes itself as a framework for visual interfaces and workflows, with dataflow and control-flow processing support.

Strengths:

- Rich plugin architecture and explicit processing concepts.
- Useful comparison for sockets, connections, and complex editor behaviors.
- React rendering support is available through its plugin ecosystem.

Risks:

- Its processing model may duplicate or compete with Wright's workflow runtime and governed MCP gateway.
- More packages and plugin interactions increase upgrade, bundle, and testing surface.
- The prototype must prevent Rete schemas or engines from becoming the product model.

Working hypothesis: valuable comparator; adopt only if editor behavior materially outweighs coupling and complexity.

### Candidate C: LiteGraph.js

Official source: [jagenjo/litegraph.js](https://github.com/jagenjo/litegraph.js/)

LiteGraph.js is MIT-licensed and provides a Canvas2D node editor/runtime, JSON serialization, subgraphs, and custom nodes.

Strengths:

- Mature graph interaction model and potentially efficient rendering for large graphs.
- Useful performance and density comparator.
- Demonstrates what Wright gains and loses with a canvas-rendered editor.

Risks:

- Canvas2D content is harder to make accessible, style with React design tokens, inspect in the DOM, and test with component tools.
- Its own runtime and JSON model can create the same ownership/coupling problem as Rivet.
- Integrating React panels and engineering document views may require more bridge code.

Working hypothesis: performance comparator, unlikely default unless the bakeoff exposes a decisive scale advantage.

### Common evaluation rubric

Each candidate receives a 0-5 score with evidence for:

1. Engineer comprehension using the reference workflow.
2. Phase-lane, gate, feedback-loop, port, and artifact presentation.
3. React/design-system integration and accessibility.
4. Ability to keep the Wright workflow specification canonical.
5. Interaction and layout behavior at 25 and 100 blocks.
6. Unit/component testability without a browser.
7. Bundle, dependency, maintenance, and license risk.
8. Estimated effort for typed editing, selection, keyboard interaction, and undo.

The selected candidate must have no score below 3 for accessibility, canonical-model separation, or component testability. If none passes, the checkpoint recommendation is to stop or test a fourth candidate—not to build a custom canvas by default.

## Generic MCP integration decision

The prototype will reuse Wright's existing generic catalog and governed invocation boundary. A workflow block binds to an exact server/tool/schema identity and supplies validated arguments. The block may display an engineer-friendly title such as “Create parametric part” or “Run structural check,” but that label is presentation data and never selects implementation code.

One prototype adapter will support all MCP tools:

1. Query the existing workspace-scoped tool catalog.
2. Select an exact tool identity and capture its reviewed schema/revision.
3. Map workflow ports and literal values to the tool input schema.
4. Validate the proposed call before invocation.
5. Invoke through the existing governed gateway.
6. Normalize status, artifacts, approvals, and evidence back into the Wright run model.

Acceptance requires at least three structurally different fixture tools to pass through this same path without tool-family branches or domain services. CAD and FEA may appear as reference-scenario fixtures, but they receive no special runtime category.

## LLM-assisted authoring decision

The LLM will not generate library-native nodes, full serialized projects, source code, or direct tool calls. It returns a versioned proposal containing small typed commands against a known base revision, for example:

- add or rename a phase;
- add, update, move, or remove a block;
- add or remove a connection;
- bind a block to an exact catalog tool;
- map an input port to a tool argument;
- add a gate or feedback connection.

The client validates the proposal, applies it to a copy through the same reducer used by manual editing, shows a semantic diff, and waits for explicit acceptance. Stale, invalid, ambiguous, or unauthorized proposals are rejected without modifying the workflow.

Development uses deterministic fixtures representing valid, invalid, stale, and partially applicable proposals. A real configured model is an optional checkpoint demonstration behind the same adapter, not a prerequisite for deterministic testing.

## Testing strategy decision

| Tier      | Scope                                                                     |                Target | When                                 |
| --------- | ------------------------------------------------------------------------- | --------------------: | ------------------------------------ |
| T0        | Schema parsing, reducer commands, validation, diff, layout inputs         |          <= 5 seconds | Every edit/watch mode                |
| T1        | Custom blocks, phase lanes, panels, selected canvas adapter               |         <= 30 seconds | Every UI slice                       |
| T2        | Fake LLM and fake generic MCP catalog/invocation contracts                |          <= 2 minutes | Before checkpoint review             |
| T3        | At most three Chromium journeys: create/edit, bind/invoke, propose/review |  Bounded and recorded | Checkpoint and pre-push only         |
| Full gate | Repository push runbook                                                   | Existing project gate | Before pushing a reviewed checkpoint |

Fast formatting, type checks for touched code, and T0 tests run before broader suites. The prototype records command, duration, result, environment, and failure class so infrastructure faults can be distinguished from product defects.

## Open questions resolved by checkpoints

- The permanent canvas library is deliberately unresolved until the bakeoff.
- Whether a production migration should be retain-Rivet, hybrid, replace, or stop is deliberately unresolved until the integrated prototype and postmortem evidence are complete.
- The prototype may use local ephemeral persistence only. Production persistence and migration are separate decisions.
- A thin API change is allowed only if the existing generic MCP gateway cannot support the contract; any such change must remain generic and receive separate approval.
