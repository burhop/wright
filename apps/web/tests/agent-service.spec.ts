import { afterEach, describe, expect, it, vi } from "vitest";
import {
  HermesAgentService,
  summarizeProgressPayload,
} from "../src/services/agent-service";

afterEach(() => {
  vi.unstubAllGlobals();
});

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

  it("shares and caches the static command catalog request", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          commands: [{ name: "wright", description: "Wright", prefix: "/" }],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    const service = new HermesAgentService();

    const [first, second] = await Promise.all([
      service.getCommands(),
      service.getCommands(),
    ]);
    const third = await service.getCommands();

    expect(first).toEqual(second);
    expect(third).toEqual(first);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
