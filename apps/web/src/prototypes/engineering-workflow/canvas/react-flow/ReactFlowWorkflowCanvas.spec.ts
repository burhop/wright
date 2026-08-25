import { describe, expect, it } from "vitest";

import { drillBitHolderWorkflow } from "../../fixtures/drill-bit-holder-workflow";
import { projectWorkflowToCanvas } from "../canvas-adapter";
import { projectReactFlowEdges } from "./ReactFlowWorkflowCanvas";

describe("projectReactFlowEdges", () => {
  it("uses a dedicated, non-color-only route for feedback connections", () => {
    const edges = projectReactFlowEdges(
      projectWorkflowToCanvas(drillBitHolderWorkflow),
    );
    const feedbackEdges = edges.filter(
      ({ data }) => data?.semantics === "feedback",
    );

    expect(feedbackEdges.length).toBeGreaterThan(0);
    expect(feedbackEdges).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          type: "workflowFeedback",
          style: expect.objectContaining({ strokeDasharray: "8 5" }),
          data: expect.objectContaining({
            feedbackRailY: expect.any(Number),
          }),
        }),
      ]),
    );
  });

  it("keeps forward data and control connections on the standard step route", () => {
    const edges = projectReactFlowEdges(
      projectWorkflowToCanvas(drillBitHolderWorkflow),
    );
    const forwardEdges = edges.filter(
      ({ data }) => data?.semantics !== "feedback",
    );

    expect(forwardEdges.every(({ type }) => type === "step")).toBe(true);
  });
});
