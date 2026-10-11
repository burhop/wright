import { describe, expect, it } from "vitest";
import {
  validationEvidenceReference,
  validationRunPresentation,
} from "./validation-run-status";

describe("process validation run status", () => {
  it.each([
    [{ kind: "design_check", status: "revise" }, "Output held for correction"],
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

  it("exposes only workspace-relative assessment evidence", () => {
    expect(
      validationEvidenceReference({
        kind: "design_check",
        assessment_id: "assessment-123",
        assessment_path: "validation/assessment-123.json",
        complete_result_ref:
          "wright://workspace/workspace/validation/assessment-123",
      }),
    ).toEqual({
      assessmentId: "assessment-123",
      path: "validation/assessment-123.json",
      completeResultRef:
        "wright://workspace/workspace/validation/assessment-123",
    });
    expect(
      validationEvidenceReference({
        kind: "design_check",
        report: { assessment_path: "../outside.json" },
      }),
    ).toBeNull();
    expect(
      validationEvidenceReference({
        kind: "design_check",
        assessment_path: "C:\\outside.json",
      }),
    ).toBeNull();
  });
});
