import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
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
  beforeEach(() => {
    vi.resetAllMocks();
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

  it("renders three-panel layout and no banner when connected", () => {
    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <ChatLayout />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

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

  it("renders health banner when Hermes Agent is disconnected", () => {
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

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <ChatLayout />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    expect(screen.getByTestId("health-banner-hermes")).toBeInTheDocument();
    expect(
      screen.getByText(/Hermes agent is not available/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Hermes gateway is offline/i)).toBeInTheDocument();
  });

  it("renders thinking indicator when streaming but no text received yet", () => {
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
            activeTool: null,
            streamActivity: [],
            streamedText: "",
            activeStreamId: "stream-1",
          },
        },
      },
      createSession: vi.fn(),
      selectSession: vi.fn(),
      deleteSession: vi.fn(),
      sendMessage: vi.fn(),
      refreshSessions: vi.fn(),
    });

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <ChatLayout />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

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

    render(
      <MemoryRouter>
        <ViewerPanelProvider>
          <ChatLayout />
        </ViewerPanelProvider>
      </MemoryRouter>,
    );

    const plusBtn = screen.getByTestId("create-session-btn");
    expect(plusBtn).toBeInTheDocument();
    plusBtn.click();

    expect(mockCreateSession).toHaveBeenCalled();
  });
});
