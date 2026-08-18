import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import WorkspacePanel from "../src/components/chat/WorkspacePanel";
import { ViewerPanelProvider } from "../src/store/viewer";

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
    updateWorkspaceSession: (...args: unknown[]) =>
      mockUpdateWorkspaceSession(...args),
    getWorkspaceFiles: (...args: unknown[]) => mockGetWorkspaceFiles(...args),
    getGitStatus: vi.fn().mockResolvedValue({
      branch_name: "main",
      is_clean: true,
      changes: [],
    }),
    getGitHistory: vi.fn().mockResolvedValue({ commits: [] }),
    getWorkspaceConfig: vi.fn().mockResolvedValue({
      workspace_id: "workspace-1",
      git_remote_url: null,
      git_username: null,
      has_token: false,
      workspace_path: "/tmp/demo",
      workspace_prompt: null,
      git_large_file_threshold: null,
    }),
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

describe("WorkspacePanel session selection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.unstubAllEnvs();
    mockSendMessage.mockResolvedValue(undefined);
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

  it("opens a Rivet tab immediately while its workflow is prepared", async () => {
    mockEnsureDefaultRivetWorkflow.mockReturnValue(new Promise(() => {}));

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByTestId("activity-bar-workflows-btn"));

    expect(await screen.findByText("rivet.rivet-project")).toBeInTheDocument();
    expect(screen.getByTestId("managed-rivet-fixture")).toBeInTheDocument();
    expect(mockEnsureDefaultRivetWorkflow).toHaveBeenCalledWith("new-session");
  });

  it("maximizes the active surface and restores the agent pane", async () => {
    vi.stubEnv("VITE_WORKSPACE_SURFACES_ENABLED", "true");
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      value: 1440,
    });

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByTestId("activity-bar-brep-btn"));
    fireEvent.click(await screen.findByTestId("workspace-tab-focus"));

    await waitFor(() =>
      expect(screen.getByTestId("workspace-panel")).toHaveAttribute(
        "data-wide-layout-mode",
        "focus",
      ),
    );
    expect(screen.getByTestId("agent-sidebar")).toHaveStyle({
      display: "none",
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

  it("shows the Git panel as a disabled coming soon placeholder", async () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <WorkspacePanel workspaceId="workspace-1" sessionId="new-session" />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    fireEvent.click(await screen.findByTestId("activity-bar-git-btn"));

    const gitPanel = await screen.findByTestId("git-panel-coming-soon");
    expect(gitPanel).toHaveAttribute("aria-disabled", "true");
    expect(gitPanel).toHaveStyle({ pointerEvents: "none" });
    expect(screen.getByText("Coming soon")).toBeInTheDocument();
    expect(screen.queryByTestId("git-new-branch-btn")).not.toBeInTheDocument();
    expect(screen.queryByTestId("git-push-btn")).not.toBeInTheDocument();
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
      { activeRivetSlug: null },
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
