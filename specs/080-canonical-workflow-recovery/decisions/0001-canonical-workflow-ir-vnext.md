# ADR 0001: One Canonical Workflow IR with Separate Layout and Runs

- **Status**: Proposed for recovery concept; product approval required before production promotion
- **Date**: 2026-08-31
- **Feature**: Canonical Workflow Recovery / spec 080
- **Supersedes for product direction**: spec 079's bounded custom-shell plan and proposed draft-boundary decision
- **Preserves**: ADR 0021's immutable released-definition boundary and all Checkpoint D model/revision/CAS/API/renderer seams named below
- **Related**: `DEC-P0-002`, `PROD-01`, `PROD-08`, LL-010, LL-017, LL-025

## Context

Checkpoint D at `b4a7e996` proves a sound provisional draft model, validation, immutable revisions, CAS persistence, closed API/browser decoding, and renderer-neutral projection/intent seam. Its current UI is not acceptable product direction: lanes and forms dominate, graph handles and routed relationships are not the primary manipulation model, text is read-only, and AI/run/artifact experiences are excluded.

The frozen prototype at `e7bb75c1` supplies valuable visual and renderer evidence but is neither complete nor usability-approved. It also contains multiple provisional or competing authorities: prototype JSON, renderer state, code experiment, AI proposal concepts, and run fixtures.

Wright needs one explicit semantic authority before the UI or runtime is hardened.

## Decision

Adopt a versioned typed `workflow-ir` as the only semantic authority. Diagram, code/text, property forms, CLI/headless projections, and AI proposals consume or propose commands against this model. No renderer-native graph or textual document is independently authoritative.

Persist separately:

1. **Canonical definition revisions**: immutable semantic content with stable identities and digest.
2. **Layout documents**: stable-ID-keyed presentation metadata with their own version/digest.
3. **Immutable run records**: exact definition revision/digest plus append-only step, activity, input, output, and artifact facts.

Normalize manual graph gestures, form edits, valid text changes, and AI suggestions into one closed atomic command protocol with `base_revision`. Apply to a clone, validate the complete candidate, produce a semantic diff and preview, and advance accepted state only through explicit user acceptance/save. Invalid or stale candidates never replace the last-valid definition.

AI may propose commands and explanations. It cannot mutate, execute, approve, or accept.

## Definition scope

IR vNext covers workflow/revision metadata; stable phases, blocks, ports, relationships, artifact contracts, bindings, and components; typed ports; data/control/decision/feedback semantics; conditions/instructions/configuration; exact tool/MCP identity and mappings; deterministic/AI/human blocks; and reusable component interfaces.

The recovery contract version `2.0.0-recovery.1` is deliberately non-production. It establishes completeness and conformance evidence, not a migration commitment.

## Text decision

Strict canonical JSON remains the internal interchange baseline. Strict JSON, YAML, and a small DSL are compared on identical workflows and edits. The recovery concept may provisionally use the highest-evidence user-facing treatment, but no permanent syntax is selected by this ADR. A production syntax decision must close `DEC-P0-002` with independent human and model evidence, comment/format policy, source-map behavior, migration, and compatibility costs.

## Renderer decision

Retain the existing renderer adapter. Reopen React Flow as the provisional concept renderer because the accepted prototype bakeoff scored it 91/100 and showed substantially better rendering/accessibility/scale evidence than alternatives. This ADR does not permanently select it: the prototype disabled dragging and connecting, so the recovery concept must newly prove visible handles, direct move/connect/disconnect, execution overlays, keyboard use, and bounded large-graph behavior.

The renderer owns mechanics and presentation only. It cannot assign semantic IDs, validate, serialize vendor state as authority, apply commands, accept proposals, or own run facts.

## Retained production foundations

- `packages/core/src/core/workflow_drafts.py`: closed model and separate semantic/layout digests.
- `packages/core/src/core/workflow_draft_validation.py`: stable complete-candidate diagnostics.
- `packages/data_vault/src/data_vault/workflow_draft_repository.py`: immutable revisions and head CAS.
- `packages/workspace_service/src/workspace_service/workflow_draft_service.py` and the closed API/browser contracts.
- `apps/web/src/components/workflow-composer/{renderer-types,draft-projection,draft-intents}.ts`.
- Strict cross-language parser/canonicalization vectors from spec 078 as a conformance seed, without making the read-only process-definition schema authoring authority.

## Consequences

### Positive

- Every editing surface shares identity, validation, revision, and diff semantics.
- Graphical-only use remains possible while text and AI become safe optional projections.
- Layout, renderer replacement, proposals, and run overlays cannot corrupt definition semantics.
- Historical runs and artifacts stay truthful after later workflow edits.
- Checkpoint D work is preserved rather than discarded.

### Costs and risks

- IR vNext is broader than the current bounded draft and needs a deliberate production migration plan later.
- Text formatting/comment preservation is harder than canonical JSON alone.
- Components and binding maps add validation complexity.
- React Flow remains a dependency risk until the new direct-manipulation evidence passes.
- The recovery concept simulates run records and AI proposals; product approval must not be misreported as production runtime integration.

## Rejected alternatives

- Renderer-native graph as authority: couples semantics to presentation and blocks lossless text/headless equivalence.
- Text source as independent authority: creates drift and makes partial invalid edits dangerous.
- Continue hardening the current custom canvas: spends work on a product grammar already rejected by the recovery goal.
- Promote the frozen prototype wholesale: its behavior, studies, and authority boundaries are incomplete and explicitly provisional.
- Keep separate manual, text, and AI mutation paths: duplicates validation and makes revision conflicts unreviewable.
- Store run state in workflow definitions: destroys historical truth and makes editor activity mutate executable intent.

## Promotion gate

This ADR can become accepted production architecture only after the capability inventory, syntax evidence, automated conformance invariants, editable renderer proof, complete walkthrough, program-artifact reordering, and product-owner review all pass. Until then, new UI/kernel code is labeled disposable concept and broad implementation remains paused.
