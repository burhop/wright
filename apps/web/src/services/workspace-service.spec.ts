import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ fetch: vi.fn() }));

vi.mock("./host-adapter", () => ({
  hostAdapter: { mode: "browser", fetch: mocks.fetch },
}));

import {
  workspaceService,
  type EngineeringScenarioPreflight,
  type SupportDiagnosticPreview,
} from "./workspace-service";

const digest = "d".repeat(64);

function response(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("engineering scenario workspace client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mocks.fetch.mockReset();
  });

  it("uses the typed list, detail, preflight, start, report, compare, cancel, and export routes", async () => {
    const entry = {
      scenario_id: "structural-bracket",
      revision: 1,
      title: "Structural bracket",
      summary: "Build and analyze a bracket.",
      domains: ["cad", "python", "fea"],
      tier: "tier1",
      resource_class: "small",
      expected_duration_seconds: 20,
      manifest_digest: digest,
    };
    const preflight: EngineeringScenarioPreflight = {
      preflight_id: "preflight",
      scenario_id: entry.scenario_id,
      scenario_revision: 1,
      manifest_digest: digest,
      workflow_slug: "scenario-structural-bracket",
      workflow_revision: 1,
      workflow_digest: digest,
      graph_id: "Main",
      binding_set_digest: "b".repeat(64),
      state: "ready",
      capabilities: [],
      environment: { tier: "tier1" },
      blockers: [],
      expires_at: "2099-01-01T00:00:00Z",
    };
    const report = {
      scenario_run_id: "scenario-run",
      workflow_run_id: "workflow-run",
      workspace_id: "workspace",
      session_id: "session",
      scenario_id: entry.scenario_id,
      scenario_revision: 1,
      manifest_digest: digest,
      workflow_digest: digest,
      binding_set_digest: "b".repeat(64),
      state: "passed",
      identity: {},
      artifacts: [],
      environment: {},
      cleanup_state: "clean",
      residue: {},
      assertions: [],
      report_digest: "e".repeat(64),
    };
    mocks.fetch.mockImplementation(
      async (input: RequestInfo | URL, init?: RequestInit) => {
        const url = String(input);
        if (url.endsWith("/engineering-scenarios"))
          return response({ scenarios: [entry] });
        if (url.endsWith("/engineering-scenarios/structural-bracket"))
          return response({
            manifest: { scenario_id: entry.scenario_id },
            manifest_digest: digest,
          });
        if (url.endsWith("/structural-bracket/preflight")) {
          expect(init?.method).toBe("POST");
          expect(JSON.parse(String(init?.body))).toEqual({
            session_id: "session",
          });
          return response(preflight);
        }
        if (url.endsWith("/structural-bracket/runs")) {
          const body = JSON.parse(String(init?.body));
          expect(body).toMatchObject({
            session_id: "session",
            manifest_digest: digest,
            binding_set_digest: preflight.binding_set_digest,
          });
          expect(body).not.toHaveProperty("review_digest");
          return response(
            {
              scenario_run_id: "scenario-run",
              state: "running",
              workflow_run: {},
            },
            202,
          );
        }
        if (url.includes("/compare/"))
          return response({
            strictly_reproducible: true,
            differences: [],
            assertion_changes: [],
          });
        if (url.includes("/cancel"))
          return response({ run_id: "workflow-run", state: "cancelled" });
        if (url.includes("/export?")) return response(report);
        if (url.includes("/runs/scenario-run?")) return response(report);
        return response({ message: "unexpected route" }, 404);
      },
    );

    expect(await workspaceService.listEngineeringScenarios()).toEqual([entry]);
    expect(
      await workspaceService.getEngineeringScenarioDetail(entry.scenario_id),
    ).toMatchObject({ manifest_digest: digest });
    expect(
      await workspaceService.preflightEngineeringScenario(
        "session",
        entry.scenario_id,
      ),
    ).toEqual(preflight);
    expect(
      await workspaceService.startEngineeringScenario("session", preflight),
    ).toMatchObject({ scenario_run_id: "scenario-run" });
    expect(
      await workspaceService.getEngineeringScenarioReport(
        "session",
        "scenario-run",
      ),
    ).toEqual(report);
    expect(
      await workspaceService.compareEngineeringScenarioReports(
        "session",
        "scenario-run",
        "scenario-run-two",
      ),
    ).toMatchObject({ strictly_reproducible: true });
    expect(
      await workspaceService.cancelEngineeringScenario(
        "session",
        "scenario-run",
      ),
    ).toMatchObject({ state: "cancelled" });

    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    const createObjectURL = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:scenario-report");
    const revokeObjectURL = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => undefined);
    await workspaceService.exportEngineeringScenarioReport(
      "session",
      "scenario-run",
    );
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:scenario-report");
  });

  it("does not start without an exact prepared tool binding", async () => {
    await expect(
      workspaceService.startEngineeringScenario("session", {
        preflight_id: "preflight",
        scenario_id: "structural-bracket",
        scenario_revision: 1,
        manifest_digest: digest,
        workflow_slug: "scenario-structural-bracket",
        workflow_revision: 1,
        workflow_digest: digest,
        graph_id: "Main",
        binding_set_digest: null,
        state: "ready",
        capabilities: [],
        environment: {},
        blockers: [],
        expires_at: "2099-01-01T00:00:00Z",
      }),
    ).rejects.toThrow("Prepare the exact scenario workflow first");
    expect(mocks.fetch).not.toHaveBeenCalled();
  });
});

describe("support diagnostic workspace client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mocks.fetch.mockReset();
  });

  it("binds export to the exact preview and downloads the inert response", async () => {
    const preview: SupportDiagnosticPreview = {
      snapshot: {
        schema_version: "1.0",
        snapshot_id: "snapshot_12345678",
        created_at: "2026-08-13T12:00:00Z",
        expires_at: "2099-08-13T12:05:00Z",
        workspace_id: "workspace-1",
        principal_digest: `sha256:${"a".repeat(64)}`,
        scope: { session_id: "session-1" },
        summary: {
          status: "healthy",
          reason: "READY",
          next_action: "REVIEW_PREVIEW",
        },
        providers: [],
        state_inventory: {
          schema_version: "1.0",
          data_schema: 16,
          catalog_snapshot: {
            channel: "stable",
            sequence: 1,
            digest: `sha256:${"b".repeat(64)}`,
            state: "active",
          },
          counts: {},
          digests: {},
          storage: [],
        },
        failures: [],
        categories: [
          {
            name: "provider-status",
            disposition: "included",
            item_count: 0,
            reason: "INCLUDED",
          },
        ],
        snapshot_digest: `sha256:${"c".repeat(64)}`,
      },
      snapshot_digest: `sha256:${"c".repeat(64)}`,
      confirmation_token: "one-use-token",
      expires_at: "2099-08-13T12:05:00Z",
      filename: "wright-support-workspace-1.json",
    };
    mocks.fetch.mockResolvedValueOnce(response(preview)).mockResolvedValueOnce(
      new Response(JSON.stringify(preview.snapshot), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const exact = await workspaceService.previewSupportDiagnostics(
      "workspace-1",
      { session_id: "session-1" },
    );
    expect(exact).toEqual(preview);
    expect(JSON.parse(String(mocks.fetch.mock.calls[0]?.[1]?.body))).toEqual({
      workspace_id: "workspace-1",
      scope: { session_id: "session-1" },
    });

    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    const createObjectURL = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:support-diagnostic");
    const revokeObjectURL = vi
      .spyOn(URL, "revokeObjectURL")
      .mockImplementation(() => undefined);
    await workspaceService.exportSupportDiagnostics(exact);

    expect(JSON.parse(String(mocks.fetch.mock.calls[1]?.[1]?.body))).toEqual({
      workspace_id: "workspace-1",
      snapshot_digest: preview.snapshot_digest,
      confirmation_token: preview.confirmation_token,
    });
    expect(createObjectURL).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:support-diagnostic");
  });

  it("maps server reason codes to safe recovery without exposing response data", async () => {
    mocks.fetch.mockResolvedValueOnce(
      response(
        {
          detail: {
            code: "DIAGNOSTIC_PREVIEW_STALE",
            message: "raw private server detail",
          },
        },
        409,
      ),
    );
    await expect(
      workspaceService.previewSupportDiagnostics("workspace-1"),
    ).rejects.toThrow("Local state changed. Create a fresh preview.");
  });
});

describe("Rivet run inspection workspace client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mocks.fetch.mockReset();
  });

  it("requests an incremental inspection with no-store semantics", async () => {
    const inspection = { schema_version: 1, run: { run_id: "run/1" } };
    mocks.fetch.mockResolvedValue(response(inspection));
    await expect(
      workspaceService.getRivetRunInspection("session 1", "run/1", 7),
    ).resolves.toEqual(inspection);
    expect(mocks.fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/workflows/runs/run%2F1/inspection?session_id=session%201&after_sequence=7",
      ),
      { cache: "no-store" },
    );
  });

  it("bounds recent-run limits and preserves the existing read-only route", async () => {
    const recent = { workflow_id: "workflow-1", current_revision: 2, runs: [] };
    mocks.fetch.mockResolvedValue(response(recent));
    await expect(
      workspaceService.getRecentRivetRuns("session 1", "my workflow", 500),
    ).resolves.toEqual(recent);
    expect(mocks.fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/workflows/my%20workflow/runs?session_id=session%201&limit=50",
      ),
      { cache: "no-store" },
    );
  });
});
