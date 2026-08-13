import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  EngineeringModelService,
  EngineeringModelServiceError,
} from "../src/services/engineering-model-service";

const mocks = vi.hoisted(() => ({ fetch: vi.fn() }));

vi.mock("../src/services/host-adapter", () => ({
  hostAdapter: {
    getApiBaseUrl: () => "",
    fetch: mocks.fetch,
  },
}));

describe("EngineeringModelService", () => {
  beforeEach(() => mocks.fetch.mockReset());

  it("encodes bounded catalog filters through the Wright host adapter", async () => {
    mocks.fetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          snapshot: {
            snapshot_id: "wright-models-bundled-1",
            catalog_digest: "a".repeat(64),
            freshness: "bundled",
            offline: true,
          },
          models: [],
          next_cursor: null,
          total: 0,
        }),
        { status: 200 },
      ),
    );
    const service = new EngineeringModelService();

    await service.listCatalog({
      search: "point cloud",
      task: "point_cloud_classification",
      readiness: ["needs_review", "blocked"],
      maximum_bytes: 6_000_000,
      limit: 25,
    });

    const url = String(mocks.fetch.mock.calls[0][0]);
    expect(url).toContain("/api/v1/engineering-models/catalog?");
    expect(url).toContain("search=point+cloud");
    expect(url).toContain("task=point_cloud_classification");
    expect(url).toContain("readiness=needs_review");
    expect(url).toContain("readiness=blocked");
    expect(url).toContain("maximum_bytes=6000000");
    expect(url).toContain("limit=25");
  });

  it("loads one detail without exposing a runtime connection", async () => {
    mocks.fetch.mockResolvedValue(
      new Response(JSON.stringify({ model_id: "wright-affine-test" }), {
        status: 200,
      }),
    );
    const service = new EngineeringModelService();

    await expect(
      service.getCatalogModel("wright-affine-test"),
    ).resolves.toEqual({ model_id: "wright-affine-test" });
    expect(mocks.fetch).toHaveBeenCalledWith(
      "/api/v1/engineering-models/catalog/wright-affine-test",
    );
  });

  it("returns the bounded server recovery envelope", async () => {
    mocks.fetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: {
            category: "catalog_cursor",
            message: "Catalog cursor is stale.",
            recovery: "Reload the current offline snapshot.",
          },
        }),
        { status: 400 },
      ),
    );
    const service = new EngineeringModelService();

    await expect(service.listCatalog({ cursor: "stale" })).rejects.toEqual(
      expect.objectContaining<Partial<EngineeringModelServiceError>>({
        category: "catalog_cursor",
        message: "Catalog cursor is stale.",
        recovery: "Reload the current offline snapshot.",
      }),
    );
  });
});
