import { describe, expect, it } from "vitest";

import { drillBitHolderWorkflow } from "../../fixtures/drill-bit-holder-workflow";
import { projectWorkflowToCanvas } from "../canvas-adapter";
import { projectLiteGraphCandidate } from "./litegraph-projection";

describe("projectLiteGraphCandidate", () => {
  it("creates disposable nodes and stable per-target input slots", () => {
    const canvas = projectWorkflowToCanvas(drillBitHolderWorkflow);
    const candidate = projectLiteGraphCandidate(canvas);

    expect(candidate.nodes).toHaveLength(drillBitHolderWorkflow.blocks.length);
    expect(candidate.links).toHaveLength(
      drillBitHolderWorkflow.connections.length,
    );
    expect(
      candidate.links
        .filter(({ targetBlockId }) => targetBlockId === "create-specification")
        .map(({ targetSlot }) => targetSlot),
    ).toEqual([0, 1, 2, 3]);
  });

  it("retains feedback semantics and engineer-facing labels", () => {
    const candidate = projectLiteGraphCandidate(
      projectWorkflowToCanvas(drillBitHolderWorkflow),
    );

    expect(
      candidate.links
        .filter(({ semantics }) => semantics === "feedback")
        .map(({ connectionId, label }) => ({ connectionId, label })),
    ).toEqual([
      { connectionId: "spec-revise", label: "revise" },
      { connectionId: "model-revise", label: "revise" },
      { connectionId: "quote-rejected", label: "reject" },
    ]);
  });
});
