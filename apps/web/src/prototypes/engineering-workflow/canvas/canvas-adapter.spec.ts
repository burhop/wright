import { describe, expect, it } from "vitest";

import { drillBitHolderWorkflow } from "../fixtures/drill-bit-holder-workflow";
import {
  DEFAULT_PHASE_GAP,
  focusCanvasProjection,
  projectWorkflowToCanvas,
} from "./canvas-adapter";

describe("projectWorkflowToCanvas", () => {
  it("keeps canonical IDs and semantics outside the canvas library", () => {
    const projection = projectWorkflowToCanvas(drillBitHolderWorkflow);

    expect(projection.workflowId).toBe(drillBitHolderWorkflow.workflowId);
    expect(projection.blocks.map(({ block }) => block.blockId)).toEqual(
      drillBitHolderWorkflow.blocks.map((block) => block.blockId),
    );
    expect(
      projection.connections.map(({ connection }) => connection.semantics),
    ).toEqual(
      drillBitHolderWorkflow.connections.map(
        (connection) => connection.semantics,
      ),
    );
  });

  it("stacks configurable phase lanes while retaining relative block positions", () => {
    const projection = projectWorkflowToCanvas(drillBitHolderWorkflow);
    const verifyPhase = projection.phases.find(
      ({ phase }) => phase.phaseId === "verify",
    );
    const analysisDefinition = projection.blocks.find(
      ({ block }) => block.blockId === "analysis-definition",
    );

    expect(verifyPhase?.position.y).toBe(
      drillBitHolderWorkflow.phases[0].height + DEFAULT_PHASE_GAP,
    );
    expect(analysisDefinition?.relativePosition).toEqual({ x: 14, y: 74 });
    expect(analysisDefinition?.absolutePosition.y).toBe(
      verifyPhase!.position.y + 74,
    );
  });

  it("rejects invalid references before a candidate library sees them", () => {
    expect(() =>
      projectWorkflowToCanvas({
        ...drillBitHolderWorkflow,
        blocks: [
          {
            ...drillBitHolderWorkflow.blocks[0],
            phaseId: "missing-phase",
          },
        ],
        connections: [],
      }),
    ).toThrow("references unknown phase");
  });
});
describe("focusCanvasProjection", () => {
  it("filters a large view without changing the canonical projection", () => {
    const projection = projectWorkflowToCanvas(drillBitHolderWorkflow);
    const focused = focusCanvasProjection(projection, "verify");

    expect(focused.phases.map(({ phase }) => phase.phaseId)).toEqual([
      "verify",
    ]);
    expect(focused.blocks.every(({ phaseId }) => phaseId === "verify")).toBe(
      true,
    );
    expect(
      focused.connections.every(
        ({ sourceBlockId, targetBlockId }) =>
          focused.blocks.some(({ block }) => block.blockId === sourceBlockId) &&
          focused.blocks.some(({ block }) => block.blockId === targetBlockId),
      ),
    ).toBe(true);
    expect(projection.phases).toHaveLength(
      drillBitHolderWorkflow.phases.length,
    );
  });

  it("returns the same projection for all phases and rejects unknown phases", () => {
    const projection = projectWorkflowToCanvas(drillBitHolderWorkflow);

    expect(focusCanvasProjection(projection, null)).toBe(projection);
    expect(() => focusCanvasProjection(projection, "missing")).toThrow(
      "Cannot focus unknown phase",
    );
  });
});
