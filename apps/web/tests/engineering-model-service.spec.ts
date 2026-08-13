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

  it("uses typed lifecycle, import, cancellation, and SSE endpoints", async () => {
    const plan = {
      schema_version: "1.0",
      plan_id: "plan-1",
      plan_digest: "a".repeat(64),
      model_id: "wright-affine-test",
      variant_id: "json-cpu-f64",
      state: "confirmable",
      effects: [],
      blockers: [],
      requirements: {
        network: "none",
        credential: "none",
        license_action: "none",
        runtime_change: "separate_plan_only",
      },
      rollback: "Remove inactive state.",
      cleanup: "Delete staging.",
      expires_at: "2026-08-13T12:10:00Z",
    };
    const operation = {
      operation_id: "operation-1",
      state: "running",
      phase: "acquiring",
      progress: {
        completed_items: 0,
        total_items: 1,
        completed_bytes: 0,
        maximum_bytes: 10,
      },
      cleanup_state: "not_needed",
    };
    mocks.fetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(plan), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(plan), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(plan), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(operation), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ...operation, state: "cancelling" }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(
        new Response(
          `id: 1\nevent: operation\ndata: ${JSON.stringify({ sequence: 1, operation })}\n\n`,
          { status: 200, headers: { "Content-Type": "text/event-stream" } },
        ),
      );
    const service = new EngineeringModelService();

    await service.createPlan("wright-affine-test", "json-cpu-f64");
    await service.createImportPlan(new Blob(["archive"]));
    await service.getPlan("plan-1");
    await service.confirmPlan("plan-1", "a".repeat(64));
    await service.cancelOperation("operation-1");
    const events = await service.readOperationEvents("operation-1", 0);

    expect(mocks.fetch.mock.calls[0][1]).toEqual(
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          operation_kind: "install",
          model_id: "wright-affine-test",
          variant_id: "json-cpu-f64",
        }),
      }),
    );
    expect(mocks.fetch.mock.calls[1][1].body).toBeInstanceOf(FormData);
    expect(mocks.fetch.mock.calls[4][0]).toContain("operation-1/cancel");
    expect(mocks.fetch.mock.calls[5][1].headers["Last-Event-ID"]).toBe("0");
    expect(events).toEqual([{ sequence: 1, operation }]);
  });

  it("uses typed standard-test evidence and workspace binding endpoints", async () => {
    const runtime = {
      installation_id: "installation-one",
      installation_state: "ready",
      adapter_id: "wright-deterministic",
      adapter_version: "1.0.0",
      evidence: [],
    };
    const binding = {
      binding_id: "binding-one",
      binding_digest: "a".repeat(64),
      workspace_id: "workspace-one",
      installation_id: "installation-one",
      task_id: "predict",
      tool_name: "wright_model__wright_affine_test__predict",
      policy_snapshot_digest: "b".repeat(64),
      state: "enabled",
    };
    mocks.fetch
      .mockResolvedValueOnce(
        new Response(JSON.stringify(runtime), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(runtime), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(binding), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ ...binding, state: "disabled" }), {
          status: 200,
        }),
      );
    const service = new EngineeringModelService();

    await service.runStandardTest("installation-one");
    await service.getStandardTestEvidence("installation-one");
    await service.createWorkspaceBinding(
      "workspace-one",
      "installation-one",
      "predict",
    );
    await service.setWorkspaceBindingState(
      "workspace-one",
      "binding-one",
      "disabled",
    );

    expect(mocks.fetch.mock.calls[0][0]).toContain(
      "installation-one/standard-test",
    );
    expect(mocks.fetch.mock.calls[0][1]).toEqual({ method: "POST" });
    expect(mocks.fetch.mock.calls[1][0]).toContain("installation-one/evidence");
    expect(mocks.fetch.mock.calls[2][1].body).toBe(
      JSON.stringify({
        installation_id: "installation-one",
        task_id: "predict",
      }),
    );
    expect(mocks.fetch.mock.calls[2][1].headers).toEqual(
      expect.objectContaining({
        "X-Wright-Workspace-ID": "workspace-one",
      }),
    );
    expect(mocks.fetch.mock.calls[3][1].body).toBe(
      JSON.stringify({ state: "disabled" }),
    );
    expect(mocks.fetch.mock.calls[3][1].headers).toEqual(
      expect.objectContaining({
        "X-Wright-Workspace-ID": "workspace-one",
      }),
    );
  });
});
