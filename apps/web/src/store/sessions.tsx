import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useCallback,
  useRef,
} from "react";
import type { ReactNode } from "react";
import type { ChatSession, ChatMessage } from "./types";
import agentService from "../services/agent-service";

export interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isStreaming: boolean;
  activeTool: { name: string; preview: string; percentage?: number } | null;
  streamedText: string;
  activeStreamId: string | null;
  promptQueue: { content: string; attachments?: string[] }[];
}

type ChatAction =
  | { type: "SET_SESSIONS"; sessions: ChatSession[] }
  | { type: "SELECT_SESSION"; sessionId: string }
  | { type: "CREATE_SESSION"; session: ChatSession }
  | { type: "DELETE_SESSION"; sessionId: string }
  | { type: "ADD_MESSAGE"; sessionId: string; message: ChatMessage }
  | { type: "LOAD_SESSION_HISTORY"; sessionId: string; messages: ChatMessage[] }
  | { type: "UPDATE_SESSION_TITLE"; sessionId: string; title: string }
  | { type: "START_STREAMING"; streamId?: string }
  | { type: "APPEND_STREAM_TOKEN"; text: string }
  | {
      type: "SET_ACTIVE_TOOL";
      name: string;
      preview: string;
      percentage?: number;
    }
  | { type: "SET_TOOL_PROGRESS"; percentage: number; message: string }
  | { type: "CLEAR_ACTIVE_TOOL" }
  | { type: "END_STREAMING"; finalSession?: ChatSession }
  | {
      type: "QUEUE_PROMPT";
      prompt: { content: string; attachments?: string[] };
    }
  | { type: "DEQUEUE_PROMPT" }
  | { type: "CLEAR_STREAM_ID" };

const initialState: ChatState = {
  sessions: [],
  activeSessionId: null,
  isStreaming: false,
  activeTool: null,
  streamedText: "",
  activeStreamId: null,
  promptQueue: [],
};

function hasUsefulTitle(session: ChatSession): boolean {
  return Boolean(
    session.title &&
    session.title !== "Untitled" &&
    session.title !== "Undefined",
  );
}

function mergeDuplicateSession(
  existing: ChatSession,
  incoming: ChatSession,
): ChatSession {
  const title = hasUsefulTitle(incoming)
    ? incoming.title
    : hasUsefulTitle(existing)
      ? existing.title
      : incoming.title || existing.title;

  return {
    ...existing,
    ...incoming,
    title,
    messages:
      incoming.messages.length > 0 ? incoming.messages : existing.messages,
    createdAt: Math.min(existing.createdAt, incoming.createdAt),
    updatedAt: Math.max(existing.updatedAt, incoming.updatedAt),
    isActive: existing.isActive || incoming.isActive,
  };
}

function dedupeSessionsById(sessions: ChatSession[]): ChatSession[] {
  const orderedIds: string[] = [];
  const sessionsById = new Map<string, ChatSession>();

  for (const session of sessions) {
    if (!session?.sessionId) continue;

    const existing = sessionsById.get(session.sessionId);
    if (existing) {
      sessionsById.set(
        session.sessionId,
        mergeDuplicateSession(existing, session),
      );
    } else {
      orderedIds.push(session.sessionId);
      sessionsById.set(session.sessionId, session);
    }
  }

  return orderedIds
    .map((sessionId) => sessionsById.get(sessionId))
    .filter((session): session is ChatSession => Boolean(session));
}

function getActiveSessionId(
  sessions: ChatSession[],
  preferredSessionId: string | null,
): string | null {
  if (
    preferredSessionId &&
    sessions.some((session) => session.sessionId === preferredSessionId)
  ) {
    return preferredSessionId;
  }

  return (
    sessions.find((session) => session.isActive)?.sessionId ||
    sessions[0]?.sessionId ||
    null
  );
}

function applyActiveSession(
  sessions: ChatSession[],
  activeSessionId: string | null,
): ChatSession[] {
  return sessions.map((session) => ({
    ...session,
    isActive: session.sessionId === activeSessionId,
  }));
}

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  let newState = state;

  switch (action.type) {
    case "SET_SESSIONS": {
      const incomingSessions = dedupeSessionsById(action.sessions);
      const mergedSessions = incomingSessions.map((newSess) => {
        const existingSess = state.sessions.find(
          (s) => s.sessionId === newSess.sessionId,
        );
        return {
          ...newSess,
          messages:
            existingSess && existingSess.messages.length > 0
              ? existingSess.messages
              : newSess.messages,
          isActive: newSess.isActive || (existingSess?.isActive ?? false),
        };
      });
      const activeSessionId = getActiveSessionId(
        mergedSessions,
        state.activeSessionId,
      );
      newState = {
        ...state,
        sessions: applyActiveSession(mergedSessions, activeSessionId),
        activeSessionId,
      };
      break;
    }

    case "SELECT_SESSION":
      newState = {
        ...state,
        activeSessionId: action.sessionId,
        sessions: state.sessions.map((s) => ({
          ...s,
          isActive: s.sessionId === action.sessionId,
        })),
      };
      break;

    case "CREATE_SESSION": {
      const existingSessions = dedupeSessionsById(state.sessions);
      const existingSession = existingSessions.find(
        (session) => session.sessionId === action.session.sessionId,
      );
      const createdSession = {
        ...action.session,
        messages:
          action.session.messages.length > 0
            ? action.session.messages
            : existingSession?.messages || [],
        isActive: true,
      };
      newState = {
        ...state,
        activeSessionId: createdSession.sessionId,
        sessions: [
          createdSession,
          ...existingSessions
            .filter((s) => s.sessionId !== createdSession.sessionId)
            .map((s) => ({ ...s, isActive: false })),
        ],
      };
      break;
    }

    case "DELETE_SESSION":
      const remainingSessions = state.sessions.filter(
        (s) => s.sessionId !== action.sessionId,
      );
      let nextActiveId = state.activeSessionId;
      if (state.activeSessionId === action.sessionId) {
        nextActiveId = remainingSessions[0]?.sessionId || null;
      }
      newState = {
        ...state,
        sessions: remainingSessions.map((s) => ({
          ...s,
          isActive: s.sessionId === nextActiveId,
        })),
        activeSessionId: nextActiveId,
      };
      break;

    case "ADD_MESSAGE":
      newState = {
        ...state,
        sessions: state.sessions.map((s) => {
          if (s.sessionId === action.sessionId) {
            const messages = [...s.messages, action.message];
            return {
              ...s,
              messages,
              updatedAt: Date.now(),
              title:
                s.title === "New Engineering Session" && messages.length > 0
                  ? messages[0].content.length > 30
                    ? `${messages[0].content.substring(0, 27)}...`
                    : messages[0].content
                  : s.title,
            };
          }
          return s;
        }),
      };
      break;

    case "UPDATE_SESSION_TITLE":
      newState = {
        ...state,
        sessions: state.sessions.map((s) =>
          s.sessionId === action.sessionId
            ? { ...s, title: action.title, updatedAt: Date.now() }
            : s,
        ),
      };
      break;

    case "START_STREAMING":
      newState = {
        ...state,
        isStreaming: true,
        streamedText: "",
        activeStreamId: action.streamId || null,
      };
      break;

    case "APPEND_STREAM_TOKEN":
      newState = {
        ...state,
        streamedText: state.streamedText + action.text,
      };
      break;

    case "SET_ACTIVE_TOOL":
      newState = {
        ...state,
        activeTool: {
          name: action.name,
          preview: action.preview,
          percentage: action.percentage,
        },
      };
      break;

    case "SET_TOOL_PROGRESS":
      newState = {
        ...state,
        activeTool: state.activeTool
          ? {
              ...state.activeTool,
              percentage: action.percentage,
              preview: action.message,
            }
          : null,
      };
      break;

    case "CLEAR_ACTIVE_TOOL":
      newState = {
        ...state,
        activeTool: null,
      };
      break;

    case "LOAD_SESSION_HISTORY":
      newState = {
        ...state,
        sessions: state.sessions.map((s) => {
          if (s.sessionId === action.sessionId) {
            let title = s.title;
            if (
              (!title || title === "Untitled" || title === "Undefined") &&
              action.messages.length > 0
            ) {
              const firstMsg = action.messages[0].content;
              title =
                firstMsg.length > 30
                  ? `${firstMsg.substring(0, 27)}...`
                  : firstMsg;
            }
            return {
              ...s,
              messages: action.messages,
              title,
            };
          }
          return s;
        }),
      };
      break;

    case "END_STREAMING":
      newState = {
        ...state,
        isStreaming: false,
        activeTool: null,
        streamedText: "",
        activeStreamId: null,
        sessions: action.finalSession
          ? state.sessions.map((s) =>
              s.sessionId === action.finalSession!.sessionId
                ? action.finalSession!
                : s,
            )
          : state.sessions,
      };
      break;

    case "QUEUE_PROMPT":
      newState = {
        ...state,
        promptQueue: [...state.promptQueue, action.prompt],
      };
      break;

    case "DEQUEUE_PROMPT":
      newState = {
        ...state,
        promptQueue: state.promptQueue.slice(1),
      };
      break;

    case "CLEAR_STREAM_ID":
      newState = {
        ...state,
        activeStreamId: null,
      };
      break;
  }

  localStorage.setItem(
    "wright-chat-sessions",
    JSON.stringify(newState.sessions),
  );
  return newState;
}

interface ChatContextProps {
  state: ChatState;
  createSession: (workspace?: string) => Promise<string | undefined>;
  selectSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  sendMessage: (
    content: string,
    attachments?: string[],
    isQueuedExecution?: boolean,
  ) => Promise<void>;
  refreshSessions: (workspaceId?: string) => Promise<void>;
  cancelActiveStream: () => Promise<void>;
}

const ChatContext = createContext<ChatContextProps | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);
  const createSessionPromiseRef = useRef<Promise<string | undefined> | null>(
    null,
  );

  const refreshSessions = useCallback(async (workspaceId?: string) => {
    try {
      const compactSessions = await agentService.listSessions(workspaceId);
      const stored = localStorage.getItem("wright-chat-sessions");
      let localSessions: ChatSession[] = [];
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) {
            localSessions = parsed;
          }
        } catch (e) {}
      }

      const sessions: ChatSession[] = compactSessions.map((cs) => {
        const matched = Array.isArray(localSessions)
          ? localSessions.find((ls) => ls?.sessionId === cs.sessionId)
          : undefined;

        let title = cs.title;
        if (
          (!title || title === "Untitled" || title === "Undefined") &&
          matched &&
          matched.title &&
          matched.title !== "Untitled" &&
          matched.title !== "Undefined"
        ) {
          title = matched.title;
        }
        if (
          (!title || title === "Untitled" || title === "Undefined") &&
          matched &&
          matched.messages &&
          matched.messages.length > 0
        ) {
          const firstMsg = matched.messages[0].content;
          title =
            firstMsg.length > 30 ? `${firstMsg.substring(0, 27)}...` : firstMsg;
        }

        return {
          sessionId: cs.sessionId,
          title,
          createdAt: cs.createdAt,
          updatedAt: cs.updatedAt,
          messages: matched ? matched.messages : [],
          isActive: matched ? matched.isActive : false,
        };
      });

      dispatch({ type: "SET_SESSIONS", sessions });
    } catch (err) {
      console.error(
        "Failed to sync sessions with backend, falling back to localStorage",
        err,
      );
      const stored = localStorage.getItem("wright-chat-sessions");
      let fallbackSessions: ChatSession[] = [];
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) {
            fallbackSessions = parsed;
          }
        } catch (e) {}
      }
      dispatch({ type: "SET_SESSIONS", sessions: fallbackSessions });
    }
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  useEffect(() => {
    if (!state.activeSessionId) return;

    let isMounted = true;
    const fetchHistory = async () => {
      try {
        const history = await agentService.getSessionHistory(
          state.activeSessionId!,
        );
        if (isMounted) {
          dispatch({
            type: "LOAD_SESSION_HISTORY",
            sessionId: state.activeSessionId!,
            messages: history,
          });
        }
      } catch (err) {
        console.error("Failed to load history for active session", err);
      }
    };

    fetchHistory();

    return () => {
      isMounted = false;
    };
  }, [state.activeSessionId]);

  const createSession = useCallback(
    async (workspace?: string) => {
      if (createSessionPromiseRef.current) {
        return createSessionPromiseRef.current;
      }

      const createPromise = (async () => {
        try {
          const session = await agentService.createSession(workspace);

          if (
            !session.title ||
            session.title === "Untitled" ||
            session.title === "Undefined"
          ) {
            const workspaceName = workspace
              ? workspace.split(/[\\/]/).pop()
              : "Workspace";
            const baseName =
              workspaceName!.charAt(0).toUpperCase() + workspaceName!.slice(1);
            const count = state.sessions.length + 1;
            session.title = `${baseName} Session ${count}`;
          }

          dispatch({ type: "CREATE_SESSION", session });
          return session.sessionId;
        } catch (err) {
          console.error("Failed to create session on backend", err);
          return undefined;
        } finally {
          createSessionPromiseRef.current = null;
        }
      })();

      createSessionPromiseRef.current = createPromise;
      return createPromise;
    },
    [state.sessions],
  );

  const selectSession = useCallback(async (sessionId: string) => {
    dispatch({ type: "SELECT_SESSION", sessionId });
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await agentService.deleteSession(sessionId);
      dispatch({ type: "DELETE_SESSION", sessionId });
    } catch (err) {
      console.error("Failed to delete session on backend", err);
    }
  }, []);

  const sendMessage = useCallback(
    async (
      content: string,
      attachments?: string[],
      isQueuedExecution?: boolean,
    ) => {
      if (!state.activeSessionId) return;
      const sessionId = state.activeSessionId;

      const isSlashCommand = content.trim().startsWith("/");
      if (!isSlashCommand && state.isStreaming) {
        const userMsg: ChatMessage = {
          id: Math.random().toString(36).substring(7),
          role: "user",
          content,
          timestamp: Date.now(),
          traceId: "tr-" + Math.random().toString(36).substring(7),
        };
        dispatch({ type: "ADD_MESSAGE", sessionId, message: userMsg });
        dispatch({ type: "QUEUE_PROMPT", prompt: { content, attachments } });
        return;
      }

      if (!isQueuedExecution) {
        const userMsg: ChatMessage = {
          id: Math.random().toString(36).substring(7),
          role: "user",
          content,
          timestamp: Date.now(),
          traceId: "tr-" + Math.random().toString(36).substring(7),
        };
        dispatch({ type: "ADD_MESSAGE", sessionId, message: userMsg });
      }

      dispatch({ type: "START_STREAMING" });

      let accumulatedText = "";
      try {
        const stream = agentService.sendMessage(
          sessionId,
          content,
          attachments,
        );
        for await (const event of stream) {
          if (event.type === "stream_start") {
            dispatch({ type: "START_STREAMING", streamId: event.streamId });
          } else if (event.type === "token") {
            accumulatedText += event.text;
            dispatch({ type: "APPEND_STREAM_TOKEN", text: event.text });
          } else if (event.type === "tool") {
            dispatch({
              type: "SET_ACTIVE_TOOL",
              name: event.name,
              preview: event.preview,
              percentage: event.percentage,
            });
          } else if (event.type === "progress") {
            dispatch({
              type: "SET_TOOL_PROGRESS",
              percentage: event.percentage,
              message: event.message,
            });
          } else if (event.type === "done") {
            const currentSessions = JSON.parse(
              localStorage.getItem("wright-chat-sessions") || "[]",
            );
            const existingSession = currentSessions.find(
              (s: ChatSession) => s.sessionId === sessionId,
            );

            const assistantMsg: ChatMessage = {
              id: Math.random().toString(36).substring(7),
              role: "assistant",
              content: accumulatedText.trim(),
              timestamp: Date.now(),
              traceId: "tr-" + Math.random().toString(36).substring(7),
            };

            const finalSession: ChatSession = existingSession
              ? {
                  ...existingSession,
                  messages: [...existingSession.messages, assistantMsg],
                  updatedAt: Date.now(),
                  title:
                    existingSession.title === "New Engineering Session" ||
                    existingSession.title === "Untitled"
                      ? content.length > 30
                        ? `${content.substring(0, 27)}...`
                        : content
                      : existingSession.title,
                }
              : {
                  ...event.session,
                  messages: [assistantMsg],
                  title:
                    content.length > 30
                      ? `${content.substring(0, 27)}...`
                      : content,
                };

            dispatch({ type: "END_STREAMING", finalSession });
          } else if (event.type === "error") {
            console.error(event.message);
            dispatch({ type: "CLEAR_ACTIVE_TOOL" });

            const errorMsg: ChatMessage = {
              id: Math.random().toString(36).substring(7),
              role: "assistant",
              content: event.message || "An error occurred during streaming.",
              timestamp: Date.now(),
              traceId: null,
            };
            const currentSessions = JSON.parse(
              localStorage.getItem("wright-chat-sessions") || "[]",
            );
            const existingSession = currentSessions.find(
              (s: ChatSession) => s.sessionId === sessionId,
            );
            const finalSession: ChatSession = existingSession
              ? {
                  ...existingSession,
                  messages: [...existingSession.messages, errorMsg],
                  updatedAt: Date.now(),
                }
              : {
                  sessionId,
                  title: "Session",
                  messages: [errorMsg],
                  createdAt: Date.now(),
                  updatedAt: Date.now(),
                  isActive: true,
                };
            dispatch({ type: "END_STREAMING", finalSession });
          }
        }
      } catch (err) {
        console.error("Failed to send message", err);
        dispatch({ type: "CLEAR_ACTIVE_TOOL" });
        dispatch({ type: "END_STREAMING" });
      }
    },
    [state.activeSessionId, state.isStreaming],
  );

  const cancelActiveStream = useCallback(async () => {
    if (!state.activeSessionId) return;
    await agentService.cancelStream(state.activeSessionId);
    dispatch({ type: "CLEAR_STREAM_ID" });
  }, [state.activeSessionId]);

  useEffect(() => {
    if (
      !state.isStreaming &&
      state.promptQueue.length > 0 &&
      state.activeSessionId
    ) {
      const nextPrompt = state.promptQueue[0];
      dispatch({ type: "DEQUEUE_PROMPT" });
      sendMessage(nextPrompt.content, nextPrompt.attachments, true);
    }
  }, [
    state.isStreaming,
    state.promptQueue,
    state.activeSessionId,
    sendMessage,
  ]);

  return (
    <ChatContext.Provider
      value={{
        state,
        createSession,
        selectSession,
        deleteSession,
        sendMessage,
        refreshSessions,
        cancelActiveStream,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
