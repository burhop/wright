import { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { ChatSession, ChatMessage } from './types';
import agentService from '../services/agent-service';

export interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string | null;
  isStreaming: boolean;
  activeTool: { name: string; preview: string } | null;
  streamedText: string;
}

type ChatAction =
  | { type: 'SET_SESSIONS'; sessions: ChatSession[] }
  | { type: 'SELECT_SESSION'; sessionId: string }
  | { type: 'CREATE_SESSION'; session: ChatSession }
  | { type: 'DELETE_SESSION'; sessionId: string }
  | { type: 'ADD_MESSAGE'; sessionId: string; message: ChatMessage }
  | { type: 'UPDATE_SESSION_TITLE'; sessionId: string; title: string }
  | { type: 'START_STREAMING' }
  | { type: 'APPEND_STREAM_TOKEN'; text: string }
  | { type: 'SET_ACTIVE_TOOL'; name: string; preview: string }
  | { type: 'CLEAR_ACTIVE_TOOL' }
  | { type: 'END_STREAMING'; finalSession: ChatSession };

const initialState: ChatState = {
  sessions: [],
  activeSessionId: null,
  isStreaming: false,
  activeTool: null,
  streamedText: '',
};

function chatReducer(state: ChatState, action: ChatAction): ChatState {
  let newState = state;

  switch (action.type) {
    case 'SET_SESSIONS':
      newState = {
        ...state,
        sessions: action.sessions,
        activeSessionId: action.sessions.find(s => s.isActive)?.sessionId || action.sessions[0]?.sessionId || null,
      };
      break;

    case 'SELECT_SESSION':
      newState = {
        ...state,
        activeSessionId: action.sessionId,
        sessions: state.sessions.map((s) => ({
          ...s,
          isActive: s.sessionId === action.sessionId,
        })),
      };
      break;

    case 'CREATE_SESSION':
      newState = {
        ...state,
        activeSessionId: action.session.sessionId,
        sessions: [
          action.session,
          ...state.sessions.map((s) => ({ ...s, isActive: false })),
        ],
      };
      break;

    case 'DELETE_SESSION':
      const remainingSessions = state.sessions.filter((s) => s.sessionId !== action.sessionId);
      let nextActiveId = state.activeSessionId;
      if (state.activeSessionId === action.sessionId) {
        nextActiveId = remainingSessions[0]?.sessionId || null;
      }
      newState = {
        ...state,
        sessions: remainingSessions.map((s) => ({ ...s, isActive: s.sessionId === nextActiveId })),
        activeSessionId: nextActiveId,
      };
      break;

    case 'ADD_MESSAGE':
      newState = {
        ...state,
        sessions: state.sessions.map((s) => {
          if (s.sessionId === action.sessionId) {
            const messages = [...s.messages, action.message];
            return {
              ...s,
              messages,
              updatedAt: Date.now(),
              title: s.title === 'New Engineering Session' && messages.length > 0
                ? (messages[0].content.length > 30 ? `${messages[0].content.substring(0, 27)}...` : messages[0].content)
                : s.title,
            };
          }
          return s;
        }),
      };
      break;

    case 'UPDATE_SESSION_TITLE':
      newState = {
        ...state,
        sessions: state.sessions.map((s) =>
          s.sessionId === action.sessionId ? { ...s, title: action.title, updatedAt: Date.now() } : s
        ),
      };
      break;

    case 'START_STREAMING':
      newState = {
        ...state,
        isStreaming: true,
        streamedText: '',
      };
      break;

    case 'APPEND_STREAM_TOKEN':
      newState = {
        ...state,
        streamedText: state.streamedText + action.text,
      };
      break;

    case 'SET_ACTIVE_TOOL':
      newState = {
        ...state,
        activeTool: { name: action.name, preview: action.preview },
      };
      break;

    case 'CLEAR_ACTIVE_TOOL':
      newState = {
        ...state,
        activeTool: null,
      };
      break;

    case 'END_STREAMING':
      newState = {
        ...state,
        isStreaming: false,
        activeTool: null,
        streamedText: '',
        sessions: state.sessions.map((s) =>
          s.sessionId === action.finalSession.sessionId ? action.finalSession : s
        ),
      };
      break;
  }

  localStorage.setItem('wright-chat-sessions', JSON.stringify(newState.sessions));
  return newState;
}

interface ChatContextProps {
  state: ChatState;
  createSession: () => Promise<void>;
  selectSession: (sessionId: string) => void;
  deleteSession: (sessionId: string) => Promise<void>;
  sendMessage: (content: string) => Promise<void>;
}

const ChatContext = createContext<ChatContextProps | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  useEffect(() => {
    const stored = localStorage.getItem('wright-chat-sessions');
    if (stored) {
      try {
        const sessions: ChatSession[] = JSON.parse(stored);
        dispatch({ type: 'SET_SESSIONS', sessions });
      } catch (err) {
        console.error('Failed to parse sessions from localStorage', err);
      }
    }
  }, []);

  const createSession = async () => {
    const session = await agentService.createSession();
    dispatch({ type: 'CREATE_SESSION', session });
  };

  const selectSession = (sessionId: string) => {
    dispatch({ type: 'SELECT_SESSION', sessionId });
  };

  const deleteSession = async (sessionId: string) => {
    await agentService.deleteSession(sessionId);
    dispatch({ type: 'DELETE_SESSION', sessionId });
  };

  const sendMessage = async (content: string) => {
    if (!state.activeSessionId) return;
    const sessionId = state.activeSessionId;

    const userMsg: ChatMessage = {
      id: Math.random().toString(36).substring(7),
      role: 'user',
      content,
      timestamp: Date.now(),
      traceId: 'tr-' + Math.random().toString(36).substring(7),
    };
    dispatch({ type: 'ADD_MESSAGE', sessionId, message: userMsg });
    dispatch({ type: 'START_STREAMING' });
    
    try {
      const stream = agentService.sendMessage(sessionId, content);
      for await (const event of stream) {
        if (event.type === 'token') {
          dispatch({ type: 'APPEND_STREAM_TOKEN', text: event.text });
        } else if (event.type === 'tool') {
          dispatch({ type: 'SET_ACTIVE_TOOL', name: event.name, preview: event.preview });
        } else if (event.type === 'done') {
          dispatch({ type: 'END_STREAMING', finalSession: event.session });
        } else if (event.type === 'error') {
          console.error(event.message);
          dispatch({ type: 'CLEAR_ACTIVE_TOOL' });
        }
      }
    } catch (err) {
      console.error('Failed to send message', err);
      dispatch({ type: 'CLEAR_ACTIVE_TOOL' });
    }
  };

  return (
    <ChatContext.Provider value={{ state, createSession, selectSession, deleteSession, sendMessage }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}
