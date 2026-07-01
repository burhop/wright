import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import WorkspacePanel from "../src/components/chat/WorkspacePanel";
import { ViewerPanelProvider } from "../src/store/viewer";

const mockUseChat = vi.fn();
const mockGetWorkspace = vi.fn();

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
      selectSession: vi.fn(),
      deleteSession: vi.fn(),
      sendMessage: vi.fn(),
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
});
