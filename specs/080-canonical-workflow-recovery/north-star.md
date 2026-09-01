# Canvas-First Workflow North Star

**Status**: recovery product-direction authority, pending product approval. This document explicitly supersedes the product direction in spec 079's four-block north star and parity matrix. The frozen 079 artifacts remain historical evidence, but their rejection of AI review, execution-state projection, and output inspection does not constrain this recovery treatment.

## Product promise

A mechanical engineer can understand, compose, inspect, and recover an engineering workflow visually before learning any syntax. The canvas is the primary experience; Code is an optional lossless projection; exact execution bindings are available without dominating the workflow story.

## One workflow, five views

Every surface answers a different question about the same accepted definition:

| Surface | Engineer question | Authority |
|---|---|---|
| Canvas | What happens, in what flow, with which typed inputs and outputs? | projection only |
| Code | What is the exact portable definition? | editable candidate until explicitly applied |
| Inspector | What does this selected concept mean and require? | form projection issuing commands |
| AI review | What change is proposed, assumed, risky, and different? | non-mutating candidate until accepted |
| Run overlay | What happened for this immutable definition revision? | immutable run projection, never definition state |

## Interaction grammar

- Friendly block names and purposes lead; IDs and bindings remain inspectable.
- Inputs are on the left; outputs are on the right; type, requiredness, and cardinality are visible.
- A connection socket and an artifact action are different controls with different shapes, labels, and behaviors.
- Data, decision, and feedback relationships remain visually distinct without relying on color alone.
- Semantic changes advance the accepted revision once. Layout, selection, previews, rejection, invalid source, and run activity do not.
- Invalid candidates stay editable while the last-valid graph remains trustworthy.
- AI may propose and explain. Only the engineer may accept, run, or approve.
- Needs-input and failure states explain consequence and offer a bounded engineering correction rather than raw JSON or logs.
- Outputs look like engineering outputs and expose exact producer, run, revision, media type, and digest lineage.

## Visual hierarchy

1. Workflow title, provisional authority, revision, validity, and `SIMULATED` status.
2. Block/flow story on the canvas.
3. Selected block’s definition and run facts.
4. Palette, attachment, and run-state language.
5. Exact provider/server/tool/schema bindings behind progressive disclosure.

## Non-negotiable trust boundaries

- No renderer-native semantic authority.
- No independent source-document authority.
- No layout or run facts in the semantic digest.
- No partial invalid mutation.
- No AI direct mutation, execution, approval, or hidden acceptance.
- No product/production claim from simulated evidence.

## Approval questions

The product reviewer should be able to answer “yes” without coaching:

1. Can I read the bracket workflow from blocks and flows alone?
2. Can I tell where to connect and where to inspect an artifact?
3. Can I add, move, connect, configure, delete, undo, and redo safely?
4. Can I reconcile canvas, source, and inspector as one workflow?
5. Can I understand an AI proposal before accepting it?
6. Can I see what is running, what needs input, what is blocked, and how to recover?
7. Can I recognize and trust the output lineage?

Any unresolved ambiguity stops the approval walkthrough and becomes the next bounded product-design task.
