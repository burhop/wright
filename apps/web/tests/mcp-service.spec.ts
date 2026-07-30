import { beforeEach, describe, expect, it, vi } from "vitest";
import { mcpService } from "../src/services/mcp-service";

const mocks = vi.hoisted(() => ({
  fetch: vi.fn(),
}));

vi.mock("../src/services/host-adapter", () => ({
  hostAdapter: {
    getApiBaseUrl: () => "",
    fetch: mocks.fetch,
  },
}));

describe("mcpService", () => {
  beforeEach(() => {
    mocks.fetch.mockReset();
  });

  it("uses the host adapter for registry fetches", async () => {
    mocks.fetch.mockResolvedValue(
      new Response(JSON.stringify({ servers: [] }), { status: 200 }),
    );

    await expect(mcpService.getServers()).resolves.toEqual([]);

    expect(mocks.fetch).toHaveBeenCalledWith("/api/mcp/servers");
  });
});
