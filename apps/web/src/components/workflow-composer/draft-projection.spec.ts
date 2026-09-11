import { describe, expect, it } from "vitest";

import fixture from "../../../../../packages/core/tests/fixtures/workflow_drafts/representative-workflow.json";
import { decodeWorkflowDraft } from "../../services/workflow-drafts";
import {
  assertSemanticIdParity,
  buildDraftProjection,
  draftSemanticIds,
  projectionSemanticIds,
} from "./draft-projection";
import type { DraftCanvasIntent } from "./draft-intents";
import type { DraftCanvasRenderer } from "./renderer-types";

describe("renderer-neutral workflow draft projection", () => {
  it("projects every canonical semantic identity exactly once", () => {
    const draft = decodeWorkflowDraft(fixture);
    const projection = buildDraftProjection(draft);

    expect(projectionSemanticIds(projection)).toEqual(draftSemanticIds(draft));
    expect(projectionSemanticIds(projection)).toHaveLength(23);
    expect(() => assertSemanticIdParity(draft, projection)).not.toThrow();
    expect(Object.isFrozen(projection)).toBe(true);
    expect(Object.isFrozen(projection.phases[0]?.blocks[0])).toBe(true);
    expect(Object.isFrozen(draft)).toBe(false);
    expect(Object.isFrozen(draft.layout.positions[0])).toBe(false);
  });

  it("fails closed when a renderer projection loses a semantic identity", () => {
    const draft = decodeWorkflowDraft(fixture);
    const projection = buildDraftProjection(draft);
    const incomplete = {
      ...projection,
      connections: projection.connections.slice(1),
    };

    expect(() => assertSemanticIdParity(draft, incomplete)).toThrow(
      "WORKFLOW_DRAFT_SEMANTIC_ID_PARITY_MISMATCH",
    );
  });

  it("allows renderer replacement without changing projection or emitted intents", () => {
    const draft = decodeWorkflowDraft(fixture);
    const projection = buildDraftProjection(draft);
    const observed: Array<{ renderer: string; ids: readonly string[] }> = [];
    const intents: DraftCanvasIntent[] = [];
    const renderer =
      (name: string): DraftCanvasRenderer =>
      (props) => {
        observed.push({
          renderer: name,
          ids: projectionSemanticIds(props.projection),
        });
        props.onIntent({ type: "select", semanticId: "block.define-product" });
        return null;
      };
    const props = {
      projection,
      selectedSemanticId: null,
      onIntent: (intent: DraftCanvasIntent) => intents.push(intent),
    } as const;

    renderer("first-party")(props);
    renderer("contract-fake")(props);

    expect(observed[0]?.ids).toEqual(observed[1]?.ids);
    expect(intents).toEqual([
      { type: "select", semanticId: "block.define-product" },
      { type: "select", semanticId: "block.define-product" },
    ]);
  });
});
