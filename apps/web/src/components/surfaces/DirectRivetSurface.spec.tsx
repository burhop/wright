import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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
  });

  const dispatchFrameMessage = (
    frame: HTMLIFrameElement,
    data: Record<string, unknown>,
    origin = "http://127.0.0.1:9180",
  ) => {
    const event = new MessageEvent("message", { data, origin });
    Object.defineProperty(event, "source", { value: frame.contentWindow });
    window.dispatchEvent(event);
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

  it("opens and saves Rivet workflows through Wright workspace APIs", async () => {
    const user = userEvent.setup();
    const loaded = vi.fn();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);
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

  it("shows an opaque run dialog and requires explicit approval", async () => {
    const user = userEvent.setup();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);
    mocks.reviewRivetWorkflow.mockResolvedValue(approvedWorkflow);

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
    const panel = screen.getByTestId("direct-rivet-run-panel");
    expect(panel.getAttribute("style")).toContain("--color-surface-elevated");
    expect(panel).toHaveStyle({ opacity: "1" });
    expect(screen.getByTestId("direct-rivet-review-state")).toHaveTextContent(
      "Revision 1 needs approval",
    );
    expect(screen.getByTestId("direct-rivet-run-start")).toBeDisabled();

    await user.click(screen.getByTestId("direct-rivet-run-approve"));
    await waitFor(() =>
      expect(mocks.reviewRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
        "approved",
        "local-user",
      ),
    );
    expect(screen.getByTestId("direct-rivet-review-state")).toHaveTextContent(
      "Revision 1 approved",
    );
    expect(screen.getByTestId("direct-rivet-run-start")).toBeEnabled();
    expect(screen.getByTestId("direct-rivet-run-feedback")).toHaveTextContent(
      "Revision 1 approved. It is ready to run.",
    );
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
    await user.click(screen.getByTestId("direct-rivet-run-start"));

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

    await user.click(screen.getByTestId("direct-rivet-run"));
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
    await waitFor(() =>
      expect(screen.getByTestId("direct-rivet-run-result")).toHaveTextContent(
        "succeeded · 42 ms",
      ),
    );
    expect(screen.getByTestId("direct-rivet-run-result")).toHaveTextContent(
      'output: "hello"',
    );
    expect(screen.getByTestId("direct-rivet-run-result")).not.toHaveTextContent(
      "cost",
    );
    expect(screen.getByTestId("direct-rivet-run-feedback")).toHaveTextContent(
      'Run succeeded in 42 ms. Output: output: "hello"',
    );
    expect(screen.getByTestId("direct-rivet-run-result")).toHaveAttribute(
      "title",
      JSON.stringify(succeeded.outputs),
    );
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
    await user.click(screen.getByTestId("direct-rivet-run-start"));
    await user.click(await screen.findByTestId("direct-rivet-cancel"));

    await waitFor(() =>
      expect(mocks.cancelRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        running,
      ),
    );
    expect(screen.getByTestId("direct-rivet-run-result")).toHaveTextContent(
      "cancelled",
    );
  });
});
