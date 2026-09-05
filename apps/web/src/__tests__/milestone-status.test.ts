import { describe, expect, it } from "vitest";
import { decodeNativeMilestone } from "../services/milestone-status";
import fixture from "./native-milestone-projection.json";

describe("native milestone strict projection", () => {
  it("accepts the Python projection and keeps missing evidence untested", () => {
    const value = decodeNativeMilestone(fixture, fixture.source_commit);
    expect(value.counts.verification).toEqual({ completed: 0, total: 32 });
    expect(value.counts.integration).toEqual({
      completed: 0,
      total: 30,
      not_applicable: 2,
    });
    expect(value.checks.every((check) => check.status === "not_tested")).toBe(
      true,
    );
  });
  it.each(["counts", "missing", "duplicate", "scope", "readiness", "unknown"])(
    "rejects %s corruption",
    (mutation) => {
      const value = structuredClone(fixture);
      if (mutation === "counts") value.counts.verification.completed = 32;
      if (mutation === "missing")
        value.source_record.acceptance[0].required_check_ids.push("UNKNOWN");
      if (mutation === "duplicate") value.tasks.push(value.tasks[0]);
      if (mutation === "scope") value.scope_revision = 2;
      if (mutation === "readiness")
        value.readiness.native_milestone = "complete";
      if (mutation === "unknown") Object.assign(value, { unverifiable: true });
      expect(() =>
        decodeNativeMilestone(value, fixture.source_commit),
      ).toThrow();
    },
  );
  it("rejects a different source identity", () => {
    expect(() => decodeNativeMilestone(fixture, "b".repeat(40))).toThrow();
  });
});
