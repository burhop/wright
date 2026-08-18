import { afterEach, describe, expect, it, vi } from "vitest";

import { LiveHealthService } from "./health-service";

function healthResponse(
  state: "connected" | "disconnected" | "unknown",
): Response {
  return {
    ok: true,
    json: async () => ({ state, latencyMs: 1 }),
  } as Response;
}

describe("LiveHealthService", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("publishes completed checks without waiting for a slow service", async () => {
    let resolveHermes: ((response: Response) => void) | undefined;
    const hermesResponse = new Promise<Response>((resolve) => {
      resolveHermes = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input);
        if (url.includes("/api/agent/health")) return hermesResponse;
        return Promise.resolve(healthResponse("connected"));
      }),
    );

    const service = new LiveHealthService();
    const unsubscribe = service.onStatusChange(() => undefined);
    service.startPolling(10_000);

    try {
      await vi.waitFor(() => {
        expect(
          service
            .getStatuses()
            .find((status) => status.serviceId === "llm-backend")?.state,
        ).toBe("connected");
      });
      expect(
        service
          .getStatuses()
          .find((status) => status.serviceId === "hermes-agent")?.state,
      ).toBe("unknown");
    } finally {
      resolveHermes?.(healthResponse("connected"));
      service.stopPolling();
      unsubscribe();
    }
  });
});
