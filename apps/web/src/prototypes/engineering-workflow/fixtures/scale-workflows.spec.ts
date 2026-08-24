import { describe, expect, it } from "vitest";

import {
  createScaleWorkflow,
  workflowForBakeoffSearch,
} from "./scale-workflows";

describe("scale workflow fixtures", () => {
  it.each([25, 100] as const)(
    "creates a deterministic, connected %i-block workflow",
    (blockCount) => {
      const workflow = createScaleWorkflow(blockCount);

      expect(workflow.blocks).toHaveLength(blockCount);
      expect(new Set(workflow.blocks.map(({ blockId }) => blockId)).size).toBe(
        blockCount,
      );
      expect(workflow.phases).toHaveLength(3);
      expect(
        workflow.connections.filter(
          ({ semantics }) => semantics === "feedback",
        ),
      ).toHaveLength(3);
      expect(workflow.connections.length).toBe(blockCount + 2);
    },
  );

  it("selects scale fixtures only for supported query values", () => {
    expect(workflowForBakeoffSearch("?scale=25").blocks).toHaveLength(25);
    expect(workflowForBakeoffSearch("?scale=100").blocks).toHaveLength(100);
    expect(workflowForBakeoffSearch("?scale=500").workflowId).toBe(
      "drill-bit-holder-design-to-fabrication",
    );
  });
});
