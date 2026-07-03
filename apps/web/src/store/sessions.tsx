import {
  createContext,
  useContext,
  useReducer,
  useEffect,
  useCallback,
  useRef,
} from "react";
import type { ReactNode } from "react";
import type { ChatSession, ChatMessage, StreamActivityEntry } from "./types";
import agentService from "../services/agent-service";

export interface ChatStreamState {
  isStreaming: boolean;
  activeTool: { name: string; preview: string; percentage?: number } | null;
  streamActivity: StreamActivityEntry[];
  streamedText: string;
  activeStreamId: string | null;
}

export interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isStreaming: boolean;
  streamingSessionId: string | null;
  activeTool: { name: string; preview: string; percentage?: number } | null;
  streamActivity: StreamActivityEntry[];
  streamedText: string;
  activeStreamId: string | null;
  streamStates: Record<string, ChatStreamState>;
  promptQueue: { sessionId: string; content: string; attachments?: string[] }[];
}

type ChatAction =
  | { type: "SET_SESSIONS"; sessions: ChatSession[] }
  | { type: "SELECT_SESSION"; sessionId: string }
  | { type: "CREATE_SESSION"; session: ChatSession }
  | { type: "DELETE_SESSION"; sessionId: string }
  | { type: "ADD_MESSAGE"; sessionId: string; message: ChatMessage }
  | { type: "LOAD_SESSION_HISTORY"; sessionId: string; messages: ChatMessage[] }
  | { type: "UPDATE_SESSION_TITLE"; sessionId: string; title: string }
  | { type: "START_STREAMING"; sessionId: string; streamId?: string }
  | {
      type: "ADD_STREAM_ACTIVITY";
      sessionId: string;
      entry: Omit<StreamActivityEntry, "id" | "timestamp">;
    }
  | { type: "APPEND_STREAM_TOKEN"; sessionId: string; text: string }
  | {
      type: "SET_ACTIVE_TOOL";
      sessionId: string;
      name: string;
      preview: string;
      percentage?: number;
    }
  | { type: "SET_TOOL_PROGRESS"; sessionId: string; percentage?: number; message: string }
  | { type: "CLEAR_ACTIVE_TOOL"; sessionId: string }
  | { type: "END_STREAMING"; sessionId: string; finalSession?: ChatSession }
  | {
      type: "QUEUE_PROMPT";
      prompt: { sessionId: string; content: string; attachments?: string[] };
    }
  | { type: "DEQUEUE_PROMPT"; sessionId: string }
  | { type: "CLEAR_STREAM_ID"; sessionId: string };

const initialState: ChatState = {
  sessions: [],
  activeSessionId: null,
  isStreaming: false,
  streamingSessionId: null,
  activeTool: null,
  streamActivity: [],
  streamedText: "",
  activeStreamId: null,
  streamStates: {},
  promptQueue: [],
};


function emptyStreamState(): ChatStreamState {
  return {
    isStreaming: false,
    activeTool: null,
    streamActivity: [],
    streamedText: "",
    activeStreamId: null,
  };
}

function setSessionStreamState(
  state: ChatState,
  sessionId: string,
  updater: (streamState: ChatStreamState) => ChatStreamState,
): ChatState {
  const current = state.streamStates[sessionId] || emptyStreamState();
  const streamStates = {
    ...state.streamStates,
    [sessionId]: updater(current),
  };
  const activeStreamState = state.activeSessionId
    ? streamStates[state.activeSessionId] || emptyStreamState()
    : emptyStreamState();
  const anyStreaming = Object.values(streamStates).some(
    (streamState) => streamState.isStreaming,
  );
  const firstStreamingId =
    Object.entries(streamStates).find(([, streamState]) => streamState.isStreaming)?.[0] ||
    null;

  return {
    ...state,
    streamStates,
    isStreaming: anyStreaming,
    streamingSessionId: firstStreamingId,
    activeTool: activeStreamState.activeTool,
    streamActivity: activeStreamState.streamActivity,
    streamedText: activeStreamState.streamedText,
    activeStreamId: activeStreamState.activeStreamId,
  };
}

function stripWorkspaceContext(content: string): string {
  return (content || "")
    .replace(/^\[Workspace::v1:[^\]]*(?:\]\s*)?/, "")
    .trim();
}

function looksLikeToolPayload(content: string): boolean {
  const text = (content || "").trim();
  if (!text || !(text.startsWith("{") || text.startsWith("["))) return false;

  try {
    const payload = JSON.parse(text);
    const toolKeys = new Set([
      "bytes_written",
      "dirs_created",
      "files_modified",
      "file_size",
      "hint",
      "lint",
      "resolved_path",
      "status",
      "truncated",
    ]);
    if (payload && typeof payload === "object" && !Array.isArray(payload)) {
      return Object.keys(payload).some((key) => toolKeys.has(key));
    }
    return (
      Array.isArray(payload) &&
      payload.every((item) => item && typeof item === "object")
    );
  } catch {
    return false;
  }
}

function normalizeMessages(messages: ChatMessage[] = []): ChatMessage[] {
  return messages
    .filter(
      (message) => message.role === "user" || message.role === "assistant",
    )
    .map((message) => ({
      ...message,
      content: stripWorkspaceContext(message.content),
    }))
    .filter(
      (message) => message.content && !looksLikeToolPayload(message.content),
    );
}

function cleanSessionTitle(title: string | undefined | null): string {
  const cleaned = stripWorkspaceContext(title || "");
  if (!cleaned || cleaned === "Untitled" || cleaned === "Undefined")
    return "Untitled";
  return cleaned.length > 30 ? `${cleaned.substring(0, 27)}...` : cleaned;
}

function titleFromMessages(messages: ChatMessage[]): string {
  const firstUser =
    messages.find((message) => message.role === "user") || messages[0];
  return cleanSessionTitle(firstUser?.content || "Untitled");
}

function titleFromSlashCommand(content: string): string | null {
  const match = content.trim().match(/^\/title\s+(.+)$/i);
  if (!match) return null;
  const title = match[1].trim().replace(/^["'“”]+|["'“”]+$/g, "");
  return title ? cleanSessionTitle(title) : null;
}

function hasUsefulTitle(session: ChatSession): boolean {
  return Boolean(cleanSessionTitle(session.title) !== "Untitled");
}

function mergeDuplicateSession(
  existing: ChatSession,
  incoming: ChatSession,
): ChatSession {
  const title = hasUsefulTitle(incoming)
    ? cleanSessionTitle(incoming.title)
    : hasUsefulTitle(existing)
      ? cleanSessionTitle(existing.title)
      : cleanSessionTitle(incoming.title || existing.title);

  return {
    ...existing,
    ...incoming,
    title,
    messages:
      incoming.messages.length > 0
        ? normalizeMessages(incoming.messages)
        : normalizeMessages(existing.messages),
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

function readCachedSessions(): ChatSession[] {
  const stored = localStorage.getItem("wright-chat-sessions");
  if (!stored) return [];

  try {
    const parsed = JSON.parse(stored);
    if (!Array.isArray(parsed)) return [];
    return parsed.map((session) => ({
      ...session,
      title: cleanSessionTitle(session?.title),
      messages: normalizeMessages(session?.messages || []),
    }));
  } catch {
    return [];
  }
}

function writeCachedSessions(visibleSessions: ChatSession[]): void {
  const cachedSessions = readCachedSessions();
  const mergedSessions = dedupeSessionsById([
    ...cachedSessions,
    ...visibleSessions,
  ]);
  localStorage.setItem("wright-chat-sessions", JSON.stringify(mergedSessions));
}

function removeCachedSession(sessionId: string): void {
  const cachedSessions = readCachedSessions().filter(
    (session) => session.sessionId !== sessionId,
  );
  localStorage.setItem("wright-chat-sessions", JSON.stringify(cachedSessions));
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
        const normalizedIncomingMessages = normalizeMessages(newSess.messages);
        const normalizedExistingMessages = normalizeMessages(
          existingSess?.messages || [],
        );
        return {
          ...newSess,
          messages:
            normalizedIncomingMessages.length > 0
              ? normalizedIncomingMessages
              : normalizedExistingMessages,
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
            ? normalizeMessages(action.session.messages)
            : normalizeMessages(existingSession?.messages || []),
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
            const messages = normalizeMessages([...s.messages, action.message]);
            return {
              ...s,
              messages,
              updatedAt: Date.now(),
              title:
                s.title === "New Engineering Session" && messages.length > 0
                  ? titleFromMessages(messages)
                  : cleanSessionTitle(s.title),
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
            ? {
                ...s,
                title: cleanSessionTitle(action.title),
                updatedAt: Date.now(),
              }
            : s,
        ),
      };
      break;

    case "START_STREAMING":
      newState = setSessionStreamState(state, action.sessionId, (streamState) => ({
        ...streamState,
        isStreaming: true,
        streamedText: action.streamId ? streamState.streamedText : "",
        streamActivity: action.streamId ? streamState.streamActivity : [],
        activeStreamId: action.streamId || null,
      }));
      break;

    case "ADD_STREAM_ACTIVITY":
      newState = setSessionStreamState(state, action.sessionId, (streamState) => ({
        ...streamState,
        streamActivity: [
          ...streamState.streamActivity,
          {
            ...action.entry,
            id: Math.random().toString(36).substring(7),
            timestamp: Date.now(),
          },
        ].slice(-12),
      }));
      break;

    case "APPEND_STREAM_TOKEN":
      newState = setSessionStreamState(state, action.sessionId, (streamState) => ({
        ...streamState,
        streamedText: streamState.streamedText + action.text,
      }));
      break;

    case "SET_ACTIVE_TOOL":
      newState = setSessionStreamState(state, action.sessionId, (streamState) => ({
        ...streamState,
        activeTool: {
          name: action.name,
          preview: action.preview,
          percentage: action.percentage,
        },
      }));
      break;

    case "SET_TOOL_PROGRESS":
      newState = setSessionStreamState(state, action.sessionId, (streamState) => ({
        ...streamState,
        activeTool: streamState.activeTool
          ? {
              ...streamState.activeTool,
              percentage: action.percentage,
              preview: action.message,
            }
          : {
              name: "Tool activity",
              preview: action.message,
              percentage: action.percentage,
            },
      }));
      break;

    case "CLEAR_ACTIVE_TOOL":
      newState = setSessionStreamState(state, action.sessionId, (streamState) => ({
        ...streamState,
        activeTool: null,
      }));
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
              title = titleFromMessages(normalizeMessages(action.messages));
            }
            return {
              ...s,
              messages: normalizeMessages(action.messages),
              title: cleanSessionTitle(title),
            };
          }
          return s;
        }),
      };
      break;

    case "END_STREAMING":
      newState = setSessionStreamState(state, action.sessionId, (streamState) => ({
        ...streamState,
        isStreaming: false,
        activeTool: null,
        streamedText: "",
        streamActivity: [],
        activeStreamId: null,
      }));
      newState = {
        ...newState,
        sessions: action.finalSession
          ? newState.sessions.map((s) =>
              s.sessionId === action.finalSession!.sessionId
                ? action.finalSession!
                : s,
            )
          : newState.sessions,
      };
      break;

    case "QUEUE_PROMPT":
      newState = {
        ...state,
        promptQueue: [...state.promptQueue, action.prompt],
      };
      break;

    case "DEQUEUE_PROMPT": {
      let removed = false;
      newState = {
        ...state,
        promptQueue: state.promptQueue.filter((prompt) => {
          if (!removed && prompt.sessionId === action.sessionId) {
            removed = true;
            return false;
          }
          return true;
        }),
      };
      break;
    }

    case "CLEAR_STREAM_ID":
      newState = setSessionStreamState(state, action.sessionId, (streamState) => ({
        ...streamState,
        activeStreamId: null,
      }));
      break;
  }

  if (action.type === "DELETE_SESSION") {
    removeCachedSession(action.sessionId);
  } else {
    writeCachedSessions(newState.sessions);
  }
  return newState;
}

interface ChatContextProps {
  state: ChatState;
  createSession: (
    workspace?: string,
    workspaceId?: string,
  ) => Promise<string | undefined>;
  selectSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  sendMessage: (
    content: string,
    attachments?: string[],
    isQueuedExecution?: boolean,
    targetSessionId?: string,
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
      const localSessions = readCachedSessions();

      const backendSessionIds = new Set(
        compactSessions.map((session) => session.sessionId),
      );
      const sessions: ChatSession[] = compactSessions.map((cs) => {
        const matched = Array.isArray(localSessions)
          ? localSessions.find((ls) => ls?.sessionId === cs.sessionId)
          : undefined;

        const normalizedMatchedMessages = normalizeMessages(
          matched?.messages || [],
        );
        let title = cleanSessionTitle(cs.title);
        if (
          title === "Untitled" &&
          matched &&
          cleanSessionTitle(matched.title) !== "Untitled"
        ) {
          title = cleanSessionTitle(matched.title);
        }
        if (title === "Untitled" && normalizedMatchedMessages.length > 0) {
          title = titleFromMessages(normalizedMatchedMessages);
        }

        return {
          sessionId: cs.sessionId,
          title,
          createdAt: cs.createdAt,
          updatedAt: cs.updatedAt,
          messages: normalizedMatchedMessages,
          isActive: matched ? matched.isActive : false,
          workspaceId: workspaceId ?? matched?.workspaceId ?? null,
          workspacePath: matched?.workspacePath ?? null,
        };
      });

      const locallyCachedOnlySessions = localSessions.filter((session) => {
        if (!session?.sessionId || backendSessionIds.has(session.sessionId)) {
          return false;
        }

        if (!workspaceId) return true;
        return session.workspaceId === workspaceId;
      });

      dispatch({
        type: "SET_SESSIONS",
        sessions: dedupeSessionsById([
          ...sessions,
          ...locallyCachedOnlySessions,
        ]),
      });
    } catch (err) {
      console.error(
        "Failed to sync sessions with backend, falling back to localStorage",
        err,
      );
      const fallbackSessions = readCachedSessions().filter((session) => {
        if (!workspaceId) return true;
        return session.workspaceId === workspaceId;
      });
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
    async (workspace?: string, workspaceId?: string) => {
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

          dispatch({
            type: "CREATE_SESSION",
            session: {
              ...session,
              workspaceId: workspaceId ?? session.workspaceId ?? null,
              workspacePath: workspace ?? session.workspacePath ?? null,
            },
          });
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
      targetSessionId?: string,
    ) => {
      const sessionId = targetSessionId || state.activeSessionId;
      if (!sessionId) return;

      const sessionStreamState = state.streamStates[sessionId];
      const isSessionStreaming = Boolean(sessionStreamState?.isStreaming);
      const isSlashCommand = content.trim().startsWith("/");
      if (!isSlashCommand && isSessionStreaming) {
        const userMsg: ChatMessage = {
          id: Math.random().toString(36).substring(7),
          role: "user",
          content,
          timestamp: Date.now(),
          traceId: "tr-" + Math.random().toString(36).substring(7),
        };
        dispatch({ type: "ADD_MESSAGE", sessionId, message: userMsg });
        dispatch({ type: "QUEUE_PROMPT", prompt: { sessionId, content, attachments } });
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

      const activeSession = state.sessions.find(
        (session) => session.sessionId === sessionId,
      );
      const workspaceId = activeSession?.workspaceId || undefined;
      const requestedTitle = titleFromSlashCommand(content);

      dispatch({ type: "START_STREAMING", sessionId });
      dispatch({
        type: "ADD_STREAM_ACTIVITY",
        sessionId,
        entry: {
          kind: "status",
          title: "Hermes is preparing a response",
          detail: "Waiting for the first response event.",
        },
      });

      let accumulatedText = "";
      try {
        const stream = agentService.sendMessage(
          sessionId,
          content,
          attachments,
        );
        for await (const event of stream) {
          if (event.type === "stream_start") {
            dispatch({
              type: "START_STREAMING",
              sessionId,
              streamId: event.streamId,
            });
            dispatch({
              type: "ADD_STREAM_ACTIVITY",
              sessionId,
              entry: {
                kind: "status",
                title: "Response stream connected",
                detail: event.streamId ? `Stream ${event.streamId}` : undefined,
              },
            });
          } else if (event.type === "token") {
            accumulatedText += event.text;
            dispatch({ type: "APPEND_STREAM_TOKEN", sessionId, text: event.text });
          } else if (event.type === "tool") {
            dispatch({
              type: "SET_ACTIVE_TOOL",
              sessionId,
              name: event.name,
              preview: event.preview,
              percentage: event.percentage,
            });
            dispatch({
              type: "ADD_STREAM_ACTIVITY",
              sessionId,
              entry: {
                kind: "tool",
                title: event.name ? `Calling ${event.name}` : "Calling a tool",
                detail: event.preview || undefined,
                percentage: event.percentage,
              },
            });
          } else if (event.type === "progress") {
            dispatch({
              type: "SET_TOOL_PROGRESS",
              sessionId,
              percentage: event.percentage,
              message: event.detail || event.message,
            });
            dispatch({
              type: "ADD_STREAM_ACTIVITY",
              sessionId,
              entry: {
                kind: "progress",
                title: event.title,
                detail: event.detail,
                percentage: event.percentage,
              },
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
              content:
                accumulatedText.trim() ||
                "Hermes ended the chat turn without returning a response.",
              timestamp: Date.now(),
              traceId: accumulatedText.trim()
                ? "tr-" + Math.random().toString(36).substring(7)
                : null,
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

            dispatch({ type: "END_STREAMING", sessionId, finalSession });
            if (requestedTitle) {
              dispatch({
                type: "UPDATE_SESSION_TITLE",
                sessionId,
                title: requestedTitle,
              });
              await refreshSessions(workspaceId);
            }
          } else if (event.type === "error") {
            console.error(event.message);
            dispatch({
              type: "ADD_STREAM_ACTIVITY",
              sessionId,
              entry: {
                kind: "error",
                title: "Stream error",
                detail: event.message,
              },
            });
            dispatch({ type: "CLEAR_ACTIVE_TOOL", sessionId });

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
            dispatch({ type: "END_STREAMING", sessionId, finalSession });
          }
        }
      } catch (err) {
        console.error("Failed to send message", err);
        dispatch({ type: "CLEAR_ACTIVE_TOOL", sessionId });
        dispatch({ type: "END_STREAMING", sessionId });
      }
    },
    [refreshSessions, state.activeSessionId, state.sessions, state.streamStates],
  );

  const cancelActiveStream = useCallback(async () => {
    if (!state.activeSessionId) return;
    await agentService.cancelStream(state.activeSessionId);
    dispatch({ type: "CLEAR_STREAM_ID", sessionId: state.activeSessionId });
  }, [state.activeSessionId]);

  useEffect(() => {
    const nextPrompt = state.promptQueue.find(
      (prompt) => !state.streamStates[prompt.sessionId]?.isStreaming,
    );
    if (!nextPrompt) return;

    dispatch({ type: "DEQUEUE_PROMPT", sessionId: nextPrompt.sessionId });
    sendMessage(
      nextPrompt.content,
      nextPrompt.attachments,
      true,
      nextPrompt.sessionId,
    );
  }, [state.promptQueue, state.streamStates, sendMessage]);

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
