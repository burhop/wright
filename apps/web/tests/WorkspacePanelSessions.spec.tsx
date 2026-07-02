import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import WorkspacePanel from "../src/components/chat/WorkspacePanel";
import { ViewerPanelProvider } from "../src/store/viewer";

const mockUseChat = vi.fn();
const mockGetWorkspace = vi.fn();
const mockSendMessage = vi.fn();
const mockUpdateWorkspaceSession = vi.fn();
const mockSelectSession = vi.fn();

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
  },
}));

vi.mock("../src/services/workspace-service", () => ({
  workspaceService: {
    getWorkspace: (...args: unknown[]) => mockGetWorkspace(...args),
    updateWorkspaceSession: (...args: unknown[]) =>
      mockUpdateWorkspaceSession(...args),
    getWorkspaceFiles: vi.fn().mockResolvedValue({
      name: "Demo",
      path: "/tmp/demo",
      type: "directory",
      size: null,
      last_modified: Date.now(),
      git_status: "Clean",
      children: [],
    }),
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
    getWorkspaceTools: vi.fn().mockResolvedValue([]),
  },
  MergeConflictError: class MergeConflictError extends Error {},
}));

describe("WorkspacePanel session selection", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSendMessage.mockResolvedValue(undefined);
    mockUpdateWorkspaceSession.mockResolvedValue("new-session");
    mockSelectSession.mockResolvedValue(undefined);
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
        activeTool: null,
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
    fireEvent.change(selector, { target: { value: "old-session" } });

    await waitFor(() => {
      expect(mockSelectSession).toHaveBeenCalledWith("old-session");
    });
    expect(mockUpdateWorkspaceSession).not.toHaveBeenCalled();
    expect(handleSessionChange).not.toHaveBeenCalled();
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

  it("shows only Hermes as selectable and OpenClaw as a disabled future option", async () => {
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
      "OpenClaw",
    ]);
    expect(options[0]).not.toBeDisabled();
    expect(options[1]).toBeDisabled();
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
    );
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
});
