import { describe, expect, it } from "vitest";

import { drillBitHolderWorkflow } from "../fixtures/drill-bit-holder-workflow";
import { DEFAULT_PHASE_GAP, projectWorkflowToCanvas } from "./canvas-adapter";

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
