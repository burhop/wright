import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ fetch: vi.fn() }));

vi.mock("./host-adapter", () => ({
  hostAdapter: { mode: "browser", fetch: mocks.fetch },
}));

import {
  workspaceService,
  type EngineeringScenarioPreflight,
  type SupportDiagnosticPreview,
  WorkspaceWorkflowSourceConflictError,
  WorkspaceWorkflowSourceNotFoundError,
} from "./workspace-service";

const digest = "d".repeat(64);

describe("engineering workflow templates", () => {
  beforeEach(() => mocks.fetch.mockReset());

  const template = {
    template_id: "printed-replacement-part",
    version: "1.0.0",
    title: "3D Printed Replacement Part",
    summary: "Create a replacement part.",
    discipline: "Additive manufacturing",
    preview: { asset: "previews/part.svg", alt: "Part workflow" },
    provided_inputs: [],
    requested_inputs: [],
    expected_outputs: [],
    external_effects: ["printer_transfer"],
    source_digest: digest,
    readiness: {
      state: "setup_required" as const,
      definition_valid: true,
      configured: false,
      qualified: false,
      available: false,
      verified_run: false,
      facts: [],
      blocking_reasons: ["Configure adapters."],
    },
  };

  it("loads exactly ten ordered catalog entries without workspace mutation", async () => {
    const templates = Array.from({ length: 10 }, (_, index) => ({
      ...template,
      template_id: `template-${index}`,
    }));
    mocks.fetch.mockResolvedValue(
      response({ catalog_version: "1.0.0", templates }),
    );
    await expect(
      workspaceService.getEngineeringWorkflowTemplates(),
    ).resolves.toEqual(templates);
    expect(mocks.fetch.mock.calls[0][1]).toEqual({ cache: "no-store" });
  });

  it("binds instance creation to version, preview digest, path, and request id", async () => {
    mocks.fetch.mockResolvedValue(response({ workspace_id: "workspace" }, 201));
    await workspaceService.instantiateEngineeringWorkflowTemplate(
      "session",
      template,
      "workflows/part.workflow.wflow",
      "request-0001",
    );
    expect(JSON.parse(mocks.fetch.mock.calls[0][1].body)).toEqual({
      session_id: "session",
      template_version: "1.0.0",
      expected_source_digest: digest,
      workflow_path: "workflows/part.workflow.wflow",
      request_id: "request-0001",
    });
  });

  it("maps collision and stale-preview conflicts to a corrective message", async () => {
    mocks.fetch.mockResolvedValue(response({}, 409));
    await expect(
      workspaceService.instantiateEngineeringWorkflowTemplate(
        "session",
        template,
        "workflows/part.workflow.wflow",
        "request-0001",
      ),
    ).rejects.toThrow("already exists");
  });
});

describe("workflow external action approvals", () => {
  beforeEach(() => mocks.fetch.mockReset());

  const checkpoint = {
    checkpoint_id: "checkpoint-1",
    workspace_id: "workspace",
    workflow_id: "workflow",
    run_id: "run-1",
    step_id: "transfer",
    action_kind: "printer_transfer" as const,
    subject: { action: { kind: "printer_transfer" } },
    subject_digest: "a".repeat(64),
    state: "pending" as const,
    continuation: {},
    actor: null,
    reason: null,
    created_at: 1,
    updated_at: 1,
    expires_at: null,
    external_action: null,
  };

  it("scopes approval detail to the active workspace session", async () => {
    mocks.fetch.mockResolvedValue(response(checkpoint));
    await workspaceService.getWorkflowApprovalCheckpoint(
      "session-1",
      checkpoint.run_id,
      checkpoint.checkpoint_id,
    );
    expect(mocks.fetch.mock.calls[0][0]).toContain("session_id=session-1");
  });

  it("sends an exact-subject approval decision and one-shot resume request", async () => {
    mocks.fetch
      .mockResolvedValueOnce(response({ ...checkpoint, state: "approved" }))
      .mockResolvedValueOnce(response({ ...checkpoint, state: "consumed" }));
    const approved = await workspaceService.decideWorkflowApproval(
      "session-1",
      checkpoint,
      "approved",
      "Checked package",
      "decision-0001",
    );
    await workspaceService.resumeWorkflowApproval(
      "session-1",
      approved,
      "resume-0001",
    );
    expect(JSON.parse(mocks.fetch.mock.calls[0][1].body)).toEqual({
      session_id: "session-1",
      subject_digest: checkpoint.subject_digest,
      decision: "approved",
      reason: "Checked package",
      request_id: "decision-0001",
    });
    expect(JSON.parse(mocks.fetch.mock.calls[1][1].body)).toEqual({
      session_id: "session-1",
      checkpoint_id: checkpoint.checkpoint_id,
      subject_digest: checkpoint.subject_digest,
      request_id: "resume-0001",
    });
  });

  it("explains stale approval conflicts without retrying", async () => {
    mocks.fetch.mockResolvedValue(response({}, 409));
    await expect(
      workspaceService.decideWorkflowApproval(
        "session-1",
        checkpoint,
        "approved",
        null,
        "decision-0001",
      ),
    ).rejects.toThrow("changed or expired");
    expect(mocks.fetch).toHaveBeenCalledOnce();
  });
});

describe("verified workflow demo capture", () => {
  beforeEach(() => mocks.fetch.mockReset());

  it("requests a local package bound to one run and selected artifacts", async () => {
    mocks.fetch.mockResolvedValue(
      response(
        {
          path: "captures/run-1.demo-capture.zip",
          size_bytes: 1024,
          sha256: "a".repeat(64),
          manifest_digest: "b".repeat(64),
          artifact_count: 2,
          published: false,
        },
        201,
      ),
    );
    await workspaceService.createWorkflowDemoCapture(
      "session-1",
      "run-1",
      "runs/example/run.json",
      ["result-1", "result-2"],
      "Verified engineering result.",
    );
    expect(mocks.fetch.mock.calls[0][0]).toContain(
      "/workflow-runs/run-1/capture",
    );
    expect(JSON.parse(mocks.fetch.mock.calls[0][1].body)).toEqual({
      session_id: "session-1",
      run_log_path: "runs/example/run.json",
      artifact_ids: ["result-1", "result-2"],
      caption: "Verified engineering result.",
    });
  });
});

describe("scoped latest execution snapshot", () => {
  beforeEach(() => mocks.fetch.mockReset());
  it("uses bounded GET and carries only its read cancellation signal", async () => {
    const signal = new AbortController().signal;
    mocks.fetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          workspace_id: "workspace",
          workflow_path: "workflows/test.workflow.wflow",
          runs: [],
        }),
      ),
    );
    await expect(
      workspaceService.getWorkspaceWorkflowRuns(
        "session",
        "workflows/test.workflow.wflow",
        { workspaceId: "workspace", latestOnly: true, signal },
      ),
    ).resolves.toEqual([]);
    expect(mocks.fetch.mock.calls[0][0]).toContain("latest_only=true");
    expect(mocks.fetch.mock.calls[0][1]).toEqual({ signal });
  });
  it.each([
    { workspace_id: "foreign", workflow_path: "path", runs: [] },
    { workspace_id: "workspace", workflow_path: "other", runs: [] },
    {
      workspace_id: "workspace",
      workflow_path: "path",
      runs: [{ path: "runs/old.json" }],
    },
  ])("rejects wrong scope or old server projection %#", async (payload) => {
    mocks.fetch.mockResolvedValue(new Response(JSON.stringify(payload)));
    await expect(
      workspaceService.getWorkspaceWorkflowRuns("s", "path", {
        workspaceId: "workspace",
        latestOnly: true,
      }),
    ).rejects.toThrow();
  });
});

describe("terminal workflow review", () => {
  beforeEach(() => mocks.fetch.mockReset());
  const review = {
    review_id: "review-1",
    workflow_path: "workflows/review.wflow",
    package_digest: "package-sha",
    state: "pending",
  } as import("./workspace-service").WorkspaceWorkflowReview;
  it("recognizes pending_review as terminal stream result", async () => {
    const result = {
      status: "pending_review",
      review,
      output_path: "reports/brief-001.html",
      output_bytes: 128,
    };
    const event = vi.fn();
    mocks.fetch.mockResolvedValue(
      new Response(JSON.stringify({ kind: "pending_review", result }) + "\n", {
        headers: { "Content-Type": "application/x-ndjson" },
      }),
    );
    await expect(
      workspaceService.runWorkspaceWorkflowSource(
        "session",
        review.workflow_path,
        digest,
        event,
      ),
    ).resolves.toEqual(result);
    expect(event).not.toHaveBeenCalled();
  });
  it("binds a decision to the exact package and local workspace without inventing actor identity", async () => {
    mocks.fetch.mockResolvedValue(response({ ...review, state: "approved" }));
    await workspaceService.decideWorkspaceWorkflowReview(
      "session",
      review,
      "approved",
      "",
    );
    expect(JSON.parse(mocks.fetch.mock.calls[0][1].body)).toEqual({
      session_id: "session",
      expected_package_digest: "package-sha",
      decision: "approved",
      reason: "",
    });
  });
  it.each([
    {
      detail: {
        message: "Reviewed file changed.",
        correction: "Run again for a new review.",
      },
    },
    {
      message: "Reviewed file changed.",
      details: { correction: "Run again for a new review." },
    },
  ])(
    "preserves stale review correction from either API envelope",
    async (body) => {
      mocks.fetch.mockResolvedValue(response(body, 409));
      await expect(
        workspaceService.decideWorkspaceWorkflowReview(
          "session",
          review,
          "approved",
          "",
        ),
      ).rejects.toThrow("Reviewed file changed. Run again for a new review.");
    },
  );
  it("rejects review history belonging to another workflow", async () => {
    mocks.fetch.mockResolvedValue(
      response({
        reviews: [{ ...review, workflow_path: "workflows/other.wflow" }],
      }),
    );
    await expect(
      workspaceService.getWorkspaceWorkflowReviews(
        "session",
        review.workflow_path,
      ),
    ).rejects.toThrow("did not match");
  });
});

describe("CAD workflow completion", () => {
  beforeEach(() => mocks.fetch.mockReset());
  it.each(["cad/bracket.psm", "cad/bracket.step", "cad/bracket.x_t"])(
    "accepts actual CAD deliverable %s from the event stream",
    async (output_path) => {
      const result = {
        output_path,
        output_bytes: 2048,
        outputs: [{ output_path, output_bytes: 2048, cad_role: "native" }],
      };
      mocks.fetch.mockResolvedValue(
        new Response(JSON.stringify({ kind: "completed", result }) + "\n", {
          headers: { "Content-Type": "application/x-ndjson" },
        }),
      );
      await expect(
        workspaceService.runWorkspaceWorkflowSource(
          "session",
          "workflows/cad.workflow.wflow",
          digest,
          vi.fn(),
        ),
      ).resolves.toEqual(result);
    },
  );
  it("still rejects a malformed result", async () => {
    mocks.fetch.mockResolvedValue(
      response({ output_path: "cad/bracket.psm", output_bytes: "unknown" }),
    );
    await expect(
      workspaceService.runWorkspaceWorkflowSource(
        "session",
        "workflows/cad.workflow.wflow",
        digest,
      ),
    ).rejects.toThrow("invalid workflow run result");
  });
  it("accepts an identified cloud result without a local file", async () => {
    const result = {
      output_path: "",
      output_bytes: 0,
      results: [
        {
          schema_version: 1,
          id: "run:task:model",
          name: "Bracket",
          kind: "cad_model",
          representations: [
            {
              kind: "cloud_resource",
              location: "https://example.invalid/models/1",
              provider_id: "cloud:cad",
              resource_id: "1",
              durability: "persistent",
            },
          ],
        },
      ],
    };
    mocks.fetch.mockResolvedValue(response(result));
    await expect(
      workspaceService.runWorkspaceWorkflowSource(
        "session",
        "workflows/cloud.wflow",
        digest,
      ),
    ).resolves.toEqual(result);
  });
  it("rejects empty completion without an identified result", async () => {
    mocks.fetch.mockResolvedValue(
      response({ output_path: "", output_bytes: 0, results: [] }),
    );
    await expect(
      workspaceService.runWorkspaceWorkflowSource(
        "session",
        "workflows/cloud.wflow",
        digest,
      ),
    ).rejects.toThrow("invalid workflow run result");
  });
  it.each([
    {
      error_code: "workflow_not_ready",
      message: "Image input is incompatible.",
      details: { correction: "Connect it as reference material." },
    },
    {
      detail: {
        message: "Image input is incompatible.",
        correction: "Connect it as reference material.",
      },
    },
  ])(
    "preserves actionable preflight errors from either host envelope",
    async (body) => {
      mocks.fetch.mockResolvedValue(response(body, 422));
      await expect(
        workspaceService.runWorkspaceWorkflowSource(
          "session",
          "workflows/image.wflow",
          digest,
        ),
      ).rejects.toThrow(
        "Image input is incompatible. Connect it as reference material.",
      );
    },
  );
});

describe("workflow input file choices", () => {
  beforeEach(() => mocks.fetch.mockReset());

  it("uses the exact-session endpoint and returns scope-safe relative choices", async () => {
    const files = [{ path: "design/requirements.md", name: "requirements.md" }];
    mocks.fetch.mockResolvedValue(
      response({ workspace_id: "workspace-1", files }),
    );
    await expect(
      workspaceService.getWorkspaceWorkflowInputFiles(
        "session 1",
        "workspace-1",
      ),
    ).resolves.toEqual(files);
    expect(mocks.fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/workflow-sources/input-files?session_id=session+1",
      ),
      { cache: "no-store" },
    );
  });

  it.each([
    "../outside.txt",
    "/outside.txt",
    "C:/secret.txt",
    ".env",
    "design/../../outside.txt",
    "design\\outside.txt",
  ])("rejects unsafe returned path %s", async (path) => {
    mocks.fetch.mockResolvedValue(
      response({
        workspace_id: "workspace-1",
        files: [{ path, name: "outside.txt" }],
      }),
    );
    await expect(
      workspaceService.getWorkspaceWorkflowInputFiles(
        "session-1",
        "workspace-1",
      ),
    ).rejects.toThrow("invalid file");
  });

  it("rejects a response from another workspace", async () => {
    mocks.fetch.mockResolvedValue(
      response({ workspace_id: "different", files: [] }),
    );
    await expect(
      workspaceService.getWorkspaceWorkflowInputFiles(
        "session-1",
        "workspace-1",
      ),
    ).rejects.toThrow("different workspace");
  });
});

function response(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });
  return { promise, resolve, reject };
}

describe("workspace activation client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mocks.fetch.mockReset();
  });

  it("serializes different workspace activations so the latest request completes last", async () => {
    const first = deferred<Response>();
    const second = deferred<Response>();
    const requestedSessions: string[] = [];
    mocks.fetch.mockImplementation(
      async (_input: RequestInfo | URL, init?: RequestInit) => {
        const sessionId = JSON.parse(String(init?.body)).session_id as string;
        requestedSessions.push(sessionId);
        return sessionId === "session-a" ? first.promise : second.promise;
      },
    );

    const activationA = workspaceService.activateWorkspace("session-a");
    await vi.waitFor(() => expect(requestedSessions).toEqual(["session-a"]));
    const activationB = workspaceService.activateWorkspace("session-b");
    await Promise.resolve();
    expect(requestedSessions).toEqual(["session-a"]);

    first.resolve(response({ success: true }));
    await expect(activationA).resolves.toBe(true);
    await vi.waitFor(() =>
      expect(requestedSessions).toEqual(["session-a", "session-b"]),
    );

    second.resolve(response({ success: true }));
    await expect(activationB).resolves.toBe(true);
  });
});

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

describe("workspace workflow source client", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    mocks.fetch.mockReset();
  });

  const workflowDocument = {
    workspace_id: "workspace-1",
    path: "workflows/mounting-bracket.workflow.wflow",
    storage_revision: 3,
    storage_digest: "a".repeat(64),
    definition_revision: 2,
    metadata_authority: "wright_host" as const,
    size_bytes: 128,
    source: "workflow mounting_bracket\nend\n",
  };

  it("loads an exact workspace path without creating it", async () => {
    mocks.fetch.mockResolvedValue(response(workflowDocument));

    await expect(
      workspaceService.getWorkspaceWorkflowSource(
        "session 1",
        "workflows/mounting bracket.workflow.wflow",
      ),
    ).resolves.toEqual(workflowDocument);

    expect(mocks.fetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/workspace/workflow-sources?session_id=session+1&path=workflows%2Fmounting+bracket.workflow.wflow",
      ),
      { cache: "no-store" },
    );
    expect(mocks.fetch.mock.calls[0]?.[1]).not.toHaveProperty("method", "POST");
  });

  it("reports a missing workflow file as an explicit non-creating state", async () => {
    mocks.fetch.mockResolvedValue(response({ message: "missing" }, 404));
    await expect(
      workspaceService.getWorkspaceWorkflowSource(
        "session",
        workflowDocument.path,
      ),
    ).rejects.toBeInstanceOf(WorkspaceWorkflowSourceNotFoundError);
  });

  it("creates only after an explicit call and leaves definition revision assignment to the host", async () => {
    mocks.fetch.mockResolvedValue(response(workflowDocument, 201));
    await expect(
      workspaceService.createWorkspaceWorkflowSource(
        "session",
        workflowDocument.path,
        workflowDocument.source,
      ),
    ).resolves.toEqual(workflowDocument);
    expect(JSON.parse(String(mocks.fetch.mock.calls[0]?.[1]?.body))).toEqual({
      session_id: "session",
      path: workflowDocument.path,
      source: workflowDocument.source,
    });
  });

  it("saves with compare-and-swap storage identity", async () => {
    mocks.fetch.mockResolvedValue(
      response({ ...workflowDocument, storage_revision: 4 }),
    );
    await workspaceService.updateWorkspaceWorkflowSource(
      "session",
      workflowDocument.path,
      "updated source",
      3,
      workflowDocument.storage_digest,
      true,
    );
    expect(JSON.parse(String(mocks.fetch.mock.calls[0]?.[1]?.body))).toEqual({
      session_id: "session",
      path: workflowDocument.path,
      source: "updated source",
      expected_storage_revision: 3,
      expected_storage_digest: workflowDocument.storage_digest,
      semantic_change_validated: true,
    });
  });

  it("projects a stale compare-and-swap response without exposing server text", async () => {
    mocks.fetch.mockResolvedValue(
      response(
        {
          error_code: "workflow_source_conflict",
          message: "server text",
          trace_id: "trace-private",
          details: {
            current_storage_revision: 9,
            current_storage_digest: "b".repeat(64),
          },
        },
        409,
      ),
    );

    const failure = await workspaceService
      .updateWorkspaceWorkflowSource(
        "session",
        workflowDocument.path,
        "local edits",
        3,
        workflowDocument.storage_digest,
        true,
      )
      .catch((error: unknown) => error);
    expect(failure).toBeInstanceOf(WorkspaceWorkflowSourceConflictError);
    expect(failure).toMatchObject({
      code: "workflow_source_conflict",
      currentStorageRevision: 9,
      currentStorageDigest: "b".repeat(64),
    });
    expect((failure as Error).message).toContain("local edits were kept");
    expect((failure as Error).message).not.toContain("server text");
  });
});
