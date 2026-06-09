import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useCallback,
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
}

type ChatAction =
  | { type: "SET_SESSIONS"; sessions: ChatSession[] }
  | { type: "SELECT_SESSION"; sessionId: string }
  | { type: "CREATE_SESSION"; session: ChatSession }
  | { type: "DELETE_SESSION"; sessionId: string }
  | { type: "ADD_MESSAGE"; sessionId: string; message: ChatMessage }
  | { type: "LOAD_SESSION_HISTORY"; sessionId: string; messages: ChatMessage[] }
  | { type: "UPDATE_SESSION_TITLE"; sessionId: string; title: string }
  | { type: "START_STREAMING" }
  | { type: "APPEND_STREAM_TOKEN"; text: string }
  | {
      type: "SET_ACTIVE_TOOL";
      name: string;
      preview: string;
      percentage?: number;
    }
  | { type: "SET_TOOL_PROGRESS"; percentage: number; message: string }
  | { type: "CLEAR_ACTIVE_TOOL" }
  | { type: "END_STREAMING"; finalSession: ChatSession };

const initialState: ChatState = {
  sessions: [],
  activeSessionId: null,
  isStreaming: false,
  activeTool: null,
  streamedText: "",
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  let newState = state;

  switch (action.type) {
    case "SET_SESSIONS":
      newState = {
        ...state,
        sessions: action.sessions,
        activeSessionId:
          action.sessions.find((s) => s.isActive)?.sessionId ||
          action.sessions[0]?.sessionId ||
          null,
      };
      break;

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

    case "CREATE_SESSION":
      newState = {
        ...state,
        activeSessionId: action.session.sessionId,
        sessions: [
          action.session,
          ...state.sessions.map((s) => ({ ...s, isActive: false })),
        ],
      };
      break;

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
        sessions: state.sessions.map((s) =>
          s.sessionId === action.sessionId
            ? { ...s, messages: action.messages }
            : s,
        ),
      };
      break;

    case "END_STREAMING":
      newState = {
        ...state,
        isStreaming: false,
        activeTool: null,
        streamedText: "",
        sessions: state.sessions.map((s) =>
          s.sessionId === action.finalSession.sessionId
            ? action.finalSession
            : s,
        ),
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
  sendMessage: (content: string, attachments?: string[]) => Promise<void>;
}

const ChatContext = createContext<ChatContextProps | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  useEffect(() => {
    const hydrateSessions = async () => {
      try {
        const compactSessions = await agentService.listSessions();
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
          return {
            sessionId: cs.sessionId,
            title: cs.title,
            createdAt: cs.createdAt,
            updatedAt: cs.updatedAt,
            messages: matched ? matched.messages : [],
            isActive: matched ? matched.isActive : false,
          };
        });

        dispatch({ type: "SET_SESSIONS", sessions });

        // Fetch history for the active session (if any)
        const activeId =
          sessions.find((s) => s.isActive)?.sessionId ||
          sessions[0]?.sessionId ||
          null;
        if (activeId) {
          try {
            const history = await agentService.getSessionHistory(activeId);
            dispatch({
              type: "LOAD_SESSION_HISTORY",
              sessionId: activeId,
              messages: history,
            });
          } catch (e) {
            console.error("Failed to hydrate active session history", e);
          }
        }
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
    };
    hydrateSessions();
  }, []);

  const createSession = useCallback(
    async (workspace?: string) => {
      try {
        const session = await agentService.createSession(workspace);

        if (
          !session.title ||
          session.title === "Untitled" ||
          session.title === "Undefined"
        ) {
          const workspaceName = workspace
            ? workspace.split("/").pop()
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
      }
    },
    [state.sessions],
  );

  const selectSession = useCallback(async (sessionId: string) => {
    dispatch({ type: "SELECT_SESSION", sessionId });
    try {
      const history = await agentService.getSessionHistory(sessionId);
      dispatch({ type: "LOAD_SESSION_HISTORY", sessionId, messages: history });
    } catch (err) {
      console.error("Failed to load session history", err);
    }
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
    async (content: string, attachments?: string[]) => {
      if (!state.activeSessionId) return;
      const sessionId = state.activeSessionId;

      const userMsg: ChatMessage = {
        id: Math.random().toString(36).substring(7),
        role: "user",
        content,
        timestamp: Date.now(),
        traceId: "tr-" + Math.random().toString(36).substring(7),
      };
      dispatch({ type: "ADD_MESSAGE", sessionId, message: userMsg });
      dispatch({ type: "START_STREAMING" });

      let accumulatedText = "";
      try {
        const stream = agentService.sendMessage(
          sessionId,
          content,
          attachments,
        );
        for await (const event of stream) {
          if (event.type === "token") {
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
            // Construct the final session with assistant's reply message
            // Load the latest sessions to find current state (which has the userMsg added above)
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
          }
        }
      } catch (err) {
        console.error("Failed to send message", err);
        dispatch({ type: "CLEAR_ACTIVE_TOOL" });
      }
    },
    [state.activeSessionId],
  );

  return (
    <ChatContext.Provider
      value={{
        state,
        createSession,
        selectSession,
        deleteSession,
        sendMessage,
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
