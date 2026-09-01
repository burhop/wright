# React Flow Recovery Evidence

**Dependency**: `@xyflow/react` 12.11.3, exact version  
**Scope**: default-off, lazy-loaded disposable recovery route  
**Adapter**: retained `DraftCanvasRenderer` / `DraftCanvasAdapterProps`

## Authority boundary

React Flow receives an immutable `DraftProjection` plus selection and an intent callback. A separate context supplies run, proposal, artifact, and non-data relationship overlays. It does not assign semantic IDs, validate, serialize authority, apply commands, accept proposals, or own run facts.

## Newly proven behavior

- six-block mounting-bracket graph with phase-secondary visual grouping;
- typed visible handles and separate artifact actions;
- pointer connection by source/target handle coordinates;
- keyboard handle contract using Enter/Space and Escape cancellation;
- drag intents produce layout-only commands;
- accessible edge selection, disconnect, and stable relationship identity;
- data, decision, and feedback relationship treatments;
- queued/running/needs-input/blocked/failed/stale/succeeded node states;
- active block banner and active edge text/pattern/arrow cues;
- reduced-motion active edge retains a static pattern and `Active flow` label;
- minimap, zoom controls, and fit-view mechanics;
- 390×844 document containment;
- zero serious/critical axe violations in the base concept and port laboratory.

## Test evidence

`tests/ui-integration/workflow-recovery.spec.ts` uses real Chromium and real React Flow. It proves direct connection, revision isolation, paired source editing, invalid containment, AI reject/accept, needs-input recovery, successful output lineage/download, reduced motion, automated accessibility, and mobile containment.

The frozen prototype’s 91/100 bakeoff and single 100-node run remain supporting but non-qualifying evidence. This recovery slice does not promote a permanent renderer or claim production-scale performance.
