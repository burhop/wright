# Recovery Research and Decisions

**Feature**: 080 Canonical Workflow Recovery  
**Evidence cutoff**: 2026-08-31  
**Decision posture**: sufficient for a disposable product concept; insufficient for production promotion

## Research questions

1. Which existing work is a production foundation, which is only evidence, and which product direction must stop?
2. Can one complete IR represent the workflow without giving diagram, source, layout, AI, or run state competing authority?
3. Which textual treatment best exposes block/port correspondence without prematurely closing `DEC-P0-002`?
4. Can React Flow supply direct manipulation and run overlays through the retained renderer seam?
5. Which port treatment makes connection and artifact inspection separately discoverable?

## Baselines

### Frozen Checkpoint D

The exact subject is commit `b4a7e996f10ec95f7d24185a43fd1401843db66d`, tree `accd9e1f45634865fa52325b64083096994d70f3`, after task T027. Its prior walkthrough passed 11 steps with 12 raw and 12 annotated images and no captured browser errors. It proves a closed draft model, validation, immutable revisions, head compare-and-set, API/browser decoding, and a renderer-neutral projection/intent seam.

It does not prove a product-acceptable authoring experience. The shell remains lane/form dominated, source is not a lossless editable projection, and run/AI/artifact interaction is absent. T028–T038 remain intentionally unchecked.

### Frozen prototype evidence

The read-only prototype subject is commit `e7bb75c1d97e70e55b943e0c94a31ff85cf9f82d`, tree `88fe1511…`. Its renderer bakeoff scored React Flow 91/100, Rete 70/100, and LiteGraph 41/100. It demonstrated the intended visual density, ports, connections, palette, and run-overlay direction.

Its direct manipulation was disabled, its five-person study did not run, and its 100-node observation was a single prototype run. It is design evidence, not code or a qualifying usability/scale result.

## Capability disposition

The source audit extracts 555/555 governed rows and maps them into 33/33 capability groups with no unexplained omission: 11/11 product gates, 100/100 engineering-process stories, 25/25 lessons, 20 priority decisions, and the named feature/spec sources. The full matrix is in [capability-inventory.md](capability-inventory.md); the deterministic check is in [evidence/capability-coverage.md](evidence/capability-coverage.md).

The principal disposition is:

- retain the model, validation, revision/CAS, service/API/browser, and renderer-adapter boundaries;
- revise the canonical definition to cover phases, blocks, typed ports, all relationship kinds, artifacts, bindings, conditions, instructions, configuration, execution capability, and reusable components;
- replace the current shell’s primary product grammar with a canvas-first block/flow treatment;
- keep exact binding details progressively disclosed;
- keep AI as reviewed commands and runs as immutable projections;
- defer production migration, release hardening, benchmark qualification, and permanent syntax/renderer commitments.

## Canonical authority decision

Adopt `workflow-ir` version `2.0.0-recovery.1` as the only semantic authority for this recovery slice. The accepted definition excludes layout, selection, diagnostics, source drafts, proposals, and run state.

All mutation paths normalize to a closed command batch with `base_revision`:

```text
graph gesture ─┐
form edit ─────┼─> atomic commands -> clone -> validate -> semantic diff -> explicit accept
parsed text ───┤                                      └-> reject: preserve last-valid
AI proposal ───┘
```

Layout is a stable-ID-keyed document with its own digest. Run activity, step state, inputs, outputs, and artifacts are immutable records bound to the accepted definition revision. The ADR and detailed boundaries are in [decisions/0001-canonical-workflow-ir-vnext.md](decisions/0001-canonical-workflow-ir-vnext.md).

## Syntax experiment

All treatments use the same 44-section mounting-bracket model and the same five direct edits. The independent study measured:

| Treatment | Bytes / lines | Direct edits | Median parse | Source spans | Original invalid controls | Strict-kernel controls |
|---|---:|---:|---:|---:|---:|---:|
| JSON | 18,858 / 622 | 5/5 | 0.1061 ms | none | 4/8 rejected | 8/8 rejected |
| YAML | 13,909 / 467 | 5/5 | 33.8944 ms | none | 4/8 rejected | 8/8 rejected |
| DSL | 13,077 / 468 | 5/5 | 0.6179 ms | 44 section spans | 4/8 rejected | 8/8 rejected |

The original failures are preserved rather than hidden. Strict duplicate-key/non-finite handling plus global identity/reference/ownership/direction/type validation repaired the recovery boundary. The focused Python conformance suite passes 20/20, including duplicate-endpoint, feedback-source/order, cycle-policy, cardinality, reciprocal phase/port ownership, binding-map, and component-interface controls.

Decision: strict JSON remains the internal interchange baseline; the compact DSL is only the disposable Code treatment because it exposes the clearest one-section-per-identity correspondence. YAML remains viable if a concrete-syntax-tree and comment/source-map policy is justified. No permanent user-facing syntax is selected.

## Renderer experiment

`@xyflow/react` 12.11.3 is loaded only by the default-off recovery route. The recovery host projects vNext through the retained `DraftCanvasRenderer` seam. React Flow owns viewport, path rendering, drag mechanics, connection gestures, minimap, and controls. The host owns IDs, commands, validation, revisions, selection, source, proposals, and run projections.

New local browser evidence closes the prototype’s most important gap:

- visible typed left-input/right-output handles;
- pointer handle-to-handle connection using bounding-box coordinates;
- separate artifact inspection buttons;
- accessible relationship selection and disconnect;
- graph/form/text/AI changes through the same batch protocol;
- non-color active block and edge cues;
- keyboard-operable handle contract;
- reduced-motion static directional treatment;
- default-off route isolation and lazy loading.

The six-to-eight-block product journey is proven. The prior single-run 100-node prototype observation is retained only as non-qualifying evidence; production scale remains open.

## Port treatment laboratory

Three treatments use the same `Approved geometry` port and state language:

| Treatment | Connection target | Artifact target | Strength | Risk |
|---|---|---|---|---|
| Round socket | compact round handle | small adjacent inspect control | familiar graph grammar | inspect action can disappear into chrome |
| Terminal block | square electrical terminal | separate inspect control | connection affordance is forceful | visually heavy and domain-specific |
| Hybrid terminal | outlined asymmetric socket | labeled `▧ artifact` control | connection and artifact action have distinct shape, label, and hit target | needs moderated confirmation at multiple densities |

The concept uses the hybrid treatment. This is an expert comparative choice, not an engineer-study result. An unprompted product reviewer must still connect a port and inspect its artifact without coaching; hesitation is a stop condition. See [evidence/block-port-lab.md](evidence/block-port-lab.md).

## Risks carried to approval

- The DSL owns a new grammar and only section-level source spans.
- React Flow dependency/scale and desktop embedding remain provisional.
- The simulated AI and run paths prove grammar, not production integration.
- The mounting-bracket fixture proves one coherent mechanical workflow, not domain breadth.
- Mobile reflow and zero serious/critical automated violations do not replace a headed 200% browser-zoom and keyboard review.
- The port choice has not passed an unprompted representative-engineer study.

## Decision summary

The recovery direction is internally coherent enough for a product-approval walkthrough: one complete typed model, one mutation protocol, separate layout/run records, lossless paired projections, real direct manipulation, reviewable AI, and a recognizable simulated output. Production implementation remains paused until the reviewer accepts the canvas/port/product grammar and explicitly authorizes the next bounded lease.
