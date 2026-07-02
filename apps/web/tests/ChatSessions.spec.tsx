import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ChatProvider, useChat } from "../src/store/sessions";
import agentService from "../src/services/agent-service";
import type { ChatSession } from "../src/store/types";

vi.mock("../src/services/agent-service", () => ({
  default: {
    listSessions: vi.fn(),
    createSession: vi.fn(),
    getSessionHistory: vi.fn(),
    deleteSession: vi.fn(),
    sendMessage: vi.fn(),
    cancelStream: vi.fn(),
  },
}));

function createLocalStorageMock(): Storage {
  let items: Record<string, string> = {};

  return {
    get length() {
      return Object.keys(items).length;
    },
    clear: vi.fn(() => {
      items = {};
    }),
    getItem: vi.fn((key: string) => items[key] ?? null),
    key: vi.fn((index: number) => Object.keys(items)[index] ?? null),
    removeItem: vi.fn((key: string) => {
      delete items[key];
    }),
    setItem: vi.fn((key: string, value: string) => {
      items[key] = value;
    }),
  };
}

function makeSession(overrides: Partial<ChatSession>): ChatSession {
  return {
    sessionId: "session-1",
    title: "Test Session",
    messages: [],
    createdAt: 1000,
    updatedAt: 1000,
    isActive: true,
    ...overrides,
  };
}

const localStorageMock = createLocalStorageMock();

function SessionsHarness() {
  const { state, createSession } = useChat();

  return (
    <div>
      <div data-testid="active-session">{state.activeSessionId}</div>
      <button onClick={() => createSession("/home/agent/wright/test")}>
        create
      </button>
      <ul>
        {state.sessions.map((session) => (
          <li data-testid="session-row" key={session.sessionId}>
            {session.title}:{session.sessionId}
          </li>
        ))}
      </ul>
    </div>
  );
}

describe("ChatProvider session state", () => {
  beforeEach(() => {
    vi.stubGlobal("localStorage", localStorageMock);
    vi.clearAllMocks();
    localStorageMock.clear();
    vi.mocked(agentService.getSessionHistory).mockResolvedValue([]);
  });

  it("deduplicates sessions returned by backend refreshes", async () => {
    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "session-1",
        title: "Test Session 2",
        createdAt: 1000,
        updatedAt: 1000,
      },
      {
        sessionId: "session-1",
        title: "Test Session 2",
        createdAt: 1000,
        updatedAt: 1001,
      },
      {
        sessionId: "session-2",
        title: "Can you tell me ho...",
        createdAt: 1002,
        updatedAt: 1002,
      },
    ]);

    render(
      <ChatProvider>
        <SessionsHarness />
      </ChatProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByTestId("session-row")).toHaveLength(2);
    });

    expect(screen.getByText("Test Session 2:session-1")).toBeInTheDocument();
    expect(
      screen.getByText("Can you tell me ho...:session-2"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("active-session")).toHaveTextContent("session-1");
  });

  it("replaces an existing session when create returns the same session id", async () => {
    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "session-1",
        title: "Test Session 2",
        createdAt: 1000,
        updatedAt: 1000,
      },
    ]);
    vi.mocked(agentService.createSession).mockResolvedValue(
      makeSession({
        sessionId: "session-1",
        title: "Test Session 2",
        createdAt: 1000,
        updatedAt: 1003,
      }),
    );

    render(
      <ChatProvider>
        <SessionsHarness />
      </ChatProvider>,
    );

    await waitFor(() => {
      expect(screen.getAllByTestId("session-row")).toHaveLength(1);
    });

    fireEvent.click(screen.getByRole("button", { name: "create" }));

    await waitFor(() => {
      expect(screen.getAllByTestId("session-row")).toHaveLength(1);
    });
    expect(screen.getByTestId("active-session")).toHaveTextContent("session-1");
  });

  it("coalesces concurrent create requests into one backend session", async () => {
    let resolveCreate: (session: ChatSession) => void = () => {};
    const createPromise = new Promise<ChatSession>((resolve) => {
      resolveCreate = resolve;
    });

    vi.mocked(agentService.listSessions).mockResolvedValue([]);
    vi.mocked(agentService.createSession).mockReturnValue(createPromise);

    render(
      <ChatProvider>
        <SessionsHarness />
      </ChatProvider>,
    );

    const createButton = screen.getByRole("button", { name: "create" });
    fireEvent.click(createButton);
    fireEvent.click(createButton);

    expect(agentService.createSession).toHaveBeenCalledTimes(1);

    resolveCreate(
      makeSession({
        sessionId: "session-2",
        title: "Test Session 1",
        createdAt: 1004,
        updatedAt: 1004,
      }),
    );

    await waitFor(() => {
      expect(screen.getAllByTestId("session-row")).toHaveLength(1);
    });
    expect(screen.getByText("Test Session 1:session-2")).toBeInTheDocument();
  });
});
