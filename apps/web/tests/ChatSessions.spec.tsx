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
    getStreamStatus: vi.fn(),
    attachStream: vi.fn(),
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
      <button
        onClick={() => createSession("/home/agent/wright/test", "workspace-1")}
      >
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

function ChatMessagesHarness() {
  const { state, sendMessage, steerMessage } = useChat();
  const activeSession = state.sessions.find(
    (session) => session.sessionId === state.activeSessionId,
  );

  return (
    <div>
      <div data-testid="chat-active-session">{state.activeSessionId}</div>
      <button onClick={() => sendMessage("hello")}>send hello</button>
      <button onClick={() => sendMessage("/title test")}>send title</button>
      <button onClick={() => steerMessage("use the upper face")}>
        steer upper face
      </button>
      <div data-testid="prompt-queue-size">{state.promptQueue.length}</div>
      <div data-testid="prompt-queue-order">
        {state.promptQueue.map((prompt) => prompt.content).join("|")}
      </div>
      <div data-testid="chat-is-streaming">
        {String(
          Boolean(
            state.activeSessionId &&
            state.streamStates[state.activeSessionId]?.isStreaming,
          ),
        )}
      </div>
      <div data-testid="chat-streamed-text">
        {state.activeSessionId
          ? state.streamStates[state.activeSessionId]?.streamedText
          : ""}
      </div>
      <div data-testid="chat-stream-started-at">
        {state.activeSessionId
          ? state.streamStates[state.activeSessionId]?.startedAt
          : ""}
      </div>
      <ul>
        {(activeSession?.messages || []).map((message) => (
          <li data-testid="chat-message" key={message.id}>
            {message.role}:{message.content}
          </li>
        ))}
      </ul>
    </div>
  );
}

function WorkspaceScopedSessionsHarness() {
  const { state, refreshSessions } = useChat();

  return (
    <div>
      <button onClick={() => refreshSessions("workspace-1")}>
        refresh workspace
      </button>
      <ul>
        {state.sessions.map((session) => (
          <li data-testid="workspace-session-row" key={session.sessionId}>
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
    vi.mocked(agentService.getStreamStatus).mockResolvedValue({
      active: false,
      sessionId: "session-1",
    });
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

  it("keeps locally saved sessions that are missing from a backend refresh", async () => {
    localStorageMock.setItem(
      "wright-chat-sessions",
      JSON.stringify([
        makeSession({
          sessionId: "local-only",
          title: "Earlier CAD Session",
          messages: [
            {
              id: "msg-local",
              role: "user",
              content: "old design question",
              timestamp: 900,
              traceId: null,
            },
          ],
          createdAt: 900,
          updatedAt: 950,
          isActive: true,
        }),
      ]),
    );

    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "backend-only",
        title: "Current Hermes Session",
        createdAt: 1000,
        updatedAt: 1000,
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

    expect(
      screen.getByText("Current Hermes Session:backend-only"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Earlier CAD Session:local-only"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("active-session")).toHaveTextContent(
      "local-only",
    );
  });

  it("preserves cached messages when backend refresh returns compact sessions", async () => {
    localStorageMock.setItem(
      "wright-chat-sessions",
      JSON.stringify([
        makeSession({
          sessionId: "session-1",
          title: "Cached Session",
          messages: [
            {
              id: "cached-message",
              role: "assistant",
              content: "cached assistant response",
              timestamp: 1001,
              traceId: null,
            },
          ],
        }),
      ]),
    );

    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "session-1",
        title: "Untitled",
        createdAt: 1000,
        updatedAt: 1002,
      },
    ]);

    render(
      <ChatProvider>
        <ChatMessagesHarness />
      </ChatProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("assistant:cached assistant response"),
      ).toBeInTheDocument();
    });
  });

  it("reattaches to a running turn after the provider reloads", async () => {
    const startedAt = Date.now() - 12_000;
    const existingHistory = [
      {
        id: "earlier-assistant",
        role: "assistant" as const,
        content: "Earlier context",
        timestamp: startedAt - 1000,
        traceId: null,
      },
    ];
    const completedHistory = [
      ...existingHistory,
      {
        id: "running-user",
        role: "user" as const,
        content: "finish the bracket",
        timestamp: startedAt,
        traceId: "stream-reload",
      },
      {
        id: "running-assistant",
        role: "assistant" as const,
        content: "Bracket finished",
        timestamp: startedAt + 1000,
        traceId: "stream-reload",
      },
    ];
    let finishStream = () => {};
    const keepRunning = new Promise<void>((resolve) => {
      finishStream = resolve;
    });

    localStorageMock.setItem(
      "wright-chat-sessions",
      JSON.stringify([makeSession({ isActive: true })]),
    );
    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "session-1",
        title: "Test Session",
        createdAt: 1000,
        updatedAt: 1001,
      },
    ]);
    vi.mocked(agentService.getSessionHistory)
      .mockResolvedValueOnce(existingHistory)
      .mockResolvedValue(completedHistory);
    vi.mocked(agentService.getStreamStatus).mockResolvedValue({
      active: true,
      sessionId: "session-1",
      streamId: "stream-reload",
      message: "finish the bracket",
      startedAt,
      eventCount: 2,
    });
    vi.mocked(agentService.attachStream).mockImplementation(async function* () {
      yield {
        type: "stream_start",
        streamId: "stream-reload",
        startedAt,
      };
      yield { type: "token", text: "Bracket " };
      await keepRunning;
      yield { type: "token", text: "finished" };
      yield {
        type: "done",
        session: makeSession({ sessionId: "session-1" }),
      };
    });

    render(
      <ChatProvider>
        <ChatMessagesHarness />
      </ChatProvider>,
    );

    expect(
      await screen.findByText("assistant:Earlier context"),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("user:finish the bracket"),
    ).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByTestId("chat-is-streaming")).toHaveTextContent("true");
      expect(screen.getByTestId("chat-streamed-text")).toHaveTextContent(
        "Bracket",
      );
      expect(screen.getByTestId("chat-stream-started-at")).toHaveTextContent(
        String(startedAt),
      );
    });

    finishStream();
    await waitFor(() => {
      expect(screen.getByTestId("chat-is-streaming")).toHaveTextContent(
        "false",
      );
      expect(
        screen.getByText("assistant:Bracket finished"),
      ).toBeInTheDocument();
    });
    expect(agentService.attachStream).toHaveBeenCalledWith("session-1");
    expect(agentService.sendMessage).not.toHaveBeenCalled();
  });

  it("shows only cached sessions for the active workspace during scoped refresh", async () => {
    localStorageMock.setItem(
      "wright-chat-sessions",
      JSON.stringify([
        makeSession({
          sessionId: "workspace-1-session",
          title: "Workspace One Session",
          workspaceId: "workspace-1",
          isActive: true,
        }),
        makeSession({
          sessionId: "workspace-2-session",
          title: "Workspace Two Session",
          workspaceId: "workspace-2",
          isActive: false,
        }),
        makeSession({
          sessionId: "legacy-session",
          title: "Unscoped Legacy Session",
          isActive: false,
        }),
      ]),
    );

    vi.mocked(agentService.listSessions).mockResolvedValue([]);

    render(
      <ChatProvider>
        <WorkspaceScopedSessionsHarness />
      </ChatProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "refresh workspace" }));

    await waitFor(() => {
      expect(screen.getAllByTestId("workspace-session-row")).toHaveLength(1);
    });

    expect(
      screen.getByText("Workspace One Session:workspace-1-session"),
    ).toBeInTheDocument();
    expect(screen.queryByText(/Workspace Two Session/)).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Unscoped Legacy Session/),
    ).not.toBeInTheDocument();

    const cachedSessions = JSON.parse(
      localStorageMock.getItem("wright-chat-sessions") || "[]",
    ) as ChatSession[];
    expect(
      cachedSessions.some(
        (session) => session.sessionId === "workspace-2-session",
      ),
    ).toBe(true);
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

  it("replaces stale cached raw messages with normalized server history", async () => {
    localStorageMock.setItem(
      "wright-chat-sessions",
      JSON.stringify([
        makeSession({
          sessionId: "session-1",
          title: "[Workspace::v1: /h...",
          messages: [
            {
              id: "raw-tool",
              role: "assistant",
              content: '{"bytes_written": 21769, "status": "skipped"}',
              timestamp: 1000,
              traceId: null,
            },
          ],
        }),
      ]),
    );

    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "session-1",
        title: "Untitled",
        createdAt: 1000,
        updatedAt: 1000,
      },
    ]);
    vi.mocked(agentService.getSessionHistory).mockResolvedValue([
      {
        id: "clean-user",
        role: "user",
        content: "hello",
        timestamp: 1001,
        traceId: null,
      },
      {
        id: "clean-assistant",
        role: "assistant",
        content: "Hello Al — I’m here.",
        timestamp: 1002,
        traceId: null,
      },
    ]);

    render(
      <ChatProvider>
        <ChatMessagesHarness />
      </ChatProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("user:hello")).toBeInTheDocument();
      expect(
        screen.getByText("assistant:Hello Al — I’m here."),
      ).toBeInTheDocument();
    });

    expect(screen.queryByText(/bytes_written/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Workspace::v1/)).not.toBeInTheDocument();
  });

  it("updates the visible session title after a Hermes title command", async () => {
    vi.mocked(agentService.listSessions)
      .mockResolvedValueOnce([
        {
          sessionId: "session-1",
          title: "Onshape Session 2",
          createdAt: 1000,
          updatedAt: 1000,
        },
      ])
      .mockResolvedValue([
        {
          sessionId: "session-1",
          title: "test",
          createdAt: 1000,
          updatedAt: 1001,
        },
      ]);
    vi.mocked(agentService.sendMessage).mockImplementation(async function* () {
      yield {
        type: "token",
        text: "Title set to “test”.",
      };
      yield {
        type: "done",
        session: makeSession({
          sessionId: "session-1",
          title: "test",
          messages: [],
        }),
      };
    });

    render(
      <ChatProvider>
        <SessionsHarness />
        <ChatMessagesHarness />
      </ChatProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByText("Onshape Session 2:session-1"),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "send title" }));

    await waitFor(() => {
      expect(screen.getByText("test:session-1")).toBeInTheDocument();
    });
    expect(
      screen.queryByText("Onshape Session 2:session-1"),
    ).not.toBeInTheDocument();
  });

  it("queues every busy submission, including slash commands", async () => {
    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "session-1",
        title: "Test Session",
        createdAt: 1000,
        updatedAt: 1000,
      },
    ]);

    let finishFirstTurn = () => {};
    const firstTurn = new Promise<void>((resolve) => {
      finishFirstTurn = resolve;
    });
    vi.mocked(agentService.sendMessage)
      .mockImplementationOnce(async function* () {
        await firstTurn;
        yield {
          type: "done",
          session: makeSession({ sessionId: "session-1" }),
        };
      })
      .mockImplementationOnce(async function* () {
        yield {
          type: "done",
          session: makeSession({ sessionId: "session-1", title: "test" }),
        };
      });

    render(
      <ChatProvider>
        <ChatMessagesHarness />
      </ChatProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("chat-active-session")).toHaveTextContent(
        "session-1",
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "send hello" }));
    await waitFor(() => {
      expect(agentService.sendMessage).toHaveBeenCalledTimes(1);
    });

    fireEvent.click(screen.getByRole("button", { name: "send title" }));

    expect(screen.getByTestId("prompt-queue-size")).toHaveTextContent("1");
    expect(screen.getByTestId("prompt-queue-order")).toHaveTextContent(
      "/title test",
    );
    expect(agentService.sendMessage).toHaveBeenCalledTimes(1);

    finishFirstTurn();
    await waitFor(() => {
      expect(agentService.sendMessage).toHaveBeenCalledTimes(2);
    });
    expect(vi.mocked(agentService.sendMessage).mock.calls[1]?.[1]).toBe(
      "/title test",
    );
  });

  it("prioritizes a steering prompt, cancels the current turn, then drains the queue", async () => {
    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "session-1",
        title: "Test Session",
        createdAt: 1000,
        updatedAt: 1000,
      },
    ]);

    let cancelFirstTurn = () => {};
    const cancelled = new Promise<void>((resolve) => {
      cancelFirstTurn = resolve;
    });
    vi.mocked(agentService.cancelStream).mockImplementation(async () => {
      cancelFirstTurn();
      return true;
    });
    vi.mocked(agentService.sendMessage)
      .mockImplementationOnce(async function* () {
        await cancelled;
        yield { type: "error", message: "Stream cancelled by user." };
      })
      .mockImplementation(async function* () {
        yield {
          type: "done",
          session: makeSession({ sessionId: "session-1" }),
        };
      });

    render(
      <ChatProvider>
        <ChatMessagesHarness />
      </ChatProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("chat-active-session")).toHaveTextContent(
        "session-1",
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "send hello" }));
    await waitFor(() => {
      expect(agentService.sendMessage).toHaveBeenCalledTimes(1);
    });
    fireEvent.click(screen.getByRole("button", { name: "send title" }));
    fireEvent.click(screen.getByRole("button", { name: "steer upper face" }));

    await waitFor(() => {
      expect(agentService.cancelStream).toHaveBeenCalledWith("session-1");
      expect(agentService.sendMessage).toHaveBeenCalledTimes(3);
    });

    const sentMessages = vi
      .mocked(agentService.sendMessage)
      .mock.calls.map((call) => call[1]);
    expect(sentMessages).toEqual([
      "hello",
      "use the upper face",
      "/title test",
    ]);
    expect(
      screen.queryByText("assistant:Stream cancelled by user."),
    ).not.toBeInTheDocument();
  });

  it("shows a diagnostic instead of saving a blank assistant message", async () => {
    vi.mocked(agentService.listSessions).mockResolvedValue([
      {
        sessionId: "session-1",
        title: "Test Session",
        createdAt: 1000,
        updatedAt: 1000,
      },
    ]);
    vi.mocked(agentService.sendMessage).mockImplementation(async function* () {
      yield {
        type: "done",
        session: makeSession({
          sessionId: "session-1",
          title: "Test Session",
          messages: [],
        }),
      };
    });

    render(
      <ChatProvider>
        <ChatMessagesHarness />
      </ChatProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("chat-active-session")).toHaveTextContent(
        "session-1",
      );
    });

    fireEvent.click(screen.getByRole("button", { name: "send hello" }));

    await waitFor(() => {
      expect(
        screen.getByText(/Hermes ended the chat turn/i),
      ).toBeInTheDocument();
    });
    expect(screen.queryByText(/^assistant:$/)).not.toBeInTheDocument();
  });
});
