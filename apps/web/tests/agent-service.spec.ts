import { describe, expect, it } from "vitest";
import { summarizeProgressPayload } from "../src/services/agent-service";

describe("summarizeProgressPayload", () => {
  it("uses generic advertised fields and computes bounded progress", () => {
    const summary = summarizeProgressPayload({
      server: "geometry",
      tool: "geometry__create",
      title: "Create geometry",
      status: "running",
      progress: 1,
      total: 4,
      message: "Sketching",
      correlationId: "request-1",
    });

    expect(summary).toMatchObject({
      title: "Create geometry",
      percentage: 25,
      server: "geometry",
      tool: "geometry__create",
      status: "running",
      progress: 1,
      total: 4,
      correlationId: "request-1",
    });
    expect(summary.detail).toContain("geometry / geometry__create");
    expect(summary.detail).toContain("Sketching");
  });

  it("falls back safely when no provider fields are supplied", () => {
    expect(summarizeProgressPayload({})).toEqual({
      title: "Tool progress",
      detail: undefined,
      message: "Tool progress",
      percentage: undefined,
      server: undefined,
      tool: undefined,
      status: undefined,
      progress: undefined,
      total: undefined,
      correlationId: undefined,
      heartbeat: undefined,
    });
  });
});
