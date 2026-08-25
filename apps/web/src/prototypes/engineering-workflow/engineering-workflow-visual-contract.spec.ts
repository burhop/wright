import { describe, expect, it } from "vitest";

import {
  ENGINEERING_WORKFLOW_VISUAL_CONTRACT_VERSION,
  engineeringWorkflowVisualContract,
  workflowRoleLabels,
} from "./engineering-workflow-visual-contract";

describe("engineering workflow visual contract", () => {
  it("locks the accepted role and status color grammar", () => {
    expect(engineeringWorkflowVisualContract.roleColors).toEqual({
      input: "#159cff",
      "ai-task": "#9b4dff",
      "mcp-action": "#16c8c1",
      artifact: "#12c881",
      decision: "#ffb20b",
      notification: "#76dc48",
    });
    expect(engineeringWorkflowVisualContract.connectionColors).toEqual({
      data: "#159cff",
      control: "#12c881",
      feedback: "#ff4058",
    });
    expect(engineeringWorkflowVisualContract.colors.feedback).not.toBe(
      engineeringWorkflowVisualContract.colors.decision,
    );
  });

  it("keeps style semantics independent of engineering capability names", () => {
    expect(ENGINEERING_WORKFLOW_VISUAL_CONTRACT_VERSION).toBe("cp2a-1");
    expect(workflowRoleLabels["mcp-action"]).toBe("MCP action");
    expect(engineeringWorkflowVisualContract.invariants).toEqual({
      colorsEncodeRoleOrStatus: true,
      phaseNamesAreConfigurable: true,
      feedbackHasNonColorCue: true,
      engineeringCategoriesDoNotSelectRuntimeServices: true,
    });
  });
});
