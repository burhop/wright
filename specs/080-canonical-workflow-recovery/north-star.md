# Canvas-First Workflow North Star

**Status**: approved recovery product/visual direction, now bound to the workspace-owned exact correction subject `38b409bf149a1241cc87cdedd48f83fed16b5050` / tree `452c1ab82b12fe94ba743e3dfe612c8cd4b9dac6` and its validated 24/24 continuation-14 walkthrough. Production and customer readiness remain incomplete. This document explicitly supersedes the product direction in spec 079's four-block north star and parity matrix. The frozen 079 artifacts remain historical evidence, but their rejection of AI review, execution-state projection, and output inspection does not constrain this recovery treatment.

## Product promise

A mechanical engineer can understand, compose, inspect, and recover an engineering workflow inside the workspace where its inputs and results belong. The canvas is the primary experience; Source is an optional lossless engineering-script projection. The surface assumes engineers are comfortable with code and technical tools, while keeping host revision machinery, digests, exact bindings, and storage controls behind technical disclosure.

## One workflow, five views

Every surface answers a different question about the same accepted definition:

| Surface | Engineer question | Authority |
|---|---|---|
| Canvas | What happens, in what flow, with which typed inputs and outputs? | projection only |
| Source | What does the editable engineering workflow file say? | editable candidate until explicitly applied |
| Inspector | What does this selected concept mean and require? | form projection issuing commands |
| AI review | What change is proposed, assumed, risky, and different? | non-mutating candidate until accepted |
| Run overlay | What happened for this immutable definition revision? | immutable run projection, never definition state |

## Interaction grammar

- Friendly step names and purposes lead; IDs and bindings remain inspectable behind technical disclosure.
- A workflow opens only from an active workspace through **Workflows**. Choosing it is explicit creation intent: if the default file is absent, Wright creates it once and opens the usable editor immediately; if it exists, Wright opens it unchanged. Merely opening a workspace creates nothing, and the primary surface has no global workflow-recovery entry.
- One visible `workflows/<name>.workflow.wflow` file carries engineer-authored workflow meaning. Host-managed revision, digest, compare-and-swap, and integrity metadata stay outside that file and remain available in technical details.
- Reference images, design intent, and company standards/context are three explicit sources with visible provenance; they feed one editable, engineer-reviewed design specification before CAD begins.
- Inputs are on the left and outputs are on the right. The overview shows a compact input/output count and small sockets; friendly file/model/report names, requiredness, exact types, and cardinality appear on focus, selection, or in the inspector.
- A connection socket and an action that opens a file, model, report, or record are different controls with different shapes, labels, and behaviors.
- Data, decision, and feedback relationships remain visually distinct without relying on color alone.
- Groups are optional organizational aids, not required workflow phases; a short workflow needs none.
- Step search is absent for 25 or fewer steps and becomes available at 26 or more, where it materially helps navigation.
- Edge labels are not persistent canvas decoration. They appear when a relationship is focused, selected, or active, and their full meaning remains available to keyboard and assistive-technology users.
- Reusable review steps show one compact group summary; internal targets and stable addresses appear only after an explicit **Details** action.
- At the 1070×791 review viewport the application is fixed-height with no document/page scrolling; the bounded source list and inspector may scroll internally when their own content requires it.
- Semantic changes advance the accepted revision once. Layout, selection, previews, rejection, invalid source, and run activity do not.
- Invalid candidates stay editable while the last-valid graph remains trustworthy.
- AI may propose and explain. Only the engineer may accept, run, or approve.
- Needs-input and failure states explain consequence and offer a bounded engineering correction rather than raw JSON or logs.
- Outputs look like engineering outputs and expose exact producer, run, revision, media type, and digest lineage. In the current concept, input attachment controls and generated-output downloads are demo fixtures and are not persisted by the workspace workflow-source save.

## Visual hierarchy

1. Workspace workflow filename, save state, provisional authority, validity, and `SIMULATED` status.
2. Block/flow story on the canvas.
3. Selected block’s definition and run facts.
4. Input-source provenance, contextual downstream step library, and run-state language.
5. Exact provider/server/tool/schema bindings behind progressive disclosure.

## Non-negotiable trust boundaries

- No renderer-native semantic authority.
- No independent source-document authority.
- No workflow authoring outside a workspace that owns its definition, inputs, and results.
- No empty missing-file dead end after a valid workspace-scoped Workflows action, and no bootstrap overwrite of an existing source.
- No layout or run facts in the semantic digest.
- No partial invalid mutation.
- No AI direct mutation, execution, approval, or hidden acceptance.
- No product/production claim from simulated evidence.

## Approval questions

The product reviewer should be able to answer “yes” without coaching:

1. Can I read the bracket workflow from blocks and flows alone?
2. Can I tell where to connect, then use focus or the inspector to see the exact item contract and artifact action without crowding the overview?
3. Can I add, move, connect, configure, delete, undo, and redo safely?
4. Can I reconcile canvas, source, and inspector as one workflow?
5. Can I understand an AI proposal before accepting it?
6. Can I see what is running, what needs input, what is blocked, and how to recover?
7. Can I recognize and trust the output lineage?
8. Can I enter Workflows, immediately reach a usable default when none exists, and identify the workspace and single visible workflow file without being asked to manage creation mechanics, host revisions, or digests?

Any unresolved ambiguity stops the approval walkthrough and becomes the next bounded product-design task.
