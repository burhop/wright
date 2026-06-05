import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import ChatLayout from "../src/components/chat/ChatLayout";

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
        activeTool: null,
        streamedText: "",
      },
      createSession: vi.fn(),
      selectSession: vi.fn(),
      deleteSession: vi.fn(),
      sendMessage: vi.fn(),
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
      {
        serviceId: "inference",
        name: "LLM Inference",
        endpoint: "/api/inference/health",
        state: "connected",
        lastChecked: Date.now(),
      },
    ]);
  });

  it("renders three-panel layout and no banner when connected", () => {
    render(
      <MemoryRouter>
        <ChatLayout />
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
      },
      {
        serviceId: "inference",
        name: "LLM Inference",
        endpoint: "/api/inference/health",
        state: "connected",
        lastChecked: Date.now(),
      },
    ]);

    render(
      <MemoryRouter>
        <ChatLayout />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("health-banner-hermes")).toBeInTheDocument();
    expect(
      screen.getByText(/Hermes agent is not available/i),
    ).toBeInTheDocument();
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
        activeTool: null,
        streamedText: "",
      },
      createSession: vi.fn(),
      selectSession: vi.fn(),
      deleteSession: vi.fn(),
      sendMessage: vi.fn(),
    });

    render(
      <MemoryRouter>
        <ChatLayout />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("thinking-indicator")).toBeInTheDocument();
  });
});
