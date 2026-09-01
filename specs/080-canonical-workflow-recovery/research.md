# Recovery Research and Decisions

**Feature**: 080 Canonical Workflow Recovery

**Evidence cutoff**: 2026-09-01
**Decision posture**: historical product direction approved; current workspace-owned correction awaits a fresh exact-subject walkthrough and remains insufficient for production promotion

## Research questions

1. Which existing work is a production foundation, which is only evidence, and which product direction must stop?
2. Can one complete IR represent the workflow without giving diagram, source, layout, AI, or run state competing authority?
3. Which engineer-facing source treatment reads like an engineering script without exposing host revision/storage machinery or prematurely closing `DEC-P0-002`?
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

The source audit extracts 881/881 governed rows and maps them into 33/33 capability groups with no unexplained omission: 11/11 product gates, 100/100 engineering-process stories, 25/25 lessons, 20 priority decisions, the frozen prototype, and every named adjacent feature/spec source through 080 (including 055, 064, and 068–075 plus 078–080). Wrapped requirements are classified from their complete statement rather than only their first physical line. The full matrix is in [capability-inventory.md](capability-inventory.md); the deterministic check is in [evidence/capability-coverage.md](evidence/capability-coverage.md).

The principal disposition is:

- retain the model, validation, revision/CAS, service/API/browser, and renderer-adapter boundaries;
- revise the canonical definition to cover stable tasks, optional groups, typed ports, all relationship kinds, artifacts, bindings, conditions, instructions, configuration, execution capability, and reusable components;
- replace the current shell’s primary product grammar with a canvas-first block/flow treatment;
- admit workflow authoring only from a real workspace and store one visible `.workflow.wflow` file there;
- give engineers Diagram, Source, and Side by side while keeping host revisions, digests, compare-and-swap, and integrity records outside authored source;
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

The original failures are preserved rather than hidden. Strict duplicate-key/non-finite handling plus global identity/reference/ownership/direction/type validation repaired the recovery boundary. The focused Python conformance suite passes 23/23, including duplicate-endpoint, feedback-source/order, cycle-policy, cardinality, reciprocal phase/port ownership, binding-map, component-interface controls, and exact semantic/layout history authority.

Historical decision: strict JSON remains the internal interchange baseline; the compact DSL was a disposable Code experiment because it exposed one-section-per-identity correspondence. YAML remains viable if a concrete-syntax-tree and comment/source-map policy is justified. No permanent user-facing syntax is selected by that experiment.

**2026-09-01 correction after hands-on engineer review:** the measured compact DSL above is preserved only as `fixtures/mounting-bracket.workflow.internal-ir.wflow` historical/internal evidence. The visible `.wflow` is a contextual engineering authoring projection using `workflow`, `item`/file, `input`, `task`, `prompt`/instructions, settings, and review-gate vocabulary. It omits revisions, digests, canonical `type.*`/`block.*`/`port.*`/`artifact.*` identities, layout, and run state. Connection points use stable lower-snake names plus closed engineering kinds such as `design_intent`, `cad_model`, and `step_file`; Wright maps those friendly kinds to exact internal contracts. `group` is optional and the nine-step subject omits its low-value default groups; an explicitly grouped or large workflow can project them. The current friendly fixture is 15,071 bytes / 328 lines, supports the same five direct edits, and provides 62 source spans. Strict JSON/YAML remain internal canonical treatments; accepted source edits bind to an exact accepted base and lower through the command/validation boundary. Current measurements are in `evidence/syntax-evaluation.md`.

## Workspace ownership and storage decision

Workflow authoring has no global `/workflow-recovery` destination. A user first enters an existing workspace at `/workspace/<real-id>`, then chooses **Workflows**, which adds `?workflow=canonical`. That choice is explicit workspace-scoped creation intent. Wright performs a side-effect-free read and, when the default path is absent, an atomic create-if-absent bootstrap with the validated default, then opens the editor immediately. A concurrent or later entry returns the existing file unchanged; ordinary workspace entry creates nothing, and no bootstrap may overwrite source. The workspace stores one visible semantic file such as `workflows/mounting-bracket.workflow.wflow`. Compare-and-swap conflict handling protects later saves; host-managed storage revision, storage digest, semantic revision, and integrity history remain outside the engineer-authored source and may be disclosed as technical detail.

This resolves the usability tradeoff in favor of a ready-to-use engineering tool rather than a missing-file setup screen. The rejected alternatives were global or ordinary-workspace auto-creation, which would create unowned or surprising state, and a second Create workflow confirmation, which adds no useful decision after the engineer has already chosen Workflows. Idempotent create-if-absent preserves the rigorous storage boundary without making that mechanism part of the engineer's task.

This boundary deliberately does not claim that the source save persists selected attachments, canvas layout, simulation state, run records, the demo report, or the demo STEP download. Those remain separate records or fixtures until independently implemented and verified.

Manual review must launch the recovery branch API with an explicit branch-compatible `DATABASE_PATH`. An isolated workspace named `Wright workflow review` is only an example of a local review setup using a disposable review database and directory. It is not evidence that the user's real Wright database or production workspace was changed.

## Renderer experiment

`@xyflow/react` 12.11.3 is loaded only by the feature-gated workspace workflow surface. The recovery host projects vNext through the retained `DraftCanvasRenderer` seam. React Flow owns viewport, path rendering, drag mechanics, connection gestures, minimap, and controls. The host owns IDs, commands, validation, revisions, selection, source, proposals, persistence, and run projections.

New local browser evidence closes the prototype’s most important gap:

- visible typed left-input/right-output handles;
- pointer handle-to-handle connection using bounding-box coordinates;
- separate artifact inspection buttons;
- accessible relationship selection and disconnect;
- graph/form/source/AI changes through the same batch protocol;
- non-color active block and edge cues;
- keyboard-operable handle contract;
- reduced-motion static directional treatment;
- workspace-only route isolation and lazy loading;
- no step-search control through 25 steps, with search available at 26 or more;
- fixed-height 1070×791 application containment with no document/page scrolling.
- overview-first nine-step projection at 1537×791 and 1070×791: compact 224 px blocks, 10 px visible sockets with larger invisible hit targets, relationship labels shown only on focus/selection/activity, and component internals behind a Details action.

The nine-step workspace-owned product journey is proven on exact subject `38b409bf` by continuation 14, including bootstrap, source/CAS conflict recovery, live drag, AI review, simulated run recovery, and output lineage. The prior single-run 100-node prototype observation is retained only as non-qualifying evidence; bounded automated 25/26/100-step navigation does not close production scale.

## Port treatment laboratory

Three treatments use the same `Approved geometry` port and state language:

| Treatment | Connection target | Artifact target | Strength | Risk |
|---|---|---|---|---|
| Round socket | compact round handle | small adjacent inspect control | familiar graph grammar | inspect action can disappear into chrome |
| Terminal block | square electrical terminal | separate inspect control | connection affordance is forceful | visually heavy and domain-specific |
| Hybrid terminal | outlined asymmetric socket | labeled `▧ artifact` control | connection and artifact action have distinct shape, label, and hit target | needs moderated confirmation at multiple densities |

The comparison remains available in the connection-style preview, but the default canvas now uses the compact round/dot treatment after the requesting engineer found the prior hybrid terminals and persistent metadata too visually heavy. The visible socket is 10 px with a larger invisible pointer target; keyboard focus exposes the friendly item name, and the inspector carries the complete contract and artifact action. This is still one engineer's formative correction, not the representative study required by T056. See [evidence/block-port-lab.md](evidence/block-port-lab.md).

## Risks carried beyond approval

- The engineer source owns a small grammar and 19 contextual source spans; comment preservation and a permanent syntax decision remain open.
- React Flow dependency/scale and desktop embedding remain provisional.
- The simulated AI and run paths prove grammar, not production integration.
- The mounting-bracket fixture proves one coherent mechanical workflow, not domain breadth.
- Mobile reflow and zero serious/critical automated violations do not replace a headed 200% browser-zoom and keyboard review.
- The port choice has not passed an unprompted representative-engineer study.

## Decision summary

The recovery direction is internally coherent and the exact `f9237763` subject remains the historical product/visual-direction baseline. The `c5fb7d8e` / continuation-5 package is prior automated correction evidence. The workspace-owned correction adds one idempotently bootstrapped and compare-and-swap-saved engineer source file, optional groups, Diagram/Source/Side by side, bounded search, fixed-height containment, compact overview-first graph treatment, and workspace-only entry. It is now bound to commit `38b409bf149a1241cc87cdedd48f83fed16b5050`, tree `452c1ab82b12fe94ba743e3dfe612c8cd4b9dac6`, and a validated 24/24 continuation-14 walkthrough with zero unexpected diagnostics. The current authorization permits dependency-ordered locally safe implementation, but no mutating production lease, push, merge, publication, release, customer action, or readiness claim.
