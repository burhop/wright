import { act, cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import ChatLayout from "../src/components/chat/ChatLayout";
import { ViewerPanelProvider } from "../src/store/viewer";

// Mock useHealthStatus hook
const mockUseHealthStatus = vi.fn();
vi.mock("../src/hooks/useHealthStatus", () => ({
  default: () => mockUseHealthStatus(),
  useHealthStatus: () => mockUseHealthStatus(),
}));

// Mock useChat to control store states
const mockUseChat = vi.fn();
vi.mock("../src/store/sessions", () => {
  const actual = vi.importActual("../src/store/sessions");
  return {
    ...actual,
    useChat: () => mockUseChat(),
    ChatProvider: ({ children }: any) => <div>{children}</div>,
  };
});

describe("ChatLayout", () => {
  let unexpectedRequests: string[];
  beforeEach(() => {
    vi.resetAllMocks();
    unexpectedRequests = [];
    // Keep the real child UI, but settle its read-only discovery before teardown.
    // These layout tests must never contact an installed/local backend.
    const responses: Record<string, unknown> = {
      "/api/agent/active": { agent: "hermes" },
      "/api/agent/models": { groups: [], selection_supported: false },
      "/api/agent/commands": { commands: [] },
      "/api/mcp/servers/installed": { servers: [] },
      "/api/workspace/files": {
        workspace: {
          name: "Test workspace",
          path: "/",
          type: "directory",
          children: [],
        },
      },
      "/api/workspace/tools": { enabled_tools: [] },
      "/api/workspace/mcp-status": {
        status: "ready",
        message: "",
        running_mcps: [],
      },
    };
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
        const path = new URL(String(input), "http://localhost").pathname;
        if ((init?.method ?? "GET") !== "GET" || !(path in responses)) {
          unexpectedRequests.push(`${init?.method ?? "GET"} ${path}`);
          throw new Error(`Unexpected layout-test request: ${path}`);
        }
        return new Response(JSON.stringify(responses[path]), {
          headers: { "Content-Type": "application/json" },
        });
      }),
    );
    // Default mock implementation for useChat
    mockUseChat.mockReturnValue({
      state: {
        sessions: [
          {
            sessionId: "session1",
            title: "Test Session",
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            isActive: true,
          },
        ],
        activeSessionId: "session1",
        isStreaming: false,
        streamingSessionId: null,
        activeTool: null,
        streamActivity: [],
        streamedText: "",
        activeStreamId: null,
        streamStates: {},
      },
      createSession: vi.fn(),
      selectSession: vi.fn(),
      deleteSession: vi.fn(),
      sendMessage: vi.fn(),
      refreshSessions: vi.fn(),
    });

    // Default mock implementation for useHealthStatus (all connected)
    mockUseHealthStatus.mockReturnValue([
      {
        serviceId: "wright-api",
        name: "Wright API",
        endpoint: "/api/health",
        state: "connected",
        lastChecked: Date.now(),
      },
      {
        serviceId: "hermes-agent",
        name: "Hermes Agent",
        endpoint: "/api/agent/health",
        state: "connected",
        lastChecked: Date.now(),
      },
    ]);
  });
  afterEach(async () => {
    cleanup();
    await act(async () => {});
    vi.unstubAllGlobals();
    expect(unexpectedRequests).toEqual([]);
  });

  async function renderLayout() {
    await act(async () => {
      render(
        <MemoryRouter>
          <ViewerPanelProvider>
            <ChatLayout />
          </ViewerPanelProvider>
        </MemoryRouter>,
      );
    });
  }

  it("renders three-panel layout and no banner when connected", async () => {
    await renderLayout();

    expect(screen.getByTestId("chat-layout")).toBeInTheDocument();
    expect(screen.getByTestId("sessions-sidebar")).toBeInTheDocument();
    expect(screen.getByTestId("chat-transcript")).toBeInTheDocument();
    expect(screen.getByTestId("workspace-panel")).toBeInTheDocument();
    expect(screen.getByTestId("left-resize-handle")).toBeInTheDocument();
    expect(screen.getByTestId("right-resize-handle")).toBeInTheDocument();
    expect(screen.getByTestId("agent-tools-window")).toBeInTheDocument();
    expect(screen.getByTestId("llm-model-select")).toBeInTheDocument();
    expect(
      screen.queryByTestId("health-banner-hermes"),
    ).not.toBeInTheDocument();
  });

  it("renders health banner when Hermes Agent is disconnected", async () => {
    mockUseHealthStatus.mockReturnValue([
      {
        serviceId: "wright-api",
        name: "Wright API",
        endpoint: "/api/health",
        state: "connected",
        lastChecked: Date.now(),
      },
      {
        serviceId: "hermes-agent",
        name: "Hermes Agent",
        endpoint: "/api/agent/health",
        state: "disconnected",
        lastChecked: Date.now(),
        error: "Hermes gateway is offline",
      },
    ]);

    await renderLayout();

    expect(screen.getByTestId("health-banner-hermes")).toBeInTheDocument();
    expect(
      screen.getByText(/Hermes agent is not available/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Hermes gateway is offline/i)).toBeInTheDocument();
  });

  it("renders thinking indicator when streaming but no text received yet", async () => {
    mockUseChat.mockReturnValue({
      state: {
        sessions: [
          {
            sessionId: "session1",
            title: "Test Session",
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            isActive: true,
          },
        ],
        activeSessionId: "session1",
        isStreaming: true,
        streamingSessionId: "session1",
        activeTool: null,
        streamActivity: [],
        streamedText: "",
        activeStreamId: "stream-1",
        streamStates: {
          session1: {
            isStreaming: true,
            startedAt: Date.now(),
            activeTool: null,
            streamActivity: [],
            streamedText: "",
            activeStreamId: "stream-1",
            rivetMutationVersion: 0,
          },
        },
      },
      createSession: vi.fn(),
      selectSession: vi.fn(),
      deleteSession: vi.fn(),
      sendMessage: vi.fn(),
      refreshSessions: vi.fn(),
    });

    await renderLayout();

    expect(screen.getByTestId("thinking-indicator")).toBeInTheDocument();
  });

  it("verifies that clicking the '+' button triggers createSession", async () => {
    const mockCreateSession = vi.fn().mockResolvedValue("new-session-id");
    const mockSelectSession = vi.fn();
    mockUseChat.mockReturnValue({
      state: {
        sessions: [
          {
            sessionId: "session1",
            title: "Test Session",
            messages: [],
            createdAt: Date.now(),
            updatedAt: Date.now(),
            isActive: true,
          },
        ],
        activeSessionId: "session1",
        isStreaming: false,
        streamingSessionId: null,
        activeTool: null,
        streamActivity: [],
        streamedText: "",
        activeStreamId: null,
        streamStates: {},
      },
      createSession: mockCreateSession,
      selectSession: mockSelectSession,
      deleteSession: vi.fn(),
      sendMessage: vi.fn(),
      refreshSessions: vi.fn(),
    });

    await renderLayout();

    const plusBtn = screen.getByTestId("create-session-btn");
    expect(plusBtn).toBeInTheDocument();
    await act(async () => plusBtn.click());

    expect(mockCreateSession).toHaveBeenCalled();
    expect(mockSelectSession).toHaveBeenCalledWith("new-session-id");
  });
});
