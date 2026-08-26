import { describe, expect, it } from "vitest";

import { workflowOutputsFrom } from "./workflow-output";

describe("workflow output references", () => {
  it("extracts serializable output references without treating arbitrary objects as artifacts", () => {
    const outputs = workflowOutputsFrom({
      accepted: true,
      outputs: [
        {
          outputId: "model-1",
          title: "Mounting plate",
          kind: "model",
          description: "Live model",
          durability: "session",
          producer: { block: "mcp", toolName: "example.create" },
          actions: [
            {
              actionId: "view",
              kind: "view",
              label: "View model",
              available: true,
            },
          ],
        },
        { title: "not a reference" },
      ],
    });

    expect(outputs).toHaveLength(1);
    expect(outputs[0].outputId).toBe("model-1");
  });
});
