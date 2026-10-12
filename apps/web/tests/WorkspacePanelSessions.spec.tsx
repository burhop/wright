import {
  act,
  fireEvent,
  render,
  screen,
  within,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import WorkspacePanel from "../src/components/chat/WorkspacePanel";
import { ViewerPanelProvider } from "../src/store/viewer";
import {
  createProcessWorkspaceTab,
  processWorkspaceQuery,
} from "../src/services/process-workspace-tabs";

const mockUseChat = vi.fn();
const mockGetWorkspace = vi.fn();
const mockSendMessage = vi.fn();
const mockUpdateWorkspaceSession = vi.fn();
const mockSelectSession = vi.fn();
const mockGetWorkspaceMcpStatus = vi.fn();
const mockGetWorkspaceFiles = vi.fn();
const mockGetWorkspaceTools = vi.fn();
const mockGetWorkspaceToolsById = vi.fn();
const mockListHermesModels = vi.fn();
const mockEnsureDefaultRivetWorkflow = vi.fn();
const mockCreateWorkflowSource = vi.fn();
const mockGetWorkspaceConfig = vi.fn();
const mockUpdateWorkspaceConfig = vi.fn();

function LocationProbe() {
  const location = useLocation();
  return (
    <output data-testid="location-probe">{`${location.pathname}${location.search}`}</output>
  );
}

vi.mock("../src/store/sessions", () => ({
  useChat: () => mockUseChat(),
}));

vi.mock("../src/hooks/useHealthStatus", () => ({
  default: () => [
    {
      serviceId: "hermes-agent",
      name: "Hermes Agent",
      endpoint: "/api/agent/health",
      state: "connected",
      lastChecked: Date.now(),
    },
  ],
}));

vi.mock("../src/services/agent-service", () => ({
  agentService: {
    getActiveAgent: vi.fn().mockResolvedValue("hermes"),
    setActiveAgent: vi.fn().mockResolvedValue("hermes"),
    getCommands: vi.fn().mockResolvedValue([]),
    listHermesModels: (...args: unknown[]) => mockListHermesModels(...args),
  },
}));

vi.mock("../src/services/workspace-service", () => ({
  workspaceService: {
    getWorkspace: (...args: unknown[]) => mockGetWorkspace(...args),
    createWorkspaceWorkflowSource: (...args: unknown[]) =>
      mockCreateWorkflowSource(...args),
    updateWorkspaceSession: (...args: unknown[]) =>
      mockUpdateWorkspaceSession(...args),
    getWorkspaceFiles: (...args: unknown[]) => mockGetWorkspaceFiles(...args),
    getGitStatus: vi.fn().mockResolvedValue({
      branch_name: "main",
      is_clean: true,
      changes: [],
    }),
    getGitHistory: vi.fn().mockResolvedValue({ commits: [] }),
    getWorkspaceConfig: (...args: unknown[]) => mockGetWorkspaceConfig(...args),
    updateWorkspaceConfig: (...args: unknown[]) =>
      mockUpdateWorkspaceConfig(...args),
    getWorkspaceTools: (...args: unknown[]) => mockGetWorkspaceTools(...args),
    getWorkspaceToolsById: (...args: unknown[]) =>
      mockGetWorkspaceToolsById(...args),
    ensureDefaultRivetWorkflow: (...args: unknown[]) =>
      mockEnsureDefaultRivetWorkflow(...args),
    readRivetWorkflow: vi.fn(),
    toggleWorkspaceTool: vi.fn().mockResolvedValue(true),
    toggleWorkspaceToolById: vi.fn().mockResolvedValue(true),
    getWorkspaceMcpStatus: (...args: unknown[]) =>
      mockGetWorkspaceMcpStatus(...args),
  },
  MergeConflictError: class MergeConflictError extends Error {},
}));

vi.mock("../src/components/surfaces/SurfaceWorkspace", () => ({
  SurfaceWorkspace: () => null,
}));

vi.mock("../src/components/surfaces/ManagedRivetSurface", () => ({
  ManagedRivetSurface: () => <div data-testid="managed-rivet-fixture" />,
}));

vi.mock("../src/components/surfaces/DirectBrepSurface", () => ({
  DirectBrepSurface: () => <div data-testid="direct-brep-fixture" />,
}));

vi.mock("../src/components/pages/WorkflowRecoveryPage", () => ({
  WorkflowRecoveryPage: (props: {
    workspaceId: string;
    sessionId: string;
    workspaceName: string;
    workflowFilePath: string;
    reopenRequest?: number;
    onOpenWorkflow?: (path: string) => void;
    onUnsavedChange?: (path: string, unsaved: boolean) => void;
    onSavingChange?: (path: string, saving: boolean) => void;
    onOpenProcess?: (process: {
      workspace_id: string;
      source_path: string;
      source_digest: string;
    }) => void;
    createIfMissing?: boolean;
    navigation?: import("../src/services/process-navigation").ProcessNavigationRequest;
  }) => (
    <div
      data-testid="workspace-workflow-fixture"
      data-workspace-id={props.workspaceId}
      data-session-id={props.sessionId}
      data-workspace-name={props.workspaceName}
      data-workflow-file={props.workflowFilePath}
      data-reopen-request={props.reopenRequest}
      data-create-if-missing={String(props.createIfMissing)}
      data-navigation-block={props.navigation?.resolution.target.block_id}
    >
      <input
        aria-label="Fixture source draft"
        defaultValue="Saved fixture source"
        onChange={() => props.onUnsavedChange?.(props.workflowFilePath, true)}
      />
      <button
        onClick={() => props.onUnsavedChange?.(props.workflowFilePath, false)}
      >
        Mark fixture saved
      </button>
      <button
        onClick={() => props.onSavingChange?.(props.workflowFilePath, true)}
      >
        Start pending fixture save
      </button>
      <button
        onClick={() => props.onSavingChange?.(props.workflowFilePath, false)}
      >
        Finish pending fixture save
      </button>
      <button onClick={() => props.onOpenWorkflow?.(props.workflowFilePath)}>
        Reopen fixture file
      </button>
      <button
        onClick={() =>
          props.onOpenWorkflow?.("workflows/other-design.workflow.wflow")
        }
      >
        Open other fixture workflow
      </button>
      <button
        onClick={() =>
          props.onOpenProcess?.({
            workspace_id: props.workspaceId,
            source_path: props.workflowFilePath.replace(/^\//, ""),
            source_digest: "a".repeat(64),
          })
        }
      >
        Use saved fixture process
      </button>
    </div>
  ),
}));

vi.mock("../src/components/process-interfaces/ProcessWorkspaceTab", () => ({
  ProcessWorkspaceTab: (
    props: import("../src/components/process-interfaces/ProcessWorkspaceTab").ProcessWorkspaceTabProps,
  ) => (
    <div
      data-testid="working-view-host-fixture"
      data-view-path={props.tab.path}
      data-session-id={props.sessionId}
      data-run-id={props.tab.processView.run_id ?? ""}
      data-navigation-result={props.navigation?.resolution.target.result_id}
      data-navigation-assessment={
        props.navigation?.resolution.target.assessment_id
      }
    >
      <button
        onClick={() =>
          props.onRunAttached(
            props.tab.path,
            props.tab.processView.process,
            "accepted-run",
          )
        }
      >
        Accept fixture run
      </button>
      <button
        onClick={() => props.onOpenDefinition?.(props.tab.processView.process)}
      >
        Open fixture definition
      </button>
      <button
        onClick={() =>
          void props.onNavigate?.(props.tab.processView.process, {
            process: props.tab.processView.process,
            target: {
              kind: "block",
              block_id: "exact-step",
              run_id: props.tab.processView.run_id,
            },
          })
        }
      >
        Navigate fixture step
      </button>
      <button
        onClick={() =>
          void props.onNavigate?.(props.tab.processView.process, {
            process: props.tab.processView.process,
            target: {
              kind: "assessment",
              result_id: "exact-result",
              assessment_id: "exact-assessment",
              run_id: props.tab.processView.run_id,
            },
          })
        }
      >
        Navigate fixture assessment
      </button>
      <button
        onClick={() =>
          void props.onNavigate?.(props.tab.processView.process, {
            process: props.tab.processView.process,
            target: {
              kind: "result",
              result_id: "other-run-result",
              run_id: "other-run",
            },
          })
        }
      >
        Navigate fixture other run
      </button>
    </div>
  ),
}));

describe("WorkspacePanel session selection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
    localStorage.clear();
    mockGetWorkspaceConfig.mockResolvedValue({
      workspace_id: "workspace-1",
      git_remote_url: null,
      git_username: null,
      has_token: false,
      workspace_path: "/tmp/demo",
      workspace_prompt: null,
      git_large_file_threshold: 10 * 1024 * 1024,
    });
    mockUpdateWorkspaceConfig.mockResolvedValue({
      success: true,
      workspace_id: "workspace-1",
    });
    mockSendMessage.mockResolvedValue(undefined);
    mockCreateWorkflowSource.mockImplementation(
      async (_session, path, source) => ({
        workspace_id: "workspace-1",
        path,
        source,
      }),
    );
    mockUpdateWorkspaceSession.mockResolvedValue("new-session");
    mockSelectSession.mockResolvedValue(undefined);
    mockGetWorkspaceMcpStatus.mockResolvedValue({
      status: "ok",
      message: "MCP configuration is active and healthy.",
      running_mcps: [],
    });
    mockGetWorkspaceFiles.mockResolvedValue({
      name: "Demo",
      path: "/tmp/demo",
      type: "directory",
      size: null,
      last_modified: Date.now(),
      git_status: "Clean",
      children: [],
    });
    mockGetWorkspaceTools.mockResolvedValue([]);
    mockGetWorkspaceToolsById.mockResolvedValue([]);
    mockEnsureDefaultRivetWorkflow.mockResolvedValue({
      slug: "rivet",
      title: "Rivet",
    });
    mockListHermesModels.mockResolvedValue({
      current_value: "local:hermes",
      current_provider: "local",
      current_model: "hermes",
      groups: [
        {
          provider: "local",
          label: "Local",
          options: [
            {
              value: "local:hermes",
              label: "Hermes (Active)",
              provider: "local",
              model: "hermes",
              is_current: true,
            },
          ],
        },
      ],
    });
    mockGetWorkspace.mockResolvedValue({
      workspace_id: "workspace-1",
      workspace_name: "Demo",
      session_id: "old-session",
      local_path: "/tmp/demo",
      git_remote_url: null,
      git_username: null,
      updated_at: Date.now(),
    });
    mockUseChat.mockReturnValue({
      state: {
        sessions: [
          {
            sessionId: "old-session",
            title: "Old Session",
            messages: [
              {
                id: "old-message",
                role: "assistant",
                content: "old session message",
                timestamp: Date.now(),
                traceId: null,
              },
            ],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            isActive: false,
          },
          {
            sessionId: "new-session",
            title: "New Session",
            messages: [
              {
                id: "new-message",
                role: "assistant",
                content: "new session message",
                timestamp: Date.now(),
                traceId: null,
              },
            ],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            isActive: true,
          },
        ],
        activeSessionId: "new-session",
        isStreaming: false,
        streamingSessionId: null,
        activeTool: null,
        streamActivity: [],
        streamedText: "",
        promptQueue: [],
      },
      createSession: vi.fn(),
      selectSession: mockSelectSession,
      deleteSession: vi.fn(),
      sendMessage: mockSendMessage,
      refreshSessions: vi.fn(),
      cancelActiveStream: vi.fn(),
    });
  });

  it("keeps workspace navigation without mounting chat or selecting a model in desktop-hosted mode", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel
            workspaceId="workspace-1"
            sessionId="desktop-binding"
            desktopConversation
          />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    expect(
      await screen.findByTestId("activity-bar-explorer-btn"),
    ).toBeVisible();
    expect(screen.queryByTestId("agent-sidebar")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("agent-sidebar-toggle"),
    ).not.toBeInTheDocument();
    expect(mockSelectSession).not.toHaveBeenCalled();
    expect(mockListHermesModels).not.toHaveBeenCalled();
    expect(
      mockUseChat.mock.results.at(-1)?.value.refreshSessions,
    ).not.toHaveBeenCalled();
  });

  it.each([10485760, 26738688, 1, null])(
    "round trips a byte threshold of %s through workspace settings",
    async (bytes) => {
      mockGetWorkspaceConfig.mockResolvedValue({
        workspace_id: "workspace-1",
        git_remote_url: null,
        git_username: null,
        has_token: false,
        workspace_path: "/tmp/demo",
        workspace_prompt: null,
        git_large_file_threshold: bytes,
      });
      render(
        <MemoryRouter>
          <ViewerPanelProvider>
            <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
          </ViewerPanelProvider>
        </MemoryRouter>,
      );
      fireEvent.click(await screen.findByTestId("activity-bar-settings-btn"));
      const threshold = await screen.findByTestId(
        "workspace-settings-git-threshold",
      );
      await waitFor(() =>
        expect(threshold).toHaveValue((bytes ?? 10485760) / 1048576),
      );
      expect(screen.getByLabelText("Large-file warning threshold (MiB)")).toBe(
        threshold,
      );
      fireEvent.click(screen.getByTestId("workspace-settings-save-btn"));
      await waitFor(() =>
        expect(mockUpdateWorkspaceConfig).toHaveBeenCalledWith(
          "new-session",
          null,
          null,
          "",
          null,
          bytes ?? 10485760,
        ),
      );
    },
  );

  it("saves an edited fractional MiB threshold as bytes and rejects empty input", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByTestId("activity-bar-settings-btn"));
    const threshold = await screen.findByTestId(
      "workspace-settings-git-threshold",
    );
    await waitFor(() => expect(threshold).toHaveValue(10));
    fireEvent.change(threshold, { target: { value: "25.5" } });
    fireEvent.click(screen.getByTestId("workspace-settings-save-btn"));
    await waitFor(() =>
      expect(mockUpdateWorkspaceConfig).toHaveBeenCalledWith(
        "new-session",
        null,
        null,
        "",
        null,
        26738688,
      ),
    );
    await waitFor(() =>
      expect(screen.getByTestId("workspace-settings-save-btn")).toBeEnabled(),
    );
    mockUpdateWorkspaceConfig.mockClear();
    const reloadedThreshold = screen.getByTestId(
      "workspace-settings-git-threshold",
    );
    fireEvent.change(reloadedThreshold, { target: { value: "" } });
    fireEvent.submit(reloadedThreshold.closest("form")!);
    expect(
      await screen.findByText(/Enter a positive file-size threshold in MiB\./),
    ).toBeVisible();
    expect(mockUpdateWorkspaceConfig).not.toHaveBeenCalled();
  });

  it("opens a working view beside the retained workflow and navigates back in the same workspace", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
        <LocationProbe />
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByText("Use saved fixture process"));
    const working = await screen.findByTestId("working-view-host-fixture");
    expect(working).toBeVisible();
    expect(working).toHaveAttribute("data-session-id", "new-session");
    expect(
      screen.getByTestId("workspace-workflow-fixture"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("workspace-workflow-fixture")).not.toBeVisible();
    expect(screen.getAllByRole("tab")).toHaveLength(2);
    expect(
      screen.queryByTestId("viewer-inspector-toggle"),
    ).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Open fixture definition"));
    expect(
      await screen.findByTestId("workspace-workflow-fixture"),
    ).toBeVisible();
    expect(screen.getByTestId("working-view-host-fixture")).not.toBeVisible();
    expect(screen.getByTestId("workspace-workflow-fixture")).toHaveAttribute(
      "data-reopen-request",
      "0",
    );
    expect(screen.getByTestId("location-probe").textContent).not.toContain(
      "processView=",
    );
  });

  it("protects an unsaved workflow on tab close and keeps its draft", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    const draft = await screen.findByRole("textbox", {
      name: "Fixture source draft",
    });
    fireEvent.change(draft, {
      target: { value: "Keep this design instruction" },
    });
    fireEvent.click(
      screen.getByTestId(
        "editor-tab-close-/workflows/mounting-bracket.workflow.wflow",
      ),
    );
    const dialog = await screen.findByRole("dialog", {
      name: "Unsaved workflow changes",
    });
    expect(
      within(dialog).getByRole("button", { name: "Keep editing" }),
    ).toHaveFocus();
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Keep editing" }),
    );
    expect(draft).toHaveValue("Keep this design instruction");
    expect(
      screen.getByTestId(
        "editor-tab-dirty-/workflows/mounting-bracket.workflow.wflow",
      ),
    ).toBeVisible();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Mark fixture saved"));
    expect(
      screen.queryByTestId(
        "editor-tab-dirty-/workflows/mounting-bracket.workflow.wflow",
      ),
    ).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByTestId(
        "editor-tab-close-/workflows/mounting-bracket.workflow.wflow",
      ),
    );
    expect(
      screen.queryByTestId("workspace-workflow-fixture"),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("keeps a saving workflow mounted until the write has settled", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    await screen.findByRole("textbox", { name: "Fixture source draft" });
    const close = screen.getByTestId(
      "editor-tab-close-/workflows/mounting-bracket.workflow.wflow",
    );
    fireEvent.click(screen.getByText("Start pending fixture save"));
    expect(close).toBeDisabled();
    fireEvent.click(close);
    expect(
      screen.getByTestId("workspace-workflow-fixture"),
    ).toBeInTheDocument();
    const unload = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(unload);
    expect(unload.defaultPrevented).toBe(true);
    fireEvent.click(screen.getByText("Finish pending fixture save"));
    expect(close).toBeEnabled();
    fireEvent.click(close);
    expect(
      screen.queryByTestId("workspace-workflow-fixture"),
    ).not.toBeInTheDocument();
  });

  it("discards workflow edits only after explicit confirmation and Escape keeps them", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    const draft = await screen.findByRole("textbox", {
      name: "Fixture source draft",
    });
    fireEvent.change(draft, { target: { value: "Draft to discard" } });
    const close = screen.getByTestId(
      "editor-tab-close-/workflows/mounting-bracket.workflow.wflow",
    );
    fireEvent.click(close);
    await screen.findByRole("dialog", { name: "Unsaved workflow changes" });
    fireEvent.keyDown(document, { key: "Escape" });
    expect(draft).toHaveValue("Draft to discard");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    fireEvent.click(close);
    fireEvent.click(
      within(await screen.findByRole("dialog")).getByRole("button", {
        name: "Discard changes",
      }),
    );
    expect(
      screen.queryByTestId("workspace-workflow-fixture"),
    ).not.toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("keeps a background workflow draft when its close is cancelled", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    const original = await screen.findByRole("textbox", {
      name: "Fixture source draft",
    });
    fireEvent.change(original, {
      target: { value: "Original unsaved design" },
    });
    fireEvent.click(screen.getByText("Open other fixture workflow"));
    const active = await screen.findByTestId(
      "editor-tab-/workflows/other-design.workflow.wflow",
    );
    expect(active).toHaveAttribute("aria-selected", "true");
    fireEvent.click(
      screen.getByTestId(
        "editor-tab-close-/workflows/mounting-bracket.workflow.wflow",
      ),
    );
    const dialog = await screen.findByRole("dialog", {
      name: "Unsaved workflow changes",
    });
    expect(
      within(dialog).getByText(/mounting-bracket.wflow has unsaved changes/),
    ).toBeVisible();
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Keep editing" }),
    );
    expect(active).toHaveAttribute("aria-selected", "true");
    expect(original).toHaveValue("Original unsaved design");
    fireEvent.click(
      screen.getByTestId(
        "editor-tab-/workflows/mounting-bracket.workflow.wflow",
      ),
    );
    expect(original).toBeVisible();
  });

  it("warns before browser unload only while a workflow has unsaved edits", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    const draft = await screen.findByRole("textbox", {
      name: "Fixture source draft",
    });
    const clean = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(clean);
    expect(clean.defaultPrevented).toBe(false);
    fireEvent.change(draft, { target: { value: "Do not lose this" } });
    const dirty = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(dirty);
    expect(dirty.defaultPrevented).toBe(true);
    fireEvent.click(screen.getByText("Mark fixture saved"));
    const saved = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(saved);
    expect(saved.defaultPrevented).toBe(false);
  });

  it("focuses an exact source step in the retained editor without discarding its draft", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
        <LocationProbe />
      </MemoryRouter>,
    );
    const draft = await screen.findByRole("textbox", {
      name: "Fixture source draft",
    });
    fireEvent.change(draft, {
      target: { value: "Unsaved exact source edits" },
    });
    const editor = screen.getByTestId("workspace-workflow-fixture");
    fireEvent.click(screen.getByText("Use saved fixture process"));
    fireEvent.click(await screen.findByText("Accept fixture run"));
    fireEvent.click(screen.getByText("Navigate fixture step"));
    await waitFor(() => expect(editor).toBeVisible());
    expect(editor).toHaveAttribute("data-navigation-block", "exact-step");
    expect(editor).toHaveAttribute("data-reopen-request", "0");
    expect(draft).toHaveValue("Unsaved exact source edits");
    expect(screen.getAllByRole("tab")).toHaveLength(2);
    expect(screen.getByTestId("working-view-host-fixture")).toHaveAttribute(
      "data-run-id",
      "accepted-run",
    );
  });

  it("focuses an exact assessment in its existing run tab without creating another tab", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    const tab = createProcessWorkspaceTab(
      {
        workspace_id: "workspace-1",
        source_path: "workflows/inspection.workflow.wflow",
        source_digest: "a".repeat(64),
      },
      { viewId: "recorded-view", runId: "recorded-run" },
    );
    render(
      <MemoryRouter
        initialEntries={[
          `/workspace/workspace-1${processWorkspaceQuery("?workflow=canonical", tab)}`,
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
        <LocationProbe />
      </MemoryRouter>,
    );
    const working = await screen.findByTestId("working-view-host-fixture");
    fireEvent.click(screen.getByText("Navigate fixture assessment"));
    await waitFor(() =>
      expect(working).toHaveAttribute(
        "data-navigation-assessment",
        "exact-assessment",
      ),
    );
    expect(working).toHaveAttribute("data-navigation-result", "exact-result");
    expect(working).toHaveAttribute("data-run-id", "recorded-run");
    expect(screen.getAllByRole("tab")).toHaveLength(1);
    expect(screen.getByTestId("location-probe").textContent).toContain(
      "processRun=recorded-run",
    );
    expect(mockEnsureDefaultRivetWorkflow).not.toHaveBeenCalled();
  });

  it("opens another recorded run in a separate tab without retargeting the original observer", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    const tab = createProcessWorkspaceTab(
      {
        workspace_id: "workspace-1",
        source_path: "workflows/inspection.workflow.wflow",
        source_digest: "a".repeat(64),
      },
      { viewId: "recorded-view", runId: "recorded-run" },
    );
    render(
      <MemoryRouter
        initialEntries={[
          `/workspace/workspace-1${processWorkspaceQuery("?workflow=canonical", tab)}`,
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
        <LocationProbe />
      </MemoryRouter>,
    );
    const original = await screen.findByTestId("working-view-host-fixture");
    fireEvent.click(screen.getByText("Navigate fixture other run"));
    await waitFor(() =>
      expect(screen.getAllByTestId("working-view-host-fixture")).toHaveLength(
        2,
      ),
    );
    expect(original).toHaveAttribute("data-run-id", "recorded-run");
    expect(original).not.toBeVisible();
    const selected = screen
      .getAllByTestId("working-view-host-fixture")
      .find((element) => element.getAttribute("data-run-id") === "other-run");
    expect(selected).toBeVisible();
    expect(selected).toHaveAttribute(
      "data-navigation-result",
      "other-run-result",
    );
    expect(screen.getAllByRole("tab")).toHaveLength(2);
    expect(screen.getByTestId("location-probe").textContent).toContain(
      "processRun=other-run",
    );
  });

  it("reopens an exact recorded-run link without creating the default workflow", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    const tab = createProcessWorkspaceTab(
      {
        workspace_id: "workspace-1",
        source_path: "workflows/inspection.workflow.wflow",
        source_digest: "a".repeat(64),
      },
      { viewId: "recorded-view", runId: "recorded-run" },
    );
    render(
      <MemoryRouter
        initialEntries={[
          `/workspace/workspace-1${processWorkspaceQuery("?workflow=canonical", tab)}`,
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
        <LocationProbe />
      </MemoryRouter>,
    );
    expect(
      await screen.findByTestId("working-view-host-fixture"),
    ).toHaveAttribute("data-run-id", "recorded-run");
    expect(
      screen.queryByTestId("workspace-workflow-fixture"),
    ).not.toBeInTheDocument();
    expect(screen.getAllByRole("tab")).toHaveLength(1);
    expect(mockEnsureDefaultRivetWorkflow).not.toHaveBeenCalled();
  });

  it("writes the accepted run into the active view link and closing removes that link", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
        <LocationProbe />
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByText("Use saved fixture process"));
    const fixture = await screen.findByTestId("working-view-host-fixture");
    fireEvent.click(screen.getByText("Accept fixture run"));
    await waitFor(() =>
      expect(screen.getByTestId("location-probe").textContent).toContain(
        "processRun=accepted-run",
      ),
    );
    expect(fixture).toHaveAttribute("data-run-id", "accepted-run");
    fireEvent.click(
      screen.getByTestId(
        `editor-tab-close-${fixture.getAttribute("data-view-path")}`,
      ),
    );
    await waitFor(() =>
      expect(
        screen.queryByTestId("working-view-host-fixture"),
      ).not.toBeInTheDocument(),
    );
    expect(screen.getByTestId("location-probe").textContent).not.toContain(
      "processView=",
    );
    expect(screen.getByTestId("workspace-workflow-fixture")).toBeVisible();
  });

  it("opens a linked definition without creation intent when its editor is not already open", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    const tab = createProcessWorkspaceTab(
      {
        workspace_id: "workspace-1",
        source_path: "workflows/inspection.workflow.wflow",
        source_digest: "a".repeat(64),
      },
      { viewId: "recorded-view", runId: "recorded-run" },
    );
    render(
      <MemoryRouter
        initialEntries={[
          `/workspace/workspace-1${processWorkspaceQuery("?workflow=canonical", tab)}`,
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByText("Open fixture definition"));
    const panel = await screen.findByTestId("workspace-workflow-fixture");
    expect(panel).toBeVisible();
    expect(panel).toHaveAttribute(
      "data-workflow-file",
      "/workflows/inspection.workflow.wflow",
    );
    expect(panel).toHaveAttribute("data-create-if-missing", "false");
    expect(panel).toHaveAttribute("data-reopen-request", "0");
  });

  it("ignores an incomplete saved process locator and reports how to reopen it", async () => {
    localStorage.setItem(
      "wright-workspace-layout-workspace-1",
      JSON.stringify({
        openTabs: [{ type: "process", name: "Missing locator" }],
      }),
    );
    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    expect(
      await screen.findByTestId("workspace-process-view-error"),
    ).toHaveTextContent("incomplete");
    expect(
      screen.queryByTestId("working-view-host-fixture"),
    ).not.toBeInTheDocument();
  });

  it("restores a saved process tab in a plain workspace with the host session", async () => {
    const tab = createProcessWorkspaceTab(
      {
        workspace_id: "workspace-1",
        source_path: "workflows/inspection.workflow.wflow",
        source_digest: "a".repeat(64),
      },
      { viewId: "saved-view", runId: "saved-run" },
    );
    localStorage.setItem(
      "wright-workspace-layout-workspace-1",
      JSON.stringify({ openTabs: [tab], activeTabPath: tab.path }),
    );
    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    const fixture = await screen.findByTestId("working-view-host-fixture");
    expect(fixture).toBeVisible();
    expect(fixture).toHaveAttribute("data-run-id", "saved-run");
    expect(fixture).toHaveAttribute("data-session-id", "new-session");
    expect(
      screen.queryByTestId("workspace-workflow-fixture"),
    ).not.toBeInTheDocument();
  });

  it("rejects foreign saved views and malformed links without resolving them as files", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    const tab = createProcessWorkspaceTab(
      {
        workspace_id: "another-workspace",
        source_path: "workflows/inspection.workflow.wflow",
        source_digest: "a".repeat(64),
      },
      { viewId: "foreign-view" },
    );
    localStorage.setItem(
      "wright-workspace-layout-workspace-1",
      JSON.stringify({ openTabs: [tab], activeTabPath: tab.path }),
    );
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&processView=broken",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    expect(
      await screen.findByTestId("workspace-process-view-error"),
    ).toBeVisible();
    expect(
      screen.queryByTestId("working-view-host-fixture"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("workspace-workflow-fixture"),
    ).not.toBeInTheDocument();
    expect(screen.queryAllByRole("tab")).toHaveLength(0);
  });

  it("keeps the parent-selected session when internal workspace info is stale", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText("new session message")).toBeInTheDocument();

    await waitFor(() => {
      expect(mockGetWorkspace).toHaveBeenCalledWith("workspace-1");
    });
    expect(screen.queryByText("old session message")).not.toBeInTheDocument();
  });

  it("loads MCP selection by workspace ID instead of the global session", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ servers: [] }),
      }),
    );

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByTestId("activity-bar-mcp-btn"));

    await waitFor(() => {
      expect(mockGetWorkspaceToolsById).toHaveBeenCalledWith("workspace-1");
    });
    expect(fetch).toHaveBeenCalledWith("/api/mcp/servers/installed");
    expect(mockGetWorkspaceTools).not.toHaveBeenCalled();

    vi.unstubAllGlobals();
  });

  it("keeps built-in Rivet out of the workspace MCP selector", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          servers: [
            {
              server_id: "rivet-workflows",
              name: "Rivet Workflows",
              type: "stdio",
              is_active: true,
              is_installed: true,
            },
            {
              server_id: "solid-edge-mcp",
              name: "Solid Edge MCP",
              type: "stdio",
              is_active: true,
              is_installed: true,
            },
          ],
        }),
      }),
    );

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByTestId("activity-bar-mcp-btn"));
    expect(
      await screen.findByTestId("mcp-server-item-solid edge mcp"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("mcp-server-item-rivet workflows"),
    ).not.toBeInTheDocument();

    vi.unstubAllGlobals();
  });

  it("creates a separate empty workflow from Workflows", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
        <LocationProbe />
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByTestId("activity-bar-workflows-btn"));

    expect(
      await screen.findByTestId("workspace-workflow-fixture"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("workspace-workflow-fixture")).toHaveAttribute(
      "data-workspace-id",
      "workspace-1",
    );
    expect(screen.getByTestId("workspace-workflow-fixture")).toHaveAttribute(
      "data-session-id",
      "new-session",
    );
    expect(screen.getByTestId("workspace-workflow-fixture")).toHaveAttribute(
      "data-workspace-name",
      "Demo",
    );
    const createdPath = mockCreateWorkflowSource.mock.calls[0][1];
    expect(createdPath).toMatch(
      /^workflows\/untitled-workflow-[a-f0-9-]+\.workflow\.wflow$/,
    );
    expect(mockCreateWorkflowSource.mock.calls[0][0]).toBe("new-session");
    expect(mockCreateWorkflowSource.mock.calls[0][2]).not.toMatch(
      /(?:task|input|output|link) /,
    );
    expect(screen.getByTestId("workspace-workflow-fixture")).toHaveAttribute(
      "data-workflow-file",
      "/" + createdPath,
    );
    expect(mockEnsureDefaultRivetWorkflow).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
        display: "flex",
      }),
    );
    await waitFor(() => expect(screen.getByTestId("location-probe")).toHaveTextContent("workflow=canonical"));
    fireEvent.click(screen.getByTitle("Collapse Agent Console"));
    const maximize = screen.getByTestId("workspace-tab-focus");
    const openAgent = await screen.findByTestId("agent-sidebar-toggle");
    expect(openAgent.parentElement).toBe(maximize.parentElement);
    expect(openAgent.parentElement).toHaveStyle({ display: "flex" });
    expect(openAgent.style.position).not.toBe("absolute");
    expect(maximize.style.position).not.toBe("absolute");
    fireEvent.click(maximize);
    expect(screen.getByTestId("workspace-tab-focus")).toHaveAccessibleName(
      "Restore workspace layout",
    );
    fireEvent.click(screen.getByTestId("workspace-tab-focus"));
    expect(screen.getByTestId("workspace-tab-focus")).toHaveAccessibleName(
      "Maximize active tab",
    );
    fireEvent.click(screen.getByTitle("Open Agent Console"));
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: "flex",
    });
    fireEvent.click(screen.getByTitle("Collapse Agent Console"));
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: "none",
    });
  });

  it("creates a blank workflow from the Workflows action in an ordinary workspace", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
        <LocationProbe />
      </MemoryRouter>,
    );

    await screen.findByTestId("activity-bar-workflows-btn");
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: "flex",
    });
    fireEvent.click(screen.getByTestId("activity-bar-workflows-btn"));

    expect(
      await screen.findByTestId("workspace-workflow-fixture"),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.getByTestId("location-probe")).toHaveTextContent(
        "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Funtitled-workflow-",
      ),
    );
    expect(mockEnsureDefaultRivetWorkflow).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
        display: "flex",
      }),
    );
  });

  it.each([true, false])("preserves the explicit workflow chat collapse preference %s independently of ordinary layout", async (collapsed) => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    localStorage.setItem(
      "wright-workspace-layout-workspace-1",
      JSON.stringify({
        isAgentCollapsed: true,
        workflowAgentCollapsed: collapsed,
      }),
    );
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Fmounting-bracket.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    await screen.findByTestId("workspace-workflow-fixture");
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: collapsed ? "none" : "flex",
    });
  });

  it("opens an explicitly named workspace workflow without replacing the default path", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Finspection.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    expect(
      await screen.findByTestId("workspace-workflow-fixture"),
    ).toHaveAttribute(
      "data-workflow-file",
      "/workflows/inspection.workflow.wflow",
    );
    expect(
      screen.queryByText("mounting-bracket.workflow.wflow"),
    ).not.toBeInTheDocument();
  });

  it("sends a fresh reopen request when the Open control selects an already retained workflow", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Finspection.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    const panel = await screen.findByTestId("workspace-workflow-fixture");
    expect(panel).toHaveAttribute("data-reopen-request", "0");
    fireEvent.click(
      screen.getByRole("button", { name: "Reopen fixture file" }),
    );
    await waitFor(() =>
      expect(panel).toHaveAttribute("data-reopen-request", "1"),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Reopen fixture file" }),
    );
    await waitFor(() =>
      expect(panel).toHaveAttribute("data-reopen-request", "2"),
    );
    expect(screen.getAllByTestId("workspace-workflow-fixture")).toHaveLength(1);
  });

  it.each([
    "../outside.workflow.wflow",
    "workflows/../outside.workflow.wflow",
    "workflows/con.workflow.wflow",
    "C:/outside.workflow.wflow",
  ])("fails closed for invalid workflow path %s", async (path) => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    render(
      <MemoryRouter
        initialEntries={[
          `/workspace/workspace-1?workflow=canonical&workflowPath=${encodeURIComponent(path)}`,
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    expect(
      await screen.findByTestId("workspace-workflow-path-error"),
    ).toHaveTextContent("valid workspace workflow");
    expect(
      screen.queryByTestId("workspace-workflow-fixture"),
    ).not.toBeInTheDocument();
  });

  it("hides Workflows when the native editor is disabled", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "false");
    vi.stubEnv("VITE_RIVET_WORKFLOWS_TAB_ENABLED", "false");

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    await screen.findByTestId("workspace-panel");
    expect(
      screen.queryByTestId("activity-bar-workflows-btn"),
    ).not.toBeInTheDocument();
  });

  it("restores an explicitly retained workflow without requiring a special query", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    vi.stubEnv("VITE_RIVET_WORKFLOWS_TAB_ENABLED", "false");
    localStorage.setItem(
      "wright-workspace-layout-workspace-1",
      JSON.stringify({
        openTabs: [
          {
            name: "mounting-bracket.workflow.wflow",
            path: "/workflows/mounting-bracket.workflow.wflow",
            type: "workflow",
          },
        ],
        activeTabPath: "/workflows/mounting-bracket.workflow.wflow",
      }),
    );

    render(
      <MemoryRouter initialEntries={["/workspace/workspace-1"]}>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    await screen.findByTestId("workspace-panel");
    expect(
      screen.getByTestId("activity-bar-workflows-btn"),
    ).toBeInTheDocument();
    expect(
      await screen.findByTestId("workspace-workflow-fixture"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("workspace-workflow-fixture")).toHaveAttribute(
      "data-workflow-file",
      "/workflows/mounting-bracket.workflow.wflow",
    );
  });

  it("does not revive Rivet when the native editor is disabled", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "false");
    vi.stubEnv("VITE_RIVET_WORKFLOWS_TAB_ENABLED", "true");
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    await screen.findByTestId("workspace-panel");
    expect(
      screen.queryByTestId("activity-bar-workflows-btn"),
    ).not.toBeInTheDocument();
    expect(mockEnsureDefaultRivetWorkflow).not.toHaveBeenCalled();
    expect(
      screen.queryByTestId("managed-rivet-fixture"),
    ).not.toBeInTheDocument();
  });

  it("keeps the agent pane live while maximizing the active workflow", async () => {
    vi.stubEnv("VITE_WRIGHT_WORKFLOW_RECOVERY", "true");
    vi.stubEnv("VITE_WORKSPACE_SURFACES_ENABLED", "true");
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1440,
    });

    render(
      <MemoryRouter
        initialEntries={[
          "/workspace/workspace-1?workflow=canonical&workflowPath=workflows%2Finspection.workflow.wflow",
        ]}
      >
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    await screen.findByTestId("workspace-workflow-fixture");
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({ display: "flex" });
    fireEvent.click(await screen.findByTestId("workspace-tab-focus"));

    await waitFor(() =>
      expect(screen.getByTestId("workspace-panel")).toHaveAttribute(
        "data-wide-layout-mode",
        "focus",
      ),
    );
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: "flex",
    });
    expect(
      screen.getByRole("button", { name: "Restore workspace layout" }),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Restore workspace layout" }),
    );

    await waitFor(() =>
      expect(screen.getByTestId("workspace-panel")).toHaveAttribute(
        "data-wide-layout-mode",
        "normal",
      ),
    );
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: "flex",
    });
  });

  it("does not show another session's busy stream on the selected session", async () => {
    const chat = mockUseChat();
    mockUseChat.mockReturnValue({
      ...chat,
      state: {
        ...chat.state,
        activeSessionId: "new-session",
        isStreaming: true,
        streamingSessionId: "old-session",
        streamedText: "still working in old session",
        activeTool: {
          name: "Onshape MCP",
          preview: "Calling Onshape",
        },
        streamActivity: [
          {
            id: "activity-1",
            kind: "tool",
            title: "Calling Onshape MCP",
            timestamp: Date.now(),
          },
        ],
      },
    });

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText("new session message")).toBeInTheDocument();
    expect(
      screen.queryByTestId("stream-activity-panel"),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId("thinking-indicator")).not.toBeInTheDocument();
    expect(
      screen.queryByText("still working in old session"),
    ).not.toBeInTheDocument();
  });

  it("changes only the chat session when selecting an existing session", async () => {
    const handleSessionChange = vi.fn();

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel
            workspaceId="workspace-1"
            sessionId="new-session"
            onSessionChange={handleSessionChange}
          />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    const selector = await screen.findByTestId("sessions-sidebar");
    await waitFor(() => {
      expect(mockGetWorkspaceFiles).toHaveBeenCalledWith("new-session");
    });
    mockGetWorkspaceFiles.mockClear();

    fireEvent.change(selector, { target: { value: "old-session" } });

    await waitFor(() => {
      expect(mockSelectSession).toHaveBeenCalledWith("old-session");
    });
    expect(mockUpdateWorkspaceSession).not.toHaveBeenCalled();
    expect(handleSessionChange).not.toHaveBeenCalled();
    expect(mockGetWorkspaceFiles).not.toHaveBeenCalled();
  });

  it("does not crash when a cached session has no title", async () => {
    const chatState = mockUseChat().state;
    mockUseChat.mockReturnValue({
      ...mockUseChat(),
      state: {
        ...chatState,
        sessions: [
          ...chatState.sessions,
          {
            sessionId: "legacy-session",
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            isActive: false,
          } as any,
        ],
      },
    });

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    expect(await screen.findByText("Untitled Session")).toBeInTheDocument();
  });

  it("disambiguates duplicate session titles in the dropdown", async () => {
    const chatState = mockUseChat().state;
    mockUseChat.mockReturnValue({
      ...mockUseChat(),
      state: {
        ...chatState,
        sessions: [
          {
            ...chatState.sessions[0],
            sessionId: "duplicate-a",
            title: "Onshape Session 2",
          },
          {
            ...chatState.sessions[1],
            sessionId: "duplicate-b",
            title: "Onshape Session 2",
          },
        ],
        activeSessionId: "duplicate-b",
      },
    });

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="duplicate-b" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    const sessionSelect = await screen.findByTestId("sessions-sidebar");
    const optionLabels = Array.from(
      sessionSelect.querySelectorAll("option"),
    ).map((option) => option.textContent?.trim());

    expect(optionLabels).toEqual([
      "Onshape Session 2",
      "Onshape Session 2 (2)",
    ]);
  });

  it("renders the model options returned by the Hermes catalog", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    const modelSelect = await screen.findByTestId("llm-model-select");
    const options = Array.from(
      modelSelect.querySelectorAll("option"),
    ) as HTMLOptionElement[];

    expect(options.map((option) => option.textContent?.trim())).toEqual([
      "Hermes (Active)",
    ]);
    expect(options[0]).not.toBeDisabled();
    expect(modelSelect).not.toBeDisabled();
    expect(mockListHermesModels).toHaveBeenCalledOnce();
  });

  it("keeps the agent chat panel visible when the MCP sidebar is toggled closed", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    const mcpButton = await screen.findByTestId("activity-bar-mcp-btn");

    fireEvent.click(mcpButton);
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: "flex",
      gridColumn: "6",
    });

    fireEvent.click(mcpButton);
    expect(screen.getByTestId("workspace-sidebar")).toHaveStyle({
      display: "none",
      gridColumn: "2",
    });
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: "flex",
      gridColumn: "6",
    });
  });

  it("shows usable Git status and controls", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );
    fireEvent.click(await screen.findByTestId("activity-bar-git-btn"));
    expect(await screen.findByTestId("git-panel")).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Create branch" }),
    ).toBeInTheDocument();
    expect(screen.getByText("No changes to commit.")).toBeInTheDocument();
    expect(screen.queryByText("Coming soon")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Push" })).toBeDisabled();
  });

  it("shows docs links and sends suggested prompts", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByTestId("activity-bar-docs-btn"));

    expect(screen.getByText("Start Here")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Wright quickstart" }),
    ).toHaveAttribute(
      "href",
      "https://github.com/burhop/wright/blob/dev/docs/getting-started/quickstart-local.md",
    );
    expect(
      screen.getByRole("link", { name: "Hermes plugin guide" }),
    ).toBeInTheDocument();

    fireEvent.click(
      screen.getByRole("button", { name: "Explain this workspace" }),
    );

    expect(mockSendMessage).toHaveBeenCalledWith(
      "Summarize this Wright workspace. Identify the open files, available MCP tools, likely CAD workflow, and the next three useful actions.",
      undefined,
      false,
      undefined,
      undefined,
    );
  });

  it("requests MCP status by workspace instead of selected session", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(mockGetWorkspaceMcpStatus).toHaveBeenCalledWith("workspace-1");
    });
    expect(mockGetWorkspaceMcpStatus).not.toHaveBeenCalledWith("new-session");
  });

  it("shows the default workspace empty state when no tabs are open", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByTestId("workspace-empty-state"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Wright Engineering Workspace"),
    ).toBeInTheDocument();
    expect(
      screen.queryByTestId("editor-tabs-container"),
    ).not.toBeInTheDocument();
  });

  it("reattaches responsive measurement after compact chat replaces the workspace root", async () => {
    const observers: Array<{
      callback: ResizeObserverCallback;
      target: Element | null;
    }> = [];

    class TestResizeObserver {
      private readonly record: (typeof observers)[number];

      constructor(callback: ResizeObserverCallback) {
        this.record = { callback, target: null };
        observers.push(this.record);
      }

      observe(target: Element) {
        this.record.target = target;
      }

      unobserve() {}

      disconnect() {}
    }

    vi.stubGlobal("ResizeObserver", TestResizeObserver);

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    expect(
      await screen.findByTestId("workspace-surface-pane"),
    ).toBeInTheDocument();
    await waitFor(() => expect(observers.at(-1)?.target).not.toBeNull());
    const wideRoot = observers.at(-1)?.target;

    act(() => {
      const observer = observers.at(-1)!;
      observer.callback(
        [{ contentRect: { width: 700 } } as ResizeObserverEntry],
        {} as ResizeObserver,
      );
    });

    await waitFor(() => {
      expect(
        screen.queryByTestId("workspace-surface-pane"),
      ).not.toBeInTheDocument();
      expect(observers.at(-1)?.target).not.toBe(wideRoot);
    });

    act(() => {
      const observer = observers.at(-1)!;
      observer.callback(
        [{ contentRect: { width: 1184 } } as ResizeObserverEntry],
        {} as ResizeObserver,
      );
    });

    expect(
      await screen.findByTestId("workspace-surface-pane"),
    ).toBeInTheDocument();
    vi.unstubAllGlobals();
  });
});
