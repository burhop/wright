import { describe, expect, it } from "vitest";

import { workflowRecoveryEnabled } from "./workflow-recovery";

describe("Workflow Recovery feature flag", () => {
  it("defaults off and rejects values outside the allowlist", () => {
    for (const value of [undefined, "", "0", "false", "no", "off", "enabled"]) {
      expect(workflowRecoveryEnabled({ VITE_WRIGHT_WORKFLOW_RECOVERY: value })).toBe(false);
    }
  });

  it("accepts only explicit truthy values", () => {
    for (const value of ["1", "true", "yes", "on", "TRUE", " Yes "]) {
      expect(workflowRecoveryEnabled({ VITE_WRIGHT_WORKFLOW_RECOVERY: value })).toBe(true);
    }
  });
});
