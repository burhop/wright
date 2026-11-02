import { StrictMode, useState } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { OpenWorkspaceToolSetup } from "../../services/workspace-tool-setup";
import thermalSource from "../../../../../packages/workspace_service/src/workspace_service/engineering_workflow_templates/templates/heat-spreader-sizing.workflow.wflow?raw";
import { providerSetupGuides } from "../../services/provider-setup-guides";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { WorkspacePanel } from "./WorkspacePanel";
import { ViewerPanelProvider } from "../../store/viewer";

// Read the real existing template, without expanding browser-wide Node types.
const thermalCrypto = await vi.importActual<{
  createHash: (algorithm: string) => {
    update: (text: string) => { digest: (encoding: "hex") => string };
  };
}>("node:crypto");
const thermalDigest = thermalCrypto
  .createHash("sha256")
  .update(thermalSource)
  .digest("hex");

const mocks = vi.hoisted(() => ({
  create: vi.fn(),
  models: vi.fn(),
  chat: {
    state: {
      activeSessionId: "session-one",
      sessions: [],
      messages: [],
      promptQueue: [],
    },
    refreshSessions: vi.fn(),
    selectSession: vi.fn(),
    createSession: vi.fn(),
    sendMessage: vi.fn(),
    steerMessage: vi.fn(),
    cancelActiveStream: vi.fn(),
  },
}));
vi.mock("../../store/sessions", () => ({ useChat: () => mocks.chat }));
vi.mock("../../config/workflow-recovery", () => ({
  workflowRecoveryEnabled: () => true,
}));
vi.mock("../../services/surfaces/feature-flags", () => ({
  workspaceSurfacesEnabled: () => false,
}));
vi.mock("../../hooks/useHealthStatus", () => ({ default: () => [] }));
vi.mock("../../services/agent-service", () => ({
  agentService: {
    getActiveAgent: vi.fn().mockResolvedValue("hermes"),
    listHermesModels: mocks.models,
  },
}));
vi.mock("../../services/workspace-service", async (importOriginal) => ({
  ...(await importOriginal<
    typeof import("../../services/workspace-service")
  >()),
  workspaceService: {
    getWorkspaceFiles: vi.fn().mockResolvedValue({
      path: "/",
      name: "Workspace",
      type: "directory",
      children: [],
    }),
    getWorkspaceToolsById: vi.fn().mockResolvedValue({ servers: [] }),
    createWorkspaceWorkflowSource: mocks.create,
  },
}));
vi.mock("../pages/WorkflowRecoveryPage", () => ({
  WorkflowRecoveryPage: function TestAuthoringView(props: {
    workflowFilePath: string;
    workspaceId: string;
    createIfMissing: boolean;
    onConfigureTools?: OpenWorkspaceToolSetup;
  }) {
    const [returned, setReturned] = useState(false);
    return (
      <div
        data-testid="mounted-authoring-view"
        data-workspace={props.workspaceId}
        data-create={String(props.createIfMissing)}
      >
        {props.workflowFilePath}
        <button
          onClick={() =>
            void props
              .onConfigureTools?.({
                workspaceId: props.workspaceId,
                sessionId: "session-one",
                sourcePath: props.workflowFilePath,
                sourceDigest: thermalDigest,
                title: "Configure thermal analysis",
                purpose: "Evaluate the existing heat-spreader workflow.",
                requirements: [
                  "An independent analysis capability is required.",
                ],
                guideText: providerSetupGuides.oasis,
              })
              .then(() => setReturned(true))
          }
        >
          Configure test capability
        </button>
        {returned && <p>Returned to exact thermal setup</p>}
      </div>
    );
  },
}));
vi.mock("./MessageComposer", () => ({ default: () => null }));
vi.mock("./ChatTranscript", () => ({ default: () => null }));

function open(search: string) {
  return render(
    <StrictMode>
      <MemoryRouter initialEntries={[`/workspace/workspace-one${search}`]}>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-one" sessionId="session-one" />
        </ViewerPanelProvider>
      </MemoryRouter>
    </StrictMode>,
  );
}
describe("ordinary workspace passive workflow links", () => {
  beforeEach(() => {
    localStorage.clear();
    mocks.create.mockClear();
    mocks.models.mockResolvedValue({ groups: [], current_value: "" });
  });
  it("uses the same workspace handoff for a different thermal process without creating or executing it", async () => {
    open(
      "?workflow=canonical&workflowPath=workflows%2Fheat-spreader.workflow.wflow",
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Configure test capability" }),
    );
    const help = await screen.findByRole("region", {
      name: "Configure thermal analysis",
    });
    expect(help).toHaveTextContent(
      "Evaluate the existing heat-spreader workflow",
    );
    expect(help).toHaveTextContent("/workflows/heat-spreader.workflow.wflow");
    expect(
      screen.getByRole("link", { name: "Open Tool Registry (new tab)" }),
    ).toHaveAttribute("href", "/tool-registry");
    fireEvent.click(
      screen.getByRole("button", { name: "Return to job setup" }),
    );
    await screen.findByText("Returned to exact thermal setup");
    expect(
      screen.queryByRole("region", { name: "Configure thermal analysis" }),
    ).toBeNull();
    expect(screen.getByTestId("mounted-authoring-view")).toHaveTextContent(
      "/workflows/heat-spreader.workflow.wflow",
    );
    expect(mocks.create).not.toHaveBeenCalled();
    expect(mocks.chat.sendMessage).not.toHaveBeenCalled();
  });
  it("reattaches the exact authoring tab after StrictMode repeats its workspace reset", async () => {
    open(
      "?workflow=canonical&workflowPath=workflows%2Fsaved-design.workflow.wflow",
    );
    const editor = await screen.findByTestId("mounted-authoring-view");
    expect(editor).toHaveTextContent("/workflows/saved-design.workflow.wflow");
    expect(editor).toHaveAttribute("data-workspace", "workspace-one");
    expect(editor).toHaveAttribute("data-create", "false");
    await waitFor(() =>
      expect(screen.getAllByTestId("mounted-authoring-view")).toHaveLength(1),
    );
    expect(
      screen.getByTestId("retained-workspace-workflow-panel"),
    ).toHaveAttribute("aria-hidden", "false");
    expect(mocks.create).not.toHaveBeenCalled();
  });
  it("does not create or mount a workflow for an invalid passive source path", async () => {
    open("?workflow=canonical&workflowPath=..%2Foutside.workflow.wflow");
    expect(
      await screen.findByTestId("workspace-workflow-path-error"),
    ).toBeVisible();
    expect(
      screen.queryByTestId("mounted-authoring-view"),
    ).not.toBeInTheDocument();
    expect(mocks.create).not.toHaveBeenCalled();
  });
  it("shows the resolved model and directs unsupported remote changes to Model Setup", async () => {
    mocks.models.mockResolvedValue({
      current_value: "configured-provider::configured-model",
      groups: [
        {
          provider: "configured-provider",
          label: "Configured provider",
          options: [
            {
              value: "configured-provider::configured-model",
              label: "configured-model",
              provider: "configured-provider",
              model: "configured-model",
              is_current: true,
            },
          ],
        },
      ],
      selection_supported: false,
      selection_message:
        "Using the configured model. Change it in Model Setup before starting a new run.",
    });
    open("");
    const model = await screen.findByTestId("llm-model-select");
    await waitFor(() =>
      expect(model).toHaveValue("configured-provider::configured-model"),
    );
    expect(model).toBeDisabled();
    expect(model).toHaveAttribute(
      "title",
      expect.stringContaining("Model Setup"),
    );
    expect(screen.getByText("Model Setup")).toBeVisible();
    expect(
      screen.queryByText("Hermes models unavailable"),
    ).not.toBeInTheDocument();
  });
});
