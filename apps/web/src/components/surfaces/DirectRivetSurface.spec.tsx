import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DirectRivetSurface } from "./DirectRivetSurface";

const workflow = {
  workflow_id: "workflow-1",
  slug: "rivet",
  revision: 1,
  etag: "etag-1",
  review_state: null,
  reviewer: null,
  reviewed_at: null,
};

const document = {
  ...workflow,
  project: "version: 4\ndata:\n  graphs: {}\n",
  datasets: {},
};

const approvedWorkflow = {
  ...workflow,
  review_state: "approved" as const,
  reviewer: "local-user",
  reviewed_at: 1,
};

const mocks = vi.hoisted(() => ({
  listRivetWorkflowOperations: vi.fn(),
  listRivetWorkflowTemplates: vi.fn(),
  readRivetWorkflow: vi.fn(),
  createBlankRivetWorkflow: vi.fn(),
  createRivetWorkflowFromTemplate: vi.fn(),
  saveRivetWorkflow: vi.fn(),
  lintRivetWorkflowGraph: vi.fn(),
  reviewRivetWorkflow: vi.fn(),
  runRivetWorkflow: vi.fn(),
  getRivetWorkflowRun: vi.fn(),
  getRivetWorkflowHistory: vi.fn(),
  getRivetRunInspection: vi.fn(),
  getRecentRivetRuns: vi.fn(),
  cancelRivetWorkflow: vi.fn(),
}));

vi.mock("../../services/workspace-service", () => ({
  workspaceService: mocks,
}));

describe("DirectRivetSurface", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.listRivetWorkflowTemplates.mockResolvedValue([]);
    mocks.getRivetWorkflowHistory.mockResolvedValue([]);
    mocks.getRecentRivetRuns.mockResolvedValue({
      workflow_id: "workflow-1",
      current_revision: 1,
      runs: [],
    });
  });

  const inspectionFor = (run: Record<string, unknown>) => ({
    schema_version: 1,
    run: {
      run_id: run.run_id,
      workspace_id: "workspace-1",
      session_id: "session-1",
      workflow_id: run.workflow_id,
      revision: run.revision,
      digest: run.digest,
      graph: run.graph,
      generation: run.generation,
      state: run.state,
      started_at: "2026-08-20T14:00:00Z",
      completed_at: run.state === "running" ? null : "2026-08-20T14:00:01Z",
      duration_ms: run.duration_ms,
      reason_code: run.reason,
      trace_id: "trace-1",
      latest_sequence: 1,
      has_outputs: Boolean(run.outputs),
      has_diagnostic: run.state === "failed" || run.state === "cancelled",
      output_truncated: false,
      output_redaction_count: 0,
    },
    progress: {
      phase: run.state,
      current_step_id: null,
      completed_steps: run.state === "running" ? 0 : 1,
      total_steps: 1,
      last_sequence: 1,
      updated_at: "2026-08-20T14:00:01Z",
    },
    events: [],
    steps: [],
    final_outputs: Object.entries(
      (run.outputs as Record<
        string,
        { type: string; value: unknown }
      > | null) || {},
    ).map(([name, output]) => ({
      result_id: name,
      name,
      kind: output.type,
      value: output.value,
      preview:
        typeof output.value === "string"
          ? output.value
          : JSON.stringify(output.value),
      media_type: null,
      size_bytes: null,
      digest: null,
      artifact_path: null,
      safe_link: null,
      redacted: false,
      truncated: false,
      complete: true,
    })),
    diagnostic:
      run.state === "cancelled"
        ? {
            code: "RIVET_RUN_CANCELLED",
            summary: "Workflow run was cancelled.",
            recovery_action: "Run the saved revision again when ready.",
            failed_step_id: null,
            node_id: null,
            qualified_tool_name: null,
            request_id: null,
            trace_id: "trace-1",
            residue_possible: false,
            retry_step_available: false,
            full_rerun_available: true,
            technical_details: {},
          }
        : null,
    completeness: {
      outputs_complete: true,
      steps_complete: true,
      events_complete: true,
      evidence_available: true,
      reasons: [],
    },
  });

  const dispatchFrameMessage = (
    frame: HTMLIFrameElement,
    data: Record<string, unknown>,
    origin = "http://127.0.0.1:9180",
  ) => {
    const event = new MessageEvent("message", { data, origin });
    Object.defineProperty(event, "source", { value: frame.contentWindow });
    act(() => window.dispatchEvent(event));
  };

  const connectBridge = (
    project = document.project,
  ): { frame: HTMLIFrameElement; postMessage: ReturnType<typeof vi.spyOn> } => {
    const frame = screen.getByTitle("Rivet graph canvas") as HTMLIFrameElement;
    const postMessage = vi
      .spyOn(frame.contentWindow!, "postMessage")
      .mockImplementation((message: unknown) => {
        const request = message as Record<string, unknown>;
        if (request.type === "wright-rivet:set-project") {
          queueMicrotask(() =>
            dispatchFrameMessage(frame, {
              type: "wright-rivet:project-set",
              requestId: request.requestId,
            }),
          );
        } else if (request.type === "wright-rivet:get-project") {
          queueMicrotask(() =>
            dispatchFrameMessage(frame, {
              type: "wright-rivet:project",
              requestId: request.requestId,
              project,
            }),
          );
        }
      });
    dispatchFrameMessage(frame, {
      type: "wright-rivet:ready",
      protocolVersion: 2,
    });
    return { frame, postMessage };
  };

  it("shows a visible, actionable result after checking the graph", async () => {
    const user = userEvent.setup();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);
    mocks.lintRivetWorkflowGraph.mockResolvedValue({
      ...workflow,
      graph_id: "graph-1",
      snapshot_digest: "snapshot-1",
      policy_snapshot_digest: "policy-1",
      requirements: [],
      capabilities: [],
      issues: [],
      next_after: null,
    });

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );
    await waitFor(() =>
      expect(mocks.readRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
      ),
    );

    await user.click(screen.getByRole("button", { name: "Check Rivet graph" }));

    expect(mocks.lintRivetWorkflowGraph).toHaveBeenCalledWith(
      "session-1",
      "rivet",
    );
    expect(
      await screen.findByTestId("direct-rivet-run-feedback"),
    ).toHaveTextContent("Graph checked · no problems found.");
  });

  it("opens and saves Rivet workflows through Wright workspace APIs", async () => {
    const user = userEvent.setup();
    const loaded = vi.fn();
    const canonicalProject =
      "version: 4\ndata:\n  graphs:\n    canonical: {}\n";
    const canonicalDocument = {
      ...document,
      revision: 2,
      etag: "etag-2",
      project: canonicalProject,
    };
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(canonicalDocument);
    mocks.saveRivetWorkflow.mockResolvedValue({ ...workflow, revision: 2 });

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
        onWorkflowLoaded={loaded}
      />,
    );

    await waitFor(() =>
      expect(mocks.readRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
      ),
    );
    expect(screen.queryByLabelText("Rivet workflow")).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText("Open Rivet workflow from workspace"),
    ).not.toBeInTheDocument();
    expect(loaded).not.toHaveBeenCalled();

    const editedProject = "version: 4\ndata:\n  graphs: edited\n";
    const { postMessage } = connectBridge(editedProject);
    await waitFor(() =>
      expect(postMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "wright-rivet:set-project",
          path: "rivet.rivet-project",
        }),
        "http://127.0.0.1:9180",
      ),
    );

    await user.click(screen.getByTestId("direct-rivet-save-workspace"));

    await waitFor(() =>
      expect(mocks.saveRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
        1,
        editedProject,
        {},
      ),
    );
    await waitFor(() =>
      expect(postMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "wright-rivet:set-project",
          project: canonicalProject,
          path: "rivet.rivet-project",
        }),
        "http://127.0.0.1:9180",
      ),
    );
  });

  it("reloads the displayed workflow after a Wright chat mutation", async () => {
    const updatedDocument = {
      ...document,
      revision: 2,
      etag: "etag-2",
      project:
        "version: 4\ndata:\n  graphs:\n    main:\n      nodes:\n        block-1:\n          type: text\n",
    };
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(updatedDocument);

    const { rerender } = render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );
    await waitFor(() =>
      expect(mocks.readRivetWorkflow).toHaveBeenCalledTimes(1),
    );
    const { postMessage } = connectBridge();
    await waitFor(() =>
      expect(postMessage).toHaveBeenCalledWith(
        expect.objectContaining({ project: document.project }),
        "http://127.0.0.1:9180",
      ),
    );

    rerender(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        externalRevisionToken="session-1:1"
        onOpenInBrowser={vi.fn()}
      />,
    );

    await waitFor(() =>
      expect(mocks.readRivetWorkflow).toHaveBeenCalledTimes(2),
    );
    await waitFor(() =>
      expect(postMessage).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "wright-rivet:set-project",
          project: updatedDocument.project,
          path: "rivet.rivet-project",
        }),
        "http://127.0.0.1:9180",
      ),
    );
    expect(screen.getByRole("status")).toHaveTextContent(
      "Workflow updated by Wright AI at revision 2.",
    );
  });

  it("creates a blank Rivet workflow in the active workspace", async () => {
    const user = userEvent.setup();
    const loaded = vi.fn();
    const createdWorkflow = {
      ...workflow,
      workflow_id: "workflow-2",
      slug: "untitled-workflow",
      etag: "etag-2",
    };
    const createdDocument = {
      ...createdWorkflow,
      project: "version: 4\ndata:\n  graphs: {}\n",
      datasets: {},
    };
    mocks.listRivetWorkflowOperations
      .mockResolvedValueOnce([workflow])
      .mockResolvedValueOnce([workflow, createdWorkflow]);
    mocks.readRivetWorkflow
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(createdDocument);
    mocks.createBlankRivetWorkflow.mockResolvedValue(createdWorkflow);

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
        onWorkflowLoaded={loaded}
      />,
    );

    await waitFor(() =>
      expect(mocks.readRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
      ),
    );
    connectBridge();
    await user.click(screen.getByTestId("direct-rivet-new-workspace"));

    await waitFor(() =>
      expect(mocks.createBlankRivetWorkflow).toHaveBeenCalledWith("session-1"),
    );
    expect(mocks.readRivetWorkflow).toHaveBeenLastCalledWith(
      "session-1",
      "untitled-workflow",
    );
    expect(loaded).toHaveBeenLastCalledWith(
      expect.objectContaining({ slug: "untitled-workflow" }),
    );
    expect(screen.queryByLabelText("Rivet workflow")).not.toBeInTheDocument();
    expect(
      screen.queryByLabelText("Open Rivet workflow from workspace"),
    ).not.toBeInTheDocument();
  });

  it("creates a workflow from the template picker without duplicate document chrome", async () => {
    const user = userEvent.setup();
    const loaded = vi.fn();
    const template = {
      template_id: "mcp-agent",
      title: "MCP Agent",
      description: "Tool-using agent wired for MCP.",
      kind: "advanced" as const,
      requirements: ["model-provider", "mcp-server-configuration"],
    };
    const createdWorkflow = {
      ...workflow,
      workflow_id: "workflow-3",
      slug: "mcp-agent",
      etag: "etag-3",
    };
    const createdDocument = {
      ...createdWorkflow,
      project: "version: 4\ndata:\n  graphs: template\n",
      datasets: {},
    };
    mocks.listRivetWorkflowTemplates.mockResolvedValue([template]);
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(createdDocument);
    mocks.createRivetWorkflowFromTemplate.mockResolvedValue(createdWorkflow);

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
        onWorkflowLoaded={loaded}
      />,
    );

    await user.click(screen.getByTestId("direct-rivet-template-picker"));
    const templateMenu = await screen.findByTestId(
      "direct-rivet-template-menu",
    );
    expect(templateMenu.style.background).toBe("var(--color-surface, #131b2e)");
    expect(templateMenu).toHaveStyle({ opacity: "1" });
    await user.click(await screen.findByText("MCP Agent"));

    await waitFor(() =>
      expect(mocks.createRivetWorkflowFromTemplate).toHaveBeenCalledWith(
        "session-1",
        template,
      ),
    );
    expect(mocks.readRivetWorkflow).toHaveBeenLastCalledWith(
      "session-1",
      "mcp-agent",
    );
    expect(loaded).toHaveBeenLastCalledWith(
      expect.objectContaining({ slug: "mcp-agent" }),
    );
    expect(
      screen.queryByTestId("direct-rivet-template-menu"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("mcp-agent.rivet-project"),
    ).not.toBeInTheDocument();
  });

  it("ignores readiness messages from the wrong origin", async () => {
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );

    await waitFor(() =>
      expect(mocks.readRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
      ),
    );
    const frame = screen.getByTitle("Rivet graph canvas") as HTMLIFrameElement;
    dispatchFrameMessage(
      frame,
      { type: "wright-rivet:ready", protocolVersion: 2 },
      "http://malicious.invalid",
    );

    expect(screen.getByTestId("direct-rivet-save-workspace")).toBeDisabled();
    expect(screen.getByTestId("direct-rivet-status")).toHaveTextContent(
      "Waiting for the graph canvas",
    );
  });

  it("reports an expired preview instead of leaving raw authorization JSON", async () => {
    const unavailable = vi.fn();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
        onEditorUnavailable={unavailable}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    const frame = screen.getByTitle("Rivet graph canvas") as HTMLIFrameElement;
    const previewDocument = window.document.implementation.createHTMLDocument();
    previewDocument.body.innerHTML =
      '<pre>{"detail":"SURFACE_PREVIEW_UNAUTHORIZED"}</pre>';
    Object.defineProperty(frame, "contentDocument", {
      configurable: true,
      value: previewDocument,
    });

    fireEvent.load(frame);

    expect(unavailable).toHaveBeenCalledWith("SURFACE_PREVIEW_UNAUTHORIZED");
    expect(screen.getByTestId("direct-rivet-status")).toHaveTextContent(
      "Rivet preview authorization expired. Reconnecting",
    );
  });

  it("renews a cross-origin preview when its verified frame reports lost authority", async () => {
    const unavailable = vi.fn();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
        onEditorUnavailable={unavailable}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    const frame = screen.getByTitle("Rivet graph canvas") as HTMLIFrameElement;

    dispatchFrameMessage(frame, {
      type: "wright-surface:authorization-failed",
      reason: "SURFACE_PREVIEW_UNAUTHORIZED",
    });

    expect(unavailable).toHaveBeenCalledWith("SURFACE_PREVIEW_UNAUTHORIZED");
    expect(screen.getByTestId("direct-rivet-status")).toHaveTextContent(
      "Rivet preview authorization expired. Reconnecting",
    );
  });

  it("ignores preview authorization messages from another origin", async () => {
    const unavailable = vi.fn();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
        onEditorUnavailable={unavailable}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    const frame = screen.getByTitle("Rivet graph canvas") as HTMLIFrameElement;

    dispatchFrameMessage(
      frame,
      {
        type: "wright-surface:authorization-failed",
        reason: "SURFACE_PREVIEW_UNAUTHORIZED",
      },
      "http://malicious.invalid",
    );

    expect(unavailable).not.toHaveBeenCalled();
  });

  it("shows Hermes AI availability and saves an AI-applied canvas revision", async () => {
    const user = userEvent.setup();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce({ ...document, revision: 2, etag: "etag-2" });
    mocks.saveRivetWorkflow.mockResolvedValue({ ...workflow, revision: 2 });

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    const generated = "version: 4\ndata:\n  graphs:\n    generated: {}\n";
    const { frame } = connectBridge(generated);
    dispatchFrameMessage(frame, {
      type: "wright-rivet:ai-status",
      available: true,
    });
    await waitFor(() =>
      expect(screen.getByTestId("direct-rivet-ai-status")).toHaveAccessibleName(
        "Rivet AI connected",
      ),
    );

    await user.click(screen.getByTestId("direct-rivet-save-workspace"));
    await waitFor(() =>
      expect(mocks.saveRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
        1,
        generated,
        {},
      ),
    );
    expect(screen.getByTestId("direct-rivet-status")).toHaveTextContent(
      "Workflow saved at revision 2",
    );
  });

  it("runs the main graph with default inputs immediately from the toolbar", async () => {
    const user = userEvent.setup();
    const succeeded = {
      run_id: "run-default",
      workflow_id: "workflow-1",
      revision: 1,
      digest: "etag-1",
      graph: null,
      generation: 1,
      state: "succeeded",
      reason: null,
      outputs: { output: { type: "string", value: "done" } },
      duration_ms: 21,
      output_truncated: false,
    };
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);
    mocks.runRivetWorkflow.mockResolvedValue(succeeded);
    mocks.getRivetRunInspection.mockResolvedValue(inspectionFor(succeeded));

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    connectBridge();

    await user.click(screen.getByTestId("direct-rivet-run"));

    await waitFor(() =>
      expect(mocks.runRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
        {
          expectedRevision: 1,
          expectedDigest: "etag-1",
          graph: undefined,
          inputs: {},
        },
      ),
    );
    expect(
      screen.queryByTestId("direct-rivet-run-panel"),
    ).not.toBeInTheDocument();
    expect(
      await screen.findByTestId("rivet-run-state-succeeded"),
    ).toBeVisible();
    await waitFor(() =>
      expect(screen.getByTestId("rivet-run-inspector")).toHaveClass("is-open"),
    );
    expect(screen.getByTestId("rivet-run-result-output")).toHaveTextContent(
      "done",
    );
  });

  it("opens an opaque run-options dialog without workflow approval", async () => {
    const user = userEvent.setup();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    connectBridge();

    await user.click(screen.getByTestId("direct-rivet-run-options"));
    const panel = screen.getByTestId("direct-rivet-run-panel");
    expect(panel.getAttribute("style")).toContain("--color-surface-elevated");
    expect(panel).toHaveStyle({ opacity: "1" });
    expect(screen.getByTestId("direct-rivet-run-start")).toBeEnabled();
    expect(screen.queryByText(/approve revision/i)).not.toBeInTheDocument();
    expect(mocks.reviewRivetWorkflow).not.toHaveBeenCalled();
  });

  it("blocks an unsaved canvas draft before exact-revision execution", async () => {
    const user = userEvent.setup();
    mocks.listRivetWorkflowOperations.mockResolvedValue([approvedWorkflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);
    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    connectBridge("version: 4\ndata:\n  graphs:\n    unsaved: {}\n");

    await user.click(screen.getByTestId("direct-rivet-run"));

    await waitFor(() =>
      expect(screen.getByTestId("direct-rivet-status")).toHaveTextContent(
        "Save the current canvas changes",
      ),
    );
    expect(screen.getByTestId("direct-rivet-run-feedback")).toHaveTextContent(
      "Save the current canvas changes",
    );
    expect(mocks.runRivetWorkflow).not.toHaveBeenCalled();
  });

  it("runs a selected graph with inputs and shows correlated progress and outputs", async () => {
    const user = userEvent.setup();
    const running = {
      run_id: "run-1",
      workflow_id: "workflow-1",
      revision: 1,
      digest: "etag-1",
      graph: "Passthrough",
      generation: 1,
      state: "running",
      reason: null,
      outputs: null,
      duration_ms: null,
      output_truncated: false,
    };
    const succeeded = {
      ...running,
      state: "succeeded",
      outputs: {
        cost: { type: "number", value: 0 },
        output: { type: "string", value: "hello" },
      },
      duration_ms: 42,
    };
    mocks.listRivetWorkflowOperations.mockResolvedValue([approvedWorkflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);
    mocks.runRivetWorkflow.mockResolvedValue(running);
    mocks.getRivetWorkflowRun.mockResolvedValue(succeeded);
    mocks.getRivetRunInspection.mockResolvedValue(inspectionFor(succeeded));
    mocks.getRivetWorkflowHistory.mockResolvedValue([
      { sequence: 1, kind: "progress", payload: { phase: "node-finish" } },
    ]);
    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    connectBridge();

    await user.click(screen.getByTestId("direct-rivet-run-options"));
    await user.type(
      screen.getByTestId("direct-rivet-run-graph"),
      "Passthrough",
    );
    fireEvent.change(screen.getByTestId("direct-rivet-run-inputs"), {
      target: { value: '{"input":"hello"}' },
    });
    await user.click(screen.getByTestId("direct-rivet-run-start"));

    await waitFor(() =>
      expect(mocks.runRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
        {
          expectedRevision: 1,
          expectedDigest: "etag-1",
          graph: "Passthrough",
          inputs: { input: "hello" },
        },
      ),
    );
    expect(
      await screen.findByTestId("rivet-run-state-succeeded"),
    ).toBeVisible();
    await waitFor(() =>
      expect(screen.getByTestId("rivet-run-inspector")).toHaveClass("is-open"),
    );
    expect(screen.getByTestId("rivet-run-result-output")).toHaveTextContent(
      "hello",
    );
    expect(screen.getByTestId("rivet-run-result-cost")).toHaveTextContent("0");
    expect(screen.getByTestId("rivet-run-inspector")).toHaveClass("is-open");
  });

  it("offers a correlated cancel control while a workflow is running", async () => {
    const user = userEvent.setup();
    const running = {
      run_id: "run-cancel",
      workflow_id: "workflow-1",
      revision: 1,
      digest: "etag-1",
      graph: null,
      generation: 1,
      state: "running",
      reason: null,
      outputs: null,
      duration_ms: null,
      output_truncated: false,
    };
    mocks.listRivetWorkflowOperations.mockResolvedValue([approvedWorkflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);
    mocks.runRivetWorkflow.mockResolvedValue(running);
    mocks.getRivetWorkflowRun.mockImplementation(() => new Promise(() => {}));
    mocks.getRivetRunInspection.mockResolvedValue(inspectionFor(running));
    mocks.cancelRivetWorkflow.mockResolvedValue({
      ...running,
      state: "cancelled",
      reason: "cancelled",
    });
    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
      />,
    );
    await waitFor(() => expect(mocks.readRivetWorkflow).toHaveBeenCalled());
    connectBridge();
    await user.click(screen.getByTestId("direct-rivet-run"));
    await user.click(await screen.findByTestId("direct-rivet-cancel"));

    await waitFor(() =>
      expect(mocks.cancelRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        running,
      ),
    );
    expect(screen.getByTestId("direct-rivet-run-feedback")).toHaveTextContent(
      "cancelled",
    );
  });
});
