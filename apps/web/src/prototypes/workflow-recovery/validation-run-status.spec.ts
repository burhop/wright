import { describe, expect, it } from "vitest";
import { validationRunPresentation } from "./validation-run-status";

describe("process validation run status", () => {
  it.each([
    [
      { kind: "design_check", status: "revise" },
      "Output held for correction",
    ],
    [
      { kind: "validation_feedback_delivered", remaining_revisions: 2 },
      "Repairing output",
    ],
    [
      { kind: "validation_exhausted", remaining_revisions: 0 },
      "Correction budget exhausted",
    ],
  ])("presents %s as %s", (event, label) => {
    expect(validationRunPresentation(event)?.label).toBe(label);
  });

  it("does not replace ordinary or passing run diagnostics", () => {
    expect(
      validationRunPresentation({ kind: "design_check", status: "pass" }),
    ).toBeNull();
    expect(validationRunPresentation({ kind: "step_started" })).toBeNull();
  });
});
